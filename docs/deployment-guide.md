# Deployment guide: Meridian AI service agent

**Deliverable D-5** of the AEA FDE Challenge (AI Call Center Agent). Written 2026-10-21 for someone other than Innocent who
has to deploy, check, restart, reset and roll back the service on Railway. It describes what the merged deploy files
([`Dockerfile`](../Dockerfile), [`railway.json`](../railway.json), [`scripts/`](../scripts/)) actually do. Where a file and
the design disagree, the file is described and the difference is listed for AEA-50's owner on issue #54.

**How to read the labels.** Same as the [technical documentation](technical-documentation.md).

| Label | Meaning |
|---|---|
| **[A]** | An engineering default that a named measurement will replace. |
| `pending: AEA-56` | A value only the live deploy can produce (the public URL, the measured redeploy downtime). AEA-56 fills it. |

**State of the tree when this was written.** The deploy files are merged (AEA-50). Several request paths they serve are not
yet: the customer chat routes (AEA-40) and the demo clock (AEA-30) were still open, so on the assembled app a real login
answered 500 and the start-up turn sweep had no caller (section 6). The checks in section 5 are the list AEA-56 runs once
those tickets are merged; they are written from the contracts, not from a run of the live service.

**Sections.** 1 What gets deployed · 2 Before you start · 3 Variables · 4 Deploy · 5 Check it is working · 6 Restarts and
what survives · 7 Reset · 8 Roll back · 9 Traces · 10 Limits and spend · 11 Monitoring after launch · 12 Running the same
image elsewhere · 13 Known limits.

---

## 1. What gets deployed

Sources: [system design](design/system-design.md) §3.1, §9, §11 decisions 2 and 10; PRD R-40;
[data contract](design/contracts/stage7/data.md) §3, §7; [`Dockerfile`](../Dockerfile); [`railway.json`](../railway.json).

One Railway project of its own, with one service, one replica and one volume.

| Piece | What it is | Where it lives |
|---|---|---|
| Project and service | One project, one service (`app`) | Railway |
| Replicas | `numReplicas: 1` (`railway.json`) | Railway |
| Volume | Mounted at `/data`, at most 5 GB on the Hobby plan | Railway |
| `meridian.sqlite` | The working copy of the issued scheduling database plus the app's own tables | The volume |
| `checkpoints.sqlite` | The graph's per-conversation saved state | The volume |
| Code | `src/meridian/` and `scripts/`, installed from the locked dependencies | The image |
| Issued dataset | `/app/docs/data/issued/`, made read-only in the image; the source for first boot and reset | The image |
| Retrieval index | `/app/index/` with `manifest.json`, `index_record.json`, `ingest_run.json`, `staff_notes.json` | The image |
| Frontend | The built `apps/web/dist`, at `/app/apps/web/dist` | The image |
| Eval reports | `/app/eval/reports/`, loaded at start-up | The image |
| `BUILD_SHA` | The commit the image was built from, at `/app/BUILD_SHA` | The image |

**Why one replica.** Railway does not allow replicas on a service with a volume, the working copy is a SQLite file, and the
live event stream, the scheduler and the watchdog are in-process. Two copies of the service would be two different
databases (system design §9, "One service, one process, one volume").

## 2. Before you start

Sources: AEA-09's record (the ledger lists it as human work); rule `gauntlet-hosting-default`.

1. A Railway account on the existing plan (Hobby: $5 a month including $5 of usage; logs kept 7 days).
2. The Railway CLI installed and signed in: `railway login`, then `railway status` from any directory shows the project.
3. The project, the service named `app`, and its volume mounted at `/data`, all created by AEA-09. This guide does not create
   them.
4. The variables in section 3 set on the service.
5. A GitLab checkout of `innocentnortey/inno-aea-callcenter` on the machine that runs `railway up`, with the commit you mean
   to deploy checked out and a clean working tree.

## 3. Variables

Sources: [`config.py`](../src/meridian/config.py) (`ENV_NAMES`, 17 names) and [`.env.example`](../.env.example) (AEA-02); graph-core
§12; data.md §7, §9 item 1; models.md §4 (MOD-6); DO-6 *Where records live*, CAP-9; PRD R-36, R-40, R-41, R-48.

**This table has names only.** No value appears in this guide, in `.env.example` or in the image. Set values with
`railway variable set NAME --stdin --service app` (the value is read from standard input, so it never lands in shell history),
or in the dashboard. A blank value counts as unset. If a required variable is missing or blank, the service stops at
start-up and names the variable, never its value.

| Variable | What it controls | Secret? | Required? | Railway value or code default |
|---|---|---|---|---|
| `ANTHROPIC_API_KEY` | The Sonnet calls (planner fallback, responder, brief, specialist) | Secret | Required | The operator's own key |
| `OPENROUTER_API_KEY` | The Jev calls (planner, classifier) | Secret | Required | The operator's own key |
| `MERIDIAN_DEMO_USERNAME` | The shared demo login name | Secret | Required | Chosen by the operator |
| `MERIDIAN_DEMO_PASSWORD` | The shared demo login password | Secret | Required | Chosen by the operator |
| `MERIDIAN_SESSION_SECRET` | Signs the login session cookie | Secret | Required | A long random string |
| `LANGFUSE_PUBLIC_KEY` | Trace export, public key | Secret | Optional, all four or none | This app's own Langfuse project |
| `LANGFUSE_SECRET_KEY` | Trace export, secret key | Secret | Optional, all four or none | This app's own Langfuse project |
| `LANGFUSE_BASE_URL` | Trace export, server address | Not secret | Optional, all four or none | The VPS Langfuse address |
| `LANGFUSE_PROJECT_ID` | Trace export, the one project the keys must see | Not secret | Optional, all four or none | This app's own Langfuse project |
| `MERIDIAN_EVAL_KEY` | Lets an eval or load run tag its requests (`X-Meridian-Eval-Key` header); without it every request counts as live | Secret | Optional | Unset on the deployed app unless a run needs it |
| `MERIDIAN_COOKIE_SECURE` | Marks the session cookie `Secure` | Not secret | Optional | `true` on Railway (code default `false`) |
| `MERIDIAN_TRUST_PROXY_HEADERS` | Reads the client address from the proxy's forwarded header | Not secret | Optional | `true` on Railway (code default `false`) |
| `MERIDIAN_REQUIRE_FRONTEND` | Start-up fails when `dist/` is missing | Not secret | Optional | `true` on Railway (code default `false`) |
| `MERIDIAN_WEB_DIST_DIR` | Where the built frontend is | Not secret | Optional | `/app/apps/web/dist` (the image also sets it; code default `apps/web/dist`) |
| `MERIDIAN_DATA_DIR` | The data directory | Not secret | Optional | `/data` (set in the image; code default `var`) |
| `MERIDIAN_INDEX_DIR` | The retrieval index directory | Not secret | Optional | `/app/index` (set in the image; code default `var/index`) |
| `MERIDIAN_AGENT_VERSION` | The agent version stamp | Not secret | Set by the start command | Never set by hand (code default `dev`) |

Notes that are easy to get wrong:

- **Model keys come from the operator's own keys.** Do not reuse another project's key.
- **The four Langfuse values go all four or none.** Set only some and trace export stays off (`Settings.langfuse_complete()`).
  They must belong to this app's own Langfuse project (section 9). Without them trace export is off and nothing else changes.
- **`MERIDIAN_AGENT_VERSION` is set by the start command**, from `python -m scripts.agent_version`, on every start. A value set
  in the dashboard is overwritten.
- **Limits are code, not variables.** Spend cap, rate limits, turn deadline and the rest are in
  [`policy/limits.py`](../src/meridian/policy/limits.py); changing one is a code change and a redeploy (section 10).
- `PORT` is read by the start command and defaults to 8080 in the image; Railway supplies it.

## 4. Deploy

Sources: AEA-50's [`Dockerfile`](../Dockerfile), [`railway.json`](../railway.json), [`scripts/`](../scripts/);
[data contract](design/contracts/stage7/data.md) §3, §7; [cases contract](design/contracts/stage7/cases.md) §1.1, §7, §8;
system design §9 *First boot and reset*; DO-6 WF-13, WF-14, WF-16; rule `build-loop-test-scope` (AEA addition).

**Step 0. Nothing deploys on a red full suite or a red journey.** On the exact commit:

```bash
export UV_LINK_MODE=hardlink
uv run pytest                  # the full suite
uv run pytest -m journey       # every journey, as the merge gate does before a deploy
```

Both must pass. Live-model tests are marked and are not part of this gate.

**Step 1. Export a clean tree of the commit and stamp it** (DAT-22). The stamp is how the app, the monitoring page and the
latest-eval page know which commit is running.

```bash
OUT="$(mktemp -d)"
git archive HEAD | tar -x -C "$OUT"
git rev-parse HEAD > "$OUT/BUILD_SHA"
```

**Step 2. Upload and build.**

```bash
railway up "$OUT" --path-as-root --service app --ci
```

`--ci` streams the build log and exits when the build ends.

**Step 3. Get the public URL** (first deploy only; the domain stays after that):

```bash
railway domain --service app
```

The URL itself is `pending: AEA-56`.

**What the image build does** (stages in order):

1. `web`: when `apps/web/package.json` exists, `npm ci && npm run build && npm run check:dist`; it reads `apps/web` and the one
   OpenAPI file and writes nothing back.
2. `index`: runs `python -m meridian.retrieval.ingest` over the knowledge base and the transcriptions, writes `/app/index`, and
   caches the embedding model inside the image.
3. `runtime`: copies in the code, the read-only issued dataset, the index, the model cache, the built frontend, `scripts/`,
   the committed eval reports and `BUILD_SHA`. If `BUILD_SHA` is missing from the build context the build prints a warning
   and the app falls back to `RAILWAY_GIT_COMMIT_SHA`, else `unknown`.

No `ARG` or `ENV` in the Dockerfile holds a secret.

**What the start command does.** It computes `MERIDIAN_AGENT_VERSION` (the first 12 characters of the commit, a `+`, and 8
characters of a hash over the model map and the prompt files), exports it, then runs one uvicorn worker on `$PORT`.

**What the first boot does** (all inside `scripts.serve:create_deployed_app` and the app's own lifespan):

1. Copies the issued database into `/data/meridian.sqlite` when the file is missing, then applies every `schema/*.sql` file
   (every boot, not only the first).
2. Loads the four demo seed cases once and writes a `seed_event` row.
3. Writes a `deploy_record` row with status `started`, before anything that can fail.
4. Loads the retrieval index and **fails readiness if it cannot**; the deploy record is marked `failed` and start-up stops.
5. Fails start-up when `dist/` is missing, because `MERIDIAN_REQUIRE_FRONTEND` is `true`.
6. Loads the committed eval reports.
7. Marks the deploy record `completed` once `/healthz` answers 200, or `incomplete` if it has not answered 200 within 60 s
   (`COMPLETE_WITHIN_S` in `scripts/serve.py`, [A]).

Railway's own health check hits `/healthz` (section 6).

## 5. Check it is working

Sources: PRD R-2, R-26, R-35, R-48; [web contract](design/contracts/stage7/web.md) §6; DO-6 WF-13, WF-18, WF-19; OpenAPI
operations `getMonitoring` and `getLatestEval` in [`ui-contracts.openapi.yaml`](ux/03-structure/ui-contracts.openapi.yaml).

This is the smoke list AEA-56 runs after its deploy. Replace `$URL` with the public URL (`pending: AEA-56`).

1. **`/healthz` answers without a login.** `curl -i "$URL/healthz"` returns 200 and `{"status":"ok"}`. It answers 503 with
   `{"status":"stale"}` when the in-process heartbeat has gone stale.
2. **Unsigned API request is refused.** `curl -i "$URL/api/session"` returns 401 with the error code `UNAUTHENTICATED`.
3. **Unsigned page request is redirected.** `curl -i "$URL/"` returns 303 with a `Location` that starts `/login`. Only `/login`,
   `/assets/`, `/fonts/` and `/healthz` answer without a session (WEB-1 option A, still awaiting Innocent; section 13).
4. **Sign in** with the demo username and password from the Railway variables.
5. **One knowledge question** (for example a membership question) gets an answer with a source shown.
6. **"Talk to a person"** gives a reference and the policy promise.
7. **Switch to the staff role** and see that case in the staff queue.
8. **The monitoring page** shows the turns, `last_restart` and the trace-export line.
9. **The latest-eval page's `current_agent_version`** starts with the first 12 characters of the deployed commit
   (`git rev-parse HEAD | cut -c1-12`).

Then run `railway logs --service app --since 15m` and read the start-up lines (section 11).

## 6. Restarts and what survives

Sources: DO-1 §8.1, §8.2 (*Process hang*), §9; DO-3 §2.3 items 6 and 7 (item 6 as amended by web.md §9, R-W-4); PRD R-35
(Q-045 = A); DO-6 WF-17; data.md §7; cases.md §8; [`railway.json`](../railway.json);
[`services/health.py`](../src/meridian/services/health.py).

**Railway's restart policy** (`railway.json`, DAT-19): `restartPolicyType: ON_FAILURE`, `restartPolicyMaxRetries: 10` [A]
(Railway's default; the health-check restart count, M-28, revisits it). The health check path is `/healthz`.

**The in-process watchdog.** A thread probes `/healthz` every `probe_every_s` = 15 s [A] with a `probe_timeout_s` of 5 s. After
`failures_to_exit` = 3 failed probes in a row it writes a `restart` health event and calls `os._exit(1)`; the non-zero exit is
what makes Railway restart the service. Values are `AlertSettings` in `services/health.py` (cases.md §8, [A]). The monitoring
page shows the restart as `last_restart`.

**The start-up sweep.** The design (web.md §9, R-W-4, which supersedes DO-3 §2.3 rule 6's "older than 65 s") is that start-up
marks every turn still `running` as failed with a degraded handoff, with no age test. The repository method exists
(`fail_running`, `adapters/sqlite/repos_core.py`), but its caller is AEA-40's `register_chat` hunk, which was still open when
this guide was written. Until AEA-40 merges, a restart does not sweep stuck turns. Listed for AEA-50's owner on issue #54.

| After a restart | Survives? |
|---|---|
| The volume (`meridian.sqlite`, `checkpoints.sqlite`) | Yes |
| Cases, conversations, bookings, the spend ledger, health events, deploy records | Yes (they are in the volume) |
| The reply in flight when the process died | No; the customer retries (the retried turn re-runs once swept) |
| In-memory rate-limit counters and the event-stream connections | No; clients reconnect |
| The login session | Yes while its 12-hour lifetime lasts (`login_session_lifetime_s` 43,200 s, WEB-5, decided) |

**Request limit.** Railway's HTTP request limit is 15 minutes (S-232, community staff answer); a 60 s turn and the browser's
65 s give-up fit inside it (DAT-20 [A], replaced if the live smoke or the load run logs any proxy 502 or 504 on a turn).

**Redeploy downtime:** `pending: AEA-56`.

## 7. Reset

Sources: [cases contract](design/contracts/stage7/cases.md) §1.3, §7; data.md §7; DO-6 *Storage and access*, WF-15; PRD R-19;
MC-19; [`scripts/reset.py`](../scripts/reset.py).

**Live reset: from the demo controls.** `POST /api/demo/reset` (CON-9, operation `resetDemo`) behind the login, from the demo
controls in the app. It holds an exclusive lock, so other requests wait a few seconds or answer 503 `RESET_IN_PROGRESS`.
This is the normal way.

**Operator reset: `scripts/reset.py`, for a stopped service only.**

```bash
export MERIDIAN_DATA_DIR=/data      # the same variables the service reads (section 3)
python -m scripts.reset
```

It takes no options (so there is no `--help`), prints one line of ids and counts, and returns 0 on success. With the variables
missing it prints `reset status=refused reason=settings variables=...` and returns 2; with no working copy it returns 2
(`reason=no_working_copy`). **Stop the service first.** The script builds its own `ResetGate`, which cannot reach a running
server's gate, so running it beside a live service could interleave two writers on one file (data.md §7, MC-19).

**A reset restores** the five issued tables (`customers`, `technicians`, `appointment_slots`, `appointments`, `invoices`) row
for row from the issued file. **It clears** conversations, messages, turns, actions, cases and their events, briefs,
activities, follow-ups, promises, flags, identity codes, the demo inbox and the lookup and check logs, and ends open chats.
**It updates** `staff_sessions` (staff roles go back to customer) and `demo_state` (the demo clock). **It keeps** `spend_ledger`,
`health_events`, `deploy_records`, `eval_runs`, `eval_case_results`, `job_runs`, `demo_events`, `reset_events`, `seed_events`
and `ended_threads`. It also clears the saved graph checkpoints and loads the four demo seed cases again. The issued file is
never written (it is opened read-only and immutable). Lists are `adapters/sqlite/migrate.py` and cases.md §1.3.

## 8. Roll back

Sources: interview Q-051; [`adapters/sqlite/migrate.py`](../src/meridian/adapters/sqlite/migrate.py) (AEA-10);
`railway deployment list --help`, `railway redeploy --help`.

**Option A: the dashboard.** In the service's deployments list, redeploy the previous successful deployment.

**Option B: from the CLI.** `railway deployment list --service app` shows deployment ids and statuses. `railway redeploy
--service app` redeploys the latest deployment as it is. To go back to an earlier commit, check it out, run section 4's steps
1 and 2 on that commit (its own clean tree and its own `BUILD_SHA`), and use `railway up`. A rollback by `railway up` keeps the
version stamp truthful: the monitoring page and the latest-eval page then show the older commit.

**Does an older image run against a volume a newer image migrated?** As `migrate.py` behaves:

- Every boot applies the image's own `schema/*.sql` files. All 54 of their `CREATE` statements use `IF NOT EXISTS`; there is no
  `ALTER` and no schema-version table.
- So an older image starts on a newer volume and ignores tables it does not know. It does not undo anything.
- **A release that changes the columns of a table that already exists is not applied to an existing volume**, by the newer
  image or the older one, because only missing tables are created. After such a release (or its rollback) the volume must be
  rebuilt: stop the service, remove `/data/meridian.sqlite` and `/data/checkpoints.sqlite`, and start it. First boot copies the
  issued database again, applies the schema and loads the demo seed. This **loses every case and conversation** on the volume.
  Say so before doing it.
- Listed for AEA-10's and AEA-50's owner on issue #54: no migration step exists for changed columns.

## 9. Traces

Sources: DO-1 §10, SDQ-3; DO-6 *Local runs and the deployed app*, CAP-9; models.md §4 MOD-6; cases.md §8; MC-24;
[`adapters/tracing_langfuse.py`](../src/meridian/adapters/tracing_langfuse.py); AEA-09's answer; DAT-4 (still awaiting Innocent).

**To turn export on:** set all four of `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` and
`LANGFUSE_PROJECT_ID` to values from **this app's own Langfuse project**, then redeploy. Built on DAT-4 option A: the keys are
ingestion-only. If Innocent picks option B, the deployed app runs with export off, the four variables stay unset and the
`trace_export_failed` alert shows for the life of the app.

**The start-up project check.** Once at start the app calls `GET /api/public/projects` with the keys. Export goes on only if
the answer is 200 and lists exactly one project whose id equals `LANGFUSE_PROJECT_ID`. Otherwise export is off and a
`trace_export_failed` alert fires, with reason `wrong_project` (a 4xx answer, more than one project, or another id) or
`project_check_failed` (the server unreachable or a 5xx answer; this one is re-checked every 600 s [A]).

**To turn export off:** unset the four variables (all four) and redeploy. With export off every turn records `off`, and the
monitoring page's alert list shows the state.

Whatever the setting, no value of a key, address or response body is logged: alerts carry the reason code only.

## 10. Limits and spend

Sources: PRD R-41, SD-1.6; DO-1 §8, §11 decisions 4 and 11; [`policy/limits.py`](../src/meridian/policy/limits.py) (AEA-01);
models.md §6; web.md §5.

All of these are code (section 3). A change is a code change, a test run and a redeploy.

| Limit | Value | Where | What the customer sees when it trips |
|---|---|---|---|
| Model spend per day | $30, by the America/Chicago day (`Limits.spend.daily_cap_usd`) | `policy/limits.py` | `SPEND_CAP_REACHED`: "I can't answer more questions right now. A person can pick this up." |
| Turn deadline | 60 s (`Limits.turn.deadline_s`, decided SDQ-1) | `policy/limits.py` | `TURN_TIMEOUT`: "This is taking longer than it should." |
| Browser give-up | deadline plus 5 s (`browser_grace_s`, [A]) | `policy/limits.py` | The browser stops waiting |
| Turns in flight | 30 (`Admission.max_in_flight`, decided SDQ-9); turn 31 gets `BUSY` and no model call | `policy/limits.py` | `BUSY` with an offer of a person |
| Chat turns per thread | 20 a minute [A] | `Limits.web` (WEB-2) | `RATE_LIMITED`: "I can't take more messages in this chat right now." |
| Chat turns per session and per IP | 600 a minute each [A] | `Limits.web` | The same |
| Reads per session and per IP | 120 and 240 a minute [A] | `Limits.web` | 429 `REQUEST_RATE_LIMITED` |
| Rejected logins per IP | 10 in a 600 s window [A] | `Limits.web` | 429 `LOGIN_RATE_LIMITED` with `Retry-After` |
| Resets per IP | 10 in a 600 s window [A] | `Limits.web` | A refusal (R-48) |

The [A] values are replaced by the load re-measure at Stage 9 (0 limited responses at 20 conversations from one IP and one
login) and by abuse seen in the logs. Notice text is `policy/texts.py`.

## 11. Monitoring after launch

Sources: PRD R-35; DO-6; web.md §10; rule `gauntlet-hosting-default`.

- **The monitoring page** (staff roles): health tiles, spend against the cap, alerts written as decision lines
  (`spend_cap_reached`, `p95_latency_over_12_5s`, `health_check_restart`, `zero_traffic`, `failure_rate_over_2pct`,
  `trace_export_failed`), `last_restart` and the trace-export line.
- **Railway logs:** `railway logs --service app --since 1h`. Logs are structured JSON through the LOG redaction profile, kept
  7 days on Hobby. Add `--lines N` for a fixed number of lines, or `--http` for request logs.
- **The VPS Langfuse**, when export is on (section 9).

## 12. Running the same image elsewhere

Sources: DO-1 SDQ-4; [`Dockerfile`](../Dockerfile); data.md §6. SDQ-4's recommendation is option A: the held-out eval and the
load run use the deployed image on the VPS, so a reported number comes from the deployed build.

```bash
OUT="$(mktemp -d)"
git archive HEAD | tar -x -C "$OUT"
git rev-parse HEAD > "$OUT/BUILD_SHA"
docker build -t meridian:local "$OUT"
docker run --rm -p 127.0.0.1:8080:8080 \
  -v "$HOME/meridian-data:/data" \
  --env-file /path/to/private.env \
  meridian:local
```

- **Its own data directory.** The volume mount is a directory used by this run only, never Railway's data and never another
  project's. An empty directory gives a first boot.
- **The variables** are section 3's: the five required ones, plus `MERIDIAN_COOKIE_SECURE=false` when you reach the container
  over plain `http` (the code default is already `false`; leave it `true` only behind HTTPS), `MERIDIAN_EVAL_KEY` for a tagged eval or load run, and the four Langfuse values
  pointing at the VPS Langfuse when you want traces. `/path/to/private.env` is a file that never enters git.
- **Ports.** Map to a free host port; other projects on the VPS use theirs. Ports 4019 and 5184 are taken by this project's
  own dev servers.
- **Check it** with section 5's first three steps, and `docker run --rm meridian:local python -m scripts.image_check` to test the index
  without a network (it prints readiness and exits 0 or 1).

## 13. Known limits

Sources: DO-1 §6.4, §7, §9; DAT-19, DAT-20, WEB-2.

- **One replica.** Volumes forbid replicas, so one process serves everyone; the scale-up path is written in system design §7,
  not built.
- **Losing the volume loses reviewer-created cases.** No backup is planned. A reset (section 7) does the same on purpose.
- **No schema migration for changed columns** (section 8).
- **The start-up turn sweep depends on AEA-40** (section 6).
- **Open decisions this guide is built on:** DAT-4 (trace export, section 9) and WEB-1 (public paths, section 5), both on their
  recommended option and awaiting Innocent.
- **Every [A] value above and what replaces it:** restart retries, 10 (M-28 and the first live month); watchdog probe values
  (AEA-56's smoke); deploy completion window of 60 s (AEA-56's smoke); the 15-minute request limit (AEA-56's smoke or the
  Stage 9 load run); rate limits and the browser grace (the Stage 9 load re-measure, E-8); trace-export re-check interval
  (first real project-check failure).
- **Not yet measured:** the public URL and the redeploy downtime, `pending: AEA-56`.

## Hosting: Render (decided 2026-10-21, deployed 2026-10-22; supersedes Railway)

Innocent moved this project to Render (approved total across the three moved apps: $40/month). AEA was never deployed on
Railway (AEA-56 stayed gated), so wherever these files say "Railway variables", `railway.json` or `railway up`, read
"Render environment group", the Render service and a mirror-driven deploy.

- **Live service:** https://inno-aea-callcenter.onrender.com, Render service `srv-dbcogjjrjlhs73e68vhg` (Docker, Ohio, Starter $7, health check `/healthz`, one instance), 1 GB disk at `/data` (SQLite; the issued dataset in the image stays read-only). Settings live in the Render environment group `inno-aea-production` (demo login, provider keys, session secret, `MERIDIAN_*` paths).
- **Flow:** GitLab `main` (source of truth) → GitLab push mirror (existing, id 113) → GitHub `innocentnortey/inno-aea-callcenter` (public) → Render auto-deploys on commit to `main`.
- **Version stamp:** `scripts/agent_version.py` also reads `RENDER_GIT_COMMIT` (after Railway's variable, so the frozen AEA-50 test is unchanged); `/api/eval/latest` reports `current_agent_version` starting with the deployed commit.
- **Known red test, not caused by the move:** `tests/capture/test_cap9_runtime_ops.py::test_wf15_reset_script` fails on `main` before this move (the fixture inserts an older `reset_events` row, the test expects exactly one). Innocent declined changing the frozen test (2026-10-21). No full-suite run was done for the deploy at his instruction (2026-10-22); the stamp change was checked with the affected deploy tests.
