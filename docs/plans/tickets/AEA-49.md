## [AEA-49] web: serve the built `apps/web/dist`

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
> acting as the customer and acting as a representative, supervisor or business owner in one click from any screen, so
> that I can play both sides of a handoff without separate accounts or passcodes." Acceptance: "nothing except the login
> and `/healthz` answers without the login".

`web/frontend.py` with `register_frontend(container: Container, app: FastAPI) -> None` and its own `register_frontend()`
hunk in `web/container.py` (stage7/web.md §12; WEB-29). The FastAPI app serves UX-4's production build of the React app
(`apps/web/dist`, built by `npm run build` in that folder; UX-4 owns it; the image builds it, AEA-50, DAT-21) from the same
origin as the API, so the deployed URL is one interactive web app:

- **Mount, read-only**, from `Settings.web_dist_dir` (default `apps/web/dist`; `/app/apps/web/dist` in the image,
  graph-core §12, data.md §7): files under `/assets/` and `/fonts/` answer with their content types; every other `GET`
  path not under `/api/` and not `/healthz` answers `dist/index.html` (**SPA fallback**), and the React router draws the
  screen; path traversal and dotfiles answer 404 (web.md §12). A missing file under `/assets/` or `/fonts/` answers 404,
  never the fallback; `index.html` and fallback responses carry `Cache-Control: no-cache`, `/assets/` files
  `public, max-age=31536000, immutable` (AEA-49-1; AC-10).
- **Public paths** registered through AEA-23's `PublicPaths` registry (web.md §6): `("GET", "/login")`, and, on WEB-1's
  recommended option A, the build's static prefixes `("GET", "/assets/")` and `("GET", "/fonts/")`. Every other page
  stays behind the login gate AEA-23 owns: an unsigned page `GET` answers `303` to
  `/login?return_to=<path+query>&reason=none` (`reason=expired` plus `Set-Cookie mhc_session` `Max-Age=0` for an expired
  session), while `/api/*` keeps the JSON 401 `UNAUTHENTICATED` (WEB-28).
- **Missing build** (WEB-30): `Settings.require_frontend` true (deploy) → start-up fails naming the setting and the path;
  false (local, CI) → one warning log `frontend_dist_missing`, nothing mounted, page paths fall through to FastAPI's JSON
  404 after the gate, and every `/api` route works.
- **WF-19** (DO-6, registered at §7, WEB-31): each page and asset request leaves the middleware's `request` record with
  the route template `spa_fallback` or `/assets/{file}`, never the raw path or query string (web.md §10). CAP-11 is this
  issue's capture check.

**Example pair (SCREEN_SPECS routes; R-48; web.md opening example).** An unsigned browser opens
`https://…/staff/queue` → `303` to `/login?return_to=%2Fstaff%2Fqueue&reason=none`. `/login` answers 200 `text/html`
(the built `index.html`) and its hashed `/assets/index-….js` and `/fonts/…` files load without a session (WEB-1 A). After
sign-in (CON-22, AEA-23) with `mhc_session` set, `GET /staff/cases/MHC-C-0007` → 200 `index.html` (the client router shows
SCR-6), while `GET /api/staff/cases/MHC-C-0007` still answers the JSON `CaseDetail` (AEA-45). `GET /api/no-such-route`
answers JSON, never `index.html`.

**Produced for other issues:** the served UI for AEA-55 (UI integration against the real backend) and, through the image,
AEA-56 (deploy and smoke test).

### Source

- PRD R-40, R-48; US-25, US-28; checklist §4b (UX-4 signed; this issue's `gate::ux4`) and §8 (UI integration).
- SCREEN_SPECS screen routes (SCR-1…SCR-12 *Route* lines) and SCR-12 (`/login` answers without a session; a gated route
  "sends the visitor here").
- stage7/web.md §6 (gate order, `PublicPaths`, the 303 and its open-redirect guard), §10 (`request` record), §12
  (`register_frontend`), cross-topic rows GRA (Settings `web_dist_dir`, `require_frontend`) and DAT (image path, Railway
  variables); graph-core.md §12 (`Settings` fields `MERIDIAN_WEB_DIST_DIR`, `MERIDIAN_REQUIRE_FRONTEND`).
- Decision ledger `docs/plans/7b-decisions/web.md`: WEB-1 (open, Innocent), WEB-28, WEB-29, WEB-30, WEB-31, WEB-32,
  WEB-36.
- DO-6 `docs/design/observability-contract.md` WF-19 row, CAP-11, *Content and redaction* (session cookies never in logs).
- `UI_CONTRACTS.md` *Access*; OpenAPI `Unauthenticated` response (read only).
- `apps/web/package.json` scripts `build` and `check:dist` (read only; the dev mock layer must not be in `dist`).
- Slice plan row AEA-49 and §0 deviation 3 ("AEA-49 serves its build"); collision map rows `web/container.py`,
  `apps/web/**`.
- **Brief check:** serves "Deploy the agent as a web application at a public URL. The interface must be interactive: a
  reviewer should be able to type questions, probe edge cases, and watch the agent escalate." (Part B §6); touches nothing
  out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] With a signed session, each SCREEN_SPECS screen path (`/`, `/demo`, `/demo/inbox`, `/role`, `/staff/queue`, `/staff/cases/MHC-C-0007`, `/staff/oversight`, `/staff/flags`, `/staff/owner`, `/monitoring`, `/eval`, `/login`) answers 200 `text/html` with the fixture `index.html`, and a fixture `/assets/app.js` and `/fonts/f.woff2` answer their bytes with their content types — verify: `tests/api/test_web_frontend.py::test_spa_fallback_and_assets` (fixture dist in a temp dir, `Settings.web_dist_dir` pointed at it) — evidence: twelve paths and two files asserted.
- [ ] AC-2 [invariant] `/api/*` and `/healthz` are never shadowed: an existing API route (a stub router in the test app) still answers its JSON; `GET /api/no-such-route` answers JSON 404 and never `index.html`; `GET /healthz` answers the health route — verify: `tests/api/test_web_frontend.py::test_api_and_healthz_not_shadowed` — evidence: content types and bodies asserted.
- [ ] AC-3 [failure/refusal] **WF-19 (page gate):** Without `mhc_session` (real AEA-23 middleware): `GET /login`, `/assets/app.js` and `/fonts/f.woff2` answer 200 (WEB-1 A); every other screen path answers `303` with `Location: /login?return_to=<path+query>&reason=none`, never `index.html`; with an expired session the 303 carries `reason=expired` and clears the cookie; `/api/staff/queue` answers JSON 401 `UNAUTHENTICATED` valid against `Unauthenticated` — verify: `tests/api/test_web_frontend.py::test_pages_behind_login` (response check via `tests/api/openapi_check.py` for the 401) — evidence: status and `Location` per path printed.
- [ ] AC-4 [negative] Nothing outside the dist directory is served and `return_to` is not an open redirect: `/assets/../../pyproject.toml`, its percent-encoded form, `/assets/.env` and a dotfile path answer 404 (or the 303 of AC-3 when unsigned) and never the file's bytes; `/login?return_to=//evil.example` is not followed by the app (web.md §6 guard) — verify: `tests/api/test_web_frontend.py::test_no_path_traversal_or_open_redirect` — evidence: the outside file's content absent from every response; no `Location` off-origin.
- [ ] AC-5 [failure/refusal] Missing build (WEB-30): with `require_frontend=False` and no dist directory the app starts, one `frontend_dist_missing` warning is logged, every `/api/*` stub route answers 200 and a signed page path answers JSON 404; with `require_frontend=True` and no dist directory start-up raises an error naming `MERIDIAN_REQUIRE_FRONTEND` and the path — verify: `tests/api/test_web_frontend.py::test_missing_dist` — evidence: the warning record, the 404 body, the start-up error text.
- [ ] AC-6 [negative] The served directory is read, never written: the diff touches no path under `apps/web/`, and the mount opens files read-only — verify: `git diff --name-only | grep '^apps/web/'` prints nothing; code review of the mount — evidence: empty grep output.
- [ ] AC-7 [capture] **CAP-11, WF-19:** through `create_app()` built by the container, the app root, a deep link (`/staff/cases/MHC-C-0007?tab=brief`) and one asset, each signed in and signed out, leave one `request` record per call with `request_id` equal to the `X-Request-ID` header, the route template (`spa_fallback` or `/assets/{file}`), status and `caller_role` (`anonymous` when signed out) — verify: `tests/capture/test_cap11_page_serving.py::test_page_requests_recorded` — evidence: six records printed with their templates.
- [ ] AC-8 [negative] **CAP-11 forbidden:** over the AC-7 run, no log line or span holds the raw path `/staff/cases/MHC-C-0007`, the query string `tab=brief`, or the `mhc_session` cookie value (DO-6 WF-19 row, *Content and redaction*) — verify: `tests/capture/test_cap11_page_serving.py::test_no_raw_path_query_or_cookie` (caplog plus the in-memory trace sink) — evidence: 0 hits for each value.
- [ ] AC-9 [journey] **J-1** (slice plan Amendment 1): `tests/journeys/j1/test_aea_49.py` runs on AEA-57's `support/` harness (real app, disposable DB copy, guards on) and asserts, over HTTP, that a signed-out `GET /` and `GET /staff/queue` redirect to `/login` with `return_to`, that `/login` and its built asset files load, and that after the login helper signs in the deep link answers the build's `index.html` while `/api/chat/sessions` still answers JSON; the browser-level J-1 is AEA-58's — verify: `uv run pytest -m journey tests/journeys/j1/test_aea_49.py` plus the evidence record `docs/testing/journeys/<date>-AEA-49.md` (integrated-journeys §4) — evidence: pass per step at level `integrated with a scripted model`, or the record's Blocked-by field naming AEA-57 if its harness has not merged.
- [ ] AC-10 [invariant] Cache rules and missing files (AEA-49-1, shell audit C4): `index.html` and every SPA-fallback response carry `Cache-Control: no-cache`; files under `/assets/` carry `Cache-Control: public, max-age=31536000, immutable`; a missing file under `/assets/` or `/fonts/` answers 404 (never `index.html`, which a browser would try to run as a script), signed in and, under WEB-1 option A, signed out — verify: `tests/api/test_web_frontend.py::test_cache_headers_and_missing_asset_404` (fixture dist; the amendment's `tests/web/test_frontend.py` is this issue's `tests/api/test_web_frontend.py`) — evidence: the headers printed per path; `/assets/missing.js` answers 404 in both states.
- [ ] AC-11 [capture] **WF-19 (status values and no outbound call; OBS-13, OBS-29):** over AC-7's run plus an unsigned page path (303) and a missing asset (404, AC-10), each `request` record's `status` equals the HTTP status the response carried and none carries `error_kind`; a page request forced to fail inside the frontend handler (the fixture `index.html` read replaced by a raising double) answers 500 and its record carries `status` 500 and a non-empty `error_kind`; and a socket guard that fails the test on any non-loopback `connect` sees none during the whole run — verify: `tests/capture/test_cap11_page_serving.py::test_wf19_status_values_and_no_outbound` — evidence: the (response status, record status, `error_kind`) triple per call printed; 0 outbound connects.
- [ ] AC-12 [regression/context] Same change updates `.claude/reference/area-map.md` (this issue's row planned → actual with the commit, naming `web/frontend.py`), `.claude/state/icm-progress.md` (routes-verified row), DO-3 §3's `web/` note and §8 collision row so they name AEA-49 and `register_frontend` — verify: `git diff --stat` — evidence: only those rows change beside this issue's owned files.

### Observability

- Responsibilities: **WF-19** (page serving): the middleware `request` record for every page and asset request with the
  route template `spa_fallback` or `/assets/{file}`, `request_id`, status and caller role (web.md §10); never the raw path,
  query string or cookie value in a log line or span (DO-6 *Content and redaction*). The one `frontend_dist_missing`
  warning when no build is mounted.
- Capture evidence: AC-7 (CAP-11 present), AC-8 (CAP-11 forbidden), AC-11 (status values, no outbound call), AC-4 and
  AC-6 (negative).

### Evaluation

N/A — WF-19's row reads "n/a — serving files decides no outcome"; no DO-5 suite (E-1…E-8) scores page delivery, and the
eval harness drives the HTTP API only (DO-3 §3: "HTTP only").

### Metrics

N/A — WF-19 inherits no metric (DO-6 row: n/a); page and asset loads are not a numerator or denominator of any M-n (M-22
counts conversations, turns and handoffs, which CON-1/CON-2 records carry, not page loads).

### Blocked by

- AEA-23 (web app, middleware, `PublicPaths`, the login gate and its 303).
- **UX-4 signed** (`PROJECT-CHECKLIST.md` §4b: "UX-4 prototype in the project's real frontend folder … — Innocent ✓"):
  `gate::ux4`.

### Agent handoff

- Area / owner: A8 web shell (DO-3 §8). Owns `web/frontend.py`, its `register_frontend()` hunk in `web/container.py`,
  `tests/api/test_web_frontend.py`, `tests/capture/test_cap11_page_serving.py` (CAP-11; the collision map's
  `tests/capture/` row should add 49), `tests/journeys/j1/test_aea_49.py`.
- Contracts and shared surfaces: consumes AEA-23's `PublicPaths` (web.md §6) and gate, the `request` log record (web.md
  §10) and `Settings.web_dist_dir` / `require_frontend` (AEA-02, graph-core §12); reads `apps/web/dist` (UX-4's). Produces
  the served UI for AEA-55 and AEA-56. AEA-01's stub list lacks `register_frontend` (WEB-29): if the stub is missing at
  start, record `blocked-on AEA-01` (a one-line follow-up there). **Must not edit:** `apps/web/**` (including its build
  output), `docs/ux/**`, `web/app.py`, `web/middleware.py`, `web/deps.py`, `routes/auth.py` (AEA-23), any route or schema
  file, the OpenAPI.
- Scope boundary / refusal: no page rendering, templates or copy (UX-4 owns the screens); no change to the gate's logic
  (AEA-23); no build of `apps/web` in tests or CI here (the image builds it, AEA-50); no Prism proxy or UX-5 suite
  (AEA-55). Contract note: `dist/favicon.svg` sits at the build root, outside `/assets/` and `/fonts/`, so web.md §12
  answers it with `index.html`; the planner keeps the contract and records the note for AEA-55's run.
- Join amendments applied: AEA-49-1 (AC-10). AEA-49-2 (join Decision 1, the B/C replacement of AC-3's public list) is
  conditional and **not applied**; under A, AC-3 and AC-9 stand as written.
- Awaiting Innocent: WEB-1 — built on the recommended option A (`/login` plus `/assets/` and `/fonts/` public); if he
  picks B, a self-contained login page at `/login` is added and the two prefixes are not registered (AC-3 lists `/login`
  only); if C, every page path is registered public and the redirect moves into the app (AC-3 asserts 200 `index.html`
  unsigned, `/api` still 401).
- Wave and gates: wave 2; `gate::ux4` (UX-4 signed by Innocent).
- Lane: `lane::build-loop` — application code and tests (ticket-lanes: changes code).
- Risk: the slice plan row carries no `risk::security`; WEB-36 and rule `build-loop-test-scope` (network exposure) label
  it security work, because it decides what an unsigned visitor can fetch. Orchestrator: add `risk::security` before
  dispatch (frozen tests from AC-3, AC-4, AC-8; `security-privacy-agent` at the wave-2 merge) or record why not.
- Entry points added or changed: WF-19 (page serving: the static mount, its asset files and the SPA fallback).
