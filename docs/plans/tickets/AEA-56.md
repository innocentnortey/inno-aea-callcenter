## [AEA-56] human: deploy to Railway and smoke test

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

The first public deployment (D-1): the merged `main`, proven green on the full suite and every journey, deployed to the
Railway project AEA-09 prepared, reachable at a public URL, and walked through a short smoke test with the demo login.
Innocent runs the deploy and the browser walk; Claude runs the pre-deploy gates and the command-line checks and records
everything. The deployed app calls the real models, so the smoke is `verified with live models` (compatibility, not
quality; integrated-journeys §4) and spends inside the $30/day cap.

#### Before the deploy (Claude)
1. On `main` at the commit to deploy, cheapest first and stop at the first red: lint and format, type check, the **full**
   test suite, then **all journeys** and the contract boundary checks (AEA-59) — rule `build-loop-test-scope` and its
   *AEA addition* ("before any deploy, run all journeys plus the full suite"). The `deploy`-marked image tests of AEA-50
   run too. Post the commit SHA, the commands and their summary lines on the issue. Red stops the ticket.
2. Confirm the inputs: AEA-61's live smoke set passed on this commit's path; AEA-09's record (project, service `app`,
   volume at `/data`, the variable-names list covering every name stage7/graph-core.md §12 and data.md §7 require, the
   DAT-4 answer); AEA-55's UI-verify-again report (`docs/testing/ui-verify-again.md`, UX-5 signed).

#### Deploy (Innocent, on the VPS; or Claude in his session if he says so on the issue, recorded)
Follow the deployment guide (`docs/deployment-guide.md`, AEA-54) section 4; the commands it gives are these:
```bash
cd /home/linuxuser/workspaces/inno-aea-callcenter
SHA=$(git rev-parse --short=12 HEAD); OUT=/tmp/aea-deploy-$SHA; rm -rf "$OUT"; mkdir -p "$OUT"
git archive HEAD | tar -x -C "$OUT"                       # a clean tree of the commit: no .env, no var/, no worktrees
git rev-parse HEAD > "$OUT/BUILD_SHA"                     # agent_version's commit part (DAT-22; railway up has no git SHA)
railway up "$OUT" --path-as-root --service app --ci       # service name as AEA-09 recorded it
railway domain --service app                              # generates the public Railway domain; record it
```
Then in a browser, signed in with the demo login (values from the Railway variables, never typed into chat).

#### Smoke test
| # | Check | Who | Expected |
|---|---|---|---|
| S-1 | `curl -s -o /dev/null -w '%{http_code}' https://<domain>/healthz` from outside the VPS | Claude | 200, no login needed (R-48 exception; web.md §6) |
| S-2 | Unsigned `curl -s -i -X POST https://<domain>/api/chat/sessions` (CON-1 `startChatSession`) and unsigned `GET /staff/queue` | Claude | 401 with `error.code` `UNAUTHENTICATED`, `details.reason` `none`; the page request answers 303 to `/login?return_to=%2Fstaff%2Fqueue&reason=none` (web.md §6, WEB-28); never a chat |
| S-3 | Sign in; the customer chat opens | Innocent | Chat screen as SCR-1 designs it; `mhc_session` set with `Secure` (`MERIDIAN_COOKIE_SECURE=true`) |
| S-4 | Ask "What does the Comfort Club membership actually include?" (WP-1) | Innocent | An answer citing its source file and version date; no `archive/` source; no stale `$149` price |
| S-5 | Tap "Talk to a person" | Innocent | A handoff on the first ask, a reference `MHC-C-…`, and the promise text for the current staffing word for word from SCREEN_SPECS (R-26; while nobody is online: "No representative is online right now. A representative will get back to you within 1 business day, by …") (R-2, R-26, R-30) |
| S-6 | Switch role to representative; open the queue | Innocent | The S-5 case is listed with its brief; the four seed cases MHC-C-0005…0008 are there labelled as demo seed (R-32, R-48 one-click switch; WF-16) |
| S-7 | Open the monitoring page (CON-19) and the latest-eval page (CON-20) | Innocent | The S-4 and S-5 turns counted; the trace-export line matches AEA-09's answer (`sent n of N`, or off with the `trace_export_failed` alert); `current_agent_version` starts with the 12-character `$SHA` |
| S-8 | `railway redeploy --service app` (or Restart in the dashboard), then reload the S-5 chat | Innocent, Claude times it | The conversation and case are still there (SD-7.2; the `/data` volume); downtime in seconds recorded (DO-1 §9 [A] "measure on the first deploy") |
| S-9 | Reset from the demo controls (CON-9) | Innocent | Seed state back; the S-5 case and chat gone ("The demo was reset, so this chat has ended."); spend and deploy records kept (cases.md §1.3) |

#### What Claude records afterwards
- On this issue: SHA, Railway deployment ID, domain, the gate results, S-1…S-9 with pass/fail and screenshots or output,
  the measured downtime, and the turn count and spend the smoke used (from CON-19).
- The evidence record `docs/testing/journeys/<date>-AEA-56.md` in the integrated-journeys §4 format (level `verified with
  live models`; tested revision = SHA and `agent_version`; no secret, demo password or personal data).
- `SUBMISSION.md` D-1: Evidence = the URL, Status `deployed <date>, smoke passed`.
- `README.md` *Try it* URL line (one line; owner AEA-25).
- The deployment guide's `pending: AEA-56` lines (URL, measured downtime) and any step that differed in practice.
- `.claude/state/icm-progress.md` row *Environment, tools and collaboration* ("Re-check at first deploy"): evidence = this
  issue. `PROJECT-CHECKLIST.md`: no tick of its own (the Stage 8 gate stays with its owner); dev-log entry; resume note
  (next: Stage 9 runs).

### Source
- Brief Part B *Deliverables* 1: "a live web app the reviewer can interact with directly. They will ask their own
  questions and try to break it, so make sure edge cases and escalation behave"; goal 6.
- PRD R-40, R-48, R-2, R-26, R-30, R-32, R-35, R-19; `SUBMISSION.md` D-1.
- DO-1 §9 (what survives a restart), §10, SDQ-3; DO-6 WF-13…WF-19, CAP-9; interview Q-051 (rollback = redeploy the
  previous Railway deployment).
- Final contracts: stage7/web.md §2, §6 (public paths, the unsigned answers); stage7/data.md §3, §7; stage7/graph-core.md
  §12; stage7/cases.md §1.3, §7, §8; stage7/models.md §4 (MOD-6). OpenAPI `startChatSession`, `getMonitoring`,
  `getLatestEval`, `resetDemo`. Ledgers: `docs/plans/7b-decisions/data.md` DAT-4, DAT-20, DAT-22, DAT-29; `web.md` WEB-1,
  WEB-28; `merge-clashes.md` MC-24.
- Rules: `build-loop-test-scope` (+ AEA addition), `integrated-journeys` §4–§5.
- Slice plan §1 row AEA-56 (wave 6); §2 critical path (… → 55 → 56).
- User stories / worked pair exercised live: US-1, US-2, US-14, US-18, US-24…US-28; WP-1; no HP of its own.
- **Brief check:** serves "Deploy the agent as a web application at a public URL" and "make sure edge cases and escalation
  behave"; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] The deployed commit passed every pre-deploy gate — verify: Claude's run on `main` at `$SHA` (lint and format, type check, full suite, all journeys, contract boundary checks, AEA-50's `deploy` tests) — evidence: summary lines on the issue, all green, naming the same SHA as the deployment's `BUILD_SHA`.
- [ ] AC-2 [invariant] The service is live at a public URL — verify: S-1 from a machine outside the VPS — evidence: HTTP 200 and the domain on the issue.
- [ ] AC-3 [failure/refusal] Every route but login, `/healthz` and the WEB-1 public files refuses an unsigned request — verify: S-2, plus unsigned `GET /api/monitoring` (CON-19) and `POST /api/demo/reset` (CON-9) — evidence: four refusals with status and `error.code` (`UNAUTHENTICATED`) or the 303 to `/login`; no data in any body.
- [ ] AC-4 [invariant] The live smoke passes — verify: S-3…S-7 and S-9 — evidence: pass per row with a screenshot or output; any fail stops the ticket and goes back to the owning ticket.
- [ ] AC-5 [invariant] A restart loses no conversation or case — verify: S-8 — evidence: the same reference number and chat before and after; downtime in seconds.
- [ ] AC-6 [capture] The deploy's runtime records exist on the live service (WF-13, WF-14, WF-16, WF-17) — verify: S-7's CON-20 `current_agent_version` (WF-13: `<12-hex SHA>+<8-hex>` from `BUILD_SHA`), S-4's cited answer and S-1's 200 (WF-14: the index loaded, readiness passed), S-6's four seed cases (WF-16), CON-19 `last_restart` after S-8 (WF-17) — evidence: the response bodies or screenshots on the issue.
- [ ] AC-7 [capture] The login and page-serving records exist (WF-18, WF-19) and the reset is logged (WF-15) — verify: `railway logs --service app --since 30m` over the smoke window, filtered to `"record": "auth_event"` and `"record": "request"` lines, and CON-19 after S-9 — evidence: one `auth_event` `ok` for S-3 with an opaque `session_id`; `request` lines with route templates (`spa_fallback`, `/assets/{file}`), never a raw path or query string; S-9's reset visible as the counts dropping to the seed state.
- [ ] AC-8 [negative] No secret, code or login value in the deployed logs — verify: `railway logs --service app` over the smoke window, searched by Innocent for the first 8 characters of each secret and for the demo username and password — evidence: "no hits" on the issue; Claude never sees the values.
- [ ] AC-9 [invariant] Trace export state matches AEA-09's answer — verify: S-7 and, if the route is on, the VPS Langfuse shows this app's project receiving the smoke turns — evidence: `off` with the `trace_export_failed` alert when the route was declined, or `sent n of N` with the traces visible in this app's project only.
- [ ] AC-10 [invariant] **WF-13 (R-42: the deployed source is public):** the GitLab project behind the deploy is public and holds what was deployed — verify: `env -u GITLAB_TOKEN glab api projects/2318 --hostname labs.gauntletai.com` (field `visibility`), `git branch -r --contains $SHA`, and `git ls-tree -r --name-only $SHA -- eval/cases docs/data/issued/meridian_dataset` — evidence: `visibility` reads `public`; `origin/main` contains the deployed SHA; the eval set and the issued dataset are listed at that SHA (held-out answer keys follow DAT-2).
- [ ] AC-11 [invariant] **WF-1 (OBS-18: export off until Innocent's yes):** while AEA-09's DAT-4 answer has not opened the trace route, the smoke's chat turns (S-4, S-5) complete with trace export off and the monitoring page says so — verify: S-7's CON-19 body read after S-4 and S-5 — evidence: the trace-export line reads export off (0 of N sent) over those turns, and both turns answered; if the route was opened before the deploy, "N/A: route opened <date>" recorded on the issue instead.
- [ ] AC-12 [invariant] **WF-13 (OBS-20: traces kept no longer than 90 days):** when the route is open, this app's VPS Langfuse project keeps traces for 90 days or less (D6) — verify: the project's data-retention setting in the VPS Langfuse, read by Innocent — evidence: the retention value or a screenshot on the issue; when the route is declined, "N/A: no traces leave" recorded.
- [ ] AC-13 [regression/context] The records in *What Claude records afterwards* are made in one commit — verify: `git diff` — evidence: the evidence record, `SUBMISSION.md` D-1, the README URL line, the guide's pending lines, the ICM row *Environment, tools and collaboration*, dev log and resume note changed; no area-map or DO-3 row changes (nothing is built here).

### Observability
- Responsibilities: none emitted by this ticket's own work; it verifies on the live deployment that DO-6's records exist
  for WF-13 (`deploy_record`, `agent_version` stamp), WF-14 (index loaded, readiness), WF-15 (reset logged), WF-16 (seed
  load), WF-17 (health events and a restart), WF-18 (`auth_event`), WF-19 (`request` with route templates), and that the
  MOD-6 project check behaves as AEA-09's answer says.
- Capture evidence: AC-6 (WF-13, WF-14, WF-16, WF-17), AC-7 (WF-15, WF-18, WF-19), AC-9 (trace export), AC-8 (no values);
  AC-10 (WF-13 public source), AC-11 (WF-1 export off), AC-12 (WF-13 trace retention).

### Evaluation
- Checks: no scored suite runs here (E-1…E-8 are Stage 9, slice plan §1 *Not tickets*). This ticket keeps them runnable
  against the deployment: WF-13's `agent_version` stamp is live (AC-6), so CON-20 can label a stale run; WF-14's index is
  the one E-2 scores (AC-6; the same image runs on the VPS per SDQ-4); `MERIDIAN_EVAL_KEY` is set so eval and load runs
  can tag their traffic (AEA-09).
- Expected-answer authority: DO-5 *Expected-answer authority* for every later scored run; for this smoke, WP-1 (S-4),
  the R-26 promise table as SCREEN_SPECS words it (S-5) and cases.md §7's seed set (S-6).

### Metrics
- References: M-28 (health-check restarts, WF-17), M-29 (trace export completeness), M-22 (volume), and WF-16's
  with-and-without-seed split of M-3, M-13 and M-27; WF-14's M-6 and M-7 stay computable from the shipped index.
- Acceptance conditions: each is computable from the deployment's stored records after the smoke (S-6, S-7, S-8); no
  target is claimed and no number from the smoke is reported as a result.

### Blocked by
AEA-09 (Railway project, variables, the DAT-4 answer), AEA-50 (deploy files), AEA-55 (UI integrated against the real
backend, UX-5 signed), AEA-61 (live-model smoke set through the real app), AEA-62 (browser journeys for the integrated
capabilities, which the pre-deploy "all journeys" gate runs) — slice plan row AEA-56 (wave 6). AEA-62 was already in the
slice-plan row; this ticket now matches it, so no wave moves.

### Agent handoff
- Area / owner: deployment (Innocent runs it; Claude gates and records).
- Contracts and shared surfaces: uses AEA-09's project and variables, AEA-50's `Dockerfile`/`railway.json`/`scripts/`,
  AEA-54's guide (and fills its pending lines). Must not change code or configuration; a failed smoke row reopens the
  owning ticket.
- Scope boundary / refusal: no deploy on a red suite or a red journey; no secret value on the issue or in chat; no Stage
  9 eval run here; rollback, if needed, is "redeploy the previous Railway deployment" (Q-051).
- Awaiting Innocent: DAT-4 — built on the recommended option A (route open, export `sent n of N` in S-7 and AC-9); if he
  picks B, S-7 and AC-9 expect export `off` with the `trace_export_failed` alert, and the Langfuse check is skipped.
- Awaiting Innocent: WEB-1 — built on the recommended option A (`/login`, `/assets/`, `/fonts/` answer unsigned); if he
  picks B, AC-3 also expects `/assets/` refused; if C, any page path returns the app shell and only `/api/*` refuses
  (S-2's 303 becomes the app's own redirect after a 401).
- Wave and gates: wave 6 (slice plan row AEA-56); `gate::human`, `gate::live`. Labels: `slice::human`, `wave::6`, `lane::human`, `gate::human`,
  `gate::live`.
- Lane: human — the deploy uses Innocent's Railway account and the smoke uses his demo login (rule `ticket-lanes`).
- Risk: not a build ticket, so no `risk::security` label; AC-3 and AC-8 cover the login gate and secret leakage live.
- Entry points added or changed: None added or changed; exercised live and verified: WF-13, WF-14, WF-15, WF-16, WF-17, WF-18, WF-19.
