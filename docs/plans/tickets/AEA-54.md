## [AEA-54] docs: deployment guide

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

The portal's **Deployment Guide** (D-5): how someone other than Innocent deploys, checks, restarts, resets and rolls back
the service on Railway, written from the merged deploy files (AEA-50) and the final contracts. It describes what the files
actually do; where the files and the design disagree, the guide follows the files and the disagreement goes on the issue
for AEA-50's owner. The live URL and the measured redeploy downtime wait for AEA-56 (`pending: AEA-56`).

**File:** `docs/deployment-guide.md` (stage7/data.md §8; DAT-8, settled by slice plan §5 Q-1). Plain Markdown.

| # | Section | Must contain | Draws from |
|---|---|---|---|
| 1 | What gets deployed | One Railway project of its own, one service, one replica (`numReplicas: 1`), one volume at `/data` (≤ 5 GB on Hobby); what is on the volume (`meridian.sqlite` working copy + app tables, `checkpoints.sqlite`) and what is in the image (code, issued dataset read-only as the reset source, the index at `/app/index/` with `manifest.json`, `index_record.json`, `ingest_run.json`, `staff_notes.json`, the built `apps/web/dist`, `eval/reports/`, `BUILD_SHA`); why one replica | DO-1 §3.1, §9, §11 decisions 2 and 10; PRD R-40; stage7/data.md §3, §7; `Dockerfile`, `railway.json` (AEA-50) |
| 2 | Before you start | Railway account on the existing plan and the CLI logged in; the project, service and volume from AEA-09; the GitLab checkout on the machine that runs `railway up` | AEA-09's record; rule `gauntlet-hosting-default` |
| 3 | Variables | A table of every variable: name, what it controls, secret or not, required or optional, the Railway value or default. Names and defaults copied from AEA-02's merged `config.py`/`.env.example` (stage7/graph-core.md §12) plus the four web values `MERIDIAN_COOKIE_SECURE`, `MERIDIAN_TRUST_PROXY_HEADERS`, `MERIDIAN_REQUIRE_FRONTEND` (`true`) and `MERIDIAN_WEB_DIST_DIR=/app/apps/web/dist` (data.md §7); **no values**. Says that model keys come from the operator's own keys; that the four Langfuse values (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `LANGFUSE_PROJECT_ID`) must belong to this app's own Langfuse project and go all four or none, and that without them trace export stays off; that `MERIDIAN_AGENT_VERSION` is exported by the start command and never set by hand; that limits are code (`policy/limits.py`), not variables | `config.py`, `.env.example` (AEA-02); graph-core §12; data.md §7, §9 item 1; models.md §4 (MOD-6); DO-6 *Where records live*, CAP-9; PRD R-36, R-40, R-41, R-48 |
| 4 | Deploy | Exact commands: the full test suite and all journeys green on the commit first (rule `build-loop-test-scope`, AEA addition: nothing deploys on a red full suite or a red journey); export a clean tree of the commit (`git archive HEAD \| tar -x -C "$OUT"`), write `git rev-parse HEAD` into `"$OUT/BUILD_SHA"` (DAT-22), `railway up "$OUT" --path-as-root --service app --ci`, `railway domain --service app` for the public URL; what the image build does (the `web` stage when `apps/web/package.json` exists, the `index` stage running `python -m meridian.retrieval.ingest`); what the first boot does (copies the issued DB into the working copy, applies `schema/*.sql`, loads the four demo seed cases, writes `deploy_record` and `seed_event`, loads the index and fails readiness if it cannot, fails start-up if `dist/` is missing because `MERIDIAN_REQUIRE_FRONTEND=true`) | AEA-50's `Dockerfile`, `railway.json`, `scripts/`; data.md §3, §7; cases.md §1.1, §7, §8; DO-1 §9 *First boot and reset*; DO-6 WF-13, WF-14, WF-16 |
| 5 | Check it is working | The smoke list AEA-56 runs: `/healthz` answers without login; an unsigned `/api/*` request answers 401 `UNAUTHENTICATED` and an unsigned page request redirects (303) to `/login` (web.md §6); sign in; one knowledge question with a source; "talk to a person" gives a reference and the policy promise; the staff role sees the case; the monitoring page shows the turns, `last_restart` and the trace-export line; the latest-eval page's `current_agent_version` starts with the deployed commit's first 12 characters | PRD R-2, R-26, R-35, R-48; web.md §6; DO-6 WF-13, WF-18, WF-19; OpenAPI `getMonitoring`, `getLatestEval` |
| 6 | Restarts and what survives | Railway's restart policy as set in `railway.json` (`ON_FAILURE`, `restartPolicyMaxRetries: 10` [A], DAT-19); the health check path `/healthz`; the in-process watchdog (probes `/healthz`, exits after `failures_to_exit` failed probes at `probe_every_s`, the values as merged; cases.md §8 [A]); the start-up sweep that turns stuck turns into a handoff (every turn still `running` at start-up, with no age test: web.md §9, R-W-4, which supersedes DO-3 §2.3 rule 6's "older than 65 s"); what survives a restart and what does not (the in-flight reply; the volume itself); the 15-minute platform request limit accepted for the 65 s turn (S-232, DAT-20 [A]); redeploy downtime `pending: AEA-56` | DO-1 §8.1, §8.2 (*Process hang*), §9; DO-3 §2.3 items 6–7 (item 6 as amended by web.md §9, R-W-4); PRD R-35 (Q-045 = A); DO-6 WF-17; data.md §7; cases.md §8 |
| 7 | Reset | The live reset from the demo controls (CON-9, `POST /api/demo/reset`, behind the login); the operator command `scripts/reset.py` **for a stopped service only** (its own `ResetGate` cannot reach a running server; data.md §7, MC-19); what a reset restores (the five issued tables row for row), clears (conversations, cases, events and the rest of cases.md §1.3's list; open chats ended), updates (staff roles back to customer) and keeps (`spend_ledger`, `health_events`, `deploy_records`, `eval_runs`, `eval_case_results`, `job_runs`, `demo_events`, `reset_events`, `seed_events`, `ended_threads`); that the issued file is never written | cases.md §1.3, §7; data.md §7; DO-6 *Storage and access*, WF-15; PRD R-19 |
| 8 | Roll back | Redeploy the previous Railway deployment (Q-051's decision: the dashboard's deployment list, or `railway up` of the previous commit's clean tree with its own `BUILD_SHA`); whether an older image runs against a volume a newer image migrated, as AEA-10's `migrate.py` actually behaves (if it does not, say "reset after rollback" and why) | Interview Q-051; `migrate.py` (AEA-10); `railway deployment list --help` |
| 9 | Traces | Turning trace export on (the four Langfuse variables and the ingestion-only route, SDQ-3, DAT-4) and off; the start-up project check (`GET /api/public/projects`; export on only when the keys see exactly one project whose ID equals `LANGFUSE_PROJECT_ID`; otherwise export off and a `trace_export_failed` alert); that with export off every turn records `off` and the alert shows on the monitoring page | DO-1 §10, SDQ-3; DO-6 *Local runs and the deployed app*, CAP-9; models.md §4 MOD-6; cases.md §8; MC-24; AEA-09's answer |
| 10 | Limits and spend | The $30/day model-spend cap (`limits.spend.daily_cap_usd`, Chicago day) and where it is configured; per-thread, per-session and per-IP rate limits (`Limits.web`, [A] values, WEB-2); the 60 s turn deadline and 30-turn admission limit; what the customer sees when each trips (`SPEND_CAP_REACHED`, `RATE_LIMITED`, `BUSY`, `TURN_TIMEOUT` notices) | PRD R-41, SD-1.6; DO-1 §8, §11 decisions 4 and 11; `policy/limits.py` (AEA-01); models.md §6; web.md §5 |
| 11 | Monitoring after launch | Where to look: the monitoring page (alerts as decision lines), Railway logs (`railway logs --service app --since 1h`; structured JSON through the LOG redaction profile, 7-day retention on Hobby), the VPS Langfuse when export is on | PRD R-35; DO-6; web.md §10; rule `gauntlet-hosting-default` |
| 12 | Running the same image elsewhere | Building and running the image locally or on the VPS with its own data directory, as SDQ-4 decided for the held-out eval and load runs; the variables it needs there | DO-1 SDQ-4; `Dockerfile` (AEA-50); data.md §6 |
| 13 | Known limits | One replica (volumes forbid replicas); losing the volume loses reviewer-created cases (no backup planned); the 10× path is written, not built; every [A] value above with the measurement that replaces it | DO-1 §6.4, §7, §9; DAT-19, DAT-20, WEB-2 |

### Source
- Brief Part A *Required Deliverables* ("Deployment Guide"); *Code Quality Expectations* ("system should be able to run
  unmanned for a month, failures should be observable").
- PRD R-43, R-40, R-41, R-35, R-36, R-19, R-48; `SUBMISSION.md` D-5; interview Q-051 (rollback deferred to the guide).
- DO-1 §3, §7–§11, SDQ-3, SDQ-4; DO-3 §2.3; DO-6 WF-13…WF-19, CAP-9.
- Final contracts: stage7/data.md §3, §7, §8, §9 item 1; stage7/graph-core.md §12; stage7/cases.md §1.3, §7, §8;
  stage7/models.md §4, §6; stage7/web.md §5, §6, §10. Ledgers: `docs/plans/7b-decisions/data.md` DAT-4, DAT-8, DAT-19,
  DAT-20, DAT-22, DAT-29; `web.md` WEB-1, WEB-2; `merge-clashes.md` MC-19, MC-24.
- Slice plan §1 wave 4 row AEA-54; §2 (*deploy → docs*: only measured numbers wait); §3 collision row (`docs/`); §5 Q-1.
- User story / worked pair / hard problem: none; US-27 (monitoring) is described, not built, here.
- **Brief check:** serves "Deployment Guide" and "could this run for a month without you?"; touches nothing out of scope;
  weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] **WF-13 (the deployment guide R-43 requires):** All 13 sections exist in order, each citing its sources — verify: `grep -n '^## ' docs/deployment-guide.md` and read each section's opening — evidence: 13 headings matching the table.
- [ ] AC-2 [invariant] The variables table matches the code — verify: compare the table's names with the names `config.py` reads and `.env.example` lists on `main`, plus data.md §7's four web values — evidence: the lists are identical (posted on the issue); every secret is marked secret; `MERIDIAN_AGENT_VERSION` is marked "set by the start command".
- [ ] AC-3 [negative] No value of any secret or credential — verify: `grep -n -i -E 'password|api[_ -]?key|secret|token' docs/deployment-guide.md` — evidence: names and descriptions only.
- [ ] AC-4 [invariant] Every command in sections 4, 7, 8, 11 and 12 exists in the merged tree or the Railway CLI — verify: run each script with `--help` (or `--dry-run` where offered) on `main`; check each `railway` subcommand and flag against `railway <cmd> --help` — evidence: each command and its exit status on the issue.
- [ ] AC-5 [invariant] Restart, reset and rollback statements match the merged files — verify: read `railway.json`, the watchdog settings, `scripts/reset.py` and `migrate.py` against sections 6–8 — evidence: one line per statement on the issue naming the file and line it rests on; any design-vs-file difference listed for AEA-50's owner.
- [ ] AC-6 [negative] Figures that need the live deploy are pending, not guessed — verify: `grep -n -E 'pending' docs/deployment-guide.md` and `grep -n -E '[0-9]+ ?(s|seconds|minutes)\b' docs/deployment-guide.md` — evidence: the URL and redeploy downtime read `pending: AEA-56`; every other time value is a configured value cited to its file, labelled [A] where its ledger says so.
- [ ] AC-7 [invariant] Every relative link resolves — verify: `grep -o '](\([^)#]*\)' docs/deployment-guide.md | sed 's/^](//' | grep -v '^http' | while read p; do [ -e "docs/$p" ] || echo "MISSING $p"; done` — evidence: no `MISSING` lines.
- [ ] AC-8 [negative] Nothing code or tests read is touched — verify: `git diff --name-only <base>..HEAD` — evidence: only the guide, the `SUBMISSION.md` D-5 row, the README's *Documents* line for the guide (one line) and the dev-log/resume files.
- [ ] AC-9 [regression/context] Same commit: `SUBMISSION.md` D-5 Evidence names `docs/deployment-guide.md` with Status `written; live URL pending AEA-56`; the README's *Documents* line links it; no area-map, ICM or DO-3 row changes (documentation only; say so on the issue); one dev-log entry; the resume note — verify: `git diff` — evidence: the changes in one commit.

### Observability
N/A — documentation only; it describes WF-13…WF-19 and adds or changes no entry point, so no record is emitted or captured.

### Evaluation
N/A — documentation only; no suite or case is added or run, and no expected answer is set.

### Metrics
N/A — documentation only; M-26 (spend vs cap), M-28 (health-check restarts) and M-29 (trace export) are described as DO-7
defines them and computed by nothing here.

### Blocked by
AEA-50 (`Dockerfile`, `railway.json`, `scripts/`: the guide describes what they do; slice plan row AEA-54).

### Agent handoff
- Area / owner: deployment documentation; `SUBMISSION.md` D-5.
- Contracts and shared surfaces: reads AEA-01 (`policy/limits.py`), AEA-02 (`config.py`, `.env.example`), AEA-10
  (`migrate.py`), AEA-31 (reset), AEA-32 (watchdog), AEA-50 (deploy files) and AEA-09's record. AEA-56 follows this guide
  for its deploy and fills its `pending: AEA-56` lines, noting any step that differed. Must not edit any of those files or
  the README beyond its one *Documents* line.
- Scope boundary / refusal: describes the deployment; changes none of it. A wrong or missing deploy behaviour found while
  writing goes on the issue for AEA-50's owner, not into the guide as a workaround.
- Awaiting Innocent: DAT-4 — built on the recommended option A (the ingestion-only route; section 9 tells how to turn
  export on); if he picks B, section 9 says the deployed app runs with export off, the four Langfuse variables are unset
  and the `trace_export_failed` alert shows for the life of the app.
- Awaiting Innocent: WEB-1 — built on the recommended option A (`/login`, `/assets/`, `/fonts/` answer without a session);
  if he picks B or C, section 5's unsigned-request check lists only `/login` and `/healthz`, or the whole app shell, as
  public.
- Wave and gates: wave 4; no gate. Labels: `slice::docs`, `wave::4`, `lane::direct`.
- Lane: direct — a Markdown guide no code or test reads (rule `ticket-lanes`).
- Risk: None (no value written; AC-3).
- Entry points added or changed: None.
