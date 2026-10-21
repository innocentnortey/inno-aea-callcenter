## [AEA-58] browser journeys: Playwright against the production build

_Conventions for every inno-aea-callcenter issue (from the approved breakdown, `docs/plans/slice-plan.md`):_
repository `/home/linuxuser/workspaces/inno-aea-callcenter` (package `src/meridian/`, tests `tests/`, eval `eval/`); GitLab
`innocentnortey/inno-aea-callcenter`. Read first: `CLAUDE.md`, `.claude/README.md`, `.claude/reference/area-map.md`, the
slice plan's row for this issue, `docs/design/code-design.md` (DO-3) and `docs/design/contracts/internal-components.md`
(DO-4: exact types and signatures). Vocabulary: PRD R-n, US-n, WP-n, HP-n, WF-n, CAP-n, E-n, M-n, CON-n as their owner
documents define them. Workflow: `lane::build-loop` issues run plan (`fanout-planner`, plan meets
`to-tickets/templates/implementation-plan.md`) → implement (`fanout-implementer`) → test → `code-review-agent`; affected tests
only (`.claude/rules/build-loop-test-scope.md`); `risk::security` issues get frozen failing tests first and the security
agent at their wave merge. **Siblings in the same or a later wave are called through their DO-4 signature by injection
(constructor, `GraphDeps`, or `web/deps.py`) and tested with a double; a plan that needs more than that signature records
`blocked-on AEA-NN` instead of inventing behaviour.** Never: edit the briefing, issued data or `docs/archive/`; edit
`docs/ux/03-structure/ui-contracts.openapi.yaml` or `UI_CONTRACTS.md` (a needed change stops the issue and goes to
Innocent); touch `apps/web/**` or `docs/ux/**`; edit another issue's owned file (collision map, slice plan §3); put a
secret, verification code, card-like number or full phone number in code, logs, traces, fixtures or test names; call a
paid model in a default test (mark `live`); bind ports 4019 or 5184; `git add -A`. Evidence: every criterion names its
test or command and the result a reviewer should see; numbers come from runs, never from targets.

### What to build

> **US-28:** "As a **reviewer**, I need to sign in once with the demo login given in the README and then switch between
> acting as the customer and acting as a representative, supervisor or business owner in one click from any screen …"
> Acceptance (R-48): "Every route except the login and `/healthz` refuses an unsigned request".

**What it does, in practice.** A reviewer runs one command. It builds UX-4's React app the production way, starts the
**real** FastAPI app (built from `web/container.py`) on an ephemeral port over a disposable copy of the issued scheduling
DB, with the deterministic scripted model adapter at the provider boundary, and drives system Chrome through it:

1. **Guard redirect.** Signed out, Chrome opens `/`. The server answers `303 See Other` to
   `/login?return_to=%2F&reason=none` (web.md §6, WEB-28) and SCR-12 draws. The same holds for a deep link,
   `/staff/queue` → `/login?return_to=%2Fstaff%2Fqueue&reason=none`, and for `/?signedin=1&role=owner`: the UX track's
   dev-only parameters do nothing against the real guard.
2. **Sign in.** The test types the harness's demo pair into SCR-12's form and presses "Sign in": a real CON-22
   `POST /api/login`. The `mhc_session` cookie is HttpOnly and SameSite=Lax (web.md §2), and the app lands on the page
   in `return_to`, here SCR-1 as the customer.
3. **Start a chat and take one turn.** SCR-1 calls CON-1 `startChatSession`, and the fixed greeting shows. The test types
   the J-1 turn AEA-57's script plays and sends it (CON-2 `submitTurn`); the reply shows. The DB copy now holds one
   `conversations` row owned by this login session and one completed turn with that `turn_id`.
4. **Refresh and resume.** The test reloads the tab. The app reads the same thread (`getChatThread`; the thread id is
   kept per tab, SCREEN_SPECS N-31) and does not call `startChatSession` again. The greeting, the customer's turn and the
   reply show in order. The DB still has one conversation and one turn: nothing was resubmitted.
5. **Signed out again.** "Sign out" (CON-22 `logout`) clears the cookie. Reloading `/` answers the 303 again, and a
   `getChatThread` call from the page answers 401 `UNAUTHENTICATED`.

Every `/api/*` response Chrome receives is validated with AEA-23's one checker
(`tests/api/openapi_check.py::assert_response_matches`, web.md §13). The issued DB file's SHA-256 is the same before
and after the run. The result is written as an evidence record at level **`integrated with a scripted model`**
(integrated-journeys §4).

**How it works.**
- **Runner.** pytest with `pytest-playwright` (Python), so backend and browser journeys run under one command and one
  `journey` marker (AEA-01 registers it). It uses system Chrome (`--browser-channel chrome`, the same channel as
  `apps/web/playwright.config.ts`), so no browser is downloaded. The disk is tight: check `df -h /home` first.
- **Server.** AEA-57's `tests/journeys/support/` builds the app, the scripted adapter, the ephemeral-port launcher, the
  login helper, the DB-state reader and the evidence-record writer. This ticket reuses them unchanged. It adds only what
  a browser needs, on top of them: the server is started with `Settings.web_dist_dir` = the build (from
  `MERIDIAN_WEB_DIST_DIR`, default `apps/web/dist`, graph-core §12) and `require_frontend=True`, so a missing build fails
  start-up loudly, naming `MERIDIAN_REQUIRE_FRONTEND` and the path (web.md §12, WEB-30; AEA-49 AC-5). Authentication,
  the login gate, rate limits, validation, the SQLite working copy and the checkpointer are all **on**. The dev-only
  sign-in parameters (`?signedin`, `?role`, `?scenario`, apps/web README) are never used.
- **Production build it consumes.** `npm --prefix apps/web run build` (`prebuild` regenerates the committed generated
  types and contract index from the signed OpenAPI, then `tsc -b && vite build` writes `apps/web/dist`). Then
  `npm --prefix apps/web run check:dist`, which fails when a dev-layer marker (`__MHC_DEV_LAYER__`, `mhc.dev.`,
  `Prototype only`, `prototype-synthetic`, `fonts.googleapis`) is in `dist`. The image builds the same way
  (`npm ci && npm run build`, data.md §7, DAT-21). This ticket reads `dist`; it never edits anything under `apps/web/`.
  `dist` is git-ignored.
- **Browser settings** are taken from `apps/web/playwright.config.ts`: viewports 1280×800 (`chrome-desktop`) and 390×844
  (`chrome-phone`), locale `en-US`, timezone `America/Chicago`, reduced motion. J-1 runs at both widths, because SCR-1
  and SCR-12 are phone-first.
- **Selectors** live in one module in `tests/journeys/browser/`, transcribed from the UX session's selector contract
  (`docs/plans/ux-join/`). A UX change is then one edit there, and no test file holds a selector string of its own.
- **Recipe.** `tests/journeys/browser/README.md` is the wave-walkthrough recipe (integrated-journeys §5, §6): how to
  build, how to start the server headed or attach chrome-devtools MCP, which journeys a wave touched, where screenshots
  and the record go.

**Verification levels used in this ticket** (integrated-journeys §4). Every journey criterion proves
**`integrated with a scripted model`**: real server, real DB copy, guards on, production build, scripted adapter. No
criterion here proves `verified with live models`: that is AEA-61's budgeted live smoke, never part of this suite or a
merge gate. The UX track's Prism sweep (`apps/web/tests/e2e/`) stays `mock-tested` and is not this ticket's evidence.

**What it extends for later tickets.** Each later ticket that moves a journey step into the browser adds **one file**,
`tests/journeys/j<N>/test_aea_<NN>.py` (one file per ticket per journey, slice plan §0a and §3 *tests/journeys/* row),
using this ticket's browser fixtures and AEA-57's `support/` without editing either. A missing helper is a follow-up
on this ticket (browser) or AEA-57 (`support/`), merged first. This ticket's own journeys follow the same convention:
`tests/journeys/j1/test_aea_58.py` (J-1 in the browser) and `tests/journeys/j9/test_aea_58.py` (the rate-limited login
state of J-9). They are the proof that the convention works from outside `browser/`.

**The exact command a reviewer runs** (the time cap is the apps/web README's rule for Playwright):

```
npm --prefix apps/web run build && npm --prefix apps/web run check:dist && \
perl -e 'alarm 300; exec @ARGV' uv run pytest -m journey tests/journeys/browser tests/journeys/j1/test_aea_58.py tests/journeys/j9/test_aea_58.py --browser-channel chrome
```

**Produced for other issues.** AEA-55 waits for this ticket: the first integrated browser evidence arrives a wave before
the UX-5 rerun. The wave-merge and pre-deploy journey gates (`build-loop-test-scope.md`, *AEA addition*) gain the
browser journeys. Later tickets get the browser fixtures and the `j<N>/test_aea_<NN>.py` pattern. The wave walkthrough
gets its recipe.

### Source

- Slice plan §0a (Amendment 1: journey map J-1, J-8, J-9; where the two tracks connect; the UX session's deliverables)
  and its row AEA-58 (title, owned `tests/journeys/browser/`, blockers 49, 57 + UX-4 signed, wave 3, `gate::ux4`);
  §3 collision rows `tests/journeys/`, `pyproject.toml`/`uv.lock`, `apps/web/**`.
- `.claude/rules/integrated-journeys.md`: §2 (worked example: build, login, no dev parameters, stored-effect checks,
  issued-DB hash), §3 rules 1, 2 (J-AUTH), 3, 5, 6, 7, §4 (levels and the evidence record), §5 (who runs what), §6
  (AEA-58's row: browser journeys on the production build through the normal login; the walkthrough recipe).
- `.claude/rules/build-loop-test-scope.md` *AEA addition*: the journey suite is part of the merge gate (affected journeys
  at ticket merge, all at wave merge and before deploy; "affected" includes the frontend build input; no paid calls;
  cheapest gate first).
- `docs/design/contracts/stage7/web.md` §2 (cookie, credential check), §5 (`WebLimits.login_rejects_per_ip`, `login`
  answers `429 LOGIN_RATE_LIMITED`), §6 (gate order, `PublicPaths`, the 303, `return_to` guard), §10 (`request`,
  `auth_event` records), §12 (`register_frontend`, missing build), §13 (`assert_response_matches`, `Contract`), §14
  (`SessionService.open` / `thread`); decision ledger `docs/plans/7b-decisions/web.md` WEB-1 (open), WEB-28, WEB-30,
  WEB-31.
- `docs/design/contracts/stage7/graph-core.md` §12 (`Settings.web_dist_dir`, `require_frontend`, `data_dir`,
  `issued_db_path`, `demo_username`, `demo_password`), §2 (`TurnContext`: the scripted adapter replaces only the provider
  call, so nodes and parsers run); `models.md` §1 (`ProviderCall` from scripted fakes), §7 (container wiring:
  `NullTraceSink` when the four `LANGFUSE_*` settings are unset).
- `docs/design/contracts/stage7/data.md` §5–§6 (held-out case and key custody, DAT-2: journeys never read them), §7
  (image builds `apps/web`, DAT-21).
- SCREEN_SPECS SCR-12 (route; states *error* "That username or password didn't work. Check the README and try again.",
  password cleared, username kept; *success* "to the page that was asked for, else SCR-1"), SCR-1 (route `/`; N-31
  thread kept in the tab), N-28 (one refusal for every cause, throttle included). OpenAPI operations `login`, `logout`,
  `getSession`, `startChatSession`, `submitTurn`, `getChatThread`, `streamChatEvents` (read only).
- PRD R-48, R-41; US-28. DO-6 `docs/design/observability-contract.md` rows WF-1, WF-18, WF-19 (CAP-10 and CAP-11 stay
  with AEA-23 and AEA-49; journeys don't re-check redaction, integrated-journeys §1).
- `apps/web/package.json` (`build`, `prebuild`, `check:dist`), `apps/web/scripts/check-dist.mjs`,
  `apps/web/playwright.config.ts`, `apps/web/README.md` (dev parameters; Playwright time cap): read only.
- **Brief check:** serves "Deploy the agent as a web application at a public URL. The interface must be interactive: a
  reviewer should be able to type questions, probe edge cases, and watch the agent escalate." (Part B §6), by proving
  that the interactive path works through the real login before deploy. It touches nothing out of scope and weakens
  nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] The browser suite serves only the production build through the real app: the server starts from `web/container.py` with `web_dist_dir` = the build and `require_frontend=True`, `check:dist` passes on that build, and in the page `window.__MHC_DEV_LAYER__` is undefined and no dev-panel root exists — verify: `tests/journeys/browser/` session fixture plus `tests/journeys/j1/test_aea_58.py::test_serves_production_build` — evidence: the build's `index.html` hash and "dist is clean: no dev-layer markers" in the run log. Level: `integrated with a scripted model`.
- [ ] AC-2 [failure/refusal] Guard redirect, signed out (J-1): `/`, `/staff/queue` and `/?signedin=1&role=owner` each reach SCR-12 through a server `303` (the redirect chain's first response) to `/login?return_to=<encoded path+query>&reason=none`; no `/api/*` call made before sign-in answers 2xx except `login` — verify: `tests/journeys/j1/test_aea_58.py::test_signed_out_pages_redirect_to_login` — evidence: per path, the 303 status, the `Location` and SCR-12 visible, at 1280 and 390. Level: `integrated with a scripted model`.
- [ ] AC-3 [journey] J-1 end to end in the browser (slice plan §0a; integrated-journeys §3 rule 2 J-AUTH): sign-in through SCR-12's form lands on the `return_to` page; SCR-1 shows the greeting; the J-1 turn's reply shows; after a reload the same thread shows greeting, customer turn and reply in order; and the stored state matches what is seen: one `conversations` row owned by this login session, one completed turn whose `turn_id` is the one CON-2 returned, the visible reply text equal to that turn's stored response text blocks, still one of each after the reload (the greeting after the reload depends on AEA-40-1; until it merges, that one assertion is reported *Blocked by* AEA-40, never passed or dropped) — verify: `tests/journeys/j1/test_aea_58.py::test_j1_login_turn_refresh_resume` — evidence: each step pass/fail with the DB-state reader's row counts and ids printed; screenshots after the reply and after the reload. Level: `integrated with a scripted model`.
- [ ] AC-4 [invariant] Resume reads, never re-creates: across the reload Chrome sends `getChatThread` for the same `thread_id` and sends no second `startChatSession` or `submitTurn` — verify: `tests/journeys/j1/test_aea_58.py::test_reload_resumes_without_new_session` (request log from Playwright's `request` events) — evidence: the operation sequence printed, e.g. `login, startChatSession, submitTurn, getChatThread`. Level: `integrated with a scripted model`.
- [ ] AC-5 [failure/refusal] The guard holds again after sign-out and still lets the legitimate path through (integrated-journeys §3 rule 5): signed in, `/staff/queue` answers the page (200, no 303); after "Sign out" (CON-22 `logout`), reloading `/` answers the 303 to `/login?return_to=%2F&reason=none`, and a `getChatThread` fetch from the page answers 401 `UNAUTHENTICATED` valid against the OpenAPI — verify: `tests/journeys/j1/test_aea_58.py::test_sign_out_restores_the_guard` — evidence: statuses and `Location` printed. Level: `integrated with a scripted model`.
- [ ] AC-6 [failure/refusal] J-9 rate-limited login in the browser, on its own server instance so the limiter state cannot leak: a wrong pair shows SCR-12's one refusal line "That username or password didn't work. Check the README and try again." with the password cleared and the username kept; after `Limits.web.login_rejects_per_ip` rejects (read from `Limits`, never a literal), the **right** pair answers `429 LOGIN_RATE_LIMITED` and the page shows the same line, and no `mhc_session` cookie is set (N-28; web.md §5) — verify: `tests/journeys/j9/test_aea_58.py::test_rate_limited_login_same_refusal` — evidence: the 401s then the 429 printed, with the identical line text. Level: `integrated with a scripted model`.
- [ ] AC-7 [invariant] Every `/api/*` response Chrome received in AC-2 to AC-6 validates through AEA-23's `assert_response_matches` against its operationId (resolved from `Contract.operations` path templates), and no response has an undocumented status; `streamChatEvents` is checked for status and `text/event-stream` only, because its frames are AEA-41's and AEA-59's — verify: the session-end hook in `tests/journeys/browser/`, run with the AC-2 to AC-6 tests — evidence: count of validated responses per operationId; 0 failures. Level: `integrated with a scripted model`.
- [ ] AC-8 [negative] The run never uses mock or third-party paths: no page navigation carries `signedin`, `role`, `scenario`, `staffing`, `ex` or `delay` query parameters (except AC-2's deliberate `/?signedin=1&role=owner` probe, which must redirect); every browser request goes to the test server's own `127.0.0.1:<ephemeral port>` origin; ports 4019 and 5184 are never bound or requested; the scripted adapter is the only model adapter, so no request leaves for a provider — verify: `tests/journeys/j1/test_aea_58.py::test_no_dev_params_or_foreign_hosts` (Playwright `request` events plus the launcher's bound port) — evidence: the set of request origins printed, one entry. Level: `integrated with a scripted model`.
- [ ] AC-9 [negative] The demo password and the `mhc_session` token value appear in none of: the evidence record, screenshot file names, test ids, captured server logs and the pytest output; the cookie is HttpOnly (absent from `document.cookie`) with SameSite=Lax; the "Show password" checkbox is never ticked, so no screenshot shows the password — verify: `tests/journeys/j1/test_aea_58.py::test_secrets_absent_from_evidence` (grep of the record, output dir and caplog for both values) — evidence: 0 hits for each value. Level: `integrated with a scripted model`.
- [ ] AC-10 [negative] Data stays issued or synthetic, and the issued files are never written: the issued scheduling DB's SHA-256 is equal before and after the run (the server writes only the `temp_sqlite()` copy), and nothing under `tests/journeys/browser/` or this ticket's `j<N>` files opens `eval/cases/heldout/` or a held-out key directory (data.md §5–§6, DAT-2 custody) — verify: `tests/journeys/j1/test_aea_58.py::test_issued_db_unchanged` and `grep -rn heldout tests/journeys/browser tests/journeys/j1/test_aea_58.py tests/journeys/j9/test_aea_58.py` — evidence: two equal hashes; empty grep. Level: `integrated with a scripted model` (hash); static (grep).
- [ ] AC-11 [capture] The browser path leaves the records its workflows require (DO-6 rows): **WF-18** one `auth_event` `ok` at sign-in and one `logged_out` at sign-out with the same opaque `session_id`, plus `rejected` and `rate_limited` in AC-6's run; **WF-19** `request` records with route template `spa_fallback` for `/` and `/login` loads and `/assets/{file}` for assets, `caller_role` `anonymous` before sign-in; **WF-1** the `conversation` and `turn` records for AC-3's thread and turn — verify: `tests/journeys/j1/test_aea_58.py::test_browser_path_records` (caplog on the in-process server plus the DB-state reader) — evidence: the records listed with their templates and ids. Level: `integrated with a scripted model`.
- [ ] AC-12 [failure/refusal] A missing prerequisite fails the run and is never skipped (integrated-journeys §3 rule 6): with `MERIDIAN_WEB_DIST_DIR` pointing at an empty temp dir, the browser tests error, and the message names `npm --prefix apps/web run build` and `MERIDIAN_REQUIRE_FRONTEND`; with no Chrome on the given channel, they error naming `--browser-channel chrome` — verify: `uv run pytest -m journey tests/journeys/j1/test_aea_58.py` with `MERIDIAN_WEB_DIST_DIR=$(mktemp -d)` — evidence: errors (not skips) with those names in the output. Level: static (a refusal, not a journey claim).
- [ ] AC-13 [invariant] One runner, one gate: `uv run pytest -m journey --collect-only -q` lists AEA-57's backend journeys and this ticket's browser journeys together; the full reviewer command above passes on the integrated branch; the run leaves `git status --porcelain apps/web` empty (the build writes only the git-ignored `dist` and unchanged generated files) — verify: the two commands — evidence: the collected ids, the pass line and empty status output. Level: `integrated with a scripted model` (the run).
- [ ] AC-14 [capture] Evidence record `docs/testing/journeys/YYYY-MM-DD-AEA-58.md`, written with AEA-57's evidence-record writer, holds every integrated-journeys §4 field: claim (J-1, J-9 login state; AEA-58), level `integrated with a scripted model`, tested revision (SHA and `agent_version`), environment (server command, DB copy source, build hash, `scripted` adapter, Chrome channel and version), the exact command, the result per journey, the evidence location (screenshots beside the record), remaining limitations (J-2…J-10 and J-8's staff-role steps not yet in the browser; SSE frames not body-checked), blocked-by `none` — verify: the record file — evidence: the file with each field filled. Level: `integrated with a scripted model`.
- [ ] AC-15 [invariant] The walkthrough recipe in `tests/journeys/browser/README.md` lets a fresh agent walk J-1 by hand on the integrated branch (build, start the server headed or attach chrome-devtools MCP, sign in with the harness pair from the environment, the screenshots and record to write), and one walk following it is recorded — verify: a reviewer follows it once — evidence: a `docs/testing/journeys/YYYY-MM-DD-wave-3-walkthrough.md` record with screenshots, or the reviewer's note of the step that failed. Level: `integrated with a scripted model`.
- [ ] AC-16 [invariant] Selectors come only from the UX session's contract (customer audit G-1, G-3; shell audit J3; AEA-58-1): each selector in the one module cites its row in `docs/plans/ux-join/selectors.md` and that file's revision; no test file holds a selector string of its own; a state the contract lacks is reported `blocked-on UX selector <state>` for that step only, never replaced by a copy-text selector — verify: `grep -rnE "locator\(|get_by_" tests/journeys --include=*.py` outside the module prints nothing; a read of the module — evidence: the empty grep; a row reference on every selector line.
- [ ] AC-17 [regression/context] Same change updates `.claude/reference/area-map.md` (journeys row: `tests/journeys/browser/` planned → actual, with the commit), `.claude/state/icm-progress.md` (the "Integrated-journey protection" row: first browser journey record and its level), and DO-3 `docs/design/code-design.md` §9's `tests/` tree (status of `tests/journeys/browser/` and the `j<N>/test_aea_<NN>.py` convention). If `pytest-playwright` was added, it is one dev-dependency line in `pyproject.toml` plus the regenerated `uv.lock` (slice plan §3), and that merge runs the full suite (`build-loop-test-scope.md`: dependency change) — verify: `git diff --stat` — evidence: only those rows and lines change beside this issue's owned files.

### Observability

- Responsibilities: emits no new record. It **preserves and proves**, through the real browser path, the records that
  WF-18 (demo login and logout: `request`, `auth_event` with the opaque `session_id`, never the username, password or
  cookie), WF-19 (page serving: `request` with route template `spa_fallback` or `/assets/{file}`) and WF-1 (customer
  chat: `conversation`, `turn` for the J-1 thread) require (DO-6 rows; web.md §10). It also writes the integrated-journeys
  §4 evidence record. Redaction checks stay with CAP-10 (AEA-23) and CAP-11 (AEA-49); journeys don't repeat them.
- Capture evidence: AC-11 (records present at the browser entry points), AC-9 (secrets absent from evidence and logs),
  AC-14 (the evidence record).

### Evaluation

N/A — the browser journeys are deterministic pass/fail checks with a scripted model. Their expected answers come from
the journey script and the stored rows, not from DO-5. They produce no E-n number and are never cited as containment or
quality (integrated-journeys §1, the E-1…E-8 row "Untouched", and rule 4). A reviewer could argue that J-1's reply should
be scored; that belongs to the E-runs through the HTTP API (AEA-24).

### Metrics

N/A — test-only. It adds and changes no emitted record, so every M-n that WF-1 inherits stays computable exactly as its
emitters (AEA-40, AEA-51's capture tests) left it; the journey only reads rows. Page loads feed no M-n (WF-19 row:
n/a). A reviewer could argue AC-11 should assert M-22's numerators; that is AEA-53's reader, on seeded rows.

### Blocked by

- AEA-49 (serves `apps/web/dist` through the real app; the public paths and the 303 it registers on AEA-23's gate).
- AEA-57 (the journey harness `tests/journeys/support/` and J-1 at the API level).
- **UX-4 signed** (`PROJECT-CHECKLIST.md` §4b: "UX-4 prototype in the project's **real frontend folder** … — Innocent ✓"):
  `gate::ux4`.
- AEA-40, for AC-3's greeting-after-reload assertion only (AEA-58-2; AEA-40-1, web.md §14 `ThreadHistory`, R-W-6). AEA-40
  is wave 2, so the wave stays 3.

Calls (injected): none. It consumes AEA-23's `assert_response_matches` (a test helper), AEA-57's `support/` and
AEA-49's `register_frontend` through the real app.

### Agent handoff

- Area / owner: journeys (integrated-journeys §6, AEA-58 row). Owns `tests/journeys/browser/` (fixtures, selectors
  module, session-end response check, `README.md` recipe), `tests/journeys/j1/test_aea_58.py`,
  `tests/journeys/j9/test_aea_58.py`, the record `docs/testing/journeys/YYYY-MM-DD-AEA-58.md` and its screenshots.
- Contracts and shared surfaces: consumes AEA-57's `support/` (app build on `temp_sqlite()`, scripted adapter, launcher,
  login helper, DB-state reader, record writer), AEA-23's `tests/api/openapi_check.py` (`load_contract`,
  `assert_response_matches`; its signature takes an `httpx.Response`, so the hook builds one from each Playwright
  response and never writes a second validator), AEA-49's frontend serving, `Settings` and `Limits.web` (AEA-02, AEA-01),
  and `apps/web/dist` (UX-4, read only). Produces the browser fixtures and the `j<N>/test_aea_<NN>.py` pattern for later
  tickets, the browser half of the journey gate, and the walkthrough recipe. **Must not edit:** `tests/journeys/support/`
  (AEA-57), `tests/conftest.py` (AEA-01), `tests/api/openapi_check.py` (AEA-23), any `src/meridian/` file, `apps/web/**`,
  `docs/ux/**`, the OpenAPI. Fixture discovery for `j<N>/` files must need no edit to those. If it does, record
  `blocked-on AEA-01` or `blocked-on AEA-57` for a one-line follow-up merged first. `pytest-playwright` is not in AEA-01's
  dependency list (written before Amendment 1). Add it as one dev-dependency line plus the lock, per slice plan §3.
- Awaiting UX session (`docs/plans/ux-join/` does not exist yet, so these are not fixed; nothing here invents them):
  (1) the **selector contract** for every state J-1 and J-9 assert: SCR-12 username, password, "Sign in", message line;
  SCR-1 greeting turn, composer, send, customer and assistant turns, "Sign out". apps/web's mock suite uses accessible
  roles and `data-screen` marks today, but that is not a contract. (2) The **production build command and output path**:
  built here on `npm run build` → `apps/web/dist` plus `check:dist` as `apps/web/package.json` stands on 2026-10-21; if
  the UX session names another, only the reviewer command and AC-1/AC-12 change. (3) The **Playwright settings to
  reuse** (channel, viewports, locale, timezone, taken from `playwright.config.ts`). (4) The **real-backend mode**: built
  on same-origin relative `/api` calls with `credentials: "include"` (observed in `apps/web/src/api/client.ts`, so no
  proxy is needed when the app serves `dist`). (5) **How a reload finds the thread**: built on the per-tab id of N-31
  (observed as sessionStorage key `mhc.chat.thread`, not contracted). The server half is now specified: `getChatThread`
  returns web.md §14's full `ThreadHistory` (R-W-6, AEA-40-1). Until (1) lands (`docs/plans/ux-join/selectors.md`, AC-16),
  the planner records `blocked-on UX session selector contract` for the steps it affects; it does not guess.
- Awaiting Innocent: WEB-1 — built on the recommended option A (`/login` plus `/assets/` and `/fonts/` load without a
  session). If he picks B (a self-contained login page), the J-1 steps stay the same, but SCR-12's selectors come from
  that page and AC-11's WF-19 asset records before sign-in disappear. If he picks C (the whole shell public), the
  redirect moves into the app: AC-2 and AC-5 assert the app reaching `/login?return_to=…` after a 401 instead of a
  server 303.
- Settled (slice plan §0a, rows AEA-58 and AEA-62): who moves J-2…J-10, and J-8's staff-role steps, into the browser.
  AEA-62 (new, wave 4) puts J-2, J-3, J-6 and J-8 in a browser; J-4, J-5, J-7, J-9 and J-10 stay at API level and in each
  wave's recorded browser walkthrough. This ticket keeps J-1, the J-1 parts of J-8 (signed-out guard, refresh) and J-9's
  rate-limited login, as written.
- needs-decision: Should a chat resume after the reviewer signs in again? SCREEN_SPECS SCR-1 (state "Session ended while
  the chat is open") says "after sign-in the reviewer returns here and the chat resumes if it is still open". But web.md
  §2 starts a new login session on every sign-in, and §4 `owned_thread` answers 404 `SESSION_NOT_FOUND` for another
  session's thread. AEA-58 asserts only same-session refresh and resume (AC-3, AC-4) and leaves the re-login resume step
  out until this is settled; neither contract is edited here.
- Scope boundary / refusal: no production code; no edits to the gate, the frontend mount or the screens; no live model
  calls (AEA-61); no Prism, Vite dev server or UX-5 suite (AEA-55); no redaction re-checks (CAP-10, CAP-11); no build of
  `apps/web` inside a test (the reviewer command and the merge gate run it before pytest). DAT-2, DAT-3 and DAT-4 do not
  change this ticket: it reads no held-out file, takes the demo pair from the harness environment rather than the
  README, and runs with `NullTraceSink`.
- Wave and gates: wave 3; `gate::ux4` (UX-4 signed by Innocent). At wave merges and before deploy, the merge agent runs
  these browser journeys with all other journeys (`build-loop-test-scope.md` *AEA addition*). Ticket merges run them
  when a diff touches a module, route, schema or frontend build input on their path.
- Lane: `lane::build-loop` — it adds test code that the merge gate runs (ticket-lanes: tests are code-read).
- Risk: None per the slice plan. It changes no production code. It handles the harness's demo pair and the session
  cookie only inside tests, and AC-9 keeps both out of evidence and logs.
- Test-only: it drives the existing chat, login and page-serving entry points owned by AEA-40, AEA-23 and AEA-49
  (listed under Observability) and registers no new one.
- Entry points added or changed: None
