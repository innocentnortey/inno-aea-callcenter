## [AEA-55] UI integration: `apps/web` against the real backend

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

**Checklist §8's "UI verify again"** (ux-pipeline UX-5, second run): the React frontend UX-4 built in `apps/web/` is
pointed at the real backend, and the UX-5 suite reruns with Prism in **proxy** mode between them, so any backend response
that breaks a UI contract fails the run.

In practice: the backend app (`create_app()` from the merged container, integrated by AEA-51, AEA-52, AEA-53) runs on a
free local port through AEA-57's launcher with its deterministic scripted model adapter (DAT-24: the automated suite never
calls a paid model); `prism proxy docs/ux/03-structure/ui-contracts.openapi.yaml <backend URL> --errors` runs on a second
free port; `apps/web` runs in its non-mock mode with `API_PORT` set to Prism's port (its `vite.config.ts` already proxies
`/api` to `API_PORT`, so no client code changes); the UX-5 Playwright suite, axe checks, screenshots at 1280 and 390 wide
in light and dark, and the Lighthouse accessibility audit run through that chain. Then the backend-served build (AEA-49)
gets one same-origin smoke run behind the real login, and Innocent's walkthrough runs on live Sonnet and Jev (DAT-24).
The report is `docs/testing/ui-verify-again.md`, linked from `PROJECT-CHECKLIST.md` §8 (DAT-25; data.md §8).

**This issue is the one exception to the conventions' `apps/web/**` refusal, and only after UX-5 is signed** (collision
map: "55 changes `apps/web` config only after UX-5"): it may change `apps/web` test and run configuration (Playwright
config, environment, scripts); it changes no screen, component or generated type. A contract mismatch stops the issue and
goes to Innocent; neither side is edited to make the other pass.

**Example pairs driven through the real UI:** **WP-2** (locate, read the code from the demo inbox screen SCR-2, type it in
the chat, see the invoice as billed), **WP-5** (the safety instruction is the first text on screen), **WP-7** (the refund
handoff's promise and reference, then the case in the staff queue). Screens: **SCR-1…SCR-12** as UX-5 covers them;
flows FLOW-n per `docs/ux/05-verify/TRACEABILITY.md`.

**Seams this issue proves (double the frontend was built against → real object here):**

| # | Consumer | Double it was built against | Real object | Proven by |
|---|---|---|---|---|
| 1 | `apps/web` API client (UX-4) | Prism **mock** of the OpenAPI, with mock-only `Prefer:` headers and the state switcher | the real backend behind Prism **proxy** (AEA-51, 52, 53 integrations) | AC-3, AC-4 |
| 2 | The built `dist/` | Vite dev server; dev-only `?signedin=1&role=…` sign-in | the backend's static mount, SPA fallback and real login gate (AEA-49, AEA-23) | AC-5 |
| 3 | SCR-9, SCR-10, SCR-11 numbers | mock examples | CON-18…CON-20 from the real `MetricsReader` (AEA-53) over records left by real WF-1/WF-2 flows | AC-8, AC-9 |
| 4 | Staff tabs' role handling | the dev mock's per-tab `sessionStorage` role | the session-held role (STF-19): a role switched in another tab answers `ROLE_NOT_ALLOWED` `wrong_role` | AC-11 |

User stories closed (their UI side): **US-1…US-28**, as UX-5's traceability maps them; especially **US-25** (nothing
misleads about what is simulated), **US-26** (failures shown cleanly), **US-28** (sign in once, switch role in one click).

### Source

- `PROJECT-CHECKLIST.md` §4b (UX-5 gate), §8 ("Frontend: one integration step per contract …"; "UI verify again: the UX-5
  suite reruns against the real backend (Prism in proxy mode) — Innocent ✓"), *Skips* row for §7.
- `/home/linuxuser/workspaces/.claude/skills/ux-pipeline/references/phases.md` UX-4 (§8 integration per contract; mock
  machinery in a dev-only layer) and UX-5 (suite contents, pitfalls, human review, loop rule, "UX-5 runs twice").
- stage7/data.md §8 (report path; the `wrong_role` check, DAT-29 e); stage7/staff.md cross-topic (apps/web UI verify,
  STF-19), §10 (time sources); stage7/web.md §6 (gate and 303), §12 (frontend serving), §13 (OpenAPI check).
- Decision ledgers: `docs/plans/7b-decisions/data.md` DAT-24, DAT-25, DAT-29; `web.md` WEB-1 (open), WEB-28, WEB-32.
- UI contracts (read only): `UI_CONTRACTS.md` CON-1…CON-22; `ui-contracts.openapi.yaml`; SCREEN_SPECS states and copy notes.
- DO-6 WF-1…WF-6, WF-18, WF-19 rows, *Content and redaction*, **CAP-6** ("after CAP-1 to CAP-3"); DO-7 M-1…M-29 as the
  pages show them.
- Project rule `.claude/rules/integrated-journeys.md` (§4 levels; §6: "The UX-5 suite and AEA-55 keep the visual and
  accessibility checks. They are not journey evidence where they sign in through dev-only parameters"); slice plan row
  AEA-55 and Amendment 1 (AEA-58 before this issue); `docs/plans/ux-join/` (what the UX session provides); collision map
  row `apps/web/**, docs/ux/**`.
- UX ↔ backend join: `docs/plans/ux-join/backend-amendments.md` AEA-55-1 (shell audit J1, C6, C7, G5), AEA-55-2 (shell
  audit G1; join-plan risk 2) and §3's AEA-55 journey criterion (runs all journeys).
- **Brief check:** serves "The interface must be interactive: a reviewer should be able to type questions, probe edge
  cases, and watch the agent escalate"; touches nothing out of scope (no deploy: AEA-56); weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [failure/refusal] Nothing in `apps/web` changes before UX-5 is signed: the checklist §4b line "UX-5 signed off" carries `Innocent ✓ <date>` and `docs/ux/05-verify/QA_REPORT.md` and `TRACEABILITY.md` exist; until then the issue stops — verify: `grep -n "UX-5 signed off" PROJECT-CHECKLIST.md` and `ls docs/ux/05-verify/` — evidence: the ticked line with date; the two files present.
- [ ] AC-2 [invariant] The frontend still matches the contract it was built against: types regenerate from the same OpenAPI with no diff and the production build passes with no mock-only code in `dist` — verify: `npm run check:gen && npm run build && npm run check:dist` in `apps/web` — evidence: exit 0 for each; no change to `src/api/types.gen.ts`.
- [ ] AC-3 [invariant] Every response the real backend gives during the suite conforms to the OpenAPI: Prism proxy with `--errors` reports **0 violations** over the full run — verify: the Prism proxy log of the AC-4 run (command recorded in `docs/testing/ui-verify-again.md`) — evidence: 0 request or response violations; any violation is a stop, reported to Innocent with the operation, field and side (UX-5 loop rule).
- [ ] AC-4 [invariant] The UX-5 suite reruns through the chain on the scripted model adapter: every Playwright flow test (including error branches), axe on every screen and state, screenshots at 1280 and 390 in light and dark, and the Lighthouse accessibility audit each end `PASS`, `FAIL`, `NOT_RUN` or `NEEDS_HUMAN_REVIEW` with evidence; a state reachable only through mock-only machinery is `NOT_RUN` with that reason, never faked against the real backend — verify: `perl -e 'alarm 500; exec @ARGV' npx playwright test` in `apps/web` with `API_PORT` set to the Prism proxy port (hard time cap per the UX-5 pitfalls) — evidence: the Playwright report and `docs/testing/ui-verify-again.md` with a row per check.
- [ ] AC-5 [failure/refusal] The backend-served build works at one origin behind the real login (R-48, AEA-49, WEB-28): an unsigned deep link to `/staff/queue` is redirected to SCR-12 with `return_to` and, after sign-in through the real form (no `?signedin` or `?role` parameters), returns there as the customer; the chat opens; the role switch to the representative is one click and opens the staff console; monitoring and evaluation pages load — verify: a Playwright smoke project in `apps/web` pointed at the backend's own URL (no Vite, no Prism) — evidence: the run's pass and screenshots.
- [ ] AC-6 [capture] **WF-1 and WF-3 through the real UI (WP-2):** after the reviewer path locates MHC-10002, reads the code on SCR-2 and types it in the chat, the stored chat holds "[code entered]"; the code appears in no DB text column, log line or captured span; every API response the page received carried an `X-Request-ID` header matching a `request` record — verify: `tests/integration/test_ui_run_records.py::test_wp2_through_ui_leaves_no_code` (reads the DB, logs and in-memory spans the backend run produced; the code value is taken from the run, never written in the file) — evidence: 0 hits; `request_id` on every captured response.
- [ ] AC-7 [invariant] **WP-5 and WP-7 through the real UI:** the CO-alarm instruction is the first reply text on SCR-1; WP-7's reply shows the policy promise "A representative will get to your refund request within 2 business days." and a reference, and after a role switch the same reference appears in the representative queue (SCR-5) beside the seed cases MHC-C-0005…MHC-C-0008 — verify: the WP-5 and WP-7 flow tests in the AC-4 suite — evidence: DOM text order; the same reference on both screens.
- [ ] AC-8 [capture] **CAP-6 end to end, WF-6 (DO-6: "after CAP-1 to CAP-3"):** after WP-2, WP-5 and WP-7 run through the real UI, CON-18 and CON-19 numbers equal direct counts over the records those runs left (volume, handoffs by reason, failures, latency sample size, spend) — verify: `tests/integration/test_ui_run_records.py::test_reads_equal_records_after_flows` — evidence: per-measure equality.
- [ ] AC-9 [invariant] SCR-9, SCR-10 and SCR-11 render the API's numbers unchanged: each displayed numerator, denominator and value equals the CON-18…CON-20 response the page received (no client recomputation); a threshold appears only as a labelled alert setting — verify: a Playwright test in the AC-4 suite comparing captured responses with the DOM — evidence: 0 mismatches.
- [ ] AC-10 [invariant] Innocent (or a person he names) attempts each core task on the real backend with live Sonnet and Jev (DAT-24: marked `live`, `gate::paid`, about 20 turns under the $30/day cap) while Claude records what was observed, the model ids and the spend-ledger total; any task left `NEEDS_HUMAN_REVIEW` at UX-5 is offered again; Innocent signs the checklist §8 line "UI verify again … — Innocent ✓ <date>" — verify: `grep -n "UI verify again" PROJECT-CHECKLIST.md` and the walkthrough section of `docs/testing/ui-verify-again.md` — evidence: the ticked line with date; observation notes at level `verified with live models`; the spend total.
- [ ] AC-11 [failure/refusal] A staff tab whose role was switched in another tab (STF-19; data.md §8, DAT-29 e): its next staff call gets 403 `ROLE_NOT_ALLOWED` `wrong_role`, and the tab treats it as "the role was switched elsewhere" and re-reads `getSession` on focus instead of showing a broken page; after a CON-9 reset the same tab gets `role_reset` and shows the role picker — verify: a two-context Playwright test in the AC-4 suite against the real backend — evidence: the two responses and the screens shown.
- [ ] AC-12 [negative] Boundaries held: no process bound to port 4019 or 5184 during the run (the UX session's ports); `git diff --name-only` shows changes only under `apps/web/` run and test configuration, `tests/integration/test_ui_run_records.py`, `docs/testing/ui-verify-again.md`, the journey record `docs/testing/journeys/YYYY-MM-DD-AEA-55.md` and the checklist (plus the AC-23 context files); nothing under `docs/ux/`, `apps/web/src/` or `src/meridian/` changed; the demo password appears in no file of the diff — verify: `ss -ltnp` captured during the run and `git diff --name-only` — evidence: the port list; the file list.
- [ ] AC-13 [journey] Runs every journey (J-1…J-10: the API legs and the AEA-58 / AEA-62 browser legs, the browser legs through the production build and the real login) on the integrated branch after its run-configuration change and before the UX-5 rerun, exactly as the wave-merge gate does, and records them at level `integrated with a scripted model`; the UX-5 rerun through Prism proxy is reported separately and is not journey evidence (integrated-journeys §6), and its `@mock-only` tests are `NOT_RUN` (backend-amendments §3, AEA-55 special) — verify: `uv run pytest -m journey` (the all-journeys command) plus the record `docs/testing/journeys/YYYY-MM-DD-AEA-55.md` (integrated-journeys §4) — evidence: pass per journey; the record's fields.
- [ ] AC-14 [invariant] The proxy chain is probed before the suite runs, and each result is recorded (AEA-55-1): (1) a chat stream and a case stream opened through `prism proxy … --errors` deliver their first frame or heartbeat within 20 s; if not, both stream paths are routed straight to the backend in the run configuration (`vite.config.ts` proxy, a configuration change this issue may make) and the exception is written down; (2) a cookieless `getChatThread` through the chain answers the backend's own `ApiError` 401 `UNAUTHENTICATED`, not a Prism body; if not, Prism's request validation is changed so the backend answers, and recorded; (3) the backend runs with `MERIDIAN_COOKIE_SECURE=false` over local http; (4) the report states that the dev-mode `[contract drift]` signal is mock-only and that AC-3's Prism log is the real contract check — verify: the run record `docs/testing/ui-verify-again.md` or `docs/testing/journeys/YYYY-MM-DD-AEA-55.md` (the amendment's alternative, a `docs/ux/05-verify/` report section, is the UX session's to write; this issue changes nothing under `docs/ux/`, AC-12) — evidence: the four results, each with its outcome.
- [ ] AC-15 [negative] No dev parameter carries a real-backend result (AEA-55-2): tests the UX session tagged `@mock-only` are recorded `NOT_RUN` with their reason, never as passed; no request in the run carries `signedin`, `role`, `scenario`, `staffing`, `ex` or `delay` query parameters; every sign-in goes through SCR-12 with the demo pair from the environment — verify: the Playwright report and the Prism proxy log — evidence: the `NOT_RUN` list with reasons; a grep of the proxy log for those parameters prints nothing.
- [ ] AC-16 [invariant] **WF-1 (NFR-3; SCR-1 customer chat):** through the AC-4 chain, axe reports 0 WCAG 2.2 AA violations (colour contrast included) on SCR-1 in every state the suite reaches, at 1280 and 390 wide in light and dark; no state is told apart by colour alone (each state's screenshot, rendered in grayscale, still shows the state by text, icon or shape); the WP-5 safety instruction is the first reply text and keeps SCREEN_SPECS SCR-1's safety treatment; a state the chain cannot reach is `NOT_RUN` per AC-4, never passed — verify: the AC-4 run's axe and Lighthouse rows for SCR-1 plus the grayscale review of its screenshots, recorded per state in `docs/testing/ui-verify-again.md` — evidence: 0 AA violations per state; the grayscale row `PASS`, or `NEEDS_HUMAN_REVIEW` with its reason.
- [ ] AC-17 [invariant] **WF-2 (NFR-3; SCR-1 after "Talk to a person"):** the same checks as AC-16 on the handoff card (reference, promise, due row) and the follow-up preference control after WP-7 and after a direct person request — verify: the AC-4 run's axe and Lighthouse rows for those SCR-1 states plus their grayscale review in `docs/testing/ui-verify-again.md` — evidence: 0 AA violations per state; the grayscale row `PASS` or `NEEDS_HUMAN_REVIEW` with its reason.
- [ ] AC-18 [invariant] **WF-3 (NFR-3; SCR-2 demo delivery inbox):** the same checks as AC-16 on SCR-2 with a code waiting and with an expired message (the expired status shown in words, not colour alone) — verify: the AC-4 run's axe and Lighthouse rows for SCR-2 plus their grayscale review in `docs/testing/ui-verify-again.md` — evidence: 0 AA violations per state; the grayscale row `PASS` or `NEEDS_HUMAN_REVIEW` with its reason. No screenshot is kept while a code is visible (AEA-62 AC-16's rule); the grayscale review uses the expired state.
- [ ] AC-19 [invariant] **WF-4 (NFR-3; SCR-4…SCR-8 staff console):** the same checks as AC-16 on the role switch, the representative queue (the P0 safety row first), the case view, the supervisor oversight lanes and the flags list; each priority, lane and case status carries text beside its colour — verify: the AC-4 run's axe and Lighthouse rows for SCR-4…SCR-8 plus their grayscale review in `docs/testing/ui-verify-again.md` — evidence: 0 AA violations per screen and state; the grayscale row `PASS` or `NEEDS_HUMAN_REVIEW` with its reason.
- [ ] AC-20 [invariant] **WF-5 (NFR-3; SCR-3 demo guide and controls):** the same checks as AC-16 on SCR-3 with staffing `nobody online` and `simulated staff on shift` (the "Demo: simulated staff on shift" banner) and after a clock advance — verify: the AC-4 run's axe and Lighthouse rows for SCR-3 plus their grayscale review in `docs/testing/ui-verify-again.md` — evidence: 0 AA violations per state; the grayscale row `PASS` or `NEEDS_HUMAN_REVIEW` with its reason.
- [ ] AC-21 [invariant] **WF-6 (NFR-3; SCR-9…SCR-11 measure pages):** the same checks as AC-16 on the owner outcomes, monitoring (each alert firing and quiet, said in words) and evaluation pages after AC-8's flows — verify: the AC-4 run's axe and Lighthouse rows for SCR-9…SCR-11 plus their grayscale review in `docs/testing/ui-verify-again.md` — evidence: 0 AA violations per page and state; the grayscale row `PASS` or `NEEDS_HUMAN_REVIEW` with its reason.
- [ ] AC-22 [invariant] **WF-18 (NFR-3; SCR-12 demo login):** the same checks as AC-16 on SCR-12 empty, after a wrong pair (the refusal line) and after an expired session ("Your demo session ended, so please sign in again.") — verify: the AC-4 run's axe and Lighthouse rows for SCR-12 plus their grayscale review in `docs/testing/ui-verify-again.md` — evidence: 0 AA violations per state; the grayscale row `PASS` or `NEEDS_HUMAN_REVIEW` with its reason.
- [ ] AC-23 [regression/context] Context updated in the same change: `PROJECT-CHECKLIST.md` §8 "Frontend: one integration step per contract" ticked with the run evidence and a link to `docs/testing/ui-verify-again.md` (Innocent's ★ line is his, AC-10); the area-map *Screens* line notes the frontend runs against the real backend; `.claude/state/icm-progress.md` routes-verified row — verify: `git diff --name-only` — evidence: those files.

### Observability

- Responsibilities: preserve **WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-18, WF-19** records when the real UI drives them (no
  new entry point; the frontend is their client): `request` records with `request_id` returned in a header, the code
  redacted to "[code entered]" before storage, logs free of values, the login's `auth_event` without credentials, page
  serving by route template, and the read pages counted, never recomputed.
- Capture evidence: AC-6 (WF-1 and WF-3 from the browser, forbidden code absent), AC-8 (WF-6 pages equal the WF-1/WF-2
  records), AC-9 (WF-6 values unchanged on screen), AC-5 (WF-18 and WF-19 through the real gate), AC-7 and AC-11 (WF-2,
  WF-4 from the UI); AC-16…AC-22 (NFR-3 accessibility, one criterion per workflow's screens).

### Evaluation

- Checks: the **UX-5 suite** (flow tests, axe, screenshots, Lighthouse) rerun against the real backend (AC-4), the
  contract check through Prism proxy (AC-3), and E-5's safety-first invariant visible on screen for WP-5 (AC-7). E-1's hard
  gates are not re-scored here; they stay AEA-51's (code) and Stage 9's (real models). The live walkthrough (AC-10) is
  compatibility evidence only, never a containment or quality number (integrated-journeys §3 rule 4).
- Expected-answer authority: SCREEN_SPECS (states and copy notes) and UI_CONTRACTS / the OpenAPI (Prism validates every
  response) decide what each screen and response must be; `TRACEABILITY.md` decides which test covers which REQ → US →
  FLOW → SCR → CON; Innocent's walkthrough decides usability (Claude never infers it from passing tests, UX-5).

### Metrics

- References: WF-1 inherits **M-1, M-3, M-4, M-6…M-9, M-14, M-16…M-26, M-29**, WF-2 **M-10…M-13, M-15**, WF-4 **M-13,
  M-27**, WF-6 displays **M-1…M-29**; this issue touches them only as the UI shows them: **M-14** (safety first, on
  screen), **M-15** (person on the first request: the persistent "Talk to a person" control), and the page metrics **M-3,
  M-13, M-18, M-22, M-23, M-24, M-26, M-28, M-29** and CON-20's R-39 list as rendered.
- Acceptance conditions: every metric the pages show equals the API value and the stored records (AC-8, AC-9); no metric
  is computed in the browser; no target is shown as a result; the live walkthrough's spend is recorded against the cap
  (AC-10) and reported as cost, not as M-25 or M-26 results.

### Blocked by

- Slice plan row AEA-55: AEA-49 (serve the built `dist/`; itself gated on UX-4 signed), AEA-51, AEA-52, AEA-53, AEA-58
  (browser journeys on the production build), AEA-62 (browser legs of J-2, J-3, J-6, J-8, which AC-13 runs; wave 4).
  AEA-62 was already in the slice-plan row; this ticket now matches it, so no wave moves (AEA-55 is wave 5).
- **UX-5 signed** (checklist §4b gate; `gate::ux5`).

### Agent handoff

- Area / owner: §8 frontend integration (checklist §8; ux-pipeline UX-4/UX-5). Owns `apps/web` run and test configuration
  only (after UX-5), `tests/integration/test_ui_run_records.py`, `docs/testing/ui-verify-again.md` (DAT-25) and its journey
  evidence record.
- Contracts and shared surfaces: consumes the signed OpenAPI, the UX-5 suite and `TRACEABILITY.md`, AEA-57's launcher and
  scripted adapter, AEA-58's and AEA-62's browser journeys, and the backend as merged after wave 4. **Must not edit** screens,
  components, `src/api/types.gen.ts`, the OpenAPI, `UI_CONTRACTS.md`, `docs/ux/**`, `tests/journeys/**` or any backend file:
  a failure goes back to the phase or issue that owns it (UX-5 loop rule: requirement → PRD, order → UX-1, emphasis → UX-3,
  styling → UX-4, backend behaviour → its AEA owner).
- Scope boundary / refusal: no deploy (AEA-56); paid model calls only in the AC-10 walkthrough (`live`, `gate::paid`,
  under the $30/day cap; DAT-24); choose free local ports (`ss -ltn` first), never 4019 or 5184. The demo login values come
  from the environment, never a file in the diff.
- Awaiting Innocent: WEB-1 — built on the recommended option A (`/login` plus `/assets/` and `/fonts/` load unsigned, every
  other page redirects); if he picks B, AC-5's unsigned deep link lands on a separate self-contained login page; if C, the
  app shell loads unsigned and the app itself sends the visitor to SCR-12 after the first 401.
- Wave and gates: wave 5 (slice plan row AEA-55); **`gate::ux5`** (UX-5 signed before start), `gate::paid` for the AC-10 walkthrough, and
  Innocent's ★ "UI verify again" sign-off (AC-10).
- Lane: `lane::build-loop` — it changes test and run configuration and integration tests (code-read).
- Risk: None (slice plan; no new auth, secret or sink; AC-6 re-checks the existing code redaction from the browser).
- Entry points added or changed: None added or changed; it drives WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-18 and WF-19 from
  the real frontend.
