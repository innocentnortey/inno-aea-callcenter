# Plan — [AEA-58] browser journeys: Playwright against the production build

**Status:** planned — READY (refreshed against `main` `3725c90`). Every import this slice needs is on `main`: AEA-57's
harness (merged `bd79a29`), AEA-49's frontend serving (merged `543cb04`), AEA-23's `openapi_check`, AEA-44's login
sessions, and since the third refresh AEA-30's demo clock and demo service (merged `cf8fd78`) and AEA-40's chat services
and CON-1/CON-2 routes (merged `f466ff7`). The UX-4 gate is signed (checklist §4b, Innocent ✓ 2026-10-21). What is
**not** on `main` is reported at run time as *blocked* steps, never imported and never passed: `run_graph` /
`reply_composer` (AEA-51: the turn, and, because `SessionService.open` and `.thread` build the settled view through
`reply_composer`, every `startChatSession` / `getChatThread` too), and the UX session's selector contract
`docs/plans/ux-join/selectors.md` (every on-screen step; see §8 R-1).
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/58 (identical to
`docs/plans/tickets/AEA-58.md`) · **Base revision:** `main` `3725c90` · **Wave:** 3 · **Lane:** build-loop ·
**Risk:** none (no `risk::security`: plan → implement with tests → review; no frozen tests) · **Gate:** `gate::ux4` (met)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 · **Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** the one the orchestrator creates (suggested `aea-58-browser-journeys` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-58`), cut from `main` at or after `3725c90`.

**Refresh log.** First written against `35aefdd`. Refreshed 2026-10-21 against `68b1412` (merges since: AEA-17, AEA-18,
AEA-21, AEA-27, AEA-28, AEA-34, AEA-38, AEA-59, AEA-02b, AEA-03b). Checked and unchanged since `35aefdd`:
`tests/journeys/support/**`, `tests/journeys/affected.py`, `tests/journeys/j1/test_aea_57.py`, `tests/conftest.py`,
`tests/api/openapi_check.py`, `src/meridian/web/{frontend,middleware,app,deps}.py`, `routes/auth.py`,
`src/meridian/config.py`, `apps/web/**`, `pyproject.toml`, `uv.lock`; web.md and data.md gained only AEA-03b's two
history texts (not used here). `web/container.py` gained the AEA-17/18/27/28 hunks (lazy Anthropic client, Jev client and
factory, `identity_service`, `scheduling`): they make no request at start-up and are replaced at the provider boundary by
AEA-57's `scripted_overrides`, so nothing in this plan changes. Still **not** on `main`: AEA-30 (`demo_clock`), AEA-40
(chat routes), AEA-51 (`run_graph`, `reply_composer`) and `docs/plans/ux-join/selectors.md` (no `data-login-message`,
`data-chat-state`, `data-speaker` or `data-block-type` hook exists in `apps/web/src` either). What changed in this plan:
step 13's exact ICM row and DO-3 insertion point (the files moved on), §7's note on reds already on `main`, §8 R-9 and
R-10.

**Second refresh, 2026-10-21, against `c9b17ea`** (merges since `68b1412`: AEA-43 demo routes `db9ef50`, AEA-29 cases and
handoff `d3facfe`, AEA-24 eval harness, AEA-50 deploy image, AEA-54 docs, the `test_spine` stale-row fix `f63ec50`).
Re-checked and unchanged: `tests/journeys/support/**` (incl. `NEED_OWNERS`, `OPERATION_OWNERS`: all 30 operations
mapped), `tests/conftest.py`, `tests/api/openapi_check.py`, `src/meridian/web/{frontend,middleware,app,deps}.py`,
`routes/auth.py`, `config.py`, `apps/web/**`, `pyproject.toml` (no `playwright` yet), `uv.lock`, `docs/plans/ux-join/`
(still no `selectors.md`; no `data-login-message` / `data-chat-state` / `data-speaker` / `data-block-type` hook in
`apps/web/src`), the stage7 addenda this plan cites (only `cases.md` changed), D-4…D-15, the ticket and its slice-plan
row. `web/container.py` gained the `register_cases` (AEA-29) and `register_demo_routes` (AEA-43) hunks: `getDemoClock`,
`getStaffing`, `listDemoInbox`, `setStaffing`, `resetDemo` are now **routed**, while `register_demo` (AEA-30),
`register_chat` (AEA-40) and `register_graph` (AEA-51) are still no-ops. The step-13 anchors (area-map row `3+` ending
`; the rest planned`, the ICM row at `2788964`, DO-3 §9's `browser/ (AEA-58)` and *Built on `main`* sentence) are
unchanged. What changed in this plan: §4.7 (the API calls the production shell makes), §5 *must not* (no `networkidle`
after sign-in), §7 (reds on `main`, capture row C-10), §8 R-2, R-9, R-11, R-12, §9 *Gates*.

**Third refresh, 2026-10-21, against `3725c90`** (merges since `c9b17ea`: AEA-30 demo clock and scheduler `cf8fd78`,
AEA-40 sessions and turns `f466ff7`, AEA-35b specialist task types, the AEA-29 typing-only test fix). Re-checked with
`git diff c9b17ea 3725c90` and unchanged: `tests/journeys/support/**`, `tests/journeys/j1/test_aea_57.py` (the §4.9
constants), `tests/journeys/{README.md,affected.py}`, `tests/conftest.py`, `tests/api/openapi_check.py`,
`src/meridian/web/{frontend,middleware,app,deps}.py`, `routes/auth.py`, `config.py`, `policy/limits.py`, `apps/web/**`,
`pyproject.toml` (still no `playwright`), `uv.lock`, the ticket, the slice plan, `stage7-signoff.md` D-4…D-15, every
stage7 addendum this plan cites, and `docs/plans/ux-join/` (still no `selectors.md`; still no `data-login-message`,
`data-chat-state`, `data-speaker` or `data-block-type` hook in `apps/web/src`). Changed on `main`: `web/container.py`
`register_demo` (binds `demo_clock`, `demo_service`, the scheduler thread) and `register_chat` (binds `session_service`,
`turn_service`, includes `routes/chat.py`; `reply_composer` and `run_graph` are resolved lazily and raise
`RuntimeError("not bound: <key>")` until AEA-51), new `web/routes/chat.py`, `web/schemas/chat.py`, and AEA-40's and
AEA-30's own journey files (`j1/test_aea_40.py`, `j9/test_aea_40.py`, `j6/test_aea_30.py`, `j7/test_aea_30.py`; not
edited here). Consequence found while re-reading: the production shell's own `startChatSession` after sign-in now
reaches a **mounted** route whose service calls the unbound `reply_composer` and answers `500 {"request_id": …}` (an
undocumented status), so the old PA-2 rule would turn every signed-in browser test red until AEA-51 merges. Added PA-4
(§3), `UNBOUND_500_NEEDS` and `teardown_failures` (step 3), the close rule (step 4), the counters (step 7), four
self-checks (step 9), the 3e wording (AEA-40-1 is on `main`), §5 *must not*, §7 C-10 and step 13's expected owners, §8
R-2, R-11, R-12, R-13 and §9. The step-13 anchors (area-map row `3+` ending `; the rest planned`, the ICM row at
`2788964`, DO-3 §9's `browser/ (AEA-58)` and *Built on `main`* sentence) are unchanged.

---

## 1. Goal and sources

### Goal (issue *What to build*, in short)

> "A reviewer runs one command. It builds UX-4's React app the production way, starts the **real** FastAPI app (built
> from `web/container.py`) on an ephemeral port over a disposable copy of the issued scheduling DB, with the
> deterministic scripted model adapter at the provider boundary, and drives system Chrome through it" — guard redirect,
> sign in through SCR-12, start a chat and take one turn, refresh and resume, sign out again; every `/api/*` response
> validated with AEA-23's one checker; the issued DB hash unchanged; an evidence record at level
> **`integrated with a scripted model`**.

**What it does, concretely (input → process → output).** The reviewer runs
`npm --prefix apps/web run build && npm --prefix apps/web run check:dist && perl -e 'alarm 300; exec @ARGV' uv run pytest -m journey tests/journeys/browser tests/journeys/j1/test_aea_58.py tests/journeys/j9/test_aea_58.py --browser-channel chrome`.
For each browser test, a session fixture checks `apps/web/dist` (index present, `check-dist.mjs` passes, index hash
printed) and starts system Chrome once. A per-test fixture composes AEA-57's harness parts (socket guard, log tap,
temp environment, scripted model, uvicorn launcher) **with** `MERIDIAN_WEB_DIST_DIR=<dist>` and
`MERIDIAN_REQUIRE_FRONTEND=true`, so the real app serves the build. Chrome opens `/`; the server answers
`303 → /login?return_to=%2F&reason=none`; the test signs in through SCR-12's form, takes the J-1 turn, reloads, and
signs out. Every `/api/*` response Chrome received is turned into an `httpx.Response` and checked by
`assert_response_matches`. Output: pass / fail / *blocked-on <owner>* per named step, and with
`--journey-record=AEA-58` the file `docs/testing/journeys/<date>-AEA-58.md` plus screenshots beside it.

### Context

The integrated-journeys rule (Riverside lesson) requires browser → real server → disposable DB, with the real login.
AEA-57 landed the API-level harness (merged `bd79a29`; its own record shows sign-in *blocked-on AEA-30*). AEA-49 serves
`dist` (merged). The UX session's selector contract (`docs/plans/ux-join/selectors.md`, due "before UX-4 sign-off" per
`FOR-UX-SESSION.md` §2) does **not** exist yet, and `apps/web` today has only `data-screen="SCR-1"` and `data-entry`
hooks. So in wave 3 this ticket lands the whole browser harness, and the HTTP-level parts of AC-1, AC-2, AC-8, AC-10 and
AC-11 can pass. Every on-screen step reports *blocked-on UX session* until the contract lands (the ticket's own rule,
AC-16). Since AEA-30 and AEA-40 merged, sign-in and the chat routes exist on the server; the turn and the settled view
(`reply_composer`, `run_graph`) still wait on AEA-51.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-58.md` (AC-1…AC-17, *Agent handoff*) | Everything below |
| Slice plan | `docs/plans/slice-plan.md` §0a (J-1 map row, "J-1 runs in two stages", AEA-62 owns J-2/3/6/8 browser legs), §1 row AEA-58 (blockers 40, 49, 57 + UX-4), §3 rows `tests/journeys/` (58 owns `browser/`; one `j<N>/test_aea_<NN>.py` per ticket), `pyproject.toml`/`uv.lock` (one line + lock; that merge runs the full suite), `apps/web/**` (read only) | Owned paths, the one-dependency-line rule |
| Amendments | `docs/plans/ux-join/backend-amendments.md` AEA-58-1…4 (applied in the ticket); `FOR-UX-SESSION.md` §3 (selector minimum), §4 (build recipe), §5 (real-backend mode); decisions D-4 (WEB-1 A), D-7 (separate throttle line), D-8 (start fresh after sign-in again) in `docs/plans/stage7-signoff.md` | Selector keys; AC-5 and AC-6 wording |
| Rules | `.claude/rules/integrated-journeys.md` §2, §3 rules 1–3, 5–7, §4 (levels, nine record fields), §5, §6 (AEA-58 row); `build-loop-test-scope.md` + *AEA addition*; `context-maintenance.md`; workspace `code-structure.md`, `code-design-solid-modularity.md` | Harness shape, record, who runs what, context rows in the same change |
| Requirements | PRD R-48 (every route except login and `/healthz` refuses unsigned), R-41 (rate limits); US-28 (one demo login, switch roles, refresh) | AC-2, AC-5, AC-6 |
| Component contracts (DO-4 + stage7 addenda; addenda win) | `stage7/web.md` §2 (cookie `mhc_session`, HttpOnly, SameSite=Lax, no Secure locally), §5 (`login_rejects_per_ip`, `429 LOGIN_RATE_LIMITED` + `Retry-After`), §6 (gate order, `PublicPaths`, the 303 with `return_to=<path+query>`), §10 (`request`, `auth_event` records), §12 (`register_frontend`, missing build fails start-up when `require_frontend`), §13 (`assert_response_matches`, `Contract`, `OperationSpec`), §14 (`SessionService.thread`, AEA-40-1 full history), §15 (`create_app`, `ContainerOverrides`); `stage7/graph-core.md` §12 (`Settings.web_dist_dir`, `require_frontend`); `stage7/data.md` §5–§6 (held-out custody: never read) | §4 below |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` | n/a: deterministic pass/fail; no E-n number (ticket *Evaluation*) |
| Observability contract | DO-6 `docs/design/observability-contract.md` rows WF-1 (records `request`, `conversation`, `turn`), WF-18 (`request`, `auth_event` ok/rejected/logged_out/rate_limited with the opaque session id), WF-19 (`request` with route `spa_fallback` or `/assets/{file}`) | AC-11 |
| Key-metrics registry | DO-7 | n/a: test-only, no record added (ticket *Metrics*) |
| Current code read for this plan | `tests/journeys/support/{plugin,run,env,server,client,db,logtap,steps,record,scripted_model}.py` and `README.md` (AEA-57, on `main`); `tests/journeys/j1/test_aea_57.py`; `tests/journeys/{README.md,affected.py}`; `tests/conftest.py`; `tests/api/openapi_check.py`; `src/meridian/web/{frontend,middleware,app,container,deps}.py`, `routes/auth.py`; `src/meridian/config.py`; `src/meridian/policy/limits.py` (`WebLimits`); `apps/web/{package.json,playwright.config.ts,README.md,scripts/check-dist.mjs,scripts/paths.mjs,src/dev/install.ts}`; `pyproject.toml`; re-read at `68b1412`: `web/container.py` (new hunks), `adapters/sqlite/schema/{00_core,20_spend,90_staff}.sql` (`conversations.demo_session`, `turns.response`, `turns.status`, `staff_sessions.session_id`, `spend_ledger.cost_usd`), `adapters/sqlite/repos_core.py` (stored response = `turns.response`); re-read at `c9b17ea`: `web/container.py` (`register_cases`, `register_demo_routes` hunks; `register_demo`, `register_chat`, `register_graph` still no-ops), `web/routes/demo.py`, `routes/auth.py` (the 401/429 paths precede the clock reading), `tests/journeys/support/steps.py` (owner maps), `tests/journeys/j1/test_aea_49.py` (AEA-49's mock-tested HTTP check; not edited), `apps/web/src/{state/session.tsx,state/demoStatus.tsx,screens/scr01/core/gateway.ts,screens/scr01/core/useChat.ts}` (the shell's own API calls) | §4 |

---

## 2. Boundary

### File map — owned files (the only files the implementer creates or edits)

| File | Create / modify | Responsibility (one sentence) | Target size |
|---|---|---|---|
| `tests/journeys/browser/__init__.py` | create | Package marker; one-line docstring | 1 line |
| `tests/journeys/browser/README.md` | create | The walkthrough recipe (AC-15): build, run, headed, chrome-devtools MCP, records | ~120 lines |
| `tests/journeys/browser/plugin.py` | create | The three fixtures and the two session hooks (summary line, record rewrite) | ≤ 200 |
| `tests/journeys/browser/build.py` | create | Production-build preflight and the Chrome launch wrapper, both failing loudly (AC-1, AC-12) | ≤ 150 |
| `tests/journeys/browser/server.py` | create | Compose AEA-57's harness parts into a run that serves `dist` with `require_frontend=True` | ≤ 120 |
| `tests/journeys/browser/network.py` | create | Record every browser request and `/api/*` exchange; resolve operationIds; validate responses (AC-7, AC-8, PA-4) | ≤ 300 |
| `tests/journeys/browser/selectors.py` | create | **The one selector module** (AC-16): logical keys, contract rows, locator builders, dev-layer markers | ≤ 200 |
| `tests/journeys/browser/pages.py` | create | `Device`, `BrowserPage`, `BrowserRun` (contexts, screenshots, teardown validation) | ≤ 200 |
| `tests/journeys/browser/steps.py` | create | `browser_step`, `sign_in_via_form`, `sign_out_via_shell`, `first_hop`, `page_fetch`, need tuples | ≤ 200 |
| `tests/journeys/browser/record.py` | create | `BrowserSession` (session-wide counts) and the browser values for the AEA-57 evidence record | ≤ 150 |
| `tests/journeys/browser/serve.py` | create | `python -m tests.journeys.browser.serve`: the same server for a hand walkthrough (AC-15) | ≤ 120 |
| `tests/journeys/browser/test_browser_support.py` | create | Self-checks (no Chrome page needed), marked `journey`; one file, keep the test names of step 9 | ≤ 450 (tests hard cap 500) |
| `tests/journeys/j1/test_aea_58.py` | create | J-1 in the browser: AC-1…AC-5, AC-8…AC-11 | ≤ 500 |
| `tests/journeys/j9/test_aea_58.py` | create | J-9 rate-limited login in the browser: AC-6 | ≤ 200 |
| `pyproject.toml` | modify **one line** (dev group) | `"pytest-playwright>=0.10",` | — |
| `uv.lock` | regenerate | `uv add --dev` writes it | — |
| `docs/testing/journeys/<run-date>-AEA-58.md` + folder `docs/testing/journeys/<run-date>-AEA-58/` (PNGs) | create (written by command C-6, then committed) | AC-14 record and its screenshots | generated |
| `.claude/reference/area-map.md` | modify **one cell**: row `3+` *Integration and journeys*, last column | AC-17 | — |
| `.claude/state/icm-progress.md` | modify **one row**: *Integrated-journey protection* (evidence and next cells) | AC-17 | ≤ 400 chars |
| `docs/design/code-design.md` | modify §9 only: the `journeys/` lines of the `tests/` tree and the *Built on `main`* sentence | AC-17 | — |

Not produced by the implementer: `docs/testing/journeys/<date>-wave-3-walkthrough.md` (AC-15's evidence) is written by
the reviewer or the wave-3 walkthrough, following the README this ticket writes.

### Shared surfaces read only (never edit)

`tests/journeys/support/**` (AEA-57), `tests/conftest.py` (AEA-01), `tests/journeys/README.md`,
`tests/journeys/affected.py`, `tests/journeys/__init__.py`, `tests/journeys/j*/__init__.py`, every other
`tests/journeys/j*/test_aea_*.py` (import from `tests/journeys/j1/test_aea_57.py` read-only, §4.9),
`tests/api/openapi_check.py` (AEA-23), `tests/fixtures/**`, `tests/fakes/**`, all of `src/meridian/**`,
`apps/web/**` (read; the build writes only the git-ignored `dist`), `docs/ux/**`,
`docs/ux/03-structure/ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, the briefing, issued data, `docs/archive/`,
`docs/parked/`, `PROJECT-CHECKLIST.md`, `.claude/state/resume.md`, the `Last reconciled:` line of `icm-progress.md`.

### Owned by other slices (do not touch)

`tests/journeys/support/` (AEA-57; a missing helper is a follow-up there, merged first), `tests/journeys/j1/test_aea_40.py`
and `j9/test_aea_40.py` (AEA-40), `routes/chat.py` and `services/{session,turn}.py` (AEA-40), `register_graph` (AEA-51),
`tests/contract/test_openapi_*.py` (AEA-59), later browser legs in `tests/journeys/browser/` for J-2/3/6/8 (AEA-62, wave 4:
it adds files, it does not edit this ticket's), `docs/plans/ux-join/selectors.md` (UX session).

---

## 3. Requirements table

Ticket criteria by ID, then plan-added rows. "Verify" names the exact test. Step names in quotes are the `journey.step`
names the evidence record shows.

| ID | Kind | Requirement (short) | How it is built | Verify (test / command) | Level |
|---|---|---|---|---|---|
| AC-1 | invariant | Only the production build through the real app: `web_dist_dir` = build, `require_frontend=True`, `check:dist` passes, `window.__MHC_DEV_LAYER__` undefined, no dev-panel root | `build.check_production_build` (session fixture `production_build`), `server.open_browser_journey`, page checks | `tests/journeys/j1/test_aea_58.py::test_serves_production_build` (+ session fixture) | integrated with a scripted model |
| AC-2 | failure/refusal | `/`, `/staff/queue`, `/?signedin=1&role=owner` each reach SCR-12 via a server 303 to the exact `Location`; no `/api/*` before sign-in answers 2xx except `login`; at 1280 and 390 | `steps.first_hop`, `network.NetworkLog` | `::test_signed_out_pages_redirect_to_login[chrome-desktop]`, `[chrome-phone]` | integrated (HTTP part); SCR-12 drawn blocked-on UX selector until the contract |
| AC-3 | **journey** | J-1 end to end in the browser: sign in via SCR-12 → `return_to` page; greeting; J-1 turn's reply; reload shows greeting, customer turn, reply in order; one `conversations` row owned by the login session; one completed turn with the CON-2 `turn_id`; visible reply = stored text blocks; still one of each after reload; greeting after reload: AEA-40-1 is on `main` (`f466ff7`; `SessionService.thread` puts the greeting first, `turn_id == "greeting"`), so it is asserted and never reported *blocked by AEA-40*; it still needs `reply_composer` (AEA-51) | `steps.sign_in_via_form`, `selectors`, `network`, `run.db` | `::test_j1_login_turn_refresh_resume[chrome-desktop]`, `[chrome-phone]` | **integrated with a scripted model** |
| AC-4 | invariant | Reload sends `getChatThread` for the same `thread_id`, no second `startChatSession` / `submitTurn` | `NetworkLog.operations(since=…)` | `::test_reload_resumes_without_new_session[chrome-desktop]`, `[chrome-phone]` | integrated |
| AC-5 | failure/refusal | Signed in, `/staff/queue` answers 200 (no 303); after "Sign out" (`logout`), reload `/` → 303; page `getChatThread` → 401 `UNAUTHENTICATED` (OpenAPI-valid); sign in again → exactly one new `startChatSession`; earlier `thread_id` → 404 `SESSION_NOT_FOUND` | `steps.sign_out_via_shell`, `steps.page_fetch` | `::test_sign_out_restores_the_guard[chrome-desktop]`, `[chrome-phone]` | integrated |
| AC-6 | failure/refusal | J-9: own server; wrong pair → refusal line, password cleared, username kept; after `Limits.web.login_rejects_per_ip` rejects the right pair → 429 `LOGIN_RATE_LIMITED`, throttle line via `[data-login-message=rate-limited]`, no `mhc_session` cookie | own `browser_journey` per test (fresh limiter) | `tests/journeys/j9/test_aea_58.py::test_rate_limited_login_throttle_line[chrome-desktop]`, `[chrome-phone]` | integrated; throttle line blocked-on UX session until in `dist` and `selectors.md` |
| AC-7 | invariant | Every `/api/*` response in AC-2…AC-6 validates via `assert_response_matches` against its operationId resolved from `Contract.operations` path templates; no undocumented status; SSE: status + `text/event-stream` only | `network.validate_exchanges`, run in `BrowserRun.close()` (teardown of every browser test); session-end summary line | every browser test's teardown + `test_browser_support.py::test_operation_resolver_covers_every_operation`, `::test_validation_rejects_undocumented_status` | integrated |
| AC-8 | negative | No navigation carries `signedin`, `role`, `scenario`, `staffing`, `ex`, `delay` (except the deliberate probe); every request to the server's own `127.0.0.1:<port>`; 4019/5184 never bound or requested; scripted adapter is the only model adapter | `NetworkLog.origins`, `NetworkLog.dev_param_hits`, launcher port, `run.models` | `::test_no_dev_params_or_foreign_hosts` | integrated |
| AC-9 | negative | Demo password and the `mhc_session` value absent from the record, screenshot names, test ids, server logs, pytest output; cookie HttpOnly (not in `document.cookie`), SameSite=Lax; "Show password" never ticked | counts-only assertions (never the value in an assert expression) | `::test_secrets_absent_from_evidence` | integrated |
| AC-10 | negative | Issued DB SHA-256 equal before and after; no file of this ticket opens held-out paths | `support.db.sha256_file`, `ISSUED_DB`; static scan | `::test_issued_db_unchanged`; `test_browser_support.py::test_no_heldout_paths_in_browser_files`; `grep -rn heldout tests/journeys/browser tests/journeys/j1/test_aea_58.py tests/journeys/j9/test_aea_58.py` prints nothing | integrated (hash); static (grep) |
| AC-11 | capture | WF-18 `auth_event` `ok` at sign-in and `logged_out` at sign-out with the same opaque `session_id` (and `rejected`, `rate_limited` in AC-6); WF-19 `request` records with route `spa_fallback` for `/` and `/login`, `/assets/{file}` for assets, `caller_role` `anonymous` before sign-in; WF-1 `conversation` and `turn` for AC-3's thread and turn | `run.logs.wait_for` by `X-Request-ID`; `run.db` | `::test_browser_path_records`; the J-9 test's "9e records" step | integrated |
| AC-12 | failure/refusal | Missing build → error (not skip) naming `npm --prefix apps/web run build` and `MERIDIAN_REQUIRE_FRONTEND`; no Chrome on the channel → error naming `--browser-channel <channel>` | `build.BrowserPrerequisiteError` raised in session fixtures | command C-7 (`MERIDIAN_WEB_DIST_DIR=$(mktemp -d)`); `test_browser_support.py::test_missing_build_message_names_build_command`, `::test_missing_build_refuses_server_start`, `::test_missing_chrome_channel_errors_with_flag_name` | static |
| AC-13 | invariant | One runner: `-m journey --collect-only` lists AEA-57's and AEA-58's journeys together; reviewer command passes on the integrated branch; `git status --porcelain apps/web` empty after | `pytest_plugins` in the two test files; build outside the test | commands C-5, C-6, C-8 | integrated (the run) |
| AC-14 | capture | Record with all nine fields: claim, level, revision (SHA + `agent_version`), environment (server command, DB source, build hash, scripted adapter, Chrome channel + version), command, result per journey, evidence location (screenshots beside), limitations, blocked-by | AEA-57's `build_record_data` + `render_record` + `record_path`, browser values from `record.browser_record_values` | the file from C-6; `test_browser_support.py::test_browser_record_fields` | integrated |
| AC-15 | invariant | `tests/journeys/browser/README.md` lets a fresh agent walk J-1 by hand | README + `serve.py` | reviewer follows it once → `docs/testing/journeys/<date>-wave-3-walkthrough.md` | integrated |
| AC-16 | invariant | Selectors only from `selectors.md`; each row cites its row and the file's revision; no test file holds a selector string; a missing state → `blocked-on UX session` for that step only | `selectors.py` is the only file calling `locator(` / `get_by_`; `browser_step(selectors=…)` | `grep -rnE "locator\(\|get_by_" tests/journeys --include=*.py \| grep -v tests/journeys/browser/selectors.py` prints nothing; `test_browser_support.py::test_selector_rows_cite_contract`, `::test_no_selector_strings_outside_module` | static |
| AC-17 | regression/context | area-map row, icm-progress row, DO-3 §9 tree; `pytest-playwright` = one dev line + lock; that merge runs the full suite | step 13 | `git diff --stat main...HEAD` | — |
| PA-1 | invariant (plan-added) | A browser test's teardown fails when any `/api/*` exchange fails validation, even when the test was skipped as *blocked* (a blocked step never hides a contract break that already happened) | `BrowserRun.close()` raises after closing every context | `test_browser_support.py::test_validation_rejects_undocumented_status` (unit) and every browser test | mock-tested (unit) |
| PA-2 | invariant (plan-added) | Responses from operations whose route is not mounted yet (sibling ticket unmerged) are counted as *unrouted, blocked-on <owner>* and never validated as passes or failures | `validate_exchanges` uses AEA-57's `missing_needs(container, app, (), (op,))` | `test_browser_support.py::test_unrouted_operations_counted_not_validated` | mock-tested |
| PA-3 | invariant (plan-added) | After the scripted turn, the script reports no `invalid_output` / `exhausted` call and every queue is empty (same as AEA-57 PA-3) | `run.script.problems()`, `remaining()` | inside `::test_j1_login_turn_refresh_resume` step "3c one turn" | integrated |
| PA-4 | invariant (plan-added) | A `500` from a **mounted** chat operation is counted as *unbound, blocked-on <owner>* only when that operation's declared service needs (`UNBOUND_500_NEEDS`: `startChatSession`, `getChatThread`, `submitTurn`) are not all bound; every other 500 fails the teardown; under `--journeys-strict` an unrouted (PA-2) or unbound exchange fails the teardown too | `network.validate_exchanges` step 2b, `network.teardown_failures`, `BrowserRun.close()` | `test_browser_support.py::test_unbound_service_500_counted_not_validated`, `::test_mounted_500_with_bound_needs_fails`, `::test_strict_fails_on_blocked_exchanges`, `::test_unbound_needs_match_aea57_scripts` | mock-tested |

**WP-N worked pair:** none applies. J-1's turn is AEA-57's synthetic no-task turn (planner `talk`, classifier `normal`,
responder text), imported unchanged from `tests/journeys/j1/test_aea_57.py` (§4.9). **The single `[journey]` criterion
is AC-3**, level `integrated with a scripted model`.

### Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| Every browser response carries `X-Request-ID` (pages and assets too) | web.md §6 step 1 | implicit | added: AC-11 test asserts the header on the 303 hop, `/login` and one asset | step 11 |
| `return_to` keeps the query string (`/?signedin=1&role=owner` → `return_to=%2F%3Fsignedin%3D1%26role%3Downer`) | web.md §6 (WEB-28) | yes (AC-2 "encoded path+query") | in-ticket; exact literal in §5 step 10 | step 10 |
| The 429 carries `Retry-After` | web.md §5; `routes/auth.py` | partly | added assert in AC-6 | step 12 |
| `auth_event` never carries username, password or cookie | DO-6 WF-18; web.md §10 | via AC-9 | in-ticket (AC-9 scans server logs) | step 10 |
| Redaction of stored text | CAP-10, CAP-11 | excluded | other-ticket (AEA-23, AEA-49) | — |
| SSE frame bodies | AEA-41, AEA-59 | excluded | other-ticket | — |
| J-2, J-3, J-6, J-8 in the browser | slice plan §0a | excluded | other-ticket AEA-62 | — |
| Live models | integrated-journeys rule 4 | excluded | other-ticket AEA-61 | — |
| Selector contract for every asserted state | FOR-UX-SESSION §3 | yes (AC-16) | blocked-on UX session (run-time; reported per step) | §8 R-1 |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (test code; drives WF-1, WF-18, WF-19, already registered) | — | — | — |

---

## 4. Shared code to use (copied from the current code on `main`; do not paraphrase)

### 4.1 AEA-57 harness — `tests/journeys/support/` (read only; import these, never edit)

```python
# env.py
REPO_ROOT = Path(__file__).resolve().parents[3]
def letters(n: int) -> str: ...                       # random lowercase letters
def journey_environ(root: Path) -> dict[str, str]: ... # ANTHROPIC_API_KEY/OPENROUTER_API_KEY placeholders, random
    # MERIDIAN_DEMO_USERNAME / _PASSWORD / MERIDIAN_SESSION_SECRET, MERIDIAN_COOKIE_SECURE="false",
    # MERIDIAN_REQUIRE_FRONTEND="false", MERIDIAN_WEB_DIST_DIR=root/"no-dist", MERIDIAN_DATA_DIR=root/"data",
    # MERIDIAN_INDEX_DIR=root/"index"
@dataclass(frozen=True)
class JourneyEnv:
    root: Path; data_dir: Path; web_dist_dir: Path; index_dir: Path; settings: Settings; issued_sha256_before: str
    db_path (property) -> Path                         # data_dir / "meridian.sqlite"
    def secret_values(self) -> tuple[str, str]: ...    # (demo password, session secret)
@contextmanager
def journey_environment() -> Iterator[JourneyEnv]: ... # temp root; asserts issued DB hash unchanged on exit

# server.py
FORBIDDEN_PORTS: frozenset[int] = frozenset({4019, 5184})
@dataclass
class RunningServer: app; container; host: str; port: int; thread; close_count: int = 0; base_url (property)
@contextmanager
def launch_server(settings: Settings, *, overrides: ContainerOverrides | None, startup_timeout_s: float = 30.0
                  ) -> Iterator[RunningServer]: ...
    # raises RuntimeError("journey server stopped during start-up (the app lifespan failed; see the captured log)")
class SocketGuard: blocked: list[tuple[str, int]]
@contextmanager
def socket_guard() -> Iterator[SocketGuard]: ...

# logtap.py
class LogTap(logging.Handler):
    def structured(self, kind: str) -> list[dict[str, object]]: ...
    def wait_for(self, kind: str, predicate: Callable[[Mapping[str, object]], bool], *, timeout_s: float = 2.0
                 ) -> dict[str, object]: ...
    def all_text(self) -> str: ...
@contextmanager
def tap_logs() -> Iterator[LogTap]: ...

# db.py
class DbReader:
    def __init__(self, db_path: Path) -> None: ...
    def rows(self, sql, params=()) -> list[dict[str, Any]]; def one(...) -> dict; def scalar(...) -> Any
    def count(self, table: str, where: str = "", params=()) -> int
def sha256_file(path: Path) -> str: ...

# scripted_model.py
class JourneyScript:
    def add(self, role: Role, *entries) -> None; calls (property); def remaining(self, role=None) -> int
    def problems(self) -> tuple[ScriptedCall, ...]
class ScriptedModel: ...      # subclasses ScriptedAnthropicModel, ScriptedJevModel
def scripted_overrides(settings: Settings, script: JourneyScript, *, wall_clock: Callable[[], datetime] | None
                       ) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]: ...

# steps.py
@dataclass(frozen=True)
class Missing: what: str; owner: str
@dataclass(frozen=True)
class StepResult: journey: str; step: str; nodeid: str; status: Literal["pass", "fail", "blocked"]; detail: str;
                  blocked_on: tuple[str, ...]; seconds: float
@dataclass(frozen=True)
class RunNote: host: str; port: int; agent_version: str; models: Mapping[str, str]; issued_sha256: str;
               spend_rows: int; spend_total_usd: float; outbound_blocked: int
@dataclass
class StepCollector: steps; tests; notes; def add_step(...); def add_test(...); def add_note(...)
JOURNEY_NODEID = re.compile(r"^tests/journeys/(j(?:[1-9]|10)|browser)/")
def missing_needs(container, app, needs: Sequence[str], operations: Sequence[str]) -> tuple[Missing, ...]: ...
def owners_of(missing) -> tuple[str, ...]; def blocked_message(missing) -> str
def stop_blocked(missing, *, strict: bool) -> NoReturn: ...   # pytest.skip(msg), or pytest.fail under strict
NEED_OWNERS / OPERATION_OWNERS   # e.g. "demo_clock" -> "AEA-30", "startChatSession" -> "AEA-40"

# run.py
@dataclass
class JourneyRun:
    env: JourneyEnv; server: RunningServer; script: JourneyScript; models: Mapping[Role, ScriptedModel];
    clock: StepClock | None; db: DbReader; logs: LogTap; guard: SocketGuard; collector: StepCollector;
    strict: bool; nodeid: str; clients: list[JourneyClient] = field(default_factory=list)
    settings / app / container / base_url / demo_username (properties)
    def secret_values(self) -> tuple[str, str]; def client(self) -> JourneyClient
    @contextmanager
    def step(self, journey: str, name: str, *, needs: Sequence[str] = (), operations: Sequence[str] = ()) -> Iterator[None]
    def files_containing(self, value: str) -> list[str]; def close_clients(self) -> None

# plugin.py
COLLECTOR_KEY = pytest.StashKey["StepCollector"]()
OPTIONS = ("--journey-record", "--journeys-strict")   # registered by AEA-57's plugin (root-loaded)

# record.py
FIELDS = ("Claim", "Level", "Tested revision", "Environment", "Command", "Result", "Evidence location",
          "Remaining limitations", "Blocked by")
@dataclass(frozen=True)
class RecordData: scope: str; values: Mapping[str, str]
def build_record_data(*, scope: str, collector: StepCollector, root: Path, command: str) -> RecordData: ...
def render_record(data: RecordData) -> str: ...
def record_path(root: Path, scope: str, day: date) -> Path: ...  # root/docs/testing/journeys/<day>-<scope>.md
```

AEA-57's `open_journey()` (in `run.py`) is the composition this ticket mirrors in `server.open_browser_journey()`; it
cannot be reused because it hard-codes `journey_environ`, which sets `MERIDIAN_REQUIRE_FRONTEND="false"` and a
`no-dist` folder (§8 R-3).

### 4.2 Settings — `src/meridian/config.py`

`Settings.from_env(environ: Mapping[str, str]) -> Settings` reads only the 17 names (pydantic lax parsing: `"true"` →
`True`, a path string → `Path`); `web_dist_dir: Path = Path("apps/web/dist")`; `require_frontend: bool = False`;
`demo_username`, `demo_password`, `session_secret: SecretStr`. Never print a `SecretStr` value.

### 4.3 Frontend serving — `src/meridian/web/frontend.py` (AEA-49)

`FrontendMissingError(RuntimeError)` with message
`"MERIDIAN_REQUIRE_FRONTEND is true but the built frontend is missing: no index.html in MERIDIAN_WEB_DIST_DIR=<path>"`;
`SPA_FALLBACK_ROUTE = "spa_fallback"`; `ASSETS_ROUTE = "/assets/{file}"`; `FONTS_ROUTE = "/fonts/{file}"`;
`INDEX_CACHE_CONTROL = "no-cache"`; public before login: `GET /login`, prefixes `/assets/`, `/fonts/` (WEB-1 A).
The `request` record's `route` is the matched route's template, resolved **before** the gate, so a signed-out `GET /`
that answers 303 is recorded with `route == "spa_fallback"`.

### 4.4 Gate, cookie, limiter — `src/meridian/web/middleware.py`, `routes/auth.py`, `policy/limits.py`

- Signed out, page GET → `303`, `Location = "/login?" + urlencode({"return_to": path+("?"+query if query), "reason":
  reason}, quote_via=quote)`. Exact values (computed 2026-10-21):
  `/` → `/login?return_to=%2F&reason=none`; `/staff/queue` → `/login?return_to=%2Fstaff%2Fqueue&reason=none`;
  `/?signedin=1&role=owner` → `/login?return_to=%2F%3Fsignedin%3D1%26role%3Downer&reason=none`.
- Signed out `/api/*` → `401` `{"error": {"code": "UNAUTHENTICATED", "details": {"reason": "none"}, ...}, "request_id"}`.
- Cookie `mhc_session=<token>; Path=/; HttpOnly; SameSite=Lax; Max-Age=43200` (no `Secure` locally).
- Login limiter: `WebLimits.login_rejects_per_ip: int = 10`, `login_reject_window_s: int = 600`. Each wrong pair is
  recorded; once the window holds `login_rejects_per_ip` rejects, **every** attempt (the right pair too) answers
  `429 LOGIN_RATE_LIMITED`, `details={"retry_after_ms": …}`, header `Retry-After`, and `auth_event` outcome
  `rate_limited` with `session_id: None`. A wrong pair before that answers `401 LOGIN_FAILED`, `auth_event`
  `rejected`. Read the number as `run.container.limits.web.login_rejects_per_ip`; never write `10`.
- Log records (`web/logging.py`): logger `meridian.web.request` record
  `{"record": "request", "request_id", "route", "status", "duration_ms", "caller_role", "thread_id", ...}`; logger
  `meridian.web.auth` record `{"record": "auth_event", "request_id", "outcome", "session_id", "at"}`. The `request`
  record is emitted after the response is sent: always use `run.logs.wait_for(...)`.

### 4.5 OpenAPI check — `tests/api/openapi_check.py` (AEA-23, read only)

```python
@dataclass(frozen=True)
class OperationSpec:
    operation_id: str
    method: Literal["get", "post", "put", "patch", "delete"]
    path_template: str                                  # e.g. "/api/chat/sessions/{thread_id}/turns"
    responses: Mapping[str, Mapping[str, JsonValue]]    # status -> {content type -> schema}
    event_schema: str | None                            # "ChatEvent" / "CaseEvent" for the two SSE operations
@dataclass(frozen=True)
class Contract: source: Path; version: str; operations: Mapping[str, OperationSpec]; error_codes; registry
def load_contract() -> Contract: ...
def assert_response_matches(response: _ResponseLike, operation_id: str) -> None: ...
# _ResponseLike needs .status_code, .headers (with .get, case-insensitive), .content (bytes), .json()
```

Build the response as `httpx.Response(status_code=status, headers=headers_list, content=body)` where `headers_list` is
`[(h["name"], h["value"]) for h in response.headers_array()]` (keeps `set-cookie`; `httpx.Headers` is
case-insensitive). The 30 operations and their paths (from `load_contract()`, version `0.1.0-ux3`) include:
`POST /api/login` login (200/400/401/429), `POST /api/logout` logout (204/401), `GET /api/session` getSession,
`POST /api/chat/sessions` startChatSession (201/401/429/503), `GET /api/chat/sessions/{thread_id}` getChatThread
(200/401/404/410), `GET /api/chat/sessions/{thread_id}/events` streamChatEvents (200/401/404; SSE),
`POST /api/chat/sessions/{thread_id}/turns` submitTurn (200/400/401/404/409/410/503), `GET /api/demo/clock`
getDemoClock.

### 4.6 pytest-playwright 0.10 (new dev dependency) and Playwright 1.6x sync API

- Fixtures used (session scope): `playwright` (a started `playwright.sync_api.Playwright`) and
  `browser_type_launch_args` (`dict`: has `"channel"` only when `--browser-channel` was given, `"headless": False` with
  `--headed`, `"slow_mo"` with `--slowmo`). Do **not** use its `browser`, `context` or `page` fixtures. If the installed
  version names these fixtures differently, read `.venv/lib/python3.12/site-packages/pytest_playwright/pytest_playwright.py`
  and use the equivalents; say so in the report.
- Its autouse session fixture deletes `<cwd>/test-results/` (its `--output` default) at session start. Harmless; nothing
  of ours is written there.
- Types: `from playwright.sync_api import Browser, BrowserContext, Error as PlaywrightError, Locator, Page, Playwright, Request, Response`.
- Sync event handlers run in their own greenlet (`playwright/_impl/_connection.py`: "Each event handler is a potentially
  blocking context, create a fiber for each"), so a handler may call `response.body()` and `response.headers_array()`.
- Never `time.sleep` while waiting on browser events (events only dispatch inside Playwright calls). Poll with
  `page.wait_for_timeout(50)`.
- `Response.request.redirected_from` walks a redirect chain; `Request.response()` returns that hop's `Response`;
  `Response.headers` (lower-case keys) holds `location`.
- `BrowserContext.cookies()` → list of dicts with `name`, `value`, `httpOnly`, `secure`, `sameSite` (`"Lax"` …).
- Context options from `apps/web/playwright.config.ts`: `viewport={"width": W, "height": H}`, `locale="en-US"`,
  `timezone_id="America/Chicago"`, `reduced_motion="reduce"`, plus `base_url=run.base_url`.

### 4.7 apps/web facts (read only)

- `apps/web/scripts/check-dist.mjs`: `ROOT` is the script's parent folder (`scripts/paths.mjs`), so
  `node <X>/apps/web/scripts/check-dist.mjs` checks `<X>/apps/web/dist`; success prints
  `dist is clean: no dev-layer markers`; missing dist prints `dist/ is missing: run npm run build first` and exits 1.
- Dev layer (must be absent from `dist`): `apps/web/src/dev/install.ts:17` `export const __MHC_DEV_LAYER__ = "mhc-dev-layer";`,
  `:48` `host.id = "mhc-dev-panel-root";`.
- Same-origin relative `/api` calls with `credentials: "include"` (`src/api/client.ts`); thread id kept per tab in
  `sessionStorage` (N-31). Neither is a contract; the tests assert behaviour through the network log, not storage.
- **API calls the production shell makes on its own** (read 2026-10-21 at `c9b17ea`, `apps/web` unchanged at `3725c90`; expect them in the network log,
  never assert their absence): `getSession` (`src/state/session.tsx`, on load and after sign-in; a signed-out 401 is
  documented), `getDemoClock` + `getStaffing` (`src/state/demoStatus.tsx`, signed in), `logout` (`session.tsx`, the
  "Sign out" control), and on SCR-1 `startChatSession` / `getChatThread` / `submitTurn` (`src/screens/scr01/core/gateway.ts`)
  plus `streamChatEvents` (`src/screens/scr01/core/useChat.ts`, an SSE stream opened after a thread exists; AEA-41's
  route is mounted). All of them pass through `validate_exchanges` (AC-7). AC-4's and AC-5's operation-sequence
  assertions only count `startChatSession` / `submitTurn` / `getChatThread`; the printed sequence shows the others too.
- **`startChatSession` on `main` `3725c90` answers `500`.** `routes/chat.py::start_chat_session` → `SessionService.open`
  → `self._settled_view(...)` → `register_chat`'s `lazy(Key("reply_composer"))` → `RuntimeError("not bound: reply_composer")`
  → `web/errors.py::render_unhandled_error`: status 500, body `{"request_id": "<uuid>"}`, header `X-Request-ID`.
  `getChatThread` (`SessionService.thread`) does the same. Only `resetDemo` documents a 500 in the OpenAPI, so for the
  chat operations it is an undocumented status; PA-4 decides when it is blocked work and when it is a failure.
  `owned_thread` (`web/deps.py`) answers the 401 / 404 / 410 **before** the service runs, so AC-5's 401 and 404 checks
  do not need AEA-51.
- SCR-12 copy (ticket AC-6, SCREEN_SPECS SCR-12 *error*): `"That username or password didn't work. Check the README and try again."`;
  throttle line (UI_CONTRACTS.md CON-22, `LOGIN_RATE_LIMITED` row, line 101): `"Too many attempts. Wait a moment and try again."`.
  These are **expected text values**, not selectors.

### 4.8 Domain values used by assertions

`from meridian.policy.texts import TextId, render` (`render(TextId.GREETING)` is the greeting);
`from meridian.domain.common import Role`; `from tests.fixtures.sqlite import ISSUED_DB`.

### 4.9 AEA-57's J-1 script (import, do not copy)

```python
from tests.journeys.j1.test_aea_57 import (
    CHAT_NEEDS,      # ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
    CLASSIFIER_RAW,  # '{"danger_level": "normal"}'
    CUSTOMER_TEXT,   # "Hi, what can you help me with?"
    LOGIN_NEEDS,     # ("login_sessions",)
    PLANNER_RAW,
    RESPONDER_TEXT,
    SIGN_IN_NEEDS,   # ("login_sessions", "demo_clock")
    TURN_NEEDS,      # (*CHAT_NEEDS, "turn_service", "run_graph")
)
```

The ticket says the browser types "the J-1 turn AEA-57's script plays"; importing keeps one source. Scripting a turn is
exactly AEA-57's: `run.script.add(Role.PLANNER, PLANNER_RAW)`, `run.script.add(Role.CLASSIFIER, CLASSIFIER_RAW)`,
`run.script.add(Role.RESPONDER, json.dumps({"text": RESPONDER_TEXT}))` **before** the Send click.

---

## 5. Steps

Build in this order; each step is checkable on its own. Dependency direction inside `browser/`: `plugin` → (`build`,
`server`, `pages`, `record`); `pages` → (`network`, `selectors`); `steps` → (`pages`, `selectors`, `network`); test files
→ (`steps`, `pages`, `selectors`, `build`, AEA-57 `support`). Nothing in `browser/` is imported by `src/meridian/` or by
`support/`. No test file imports `tests.journeys.browser.plugin` directly (it is loaded through `pytest_plugins`;
importing it first would trigger pytest's "already imported, cannot rewrite" warning).

### Step 0 — environment (no code)

1. `export UV_LINK_MODE=hardlink`; `df -h /home` (stop and report if under 5 GB free).
2. `cd <worktree> && uv add --dev "pytest-playwright>=0.10"`. Expect `pyproject.toml` to gain exactly one line in
   `[dependency-groups] dev` and `uv.lock` to be regenerated (it pulls `playwright`, `greenlet`, `pyee`,
   `python-slugify`, `text-unidecode`). Record the resolved `pytest-playwright` and `playwright` versions for the report.
   **Never** run `playwright install`: system Chrome is at `/usr/bin/google-chrome`.
3. The production build. Backend worktrees have no `apps/web/node_modules` and must not get one. Build in the primary
   checkout and point the tests at it:
   `npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run build && npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run check:dist`,
   then `git -C /home/linuxuser/workspaces/inno-aea-callcenter status --porcelain apps/web` must print nothing (the
   build writes only the git-ignored `dist`; the regenerated `types.gen.ts` / `contract.gen.json` must be unchanged).
   If it prints anything, **stop and report**; do not revert or commit anything in the primary checkout.
   Then `export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist` for every pytest
   command in this worktree.
4. Check `ls /home/linuxuser/workspaces/inno-aea-callcenter/docs/plans/ux-join/selectors.md` and
   `git log -1 --format=%h main -- docs/plans/ux-join/selectors.md`. If it exists, step 5 transcribes it; if not, step 5
   leaves the contract rows empty.

### Step 1 — `build.py`: build preflight and Chrome launch

```python
BUILD_COMMAND: Final = "npm --prefix apps/web run build && npm --prefix apps/web run check:dist"
CHECK_DIST_OK: Final = "dist is clean: no dev-layer markers"
DEFAULT_CHANNEL: Final = "chrome"

class BrowserPrerequisiteError(RuntimeError):
    """A browser journey cannot run; raised as an error (never a skip). Integrated-journeys rule 6."""

@dataclass(frozen=True)
class ProductionBuild:
    dist_dir: Path
    index_sha256: str
    check_line: str            # CHECK_DIST_OK, as printed by check-dist.mjs

def dist_dir_from_env(environ: Mapping[str, str] = os.environ) -> Path:
    """MERIDIAN_WEB_DIST_DIR, default apps/web/dist; a relative path is relative to REPO_ROOT; resolved."""

def check_production_build(dist_dir: Path) -> ProductionBuild: ...
def launch_chrome(playwright: Playwright, launch_args: Mapping[str, object]) -> tuple[Browser, str]: ...
    # returns (browser, channel)
```

`check_production_build` steps:
1. If `(dist_dir / "index.html")` is not a file → raise `BrowserPrerequisiteError(f"browser journeys need the production build: no index.html in MERIDIAN_WEB_DIST_DIR={dist_dir}. Build it first: {BUILD_COMMAND} (the server runs with MERIDIAN_REQUIRE_FRONTEND=true and refuses to start without it)")`.
   *Invariant: a missing build is an error naming both the command and the setting (AC-12), never a skip.*
2. `script = dist_dir.parent / "scripts" / "check-dist.mjs"`; if `dist_dir.name != "dist"` or the script is missing →
   raise `BrowserPrerequisiteError(f"cannot run check:dist for MERIDIAN_WEB_DIST_DIR={dist_dir}: point it at an apps/web/dist folder")`.
3. `subprocess.run(["node", str(script)], cwd=dist_dir.parent, capture_output=True, text=True, timeout=60, check=False)`;
   `FileNotFoundError` → `BrowserPrerequisiteError("node is not on PATH: check:dist needs Node 24")`. Return code ≠ 0
   or `CHECK_DIST_OK` not in stdout → `BrowserPrerequisiteError(f"check:dist failed on {dist_dir}: {first 400 chars of stderr or stdout}")`.
   *Invariant: the build under test is the one the UX track's own dev-layer check accepts (AC-1).*
4. Return `ProductionBuild(dist_dir, sha256_file(dist_dir / "index.html"), CHECK_DIST_OK)`.

`launch_chrome` steps: `args = dict(launch_args)`; `channel = str(args.get("channel") or DEFAULT_CHANNEL)`;
`args["channel"] = channel`; `try: browser = playwright.chromium.launch(**args)` `except PlaywrightError as exc:` raise
`BrowserPrerequisiteError(f"system Chrome did not start for --browser-channel {channel}: {first line of str(exc)}. Install that channel or pass --browser-channel with an installed one")`
from `None`. Return `(browser, channel)`. *Invariant: the default channel is `chrome` (the same as
`apps/web/playwright.config.ts`), so the merge gate's `python -m tests.journeys.affected` run works without the flag;
no browser is ever downloaded.*

### Step 2 — `server.py`: the browser run

```python
def browser_environ(root: Path, dist_dir: Path) -> dict[str, str]:
    """AEA-57's journey_environ(root) plus the build: MERIDIAN_WEB_DIST_DIR=str(dist_dir), MERIDIAN_REQUIRE_FRONTEND="true"."""

@contextmanager
def open_browser_journey(*, collector: StepCollector, strict: bool, nodeid: str, build: ProductionBuild
                         ) -> Iterator[JourneyRun]: ...
```

`open_browser_journey` mirrors AEA-57's `open_journey` line for line, with two changes (numbered):
1. `with socket_guard() as guard, tap_logs() as logs, journey_environment() as base:`
2. **Change 1:** `settings = Settings.from_env(browser_environ(base.root, build.dist_dir))`;
   `env = dataclasses.replace(base, settings=settings, web_dist_dir=build.dist_dir)`. (`journey_environ` makes new
   random demo values; `env.settings` is the only holder, so `env.secret_values()` stays consistent.)
3. `script = JourneyScript()`; **Change 2:** no wall clock: `overrides, models = scripted_overrides(settings, script, wall_clock=None)`.
4. `with launch_server(settings, overrides=overrides) as server:` build `JourneyRun(env=env, server=server, script=script,
   models=models, clock=None, db=DbReader(env.db_path), logs=logs, guard=guard, collector=collector, strict=strict,
   nodeid=nodeid)`; `try: yield run` `finally: run.close_clients()`.
5. After the server stops, add the same `RunNote` as `open_journey` (spend rows and total from
   `DbReader(env.db_path).one("SELECT COUNT(*) AS n, COALESCE(SUM(cost_usd), 0.0) AS total FROM spend_ledger")`).
6. After the guard exits: if `guard.blocked`, raise the same `AssertionError` text as `open_journey`.
   *Invariant: everything AEA-57 guarantees (loopback only, issued hash unchanged, placeholder keys, no Langfuse, no
   eval key) still holds; only the build settings differ.*

### Step 3 — `network.py`: what Chrome sent and received

```python
DEV_PARAMS: Final = frozenset({"signedin", "role", "scenario", "staffing", "ex", "delay"})

# PA-4: service needs per mounted chat operation. A 500 from one of these while a listed need is unbound is blocked
# work, not a contract failure. Names are AEA-57 NEED_OWNERS keys, equal to tests/journeys/j1/test_aea_57.py
# CHAT_NEEDS / TURN_NEEDS on main 3725c90 (a self-check pins the equality). Never add other operations.
_CHAT: Final = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
UNBOUND_500_NEEDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "startChatSession": _CHAT,
    "getChatThread": _CHAT,
    "submitTurn": (*_CHAT, "turn_service", "run_graph"),
})

@dataclass
class SeenRequest:
    index: int; method: str; url: str; resource_type: str; is_navigation: bool

@dataclass
class ApiExchange:
    index: int                      # SeenRequest.index of the request
    method: str; url: str; path: str
    operation_id: str | None
    status: int
    headers: list[tuple[str, str]]
    request_body: bytes | None
    body: bytes | None = None       # filled on requestfinished; stays None for SSE
    is_sse: bool = False
    failed: str | None = None       # requestfailed text
    def header(self, name: str) -> str | None: ...   # first value whose name matches case-insensitively

@dataclass
class ValidationSummary:
    validated: Counter[str]; unrouted: Counter[str]; unrouted_owners: dict[str, str]
    unbound: Counter[str]; unbound_owners: dict[str, str]          # PA-4
    sse_checked: Counter[str]; unfinished: int; failures: list[str]

def operation_for(method: str, path: str, contract: Contract) -> str | None: ...
def to_httpx(exchange: ApiExchange) -> httpx.Response: ...
def validate_exchanges(exchanges: Sequence[ApiExchange], *, container: Container, app: FastAPI,
                       contract: Contract) -> ValidationSummary: ...
def teardown_failures(summary: ValidationSummary, *, strict: bool) -> list[str]: ...   # PA-1, PA-4

class NetworkLog:
    def __init__(self, contract: Contract) -> None: ...
    def attach(self, context: BrowserContext) -> None: ...   # "request", "response", "requestfinished", "requestfailed"
    requests: list[SeenRequest]; exchanges: list[ApiExchange]
    def mark(self) -> int: ...                                 # len(self.requests)
    def operations(self, since: int = 0) -> list[str]: ...     # operation ids of exchanges with index >= since, in order
    def wait_for(self, page: Page, operation_id: str, *, since: int = 0, timeout_ms: int = 15_000,
                 finished: bool = True) -> ApiExchange: ...
    def origins(self) -> set[str]: ...                         # scheme://host:port of every http(s) request
    def dev_param_hits(self, *, allowed_urls: Collection[str] = ()) -> list[str]: ...
```

Algorithms:
- `operation_for`: for each `OperationSpec`, compile `^` + `re.escape(template)` with each escaped `\{name\}` replaced by
  `[^/]+` + `$`; keep the specs whose method (`spec.method.upper()`) equals `method` and whose regex matches `path`;
  if several match, pick the one with the fewest `{` (a literal path beats a template); none → `None`. Compile once per
  `Contract` (cache in a module-level dict keyed by `id(contract)`).
- `attach`: on `request` append `SeenRequest(len(requests), req.method, req.url, req.resource_type,
  req.is_navigation_request())` and remember `request → index` in a dict keyed by the `Request` object. On `response`:
  if the URL path starts with `/api/`, create an `ApiExchange` with `operation_for(...)`, `status`,
  `headers=[(h["name"], h["value"]) for h in resp.headers_array()]`, `request_body=req.post_data_buffer`,
  `is_sse = content-type startswith "text/event-stream"`. On `requestfinished`: if it has an exchange and not SSE,
  `exchange.body = req.response().body()` (inside `try`; a `PlaywrightError` sets `failed`). On `requestfailed`: set
  `failed = req.failure or "failed"` on its exchange if any.
- `wait_for`: loop until an exchange with that `operation_id`, `index >= since` and (`finished` → `body is not None or
  is_sse or failed`) exists; poll with `page.wait_for_timeout(50)`; on timeout raise
  `AssertionError(f"no {operation_id} response within {timeout_ms} ms (seen: {self.operations(since)})")`.
- `dev_param_hits`: for every `SeenRequest` whose URL is not in `allowed_urls` (compare the path+query part), parse
  `urllib.parse.parse_qs(urlsplit(url).query, keep_blank_values=True)`; any key in `DEV_PARAMS` → add the path+query to
  the result. `data:`/`blob:` URLs are skipped by `origins()` and `dev_param_hits()`.
- `validate_exchanges` (AC-7, PA-1, PA-2), for each exchange in order:
  1. `operation_id is None` → failure `"<METHOD> <path>: no operationId in the OpenAPI matches"`.
  2. `missing_needs(container, app, (), (op,))` non-empty → `unrouted[op] += 1`, `unrouted_owners[op] = owner`; skip.
     *Invariant: a route that does not exist yet is reported as blocked work, never as a contract pass or fail.*
  2b. (PA-4) `ex.status == 500` and `op in UNBOUND_500_NEEDS` and
     `missing = missing_needs(container, app, UNBOUND_500_NEEDS[op], ())` is non-empty → `unbound[op] += 1`,
     `unbound_owners[op] = ", ".join(owners_of(missing))`; skip. Otherwise fall through (a 500 then fails at step 5,
     because no chat operation documents a 500). *Invariant: only a 500 whose declared services really are unbound is
     blocked work; a 500 with every listed service bound, or from any other operation, is a failure.*
  3. `is_sse` → status must be in `spec.responses` and, for 200, content type `text/event-stream`; `sse_checked[op] += 1`.
  4. `body is None` and `failed is None` → `unfinished += 1`; skip. `failed` and not SSE → failure
     `"<op> <status>: request failed: <text>"`.
  5. Else `assert_response_matches(to_httpx(ex), op)`; on `AssertionError as exc` append `f"{op}: {exc}"` (first line,
     ≤ 300 chars); else `validated[op] += 1`.
  `to_httpx` returns `httpx.Response(status_code=ex.status, headers=ex.headers, content=ex.body or b"")`.
- `teardown_failures`: `list(summary.failures)`; when `strict`, also append
  `f"{op}: unrouted, blocked-on {summary.unrouted_owners[op]} [--journeys-strict]"` for each `op` in `unrouted` and
  `f"{op}: 500 while a service is unbound, blocked-on {summary.unbound_owners[op]} [--journeys-strict]"` for each `op`
  in `unbound` (sorted by `op`). *Invariant: under `--journeys-strict` (wave merge, pre-deploy) blocked work fails, the
  same as a blocked step (integrated-journeys rule 6).*

### Step 4 — `pages.py`: devices, pages, the run object

```python
@dataclass(frozen=True)
class Device:
    name: str; width: int; height: int

DESKTOP = Device("chrome-desktop", 1280, 800)     # apps/web/playwright.config.ts projects
PHONE = Device("chrome-phone", 390, 844)
DEVICES: tuple[Device, ...] = (DESKTOP, PHONE)
LABEL = re.compile(r"^[a-z0-9-]{1,40}$")

@dataclass
class BrowserPage:
    device: Device; context: BrowserContext; page: Page; net: NetworkLog

@dataclass
class BrowserRun:
    run: JourneyRun; browser: Browser; channel: str; build: ProductionBuild; shots_dir: Path
    session: BrowserSession; test_name: str; pages: list[BrowserPage] = field(default_factory=list)
    def open(self, device: Device) -> BrowserPage: ...
    def screenshot(self, bp: BrowserPage, label: str) -> Path: ...
    def close(self) -> None: ...
```

- `open`: `context = browser.new_context(viewport={"width": d.width, "height": d.height}, locale="en-US",
  timezone_id="America/Chicago", reduced_motion="reduce", base_url=run.base_url)`;
  `context.set_default_timeout(15_000)`; `net = NetworkLog(load_contract())`; `net.attach(context)`;
  `page = context.new_page()`; append and return. `self.session.devices.add(d.name)`.
- `screenshot`: `LABEL.fullmatch(label)` else `ValueError`; path `shots_dir / f"{test_name}-{bp.device.name}-{label}.png"`;
  `bp.page.screenshot(path=str(path), full_page=False)`; append to `session.screenshots`; return the path.
  *Invariant: file names hold only the test function name, the device name and a fixed label (AC-9).*
- `close` (teardown; PA-1): for every page, `validate_exchanges(bp.net.exchanges, container=run.container, app=run.app,
  contract=load_contract())`, merge into `session` counters; then close every context (each in its own
  `try/finally`); then collect `teardown_failures(summary, strict=self.run.strict)` over every page's summary (PA-4) and, if any, raise
  `AssertionError("browser API responses broke the OpenAPI:\n" + "\n".join(failures[:20]))`.

### Step 5 — `selectors.py`: the one selector module (AC-16)

```python
SELECTORS_SOURCE: Final = "docs/plans/ux-join/selectors.md"
SELECTORS_REVISION: Final[str | None] = None   # short SHA of the last commit touching SELECTORS_SOURCE; None until it exists
SelectorKind = Literal["css", "role", "label"]

@dataclass(frozen=True)
class SelectorRow:
    key: str            # one of SELECTOR_KEYS
    kind: SelectorKind
    value: str          # css: the selector text; role: the ARIA role; label: the accessible label text
    name: str | None    # role only: the exact accessible name
    row: str            # the row's id or heading in selectors.md, quoted exactly

SELECTOR_KEYS: Mapping[str, str] = MappingProxyType({   # key -> the state it asserts (FOR-UX-SESSION §3)
    "screen.scr1": "SCR-1 root is drawn",
    "screen.scr12": "SCR-12 root is drawn",
    "login.username": "SCR-12 username input",
    "login.password": "SCR-12 password input",
    "login.submit": "SCR-12 'Sign in' button",
    "login.show_password": "SCR-12 'Show password' checkbox",
    "login.message.refused": "SCR-12 refusal line ([data-login-message=refused])",
    "login.message.rate_limited": "SCR-12 throttle line ([data-login-message=rate-limited])",
    "chat.ready": "SCR-1 chat ready to type ([data-chat-state=ready])",
    "chat.entry": "each thread entry, in order ([data-entry])",
    "chat.entry.customer": "a customer entry ([data-speaker=customer])",
    "chat.entry.assistant": "an assistant entry ([data-speaker=assistant])",
    "chat.block.text": "a text reply block inside an entry ([data-block-type=text])",
    "chat.composer": "SCR-1 message box",
    "chat.send": "SCR-1 'Send' button",
    "shell.sign_out": "the shared header's 'Sign out' control",
})
CONTRACT_ROWS: Mapping[str, SelectorRow] = MappingProxyType({})   # filled only from SELECTORS_SOURCE

# Dev-layer absence markers: not UI selectors; used only with page.evaluate to prove absence (AC-1).
DEV_LAYER_GLOBAL: Final = "__MHC_DEV_LAYER__"        # apps/web/src/dev/install.ts:17
DEV_PANEL_ROOT_ID: Final = "mhc-dev-panel-root"     # apps/web/src/dev/install.ts:48

UX_OWNER: Final = "UX session"

def missing_selectors(keys: Sequence[str]) -> tuple[Missing, ...]: ...
def locate(page: Page, key: str) -> Locator: ...
def locate_in(parent: Locator, key: str) -> Locator: ...
```

- `missing_selectors`: unknown key → `KeyError(f"unknown selector key {key!r}: add it to SELECTOR_KEYS")` (a harness
  bug); a key without a row → `Missing(f"UX selector {key} not in {SELECTORS_SOURCE}", UX_OWNER)`.
  `blocked_message` then reads `blocked-on UX session: UX selector login.message.rate_limited not in docs/plans/ux-join/selectors.md`.
- `locate`: row = `CONTRACT_ROWS[key]` (a missing row here is a bug: callers check first, so raise `KeyError`);
  `css` → `page.locator(row.value)`; `role` → `page.get_by_role(row.value, name=row.name, exact=True)`
  (`# type: ignore[arg-type]` on the role literal if mypy needs it); `label` → `page.get_by_label(row.value, exact=True)`.
  `locate_in` does the same on a `Locator` parent. **This file is the only one under `tests/journeys/` that calls
  `locator(` or `get_by_`.**
- **Transcription (only if step 0.4 found `selectors.md`):** for each key in `SELECTOR_KEYS`, find the row in
  `selectors.md` that names that state (the `Required hook` column of FOR-UX-SESSION §3 is the guide). Transcribe it
  literally: an attribute selector → `css`; "role=X name=Y" → `role`; "input labelled Y" → `label`. Put the row's
  exact id or heading in `row` and the file's short SHA in `SELECTORS_REVISION`. A state the file does not list stays
  absent (its steps report blocked). **Never invent a row, never use copy text the file does not give, never read
  `apps/web/src` to fill a gap.** Each `SelectorRow(...)` line ends with a comment `# selectors.md <row> @ <rev>`.

### Step 6 — `steps.py`: step wrapper and UI helpers

```python
@contextmanager
def browser_step(run: JourneyRun, journey: str, name: str, *, needs: Sequence[str] = (),
                 operations: Sequence[str] = (), selectors: Sequence[str] = ()) -> Iterator[None]: ...

@dataclass(frozen=True)
class BrowserLogin:
    session_id: str
    login: ApiExchange           # the POST /api/login exchange (status 200)

def sign_in_via_form(run: JourneyRun, bp: BrowserPage) -> BrowserLogin: ...
def fill_login(run: JourneyRun, bp: BrowserPage, *, password: str) -> None: ...
def sign_out_via_shell(run: JourneyRun, bp: BrowserPage) -> ApiExchange: ...
def first_hop(response: Response) -> Response: ...
def page_fetch(bp: BrowserPage, path: str) -> dict[str, object]: ...  # {"status": int, "text": str}

SIGN_IN_SELECTORS: Final = ("login.username", "login.password", "login.submit")
```

- `browser_step` (the only way tests open a step): (1) `sel = missing_selectors(selectors)`; (2) if `sel`:
  `svc = missing_needs(run.container, run.app, needs, operations)`; `allm = (*svc, *sel)`;
  `run.collector.add_step(StepResult(journey, name, run.nodeid, "blocked", blocked_message(allm), owners_of(allm), 0.0))`;
  `stop_blocked(allm, strict=run.strict)`. (3) Else `with run.step(journey, name, needs=needs, operations=operations): yield`.
  *Invariant: a step lacking a selector is reported blocked with the UX session (and any service owner) and is never
  passed; under `--journeys-strict` it fails (AC-16, rule 6).*
- `fill_login`: `locate(page, "login.username").fill(run.demo_username)`;
  `locate(page, "login.password").fill(password)`. Never touch `login.show_password`.
- `sign_in_via_form`: (1) `before = {r["session_id"] for r in run.db.rows("SELECT session_id FROM staff_sessions")}`;
  (2) `mark = bp.net.mark()`; (3) `fill_login(run, bp, password=run.settings.demo_password.get_secret_value())`;
  (4) `locate(page, "login.submit").click()`; (5) `ex = bp.net.wait_for(page, "login", since=mark)`; `ex.status == 200`
  else `AssertionError(f"login answered HTTP {ex.status}")`; (6) new ids = after − before, exactly one; (7) return.
  Never print or assert on the password; failure messages name only statuses and counts.
- `sign_out_via_shell`: `mark`; `locate(page, "shell.sign_out").click()`; `ex = wait_for(page, "logout", since=mark)`;
  `ex.status == 204`; return `ex`.
- `first_hop`: walk `response.request.redirected_from` to the first request; return its `.response()` (assert not None).
- `page_fetch`: `bp.page.evaluate("async (p) => { const r = await fetch(p, {credentials: 'include'}); return {status: r.status, text: await r.text()}; }", path)`.

### Step 7 — `record.py`: session-wide browser facts and the record values

```python
@dataclass
class BrowserSession:
    build: ProductionBuild | None = None
    channel: str | None = None
    chrome_version: str | None = None
    devices: set[str] = field(default_factory=set)
    screenshots: list[Path] = field(default_factory=list)
    validated: Counter[str] = field(default_factory=Counter)
    unrouted: Counter[str] = field(default_factory=Counter)
    unrouted_owners: dict[str, str] = field(default_factory=dict)
    unbound: Counter[str] = field(default_factory=Counter)
    unbound_owners: dict[str, str] = field(default_factory=dict)
    sse_checked: Counter[str] = field(default_factory=Counter)
    unfinished: int = 0
    failures: int = 0
    def summary_line(self) -> str: ...

BROWSER_KEY = pytest.StashKey[BrowserSession]()
SHOTS_SUFFIX: Final = ""   # screenshots folder = record path without ".md"

def browser_record_values(base: RecordData, session: BrowserSession, *, collector: StepCollector, root: Path
                          ) -> dict[str, str]: ...
```

- `summary_line`: `"browser API responses validated: N (op=n, …); SSE checked: …; unrouted (blocked): op=n (AEA-NN), …; unbound 500 (blocked): op=n (AEA-NN), …; unfinished: n; failures: n"`.
- `browser_record_values` returns `dict(base.values)` with four fields replaced (all others, including *Level*,
  *Tested revision*, *Result* and *Blocked by*, kept from AEA-57's builder):
  - **Claim:** `f"{base.scope}: journeys {journeys} in system Chrome against the production build served by the real app (browser level), through the normal SCR-12 login, with the scripted model; per-step results under Result"`
    (`journeys` = `", ".join(sorted({s.journey for s in collector.steps if JOURNEY_NODEID.match(s.nodeid)}))`, or `none`).
  - **Environment:** `127.0.0.1, ephemeral port per test; server: uvicorn.Server in a background thread over create_app(Settings.from_env(<journey environ> + MERIDIAN_WEB_DIST_DIR=<dist>, MERIDIAN_REQUIRE_FRONTEND=true), overrides=ContainerOverrides(choice, structured, tools)); DB copy: <issued rel path> (sha256 <from note>) copied by the app's first boot into a temp MERIDIAN_DATA_DIR; frontend build: <dist path relative to its repo or absolute> (index.html sha256 <hash>; check:dist: "dist is clean: no dev-layer markers"); model adapter: ScriptedModel (tests/journeys/support/scripted_model.py); model ids: <from note>; browser: Google Chrome channel <channel> version <version>; devices: <sorted names> (1280×800, 390×844), locale en-US, timezone America/Chicago, reduced motion`.
  - **Evidence location:** base value + `f"; screenshots: {folder rel to root} ({n} files); {session.summary_line()}"`.
  - **Remaining limitations:** `"J-2…J-10 and J-8's staff-role steps are not in the browser yet (AEA-62; per-wave walkthroughs); SSE frames are not body-checked (status and content type only; frames are AEA-41's and AEA-59's); scripted model only (live models: AEA-61); redaction is not re-checked here (CAP-10, CAP-11); the Prism/UX-5 sweep is not this evidence (AEA-55); held-out data is never read"`.

### Step 8 — `plugin.py`: fixtures and hooks

```python
@pytest.fixture(scope="session")
def production_build(request: pytest.FixtureRequest) -> ProductionBuild: ...
@pytest.fixture(scope="session")
def journey_chrome(request: pytest.FixtureRequest, playwright: Playwright,
                   browser_type_launch_args: dict[str, Any]) -> Iterator[Browser]: ...
@pytest.fixture
def browser_journey(request: pytest.FixtureRequest, journey_chrome: Browser, production_build: ProductionBuild,
                    tmp_path: Path) -> Iterator[BrowserRun]: ...
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None: ...
```

- Module level imports only the standard library, `pytest` and `TYPE_CHECKING`-only imports; import everything else
  inside fixture and hook bodies (same reason as AEA-57's plugin).
- `_session(config)`: `config.stash.setdefault(BROWSER_KEY, BrowserSession())`.
- `production_build`: `build = check_production_build(dist_dir_from_env())`; store in the session; write two lines
  through `request.config.pluginmanager.get_plugin("terminalreporter")` (if present):
  `f"production build: {build.dist_dir} index.html sha256 {build.index_sha256}"` and `build.check_line`.
- `journey_chrome`: `browser, channel = launch_chrome(playwright, browser_type_launch_args)`; store `channel` and
  `browser.version`; write `f"browser: Chrome channel {channel} version {browser.version}"`; `yield browser`;
  `finally: browser.close()`.
- `browser_journey`:
  1. `from tests.journeys.support.plugin import COLLECTOR_KEY`; `collector = request.config.stash[COLLECTOR_KEY]`;
     `strict = bool(request.config.getoption("--journeys-strict"))`.
  2. Screenshot folder: `scope = request.config.getoption("--journey-record")`; if `scope`:
     `shots = record_path(REPO_ROOT, scope, today_chicago).with_suffix("")` (create it); else `shots = tmp_path / "shots"`.
     `today_chicago = datetime.now(ZoneInfo("America/Chicago")).date()` (AEA-57's convention).
  3. `with open_browser_journey(collector=collector, strict=strict, nodeid=request.node.nodeid, build=production_build) as run:`
     `brun = BrowserRun(run=run, browser=journey_chrome, channel=session.channel, build=production_build, shots_dir=shots,
     session=session, test_name=request.node.originalname)`; `try: yield brun` `finally: brun.close()`.
- `pytest_sessionfinish` (trylast, so it runs after AEA-57's recorder):
  1. If `hasattr(config, "workerinput")` → return (an xdist worker writes nothing).
  2. `session_data = config.stash.get(BROWSER_KEY, None)`; if `None` or `session_data.build is None` → return.
  3. Write `session_data.summary_line()` to the terminal reporter.
  4. `scope = config.getoption("--journey-record")`; if `None` → return.
  5. Rebuild exactly as AEA-57's recorder does: `command = "uv run pytest " + shlex.join(str(a) for a in config.invocation_params.args)`;
     `base = build_record_data(scope=scope, collector=config.stash[COLLECTOR_KEY], root=Path(config.rootpath), command=command)`;
     `values = browser_record_values(base, session_data, collector=config.stash[COLLECTOR_KEY], root=Path(config.rootpath))`;
     `path = record_path(Path(config.rootpath), scope, today_chicago)`;
     `path.write_text(render_record(RecordData(scope=scope, values=values)), encoding="utf-8")`.
     *Invariant: one record per scope per run, written with AEA-57's writer; the browser run overwrites the API-level
     wording AEA-57's recorder wrote a moment earlier for the same scope.*
- How tests load this plugin (no edit to `tests/conftest.py`): each browser test module declares
  `pytest_plugins = ("tests.journeys.browser.plugin",)`. pytest 9.1 registers it when it imports the module
  (`_pytest/python.py`: `config.pluginmanager.consider_module(mod)`); a second module declaring it is a no-op; fixtures
  of a non-conftest plugin are global. *Invariant: later `j<N>/test_aea_<NN>.py` files get the browser fixtures with one
  line and no edit to AEA-01's or AEA-57's files.*

### Step 9 — `test_browser_support.py`: self-checks (`pytestmark = pytest.mark.journey`; no page opened)

| Test | Asserts |
|---|---|
| `test_operation_resolver_covers_every_operation` | For every spec in `load_contract().operations`: the template with each `{x}` replaced by `x1` resolves via `operation_for(spec.method.upper(), path, contract)` back to that operationId; `operation_for("GET", "/api/nope", c) is None`; `operation_for("POST", "/api/chat/sessions/t1/turns", c) == "submitTurn"` |
| `test_validation_rejects_undocumented_status` | `app = FastAPI(); app.add_api_route("/api/session", lambda: None, methods=["GET"], operation_id="getSession")` (a bare app whose only route carries that operationId; `missing_needs` with empty `needs` never touches the container, so pass `container=cast(Any, object())`). A synthetic `ApiExchange` for `getSession` with status 418, a JSON body and an `X-Request-ID` header → `validate_exchanges` reports 1 failure naming `getSession` and `418`; a valid 401 body `{"error": {"code": "UNAUTHENTICATED", "field": null, "constraint": null, "details": {"reason": "none"}}, "request_id": <same uuid as the header>}` → 0 failures and `validated["getSession"] == 1` |
| `test_unrouted_operations_counted_not_validated` | Same bare `FastAPI()` but with **no** routes; an exchange for `startChatSession` (status 404, body `{"detail": "Not Found"}`) → `unrouted["startChatSession"] == 1`, `unrouted_owners["startChatSession"] == "AEA-40"`, 0 failures |
| `test_unbound_service_500_counted_not_validated` | A container double: `class _Container:` with `absent = {"reply_composer"}` and `def get(self, key): if key.name in self.absent: raise ContainerError(f"not provided: {key.name}"); return object()` (`ContainerError` from `meridian.web.container`); a bare `FastAPI()` with one route carrying `operation_id="startChatSession"`. An exchange for `startChatSession`, status 500, body `{"request_id": "<uuid4>"}` → `unbound["startChatSession"] == 1`, `unbound_owners["startChatSession"] == "AEA-51"`, `validated` empty, 0 failures |
| `test_mounted_500_with_bound_needs_fails` | Same double with `absent = set()`: the same 500 exchange → 1 failure naming `startChatSession` and `500`. Then `absent = {"reply_composer"}` and a route with `operation_id="getSession"`: a `getSession` 500 → 1 failure (not in `UNBOUND_500_NEEDS`) |
| `test_strict_fails_on_blocked_exchanges` | A `ValidationSummary` with `unrouted={"startChatSession": 1}`, `unrouted_owners={"startChatSession": "AEA-40"}`, `unbound={"submitTurn": 1}`, `unbound_owners={"submitTurn": "AEA-51"}`, no failures: `teardown_failures(s, strict=False) == []`; `strict=True` → two lines, one containing `blocked-on AEA-40`, one `blocked-on AEA-51`, both `[--journeys-strict]` |
| `test_unbound_needs_match_aea57_scripts` | `UNBOUND_500_NEEDS["startChatSession"] == CHAT_NEEDS`, `["getChatThread"] == CHAT_NEEDS`, `["submitTurn"] == TURN_NEEDS` (imported from `tests.journeys.j1.test_aea_57`); `set(UNBOUND_500_NEEDS) == {"startChatSession", "getChatThread", "submitTurn"}`; every name is a key of `NEED_OWNERS` |
| `test_selector_rows_cite_contract` | Every `CONTRACT_ROWS` key is in `SELECTOR_KEYS`, `row.key == key`, `row.row` non-empty; if `CONTRACT_ROWS` is non-empty then `SELECTORS_REVISION` is a 7–12 char hex string and `REPO_ROOT / SELECTORS_SOURCE` exists; if `SELECTORS_REVISION is None` then `CONTRACT_ROWS` is empty |
| `test_no_selector_strings_outside_module` | Scan every `*.py` under `tests/journeys/` except `browser/selectors.py`: no line matches `re.compile(r"locator\(\|get_by_")` |
| `test_missing_selector_reports_ux_owner` | `missing_selectors(("login.message.rate_limited",))` (absent row) → one `Missing` with owner `"UX session"`; `blocked_message(...)` starts with `"blocked-on UX session"`; unknown key raises `KeyError` |
| `test_missing_build_message_names_build_command` | `check_production_build(tmp_path)` raises `BrowserPrerequisiteError` whose text contains `"npm --prefix apps/web run build"` and `"MERIDIAN_REQUIRE_FRONTEND"` |
| `test_missing_build_refuses_server_start` | With `tap_logs() as logs` and `journey_environment() as base`: `settings = Settings.from_env(browser_environ(base.root, tmp_path / "empty"))`; `pytest.raises(RuntimeError, match="stopped during start-up")` around `launch_server(settings, overrides=None)`; then `"MERIDIAN_REQUIRE_FRONTEND" in logs.all_text()` |
| `test_missing_chrome_channel_errors_with_flag_name` | Uses pytest-playwright's `playwright` fixture: `launch_chrome(playwright, {"channel": "msedge-canary"})` raises `BrowserPrerequisiteError` containing `"--browser-channel msedge-canary"` |
| `test_browser_record_fields` | Build a `StepCollector` with one pass step for `tests/journeys/j1/test_aea_58.py::t` and one `RunNote`; a `BrowserSession` with a fake `ProductionBuild`, channel `"chrome"`, version `"1.0"`; `values = browser_record_values(build_record_data(...), session, collector=collector, root=REPO_ROOT)`: all nine `FIELDS` present; Environment contains `"MERIDIAN_REQUIRE_FRONTEND=true"`, the index hash, `"channel chrome"`, `"version 1.0"`; nothing in it says `"none (API level)"` |
| `test_no_heldout_paths_in_browser_files` | `needle = "held" + "out"` (so this file does not match itself); no owned browser file nor `j1/test_aea_58.py`, `j9/test_aea_58.py` contains `needle` or `"key_dir"` |
| `test_dev_params_and_origins_helpers` | A `NetworkLog` with hand-made `SeenRequest`s: `origins()` ignores `data:`; `dev_param_hits(allowed_urls=("/?signedin=1&role=owner",))` returns only the non-allowed hit |

### Step 10 — `tests/journeys/j1/test_aea_58.py` (J-1 in the browser)

Header: module docstring stating level `integrated with a scripted model` and the run-time blocked owners; then
`pytest_plugins = ("tests.journeys.browser.plugin",)`, `pytestmark = pytest.mark.journey`, `J1 = "J-1"`,
`REDIRECTS: Mapping[str, str]` (the three exact pairs in §4.4), `PROBE = "/?signedin=1&role=owner"`. Two-width tests use
`@pytest.mark.parametrize("device", DEVICES, ids=lambda d: d.name)`; one-width tests use `DESKTOP`. Every step uses
`browser_step(...)`. Print one evidence line per step (statuses, ids, counts; never a secret).

1. **`test_serves_production_build(browser_journey)`** — DESKTOP.
   - "1a build served" (no needs): `run.settings.require_frontend is True`; `run.settings.web_dist_dir == build.dist_dir`;
     `resp = page.goto("/login")`; `resp.status == 200`; `resp.request.redirected_from is None`;
     `hashlib.sha256(resp.body()).hexdigest() == build.index_sha256`; `resp.headers["cache-control"] == "no-cache"`.
   - "1b no dev layer" (no needs): `page.evaluate(f"() => typeof window.{DEV_LAYER_GLOBAL}") == "undefined"`;
     `page.evaluate("id => document.getElementById(id) === null", DEV_PANEL_ROOT_ID) is True`; screenshot `login-page`.
     Print `index.html sha256 <hash>; dev layer absent`.
2. **`test_signed_out_pages_redirect_to_login(browser_journey, device)`** — both widths.
   - "2a redirect <path>" for each of `REDIRECTS` (no needs): `hop = first_hop(page.goto(path))`; `hop.status == 303`;
     `hop.headers["location"] == REDIRECTS[path]`; `page.url == run.base_url + REDIRECTS[path]`. Print path, status, Location.
   - "2b no api 2xx before sign-in" (no needs): `page.wait_for_load_state("networkidle")`; every exchange with
     `200 <= status < 300` has `operation_id == "login"` (there are none: nobody signed in).
   - "2c SCR-12 drawn" (`selectors=("screen.scr12",)`): for each path, `page.goto(path)`;
     `locate(page, "screen.scr12").wait_for(state="visible")`; screenshot `scr12-<n>` (n = 1, 2, 3).
3. **`test_j1_login_turn_refresh_resume(browser_journey, device)`** — both widths; **the `[journey]` test (AC-3)**.
   - "3a sign in" (`needs=SIGN_IN_NEEDS, operations=("login",), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`):
     `hop = first_hop(page.goto("/"))` → 303 to `REDIRECTS["/"]`; `login = sign_in_via_form(run, bp)`;
     `locate(page, "screen.scr1").wait_for(state="visible")`; `page.url == run.base_url + "/"` (the `return_to` page).
   - "3b greeting" (`needs=CHAT_NEEDS, operations=("startChatSession",), selectors=("chat.entry", "chat.entry.assistant", "chat.block.text")`):
     `start = bp.net.wait_for(page, "startChatSession", since=…)`; `start.status == 201`;
     `body = json.loads(start.body)`; `thread_id = body["thread_id"]`; `body["greeting"]["text"] == render(TextId.GREETING)`;
     first entry: `locate_in(locate(page, "chat.entry").first, "chat.block.text").inner_text().strip() == render(TextId.GREETING)`;
     DB: `conv = run.db.one("SELECT * FROM conversations WHERE thread_id = ?", (thread_id,))`,
     `conv["demo_session"] == login.session_id`; `run.db.count("conversations", "demo_session = ?", (login.session_id,)) == 1`.
   - "3c one turn" (`needs=TURN_NEEDS, operations=("submitTurn",), selectors=("chat.ready", "chat.composer", "chat.send", "chat.entry.customer", "chat.entry.assistant", "chat.block.text")`):
     script the three roles (§4.9); `locate(page, "chat.ready").wait_for()`; `mark`; `locate(page, "chat.composer").fill(CUSTOMER_TEXT)`;
     `locate(page, "chat.send").click()`; `ex = wait_for(page, "submitTurn", since=mark)`; `ex.status == 200`;
     `sent_turn_id = json.loads(ex.request_body)["turn_id"]`; `resp = json.loads(ex.body)`; `resp["turn_id"] == sent_turn_id`;
     wait until `locate(page, "chat.entry.assistant").count() >= 2`; `reply = locate_in(locate(page, "chat.entry.assistant").last, "chat.block.text").inner_text().strip()`;
     `turn = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (sent_turn_id,))`; `turn["status"] == "completed"`;
     `turn["thread_id"] == thread_id`; `stored = [b["text"] for b in json.loads(turn["response"])["blocks"] if b["type"] == "text"]`;
     `stored == [reply]` and `reply == RESPONDER_TEXT`; `run.script.problems() == ()`; `run.script.remaining() == 0`
     (PA-3); `run.db.count("turns", "thread_id = ?", (thread_id,)) == 1`; screenshot `after-reply`.
   - "3d reload resumes" (`needs=TURN_NEEDS, operations=("getChatThread",), selectors=("chat.entry.customer", "chat.entry.assistant", "chat.block.text")`):
     `mark`; `page.reload()`; `read = wait_for(page, "getChatThread", since=mark)`; `read.status == 200`;
     `read.path.endswith("/" + thread_id)`; `"startChatSession" not in bp.net.operations(mark)` and
     `"submitTurn" not in bp.net.operations(mark)`; visible: the customer entry text contains `CUSTOMER_TEXT`, the last
     assistant entry's text block equals `reply`, and the customer entry is drawn above that assistant entry
     (`customer.bounding_box()["y"] < assistant.bounding_box()["y"]`; both boxes not `None`);
     DB still `count("conversations", "demo_session = ?", …) == 1` and `count("turns", "thread_id = ?", …) == 1`;
     screenshot `after-reload`.
   - "3e greeting after reload" (`needs=CHAT_NEEDS, operations=("getChatThread",), selectors=("chat.entry", "chat.block.text")`):
     first entry's text block == greeting; `json.loads(read.body)["turns"][0]["turn_id"] == "greeting"`. (AEA-40-1 is on `main`
     since `f466ff7`: this assertion runs whenever the step's needs are bound. On `main` `3725c90` the step reports
     `blocked-on AEA-51` through `reply_composer` (and the UX session through its selectors), never `blocked-on AEA-40`.)
4. **`test_reload_resumes_without_new_session(browser_journey, device)`** — both widths (AC-4).
   - "4a sign in" as 3a. "4b reload before a turn" (`needs=CHAT_NEEDS, operations=("startChatSession", "getChatThread"), selectors=("screen.scr1",)`):
     wait `startChatSession`; `thread_id`; `mark`; `page.reload()`; wait `getChatThread` since mark with path ending
     `thread_id`; `bp.net.operations(mark).count("startChatSession") == 0`.
   - "4c one turn then reload" (`needs=TURN_NEEDS, operations=("submitTurn", "getChatThread"), selectors=("chat.ready", "chat.composer", "chat.send")`):
     script, type, send, wait `submitTurn` (200); `mark`; reload; wait `getChatThread`; after `mark`: no
     `startChatSession`, no `submitTurn`. Print `"operations: " + ", ".join(bp.net.operations())`.
5. **`test_sign_out_restores_the_guard(browser_journey, device)`** — both widths (AC-5).
   - "5a sign in and start" (`needs=CHAT_NEEDS, operations=("login", "startChatSession"), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`): 3a then wait `startChatSession`; keep `thread_1`, `session_1`.
   - "5b signed-in deep link" (`needs=SIGN_IN_NEEDS`): `r = page.goto("/staff/queue")`; `r.status == 200`;
     `r.request.redirected_from is None`.
   - "5c sign out" (`needs=SIGN_IN_NEEDS, operations=("logout",), selectors=("shell.sign_out",)`): `sign_out_via_shell`;
     no cookie named `mhc_session` with a non-empty value in `context.cookies()`.
   - "5d guard again" (no extra needs): `hop = first_hop(page.goto("/"))` → 303, `REDIRECTS["/"]`;
     `f = page_fetch(bp, f"/api/chat/sessions/{thread_1}")`; `f["status"] == 401`;
     `json.loads(f["text"])["error"]["code"] == "UNAUTHENTICATED"`; the matching exchange (last `getChatThread`)
     passes `assert_response_matches(to_httpx(ex), "getChatThread")` here too.
   - "5e sign in again starts fresh" (`needs=CHAT_NEEDS, operations=("login", "startChatSession", "getChatThread"), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`):
     `mark`; `login_2 = sign_in_via_form(run, bp)`; `login_2.session_id != session_1`; wait `startChatSession` since
     mark; `bp.net.operations(mark).count("startChatSession") == 1`; `thread_2 != thread_1`;
     `f = page_fetch(bp, f"/api/chat/sessions/{thread_1}")` → 404 and code `SESSION_NOT_FOUND` (Decision 6 A, D-8).
     Print the operation sequence after `mark` and the 404 body (it holds only `error` and `request_id`).
6. **`test_no_dev_params_or_foreign_hosts(browser_journey)`** — DESKTOP (AC-8).
   - "8a signed-out loads" (no needs): `page.goto("/")`; `page.goto(PROBE)` (must redirect: first hop 303);
     `page.goto("/login")`; `wait_for_load_state("networkidle")`; then the checks below.
   - "8b signed in" (`needs=SIGN_IN_NEEDS, operations=("login",), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`):
     sign in; wait 1 s with `page.wait_for_timeout(1000)`; the checks again.
   - Checks: `bp.net.origins() == {run.base_url}`; `bp.net.dev_param_hits(allowed_urls=(PROBE,)) == []`;
     `run.server.port not in FORBIDDEN_PORTS`; no request URL's port in `FORBIDDEN_PORTS`;
     `all(isinstance(m, ScriptedModel) for m in run.models.values())`; `run.guard.blocked == []`.
     Print `origins: {…}` (one entry).
7. **`test_secrets_absent_from_evidence(browser_journey, capsys)`** — DESKTOP (AC-9).
   - "9a sign in" (`needs=SIGN_IN_NEEDS, operations=("login",), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`): sign in;
     screenshot `signed-in`.
   - "9b cookie flags" (`needs=SIGN_IN_NEEDS`): `c = [x for x in context.cookies() if x["name"] == "mhc_session"]`;
     `len(c) == 1`; `c[0]["httpOnly"] is True`; `c[0]["sameSite"] == "Lax"`; `c[0]["secure"] is False`;
     `"mhc_session" not in page.evaluate("document.cookie")`.
   - "9c secret values absent" (`needs=SIGN_IN_NEEDS`): `values = {"demo password": pw, "session secret": secret, "mhc_session value": c[0]["value"]}`;
     `places = {"server logs": run.logs.all_text(), "screenshot names": "\n".join(p.name for p in shots_dir.glob("*")),
     "test id": request.node.nodeid, "record": render_record(RecordData("AEA-58", browser_record_values(build_record_data(scope="AEA-58", collector=run.collector, root=REPO_ROOT, command="j1"), brun.session, collector=run.collector, root=REPO_ROOT))),
     "pytest output": capsys.readouterr()…}`; for each value compute `hits = {where: text.count(value) for where, text in places.items()}`
     and `assert sum(hits.values()) == 0, f"{label}: {hits}"` (**counts only**: never put a secret in an `assert`
     expression pytest would print); and `found = len(run.files_containing(value))`, `assert found == 0, f"{label}: {found} working-copy files"`
     for all three values (the DB stores `token_hash`, never the token). Take `captured = capsys.readouterr()` once for
     the "pytest output" place, then re-print `captured.out` (`print(captured.out, end="")`) so the evidence lines stay
     visible. Print `secret hits: 0 per value`. The test signature is
     `test_secrets_absent_from_evidence(browser_journey, capsys, request)`.
   - "9d show password never ticked" (`selectors=("login.show_password",)`): `page.goto("/login")` is not possible
     while signed in (it may redirect in-app); so open a **second** page `bp2 = brun.open(DESKTOP)` (signed out,
     fresh context), `bp2.page.goto("/login")`, `fill_login(run, bp2, password=…)`, then
     `locate(bp2.page, "login.show_password").is_checked() is False`; screenshot `login-filled` (the password is
     masked). Do not submit.
8. **`test_issued_db_unchanged(browser_journey)`** — DESKTOP (AC-10).
   - "10a hash after signed-out loads" (no needs): load `/`, `/login`; `sha256_file(ISSUED_DB) == run.env.issued_sha256_before`;
     `run.env.db_path.resolve() != ISSUED_DB.resolve()` and `run.env.db_path.exists()`.
   - "10b hash after sign-in and start" (`needs=CHAT_NEEDS, operations=("login", "startChatSession"), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`):
     sign in, wait `startChatSession`; the hash again. Print both hashes.
9. **`test_browser_path_records(browser_journey)`** — DESKTOP (AC-11).
   - "11a page records signed out" (no needs): `r = page.goto("/")`; `hop = first_hop(r)`;
     `rec = run.logs.wait_for("request", lambda x: x["request_id"] == hop.headers["x-request-id"])` →
     `rec["route"] == "spa_fallback"`, `rec["status"] == 303`, `rec["caller_role"] == "anonymous"`;
     same for the final `/login` response (`r`): `route == "spa_fallback"`, `status == 200`. For an asset: open a new
     page `bp2 = brun.open(DESKTOP)` and run `with bp2.page.expect_response(lambda x: "/assets/" in x.url) as info: bp2.page.goto("/login")`;
     `rid = info.value.headers["x-request-id"]` → its record has `route == "/assets/{file}"`, `status == 200`,
     `caller_role == "anonymous"`. Every one of these three responses carries `x-request-id` (web.md §6 step 1).
   - "11b auth_event ok" (`needs=SIGN_IN_NEEDS, operations=("login",), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`):
     `login = sign_in_via_form(...)`; `rid = login.login.header("x-request-id")`;
     `ev = run.logs.wait_for("auth_event", lambda x: x["request_id"] == rid)`; `ev["outcome"] == "ok"`;
     `ev["session_id"] == login.session_id`.
   - "11c auth_event logged_out" (`needs=SIGN_IN_NEEDS, operations=("logout",), selectors=("shell.sign_out",)`):
     `ex = sign_out_via_shell(...)`; its `auth_event` `outcome == "logged_out"` and `session_id == login.session_id`.
   - "11d conversation record" (`needs=CHAT_NEEDS, operations=("login", "startChatSession"), selectors=(*SIGN_IN_SELECTORS, "screen.scr1")`):
     sign in again; `ex = wait_for(page, "startChatSession")`; `thread_id = json.loads(ex.body)["thread_id"]`;
     `run.db.count("conversations", "thread_id = ?", (thread_id,)) == 1`; its `request` record (by
     `ex.header("x-request-id")`) has `status == 201` and `caller_role == "customer"`.
   - "11e turn record" (`needs=TURN_NEEDS, operations=("submitTurn",), selectors=("chat.ready", "chat.composer", "chat.send")`):
     one scripted turn; `run.db.count("turns", "turn_id = ?", (sent_turn_id,)) == 1`; its `request` record has
     `status == 200` and `caller_role == "customer"`. Print each record's `record`, `route`, `outcome` / `status` and ids.

### Step 11 — `tests/journeys/j9/test_aea_58.py` (J-9 rate-limited login, AC-6)

Header as step 10 with `J9 = "J-9"`, `REFUSED_LINE`, `THROTTLE_LINE` (§4.7, each with its source comment).
**`test_rate_limited_login_throttle_line(browser_journey, device)`** — both widths; each test has its own server, so
the limiter is fresh (AC-6 "on its own server instance").

1. "9a wrong pair refused" (`needs=LOGIN_NEEDS, operations=("login",), selectors=(*SIGN_IN_SELECTORS, "login.message.refused")`):
   `page.goto("/")` (303 → SCR-12); `wrong = "wrongpass" + letters(12)` (AEA-57 `env.letters`); `mark`;
   `fill_login(run, bp, password=wrong)`; click submit; `ex = wait_for(page, "login", since=mark)`; `ex.status == 401`,
   code `LOGIN_FAILED`; `locate(page, "login.message.refused").inner_text().strip() == REFUSED_LINE`;
   `locate(page, "login.password").input_value() == ""`; `locate(page, "login.username").input_value() == run.demo_username`
   (compare, never print).
2. "9b rejects up to the limit" (same needs/selectors): `limit = run.container.limits.web.login_rejects_per_ip`; repeat
   step 1's fill (password only: `locate(page, "login.password").fill(wrong)`), submit and wait until **`limit`** login
   exchanges in total answered 401. *Invariant: the number comes from `Limits`, never a literal.*
3. "9c right pair throttled" (same needs, `selectors=SIGN_IN_SELECTORS`): fill the **right** password, submit;
   `ex.status == 429`; code `LOGIN_RATE_LIMITED`; header `retry-after` present; no `mhc_session` cookie with a value
   in `context.cookies()`; `run.db.count("staff_sessions") == 0`. Print `401 ×{limit}, then 429`.
4. "9d throttle line shown" (`selectors=("login.message.rate_limited",)`):
   `locate(page, "login.message.rate_limited").inner_text().strip() == THROTTLE_LINE`; `THROTTLE_LINE != REFUSED_LINE`;
   screenshot `throttled`. (Reported `blocked-on UX session` until the line and its row exist.)
5. "9e records" (`needs=LOGIN_NEEDS`): `outcomes = [r["outcome"] for r in run.logs.structured("auth_event")]`;
   `outcomes.count("rejected") == limit`; `outcomes.count("rate_limited") == 1`; every `session_id` is `None`.

Order matters: put "9e records" **before** "9d" so a blocked throttle line does not hide the records check.

### Step 12 — `README.md` (AC-15) and `serve.py`

`serve.py` (`python -m tests.journeys.browser.serve`):
1. Refuse to start (exit 2, message naming both variables) unless `MERIDIAN_DEMO_USERNAME` and
   `MERIDIAN_DEMO_PASSWORD` are set in the shell (the walker chooses synthetic values; nothing is printed or invented).
2. `build = check_production_build(dist_dir_from_env())`.
3. Same composition as `open_browser_journey`, but `browser_environ(...)` values for the two demo names are replaced by
   the shell's; `collector = StepCollector()`; `strict=False`; `nodeid="serve"`.
4. Pre-load the J-1 script once (§4.9) so the walker's first turn gets the J-1 reply.
5. Print exactly: `serving <base_url> (production build <dist>, scripted model; sign in with MERIDIAN_DEMO_USERNAME / MERIDIAN_DEMO_PASSWORD from your shell). Ctrl-C to stop.`;
   block on `threading.Event().wait()` inside `try/except KeyboardInterrupt`.

`README.md` sections, in this order (plain sentences, commands in code blocks):
1. *What it is* (three lines: production build, real app, real login, scripted model, level).
2. *Prerequisites*: system Chrome (`/usr/bin/google-chrome`), Node 24, `df -h /home`; never `playwright install`.
3. *Build*: `npm --prefix apps/web run build && npm --prefix apps/web run check:dist`; in a backend worktree without
   `node_modules`, build in the primary checkout and `export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist`.
4. *Run*: the reviewer command (§7 C-6) and the merge-gate command
   (`uv run python -m tests.journeys.affected --base <sha> -- --browser-channel chrome`, after the build).
5. *Watch it headed*: add `--headed --slowmo 300` (never `--tracing`, `--video` or `--screenshot` from pytest-playwright
   when recording evidence: traces hold typed text).
6. *Walk J-1 by hand* (wave walkthrough): set the two demo variables in your shell; `uv run python -m tests.journeys.browser.serve`;
   open the printed URL with chrome-devtools MCP (`navigate_page`), or a headed Chrome; walk: `/` → SCR-12 → sign in →
   greeting → type "Hi, what can you help me with?" → reply → reload → same thread → Sign out → `/` redirects. Never
   tick "Show password" and never screenshot a filled password field unmasked.
7. *Which journeys a wave touched*: `uv run python -m tests.journeys.affected --base <wave base> --list-only`.
8. *Records and screenshots*: `--journey-record=<scope>` writes `docs/testing/journeys/<date>-<scope>.md` and
   screenshots in `docs/testing/journeys/<date>-<scope>/`; walkthrough records are
   `docs/testing/journeys/<date>-wave-N-walkthrough.md` with the nine fields of integrated-journeys §4.
9. *Adding a browser journey later*: one file `tests/journeys/j<N>/test_aea_<NN>.py` with
   `pytest_plugins = ("tests.journeys.browser.plugin",)`, the `browser_journey` fixture, `browser_step`, selectors only
   by key from `selectors.py`; a missing helper is a follow-up on AEA-58 merged first.
10. *Selectors*: how a `selectors.md` row becomes a `SelectorRow` (step 5's transcription rule).

### Step 13 — run, record, context rows, commits

1. Iterate with C-1…C-4 (§7) until green (pass or *blocked*, never red).
2. Run C-6 with `--journey-record=AEA-58` → `docs/testing/journeys/<date>-AEA-58.md` and its screenshot folder.
   Read the file: nine fields filled; *Blocked by* lists each run-time owner (expect `AEA-51, UX session` on
   `main` `3725c90`).
3. **Commit 1** (code): `git add tests/journeys/browser tests/journeys/j1/test_aea_58.py tests/journeys/j9/test_aea_58.py pyproject.toml uv.lock`;
   message `test(AEA-58): browser journeys on the production build (J-1, J-9)` + body (what, levels, blocked owners) +
   last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
4. Context rows (AC-17), using commit 1's short SHA `<sha>`:
   - `.claude/reference/area-map.md`, row `3+`, last cell: replace `; the rest planned` with
     `; `tests/journeys/browser/` (browser fixtures, selector module, response check, walkthrough recipe) and J-1 / J-9 in the browser `tests/journeys/j1/test_aea_58.py`, `tests/journeys/j9/test_aea_58.py` actual (AEA-58, `<sha>`); the rest planned`.
   - `.claude/state/icm-progress.md`: the *Integrated-journey protection* row whose evidence cell begins
     `2026-10-21: harness \`tests/journeys/support/\` + J-1 (AEA-57` (the file has a second, older row with the same
     name whose evidence begins `2026-10-21: [integrated-journeys rule]`; leave that one alone, §8 R-10). Evidence cell →
     `2026-10-2x: harness + J-1 API (AEA-57, `2788964`); browser J-1/J-9 on the production build (AEA-58, `<sha>`); records [`…-AEA-57.md`](…), [`…-AEA-58.md`](…) list blocked steps and owners` (≤ 400 chars);
     next cell → `Every J-1 browser step integrated under --journeys-strict (needs AEA-51 and the UX selector contract)`.
   - `docs/design/code-design.md` §9: in the `journeys/` lines replace `browser/ (AEA-58)` with
     `browser/ = AEA-58's browser fixtures (system Chrome via pytest-playwright, the production build served by the real app, the one selector module, the response check, the walkthrough recipe)`;
     in the *Built on `main`* sentence insert `; `tests/journeys/browser/`, `j1/test_aea_58.py`, `j9/test_aea_58.py` (AEA-58, `<sha>`)`
     immediately before its closing `; the rest of this tree is planned.` (keep the AEA-11, AEA-57 and AEA-59 entries).
5. **Commit 2** (docs): `git add docs/testing/journeys/<date>-AEA-58.md docs/testing/journeys/<date>-AEA-58 .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`;
   message `docs(AEA-58): journey record and context rows` + the Co-Authored-By line. No push.

### What the implementer must NOT do

- Edit anything under `tests/journeys/support/`, `tests/conftest.py`, `tests/api/openapi_check.py`, `src/meridian/`,
  `apps/web/`, `docs/ux/`, the OpenAPI, `UI_CONTRACTS.md`, `PROJECT-CHECKLIST.md`, or another ticket's journey file.
- Invent a selector, use copy text as a selector, or read `apps/web/src` to fill a selector gap (AC-16). Copy text is
  only ever an **expected value** (§4.7).
- Use `?signedin`, `?role`, `?scenario`, `?staffing`, `?ex`, `?delay` anywhere except the one `PROBE` navigation.
- Use pytest-playwright's `page`, `context` or `browser` fixtures, `TestClient`, `dependency_overrides`, or a monkeypatch
  of `meridian`.
- Build `apps/web` inside a test; run `playwright install`; add `node_modules` to the worktree; bind 4019 or 5184.
- Print, assert-compare in a printable expression, log or write the demo password, session secret or `mhc_session` value;
  tick "Show password".
- Turn a blocked step into a pass, a skip with another message, or a removed assertion; `pytest.skip` directly (use
  `browser_step`).
- Call `page.wait_for_load_state("networkidle")` after a sign-in: the signed-in shell polls and holds an SSE stream open,
  so the network never goes idle. Signed-out pages (steps 2b, 8a) are the only `networkidle` waits; signed in, wait for a
  named operation (`bp.net.wait_for`) or `page.wait_for_timeout(…)`.
- Treat a `500` as "blocked" beyond PA-4's exact rule. A 500 is an undocumented status and fails the teardown (AC-7);
  report it with the server log line. Only an **unrouted** operation (PA-2), or a 500 from an operation in
  `UNBOUND_500_NEEDS` while one of its listed services is not bound (PA-4), is counted as blocked. Never add an
  operation or a need to `UNBOUND_500_NEEDS` to make a run green.
- Read `eval/cases/heldout/` or any key directory; call a paid model; `git add -A`; push; force-push.

---

## 6. Data and fixtures

Synthetic only. The demo pair and session secret are random per run (`support/env.py` `journey_environ`); the wrong
password is `"wrongpass" + letters(12)`. The DB is the issued scheduling DB copied by the app's first boot into a temp
folder (`docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite`, never written; hash checked). The
J-1 turn script is AEA-57's (`tests/journeys/j1/test_aea_57.py`). The frontend is `apps/web/dist` from
`npm run build` (git-ignored). No customer identity, code, card-like number or phone number appears in any test.

---

## 7. Checks

All commands from the worktree root with `export UV_LINK_MODE=hardlink` and
`export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist` (step 0.3). Cap any browser
run with `perl -e 'alarm 300; exec @ARGV'`. pytest `-n 2` at most (not needed here).

| # | When | Command | Passing looks like |
|---|---|---|---|
| C-1 | while iterating | `uv run pytest tests/journeys/browser/test_browser_support.py -q -rs` | all pass |
| C-2 | while iterating | `perl -e 'alarm 300; exec @ARGV' uv run pytest -m journey tests/journeys/j1/test_aea_58.py tests/journeys/j9/test_aea_58.py --browser-channel chrome -rs` | every test passed or skipped with `blocked-on <owner>`; no failures, no errors |
| C-3 | before the final commit (fast gates, cheapest first) | `uv run ruff format --check . && uv run ruff check . && uv run mypy` | clean |
| C-4 | before the final commit (affected tests) | `uv run pytest tests/journeys/support -q` then `perl -e 'alarm 300; exec @ARGV' uv run python -m tests.journeys.affected --base main -- --browser-channel chrome -rs` (pyproject, uv.lock and `tests/journeys/` changed → every journey is selected) | AEA-57's self-checks pass; every journey passes or is blocked; 0 failures |
| C-5 | before the final commit | `uv run pytest -m journey --collect-only -q` and `uv run pytest --collect-only -q` | the first lists `tests/journeys/j1/test_aea_57.py::…` and `tests/journeys/j1/test_aea_58.py::…` together (AC-13); the second collects the whole suite with no error (the new plugin loads into every session) |
| C-6 | evidence (AC-1, AC-13, AC-14) | `npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run build && npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run check:dist && perl -e 'alarm 300; exec @ARGV' uv run pytest -m journey tests/journeys/browser tests/journeys/j1/test_aea_58.py tests/journeys/j9/test_aea_58.py --browser-channel chrome --journey-record=AEA-58 -rs` | exit 0; terminal shows `dist is clean: no dev-layer markers`, `production build: … index.html sha256 …`, `browser: Chrome channel chrome version …`, the validation summary with `failures: 0`, and `journey record: …` |
| C-7 | AC-12 | `MERIDIAN_WEB_DIST_DIR=$(mktemp -d) uv run pytest -m journey tests/journeys/j1/test_aea_58.py -q` | **errors** (not skips) whose text names `npm --prefix apps/web run build` and `MERIDIAN_REQUIRE_FRONTEND` |
| C-8 | AC-13, AC-10 | `git -C /home/linuxuser/workspaces/inno-aea-callcenter status --porcelain apps/web`; `grep -rn heldout tests/journeys/browser tests/journeys/j1/test_aea_58.py tests/journeys/j9/test_aea_58.py`; `grep -rnE "locator\(\|get_by_" tests/journeys --include=*.py \| grep -v tests/journeys/browser/selectors.py` | all three print nothing |
| C-9 | AC-17 | `git diff --stat main...HEAD` | only the owned files of §2 |
| C-10 | capture verification (WF-1, WF-18, WF-19; AC-11) | inside C-2: `tests/journeys/j1/test_aea_58.py::test_browser_path_records` and the J-9 step "9e records" | 11a passes on today's `main` (`spa_fallback` 303/200 and `/assets/{file}` 200 records, `caller_role` `anonymous`, `x-request-id` on each); 11b–11e and 9e pass or report `blocked-on` their owners (on `main` `3725c90`: AEA-51 and the UX session) |

**Reds already on `main` (not this ticket's; do not fix, do not count against it):**
`tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0` (stale since the first journey
landed, AEA-57 ledger row; still present at `3725c90`). The four `tests/graph/test_spine.py` stub rows noted at the
first refresh were fixed on `main` (`f63ec50`). Neither file is in C-1…C-5. If the merge agent's full suite shows them, it compares with the same run on `main` and
treats only new reds as this ticket's.

**Full suite:** `pytest-playwright` is a new dev dependency and a pytest plugin that loads into every session, so this
change "reaches everything" (`build-loop-test-scope.md`). The **merge agent** runs the full suite at this ticket's merge
(`uv run --with pytest-xdist pytest -n 2 -q`, with `MERIDIAN_WEB_DIST_DIR` set and the build present); the implementer
runs C-5's whole-suite collect instead of a second full run. Tests the implementer writes: everything in steps 9–11
(the `[journey]` test is `test_j1_login_turn_refresh_resume`). Existing tests that must stay green: `tests/journeys/support/test_support.py`,
every `tests/journeys/j*/test_aea_*.py`, and the whole suite at merge.

---

## 8. Risks and requests

- **R-1 (biggest): the UX selector contract does not exist** (re-checked at `3725c90`: no file, no commit ever touched
  that path, and none of the contract's `data-*` hooks is in `apps/web/src`). `docs/plans/ux-join/selectors.md` was due before UX-4
  sign-off (`FOR-UX-SESSION.md` §2) but UX-4 was signed without it, and `apps/web` has only `data-screen="SCR-1"` and
  `data-entry`. Consequence: every on-screen step (sign-in form, SCR-12 drawn, chat entries, composer, sign-out, refusal
  and throttle lines) reports `blocked-on UX session` until the file lands and the hooks are in `dist`. AC-3 (the
  `[journey]` criterion) cannot pass in wave 3 without it. **Request to the orchestrator:** ask the UX session (via
  `docs/plans/ux-join/`) to publish `selectors.md` and build the hooks; then a one-file follow-up on AEA-58 transcribes
  the rows into `selectors.py` (step 5). This is the ticket's own rule, not a new decision.
- **R-2: run-time blocked owners on `main` `3725c90`.** AEA-30 (`demo_clock`, `demo_service`) and AEA-40
  (`session_service`, `turn_service`, the CON-1/CON-2 routes) are merged, so `SIGN_IN_NEEDS` is bound and the chat
  operations are routed. Still unbound: `reply_composer` and `run_graph` (AEA-51, wave 3). Because `SessionService.open`
  and `.thread` call `settled_view` → `reply_composer`, every `CHAT_NEEDS` step (3b, 3e, 4b, 5a, 5e, 10b, 11d) and
  every `TURN_NEEDS` step reports `blocked-on AEA-51`, and the shell's own `startChatSession` 500 is counted under PA-4.
  Under `--journeys-strict` all of them fail, as intended. **The wrong-pair and throttled paths need only
  `login_sessions`:** `routes/auth.py` answers `401 LOGIN_FAILED` / `429 LOGIN_RATE_LIMITED` before `sessions.start`
  reads the demo clock, so J-9 keeps `LOGIN_NEEDS = ("login_sessions",)`. If C-2 shows a 500 on a wrong pair, report
  it as a finding with the log line; do not relabel the step as blocked.
- **R-3: duplication with AEA-57's `open_journey`.** `server.open_browser_journey` repeats ~35 lines because
  `journey_environ` hard-codes the no-frontend settings and `support/` is AEA-57's. Optional follow-up on AEA-57 (not
  requested now): an `environ_overrides` argument on `open_journey`, after which `server.py` shrinks to a call.
- **R-4: the merge gate must build `dist` first.** `affected.py` selects every journey (browser ones included) when
  `tests/journeys/`, `apps/web/`, `pyproject.toml` or `uv.lock` change. Without a build the browser tests **error**
  (by design, AC-12). The merge agent must run the build (primary checkout) and set `MERIDIAN_WEB_DIST_DIR` before the
  journey gate; the README says so. System Chrome must be present (it is on the VPS).
- **R-5: shared-file collisions in wave 3.** AEA-51, AEA-52 and AEA-60 may also edit area-map row `3+`, the
  icm-progress journey row and DO-3 §9's `tests/` tree. Each edit is one cell; the merge agent keeps both sides.
  `pyproject.toml` / `uv.lock`: no other wave-3 ticket is known to add a dependency; if one does, the second merge
  regenerates the lock.
- **R-6: the record is written twice per run.** AEA-57's recorder writes the API-level wording, then this plugin's
  `trylast` hook rewrites the same file with browser values. Deterministic (pluggy calls `trylast` hooks last); if
  AEA-57 ever marks its hook `trylast`, the order must be re-checked.
- **R-7: screenshots and secrets.** Screenshots are taken only of masked fields; Playwright tracing/video stay off. If a
  future helper types into a visible field, AC-9's file-name and log scans do not cover image pixels; keep "Show
  password" untouched.
- **R-8: pytest-playwright side effect.** Its autouse session fixture deletes `<cwd>/test-results/` at session start
  (nothing of ours lives there).
- **R-9: dependency footprint.** `uv add --dev "pytest-playwright>=0.10"` also pulls its own dependencies (among them
  `playwright`, `greenlet`, `pyee`, `pytest-base-url` and what they need); all of them land in `uv.lock` only, never as
  extra `pyproject.toml` lines. `pytest-base-url` adds a `base_url` fixture and a `--base-url` option; this plan uses
  neither (contexts get `base_url=run.base_url` directly). Disk at the second refresh: 16 GB free on `/`; system Chrome
  `153.0.8010.47`; Node `v24.21.0`; `apps/web/node_modules` present in the primary checkout.
- **R-10: duplicate ICM row.** `.claude/state/icm-progress.md` has two *Integrated-journey protection* rows; the older
  (evidence "nothing executable yet") is stale since AEA-57. Not this ticket's to delete (context-maintenance: replace
  evidence in the affected row); reported so the orchestrator's wave-3 context pass can drop it.
- **R-11: the shell's own calls are validated too.** After sign-in the production shell calls `getSession`,
  `getDemoClock`, `getStaffing` and, on SCR-1, `startChatSession` and then `streamChatEvents` (§4.7). On `main`
  `3725c90` the first three are mounted with their services bound (AEA-44, AEA-43, AEA-30), so they are **validated**.
  `startChatSession` is mounted but answers 500 until AEA-51 binds `reply_composer`; PA-4 counts it as *unbound,
  blocked-on AEA-51*. Any other 500 fails the teardown: the implementer reports it with the operationId and the server
  log line and does not suppress it. Today every signed-in step is blocked by the UX selector contract first (R-1), so
  this path is reached in a run only after `selectors.md` and its hooks land.
- **R-12: ledger vs `main`.** `.claude/state/build-ledger.md` lists AEA-58 as blocked on AEA-40, AEA-49, AEA-57 and
  still shows AEA-40's own row as `blocked` (NEEDS-DECISION text), while `git log` on `main` shows
  `f466ff7 Merge AEA-40 sessions and turns` and its code (`routes/chat.py`, the `register_chat` hunk) is present. All
  three blockers' code is on `main`. This plan imports nothing from AEA-40 (its routes are reached over HTTP).
  **Request to the orchestrator:** reconcile the AEA-40 ledger row before dispatch; nothing in this plan depends on it.
- **R-13: PA-4 is a harness rule, not a product change.** It narrows what counts as blocked to three chat operations
  whose services AEA-51 binds, and only for status 500. When AEA-51 merges, `missing_needs` finds nothing missing, the
  same 500 (if it still happens) fails the teardown, and no edit to this ticket's files is needed. A side effect on
  `main` that this ticket does not own: `SessionService.open` writes the `conversations` row and the greeting before it
  calls `settled_view`, so a 500 there may leave a stored conversation behind. The blocked steps never assert on it;
  AEA-51's integration closes it.
- **No contract change needed.** Decisions 5 and 6 (D-7, D-8) are applied as written; WEB-1 is A (D-4). Nothing here asks
  for an OpenAPI or `UI_CONTRACTS.md` edit.

---

## 9. Readiness

**READY.** No import is missing: AEA-57, AEA-49, AEA-23, AEA-44, AEA-30 and AEA-40 are on `main` `3725c90`, and UX-4
is signed. Run-time dependencies (reported as *blocked* steps or PA-4 counts, never imported, never passed): AEA-51
(`run_graph`, `reply_composer`; also every `startChatSession` / `getChatThread` through the settled view), and the UX
session's `selectors.md` plus its hooks in `dist` (R-1). No `NEEDS-DECISION`: Decisions 5 and 6 (D-7, D-8) and WEB-1 A
(D-4) are applied as recorded, and nothing needs an OpenAPI or `UI_CONTRACTS.md` edit.

**Gates.** `gate::ux4`: met (UX-4 signed, Innocent ✓ 2026-10-21). No paid, live or human gate: the suite uses the
scripted model only (AEA-61 owns live smoke). The full suite runs at this ticket's merge because a dev dependency and a
session-wide pytest plugin are added (§7 *Full suite*).
