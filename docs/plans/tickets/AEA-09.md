## [AEA-09] human: Railway project, variables, Langfuse route

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

Innocent prepares everything the deploy (AEA-56) will *use*, while agents build: the dedicated Railway project with its one
service and its volume, the service's variables, a new Langfuse project with its own keys, and his yes or no on opening the
ingestion-only route from Railway to the VPS Langfuse (DAT-4). Nothing here is deployed. **Values never appear on this
issue, in the repo, in a log or in chat; this ticket names variables only.**

**Facts already checked (2026-10-21, on the VPS):** the Railway CLI is 5.71.0 and logged in as Innocent; his account has
projects for six other repos and **no** project for this one. `railway variable set --help` confirms `--stdin` (single
key) and `--skip-deploys`; `railway volume add --help` confirms `--mount-path`. The VPS Langfuse web listens on
`127.0.0.1:3100` (container `yourai-langfuse-langfuse-web-1`). **Ports 80 and 443 on the VPS are already bound** by a
process the earlier read could not name (`ss -ltn`; no Docker container publishes them), so the route in step 5 goes
through whatever already owns them.

#### Steps for Innocent

1. **Create the Railway project** (R-40: its own dedicated project; Railway on the existing plan, SD-1.6). Either
   railway.com → *New Project* → *Empty Project*, or on the VPS:
   `cd /home/linuxuser/workspaces/inno-aea-callcenter && railway init --name inno-aea-callcenter`
   (his other projects are named after their repos; any name works, Claude records the one used).
2. **Create the one service and link the checkout:** `railway add --service app`, then `railway link` (choose the project,
   environment `production`, service `app`). One service, one replica (DO-1 §3, §11 decision 2; `railway.json`
   `numReplicas: 1`, stage7/data.md §7). AEA-56 deploys with `railway up` from the VPS, not from a Git integration (the
   repo is on Gauntlet's GitLab), so `RAILWAY_GIT_COMMIT_SHA` stays empty and the version comes from `BUILD_SHA` (DAT-22).
3. **Attach the volume:** `railway volume add --mount-path /data` (DO-1 §9: `meridian.sqlite` and `checkpoints.sqlite` on
   a volume at `/data`, ≤ 5 GB on Hobby). Do not add a database service.
4. **Create the Langfuse project and its keys** (only needed if step 5 is yes). Open the VPS Langfuse through the SSH
   tunnel to `localhost:3100` → *New project* (one for this app only, never YourAI's project) → *Settings* → *API Keys* →
   *Create new API keys*; note the project's **ID** from its settings page. These are **new keys, not the YourAI keys**
   (DO-6 *Local runs and the deployed app*); the app's start-up check turns export on only when the keys see exactly one
   project whose ID equals `LANGFUSE_PROJECT_ID` (stage7/models.md §4 MOD-6), so an organisation-scoped key fails it.
5. **Decide the Langfuse route (DAT-4; Q-062).** SDQ-3 decided the method: a TLS reverse proxy on a VPS hostname that
   exposes **only** Langfuse's ingestion path; the UI stays on localhost behind the SSH tunnel. Turning it on, and the
   hostname, are his.
   - **If yes (option A, recommended):** name the hostname (a name under a domain he controls), create its DNS record, and
     run `sudo ss -ltnp 'sport = :443'` to name what owns 443. Claude then posts on this issue the exact proxy
     configuration for that server, allowing only (a) `GET /api/public/projects`, the project check the app makes at
     start-up (models.md §4 MOD-6), and (b) the OTLP trace path AEA-19's exporter posts to, read from AEA-19's merged
     `adapters/tracing_langfuse.py` and Langfuse's own documentation, both cited. Innocent applies it (or tells Claude in
     writing on the issue to apply it).
   - **If no (option B):** nothing is exposed. The deployed app builds `NullTraceSink`; every turn records
     `trace_export = off`, M-29 reads off, and the monitoring page shows the `trace_export_failed` alert for the life of
     the app (MC-24; cases.md §8). Local and VPS runs still trace through `localhost:3100`.
6. **Set the service variables, by name, values typed or piped, never pasted into chat.** Use
   `railway variable set --service app --stdin <NAME> --skip-deploys` so a value never lands on the command line or in shell
   history. Names are AEA-02's `Settings` (stage7/graph-core.md §12, GRC-22; data.md §7 and §9 item 1, DAT-9, DAT-29); they
   are fixed in the contract, so this step does not wait for a merge, and AC-2 re-checks them against AEA-02's merged
   `.env.example`.

   | Variable | Secret | What it holds | Source of the value |
   |---|---|---|---|
   | `ANTHROPIC_API_KEY` | yes | Sonnet roles (R-40) | YourAI `.env` key `SCP_LLM_API_KEY`: `grep '^SCP_LLM_API_KEY=' /home/linuxuser/workspaces/inno-yourai-pipeline/.env \| cut -d= -f2- \| railway variable set --service app --stdin ANTHROPIC_API_KEY --skip-deploys` |
   | `OPENROUTER_API_KEY` | yes | Jev planner and classifier (model mix B) | YourAI `.env` key `SCP_OPENROUTER_API_KEY`, same pipe |
   | `MERIDIAN_DEMO_USERNAME` | yes | The one demo login's username (R-48) | Innocent chooses |
   | `MERIDIAN_DEMO_PASSWORD` | yes | The one demo login's password (R-48) | Innocent chooses |
   | `MERIDIAN_SESSION_SECRET` | yes | HMAC key for login tokens and code hashing (staff.md §2, STF-5; DO-3 §2.4) | `openssl rand -hex 32 \| railway variable set --service app --stdin MERIDIAN_SESSION_SECRET --skip-deploys` |
   | `MERIDIAN_EVAL_KEY` | yes | Lets eval and load runs tag their traffic (DO-6 *Correlation*; header `X-Meridian-Eval-Key`, web.md §4); unset means nothing is ever tagged | A new random value, same command |
   | `MERIDIAN_DATA_DIR` | no | `/data` (the volume) | literal |
   | `MERIDIAN_INDEX_DIR` | no | `/app/index` (built into the image) | literal |
   | `MERIDIAN_COOKIE_SECURE` | no | `true` | literal (data.md §7) |
   | `MERIDIAN_TRUST_PROXY_HEADERS` | no | `true` | literal |
   | `MERIDIAN_REQUIRE_FRONTEND` | no | `true`: an image without `dist/` fails start-up instead of serving no UI (WEB-32) | literal |
   | `MERIDIAN_WEB_DIST_DIR` | no | `/app/apps/web/dist` | literal |
   | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | yes | Trace export keys (R-36) | step 4's keys. **Only if step 5 is yes** |
   | `LANGFUSE_BASE_URL` | no | `https://<the step 5 hostname>` | **Only if step 5 is yes** |
   | `LANGFUSE_PROJECT_ID` | no | The new project's ID (MOD-6, MC-21) | step 4. **Only if step 5 is yes**; all four or none |

   **Not set as variables:** `MERIDIAN_AGENT_VERSION` (the start command exports it, data.md §7), the spend cap and every
   other limit (code in `policy/limits.py`, graph-core §12 *Not in Settings*), and the parked `.env.example` names
   `MERIDIAN_DAILY_SPEND_CAP_USD`, `MERIDIAN_LLM_MODEL`, `MERIDIAN_FAST_MODEL`, `MERIDIAN_TODAY` (retired).
7. **Confirm without revealing:**
   `railway variable list --service app --json | python3 -c 'import json,sys; print(sorted(json.load(sys.stdin)))'`
   prints the names only; paste that list on the issue.

#### What Claude records afterwards
- On this issue: the project and service names, the volume mount path, the variable **names** list from step 7, the
  Langfuse project name (not its keys or ID), and step 5's answer in Innocent's words with the date.
- `.claude/rules/project-provenance.md` *Host* line: the Railway project name and that it exists (date).
- `PROJECT-CHECKLIST.md` §0 *Remote and host set per policy*: the Railway half (GitLab was done 2026-10-21).
- `docs/design/observability-contract.md` *Open items* 1: the route answer (yes with hostname, or no → deployed export off).
- `docs/plans/7b-decisions/data.md` DAT-4: the answer and date (resolution recorded, per memory `decisions-must-be-defensible`).
- One dev-log entry; the resume note.

### Source
- PRD R-40 (own Railway project, keys from the YourAI `.env`), R-36 (traces to the VPS Langfuse, redacted), R-48 (demo
  login variables), R-41/SD-1.6 (spend cap; Railway on the existing plan).
- DO-1 `docs/design/system-design.md` §3.1 (one service, one replica, volume `/data`), §9, §10 (*Secrets*, *The Langfuse
  route*), SDQ-3; DO-6 *Where records live*, *Open items* 1, CAP-9.
- Final contracts: stage7/graph-core.md §12 (the `Settings` field list and env names, GRC-22); stage7/data.md §7 (Railway
  variables), §9 item 1; stage7/models.md §4 (MOD-6 project check), cross-topic 7; stage7/web.md §4 (eval header).
  Ledgers: `docs/plans/7b-decisions/data.md` DAT-4, DAT-9, DAT-22, DAT-29; `merge-clashes.md` MC-21, MC-24.
- Rule `gauntlet-hosting-default` (secrets are Railway variables, never committed).
- Slice plan §1 wave 0 row AEA-09; §2 *Human gates* ("only its use (AEA-56) waits"); §5 Q-2, Q-3.
- **Brief check:** serves "Deploy the agent as a web application at a public URL" and Part A *Other Requirements*
  "observability/monitoring tooling for production metrics"; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] A dedicated Railway project with one service and a volume at `/data` exists — verify: `railway status` and `railway volume list` from the linked checkout — evidence: output on the issue naming the project, service `app` (or the recorded name) and one volume mounted at `/data`; no other service in the project.
- [ ] AC-2 [invariant] Every required variable is set on the service, by the names `Settings` reads — verify: step 7's names-only list compared with graph-core §12 / data.md §7 and, once AEA-02 merges, with the names its `.env.example` lists — evidence: the list holds the twelve non-Langfuse names of step 6; the four `LANGFUSE_*` names are all present (route yes) or all absent (route no); no `MERIDIAN_AGENT_VERSION` and no retired name.
- [ ] AC-3 [negative] No value leaked — verify: Innocent runs, locally, `grep -rn -F` for the first 8 characters of each secret over the repo, this issue's text and the dev log (Claude never sees the values) — evidence: Innocent's "no hits" on the issue; the issue shows names only.
- [ ] AC-4 [invariant] If the route is yes, the Langfuse keys belong to a new project, not YourAI's — verify: Langfuse UI → the new project's *API Keys* list shows the created pair; YourAI's project keys unchanged — evidence: Innocent's confirmation on the issue (project name only). The automated proof is AEA-19's MOD-6 test and AEA-50's AC-8 (wrong project → export off and an alert). If the route is no: `N/A, route declined <date>`.
- [ ] AC-5 [invariant] Step 5 has an answer in Innocent's words — verify: read the issue and DO-6 *Open items* 1 — evidence: the quoted answer and date in both places, and the DAT-4 row resolved.
- [ ] AC-6 [failure/refusal] If the route is on, only the two allowed paths are public — verify: from outside the VPS, `curl -s -o /dev/null -w '%{http_code}' https://<host>/` (the UI root), the same for `/api/public/projects` and the OTLP trace path without credentials — evidence: the UI root is refused (403 or 404); both allowed paths answer 401 (they exist but need keys). If the route is off: `N/A, route declined <date>`.
- [ ] AC-7 [regression/context] The records in *What Claude records afterwards* are made in one commit; no area-map or DO-3 row changes (nothing is built), and the ICM row *Environment, tools and collaboration* gets its "Re-check at first deploy" evidence only at AEA-56 — verify: `git diff` — evidence: `project-provenance.md`, `PROJECT-CHECKLIST.md` §0, DO-6 *Open items*, the DAT-4 ledger row, dev log and resume note changed.

### Observability
N/A — account and hosting setup; no code runs and no entry point is added or changed. The records this setup enables
(`deploy_record`, `turn.trace_export`, the MOD-6 project check and its alert) are emitted by AEA-19, AEA-32 and AEA-50 and
verified live in AEA-56.

### Evaluation
N/A — no suite or case runs here; setting `MERIDIAN_EVAL_KEY` only lets AEA-24's runs tag traffic later.

### Metrics
N/A — affects no metric's records directly. M-29 (trace export completeness) reads `off` on the deployment if step 5 is
no; that is recorded on the issue, not a failure of this ticket.

### Blocked by
None (wave 0).

### Agent handoff
- Area / owner: hosting and secrets (Innocent); Claude writes the steps, posts the proxy configuration if the route is
  yes, and records the outcome.
- Contracts and shared surfaces: produces the Railway project, service, volume and variables that AEA-50 (`railway.json`)
  and AEA-56 (deploy) use, and the Langfuse keys and project ID AEA-19's sink reads. Must not edit code, `config.py` or
  `.env.example` (AEA-02) or any YourAI file; reading `inno-yourai-pipeline/.env` is by Innocent's pipe only, never printed.
- Scope boundary / refusal: no deploy (AEA-56); no Langfuse UI exposed to the internet; no value in any file or message;
  no proxy change applied by Claude without Innocent's written yes on the issue.
- Awaiting Innocent: DAT-4 — built on the recommended option A (ingestion-only route on a hostname he names, the four
  `LANGFUSE_*` variables set); if he picks B, steps 4 and 5's proxy work and the `LANGFUSE_*` rows are skipped, AC-4 and
  AC-6 read `N/A, route declined`, and the deployed app runs with export off and the `trace_export_failed` alert showing.
- Wave and gates: wave 0; `gate::human`, `gate::live` (it changes live accounts and, if yes, a public network route).
  Labels: `slice::human`, `wave::0`, `lane::human`, `gate::human`, `gate::live`.
- Lane: human — accounts, credentials and a network-exposure decision only Innocent can make (rule `ticket-lanes`).
- Risk: not a build ticket, so no `risk::security` label; the exposure risk is covered by AC-3 and AC-6's outside check.
- Entry points added or changed: None.
