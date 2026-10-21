## [AEA-50] deploy: Dockerfile, Railway config, scripts

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

The deployable image and its Railway configuration, proven locally, so AEA-56 (human) can deploy it without editing
anything. Exactly as stage7/data.md §7 decides:

- **`Dockerfile`**, three stages in order: `web` (only when `apps/web/package.json` exists: `npm ci && npm run build`,
  reads `apps/web` and the one file `docs/ux/03-structure/ui-contracts.openapi.yaml`, writes nothing back; DAT-21,
  AEA-50-1, AC-17) → `index` (`python -m meridian.retrieval.ingest --kb-dir … --transcriptions-dir …
  --out-dir …`, the WF-14 entry point of data.md §3, with the `BAAI/bge-small-en-v1.5` fastembed model cached in the image
  so nothing downloads at run time) → `runtime` (the code, the issued dataset read-only, `/app/index/`,
  `/app/apps/web/dist/` when built, `/app/eval/reports/`, `BUILD_SHA`). No `ARG` or `ENV` holds a secret.
- **Start command** (data.md §7; DAT-22): `sh -c 'export MERIDIAN_AGENT_VERSION="$(python -m scripts.agent_version)" &&
  exec uvicorn … --workers 1 --port "$PORT"'`: one Uvicorn worker (DO-1 §11 decision 1) on Railway's `PORT`.
- **`scripts/agent_version.py`**: `compute_agent_version(git_sha, model_config, prompt_files) -> str` =
  `f"{git_sha[:12]}+{h[:8]}"`, `h` the SHA-256 of canonical JSON `{"models": model_config, "prompts": {relative path:
  sha256(bytes)}}` over `src/meridian/agent/prompts/*.py` and `src/meridian/policy/texts.py`; `git_sha` from
  `$RAILWAY_GIT_COMMIT_SHA` when set, else the `BUILD_SHA` file the deploy step writes (`git rev-parse HEAD`, `-dirty`
  appended for a dirty tree), else `"unknown"`. The model map comes from `Settings.role_model_map()` (graph-core §12); the
  value reaches every stamp through `Settings.agent_version` (`MERIDIAN_AGENT_VERSION`).
- **`.dockerignore`** that keeps every local secret and run artefact out of the build context (the repo root holds a real
  `.env`; `var/` holds SP-1 run records and a ledger; `eval/cases/` holds the eval scripts and, under DAT-2 option A, the
  held-out keys; the runtime image needs none of them).
- **`railway.json`** (data.md §7): `build.builder` `DOCKERFILE`, `dockerfilePath` `Dockerfile`; `deploy.healthcheckPath`
  `/healthz`, `restartPolicyType` `ON_FAILURE`, `restartPolicyMaxRetries` 10 ([A] DAT-19, Railway's default, revisited
  with M-28), `numReplicas` 1 (DO-1 §11 decision 2). No slow endpoint is added for a proxy-hold check: DAT-20 accepts
  S-232's 15-minute platform limit [A].
- **`scripts/reset.py`** (WF-15, operator path, stopped service only): calls `ResetService.reset(datetime.now(UTC),
  request_id=<new UUID4>, session_id=None, role=None)` (cases.md §7, MC-19, MC-20) with the real injected callables
  (`migrate.restore_working_copy`, `Checkpointer.clearing`, `seed_demo`; cases.md §1.4, §7) and its own `ResetGate`
  (web.md §7). The live path is CON-9 (AEA-43); AEA-54's guide says the script is for a stopped service.
- **CAP-9** (`tests/capture/test_cap9_runtime_ops.py`): WF-13…WF-17 proven at their real entry points: the image build
  (ingestion), the image's start command, the reset script, first boot (migration and seed) and a forced health-check
  failure.

**Example pair it protects end to end: WP-1.** The stale twin `archive/comfort_club_overview.md` is excluded by the
manifest (R-10); this image's index must hold no passage from it, so no customer can ever be quoted `$149` or "cancel any
time for a full prorated refund" from the shipped index.

**Seams this issue wires (which double each consumer used, and the real object here):**

| Consumer (ticket) | What its tests used | Real object proven here |
|---|---|---|
| `scripts/reset.py` (this issue) | — | `ResetService` (AEA-31) with `restore_working_copy(tx)`, `Checkpointer.clearing()` (AEA-10), `seed_demo` (AEA-31) and a `ResetGate` (AEA-23) |
| `FastembedIndex` readiness (AEA-33) | an index built in a temp dir | the index built by `retrieval/ingest.py` (AEA-16) during `docker build`, loaded from `/app/index/` |
| Start-up records (AEA-32 `deploy_record`, `health_event`, `load_eval_reports`; AEA-31 `seed_event`) | temp SQLite | the image's start command on an empty data directory |
| Langfuse project check (AEA-19, MOD-6) and `on_alert` → `AlertWriter.fire` (AEA-32, MOD-7) | a stub in its own tests | the start-up the image runs, against a local stub Langfuse with this project's ID and with another |
| `Watchdog` exit (AEA-32) → restart | an injected exit callable | a real process exit under `docker run --restart on-failure` |
| `Settings.agent_version` (AEA-02) | the `"dev"` default | `MERIDIAN_AGENT_VERSION` exported by the start command |

User stories served: **US-27** (the reviewer can see the system's health and the restart behind it), **US-25** (reset
restores the demo honestly). PRD **R-40** (Railway, own project, secrets in variables), **R-19** (working copy; reset),
**R-35** (health check restarts the service), **R-36** (no trace leaves for another project), **R-48** (`/healthz` is the
only route besides login that answers without a session).

### Source

- PRD R-19, R-35, R-36, R-40, R-42, R-48; §5 *Reliability*.
- stage7/data.md §3 (ingest CLI, index directory layout, `IngestRun`, `manifest_hash`), §7 (deploy, the decision of
  record), §9 item 1 (env names); graph-core.md §12 (`Settings` fields `agent_version`, `role_model_map`, `data_dir`,
  `index_dir`, the four Langfuse values); models.md §4 (MOD-6 project check, `on_alert`), §7 (container wiring);
  cases.md §1.1 (`deploy_records`, `reset_events`, `seed_events`, `health_events`), §1.3–§1.4 (what a reset restores and
  keeps; the two callables), §7 (`ResetService.reset`, the seed set), §8 (`AlertSettings`, `Watchdog`, `load_eval_reports`);
  web.md §6–§7 (`/healthz` public; `ResetGate`).
- Decision ledgers: `docs/plans/7b-decisions/data.md` DAT-12, DAT-19, DAT-20, DAT-21, DAT-22, DAT-23 (and open DAT-2,
  DAT-4); `merge-clashes.md` MC-19, MC-20, MC-21, MC-24.
- DO-1 `docs/design/system-design.md` §8.1 (60 s deadline; S-232), §8.2 (*Retrieval index*, *Langfuse on the VPS*,
  *Process hang*), §9 (volume vs image; first boot and reset), §10 (*Secrets*), §11 decisions 1, 2, 8, 10; SDQ-3.
- DO-3 `docs/design/code-design.md` §2.3 rules 3 and 7, §3 (`Dockerfile · railway.json · scripts/`), §8 (A12 Deploy).
- DO-6 `docs/design/observability-contract.md`: WF-13…WF-17 rows; *Correlation* (`deploy_id`, `agent_version`);
  *Storage and access*; *Missing instrumentation* (wrong Langfuse project); **CAP-9**.
- DO-5 `docs/design/evaluation-plan.md`: E-2 (WF-14 inherits it). DO-7: M-3, M-6, M-7, M-13, M-26, M-27, M-28, M-29.
- `.claude/rules/gauntlet-hosting-default.md` (Railway default; secrets are Railway variables, never committed);
  `.claude/rules/integrated-journeys.md` §4 (evidence record) and `build-loop-test-scope.md` *AEA addition*.
- Slice plan row AEA-50; collision map rows `tests/capture/` (CAP-9 is this issue's) and `README.md`/`docs/` (the
  deployment guide is AEA-54's).
- **Brief check:** serves "Deploy the agent as a web application at a public URL" and "Could this run for a month without
  you? Would the business know if it broke?"; touches nothing out of scope (the deploy itself is AEA-56); weakens nothing →
  proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] One command builds the image from a clean checkout, the `index` stage runs the ingest CLI, and the runtime image holds `/app/index/` (`manifest.json`, `passages.jsonl`, `vectors.npy`, `index_record.json`, `ingest_run.json`, `staff_notes.json`), `/app/eval/reports/`, `BUILD_SHA` and the issued dataset — verify: `docker build -t meridian:aea50 .` then `tests/deploy/test_image.py::test_index_built_in_image` (`-m deploy`) — evidence: build log shows the ingest step; `index_record.json` reads embedding model `BAAI/bge-small-en-v1.5`, 17 files, a chunk count and a manifest hash; `ingest_run.json` status `completed`.
- [ ] AC-2 [invariant] The `web` stage runs only when `apps/web/package.json` exists (DAT-21): with it, the runtime image holds `/app/apps/web/dist/index.html` and no `node_modules`; built from a temp copy of the context without that file, the build succeeds and the image holds no `dist` — verify: `tests/deploy/test_image.py::test_web_stage_conditional` (`-m deploy`) — evidence: both builds' file listings.
- [ ] AC-3 [invariant] **CAP-9, WF-13 (readiness):** The container passes `FastembedIndex` readiness and answers a knowledge search with **no network** (model files and index are in the image) — verify: `tests/deploy/test_image.py::test_runs_without_network` (`docker run --network none`) — evidence: readiness passes; no download attempt in the container log.
- [ ] AC-4 [negative] **WF-13 (image):** No secret, run artefact or eval case reaches the image: the test builds from a temp copy of the context into which it writes sentinel `.env`, `.env.local`, `var/sp1-runs/ledger.jsonl` and `eval/cases/heldout/x.key.json` (sentinel strings generated at test time, never real values), then greps `docker save` output and `docker history --no-trunc`; the Dockerfile declares no `ARG`/`ENV` named like a key, password or secret — verify: `tests/deploy/test_image.py::test_no_secrets_in_image` (`-m deploy`) — evidence: 0 sentinel hits; `.dockerignore` read-back lists `.env`, `.env.*`, `var/`, `.venv/`, `.git/`, `**/node_modules`, `eval/cases/`.
- [ ] AC-5 [invariant] The issued data is never written and the working copy lives only in the data directory (R-19, DO-1 §9): the image starts on an empty mounted directory set as `MERIDIAN_DATA_DIR`, then the reset script runs — verify: `tests/deploy/test_image.py::test_first_boot_writes_only_data_dir` (`-m deploy`) — evidence: `meridian.sqlite` and `checkpoints.sqlite` exist only in that directory; the image holds no working copy; the issued SQLite file's SHA-256 is identical before first boot, after first boot and after reset.
- [ ] AC-6 [capture] **CAP-9, WF-13 (deploy):** the image's start command writes one `deploy_record` with a non-empty `deploy_id`, the commit SHA, `agent_version`, and the other fields DO-6's WF-13 row lists (config hash; trace export `on`/`off`), and `agent_version` equals `Settings.agent_version` and has the form `<12 hex>+<8 hex>` from the `BUILD_SHA` the test writes; with no Langfuse values set, trace export reads `off` — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf13_startup_writes_deploy_record` (`-m deploy`, reads the row back from the mounted data directory) — evidence: the row with every field non-empty.
- [ ] AC-7 [invariant] `compute_agent_version` is stable and sensitive (DAT-22): the same inputs give the same value; one changed byte in a prompt file or in the role → model map changes the 8-hex suffix only; `RAILWAY_GIT_COMMIT_SHA` wins over `BUILD_SHA`, which wins over `"unknown"`; a `-dirty` SHA is kept — verify: `tests/deploy/test_agent_version.py` — evidence: each case asserted.
- [ ] AC-8 [capture] **CAP-9, WF-13/WF-17 (wrong Langfuse project, MOD-6):** against a local stub Langfuse that answers `GET /api/public/projects` and counts ingested spans: keys whose one project `id` equals `LANGFUSE_PROJECT_ID` → export `on`; another project's id → export `off`, `on_alert("wrong_project")` once, an `alert_fired` `health_event` of type `trace_export_failed`; any of the four Langfuse values missing → `NullTraceSink` and no `wrong_project` alert — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf13_wrong_project_keys_turn_export_off` — evidence: export state per case; the alert row; **0 spans received** by the stub in the wrong-project case (DO-6 forbidden: any span sent to a project that is not this app's).
- [ ] AC-9 [capture] **CAP-9, WF-14 (ingestion):** the built image's `manifest.json` has **17 rows**, each with status and parse method; every non-current row (R-10), including `archive/comfort_club_overview.md` (WP-1's stale twin), has `chunks` 0; `passages.jsonl` holds no passage whose id starts with `archive/` and none from `internal/agent_discretion_notes.md` (that file is only in `staff_notes.json`); `ingest_run.json` carries `ingest_run_id`, the manifest hash and the chunk count that `index_record.json` reports — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf14_manifest_and_index_in_image` (`-m deploy`, reads from the built image) — evidence: 17 rows; the excluded rows; 0 forbidden passage ids.
- [ ] AC-10 [capture] **CAP-9, WF-15 (reset script):** on a stopped data directory with a live conversation, a case and spend rows, `scripts/reset.py` writes one `reset_event` (`asked_by_role` and `asked_by_session` NULL, `request_id`, `restored_json`, `open_chats_ended`, `roles_reset`, `checkpoints_cleared` 1) and one `seed_event` (`reset_id` set, `seed_count` 4, label `demo seed`); the five issued tables equal the issued file row for row; the cleared tables of cases.md §1.3 are empty apart from the 4 seed cases; `spend_ledger`, `health_events`, `deploy_records`, `eval_runs` and `job_runs` row counts are unchanged — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf15_reset_script` — evidence: the two event rows; per-table counts before and after.
- [ ] AC-11 [capture] **CAP-9, WF-16 (first boot and seed):** first boot on an empty data directory copies the issued DB, applies every `schema/*.sql`, loads the seed (MHC-C-0005…MHC-C-0008, `run_tag = 'seed'`, cases.md §7) and writes one `seed_event` with `deploy_id` set, `seed_count` 4 and label `demo seed`; a second start on the same directory writes no second seed — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf16_first_boot_seed` — evidence: the `seed_event` row; the four seed refs; one seed event after two starts.
- [ ] AC-12 [capture] **CAP-9, WF-17 (health check and restart):** `/healthz` answers 200 without a login from the running image; with the probe forced to fail, the `Watchdog` exits after `failures_to_exit` (3) failed probes at `probe_every_s` (15 s) (cases.md §8, [A]); under `docker run --restart on-failure` the process comes back; `health_event` rows record each `check_failed` and the `restart` with time and reason — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf17_forced_failure_restarts` (`-m deploy`) — evidence: `/healthz` 200 unsigned; container restart count 1; the failure and restart rows. The fault switch the planner chooses is **not reachable in the deployed configuration** (read back in AC-13).
- [ ] AC-13 [invariant] Configuration read-back: `railway.json` holds exactly the data.md §7 values (`DOCKERFILE`, `Dockerfile`, `/healthz`, `ON_FAILURE`, `restartPolicyMaxRetries` 10, `numReplicas` 1); the image's start command exports `MERIDIAN_AGENT_VERSION` and runs one Uvicorn worker on `0.0.0.0:$PORT`; the image declares no secret `ENV`; the AC-12 fault switch is absent from the deployed settings — verify: `tests/deploy/test_railway_config.py` (JSON and `docker inspect` read-back, `-m deploy`) — evidence: each field printed and matched.
- [ ] AC-14 [invariant] Nothing in the image or `railway.json` shortens a request below the 65 s the browser waits (DO-3 §2.3 rule 7), and no endpoint exists only to hold a request open (DAT-20 accepts S-232 [A]; AEA-56's smoke or the Stage 9 load run replaces it) — verify: `tests/deploy/test_railway_config.py::test_no_timeout_below_65s` — evidence: no server or proxy timeout below 65 s; route list unchanged by this diff.
- [ ] AC-15 [negative] The reset script, the agent-version script and the image checks print IDs, counts and statuses only: sentinel name, phone, key and password values seeded at test time appear in no stdout line and no container log line — verify: `tests/capture/test_cap9_runtime_ops.py::test_ops_output_has_no_values` — evidence: 0 sentinel hits.
- [ ] AC-16 [journey] No journey path imports `Dockerfile`, `railway.json` or `scripts/`, so this issue extends none: the merge gate's affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the evidence record (`docs/testing/journeys/<date>-AEA-50.md`, integrated-journeys §4) states the level of every CAP-9 claim and that the all-journeys pre-deploy run is AEA-56's — verify: the affected-journey command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.
- [ ] AC-17 [invariant] The `web` stage builds exactly as the UX session's recipe says (AEA-50-1; shell audit F2, F3, F4; customer audit F-1): it copies `apps/web/` and the one file `docs/ux/03-structure/ui-contracts.openapi.yaml` to the same relative paths, uses the Node version `apps/web/package.json` `engines.node` names (or the recipe's, until `engines` exists), runs `npm ci` with dev dependencies (no `--omit=dev`, no `NODE_ENV=production` before the build), then `npm run build && npm run check:dist` with no `--mode`, and copies only `dist/` into the runtime image — verify: `docker build --target web .` then the AC-2 check on the full image — evidence: the build log shows `prebuild` regenerating from the copied spec and `check:dist` passing; `/app/apps/web/dist/index.html` present; no `node_modules` and no OpenAPI file in the runtime image.
- [ ] AC-18 [negative] **WF-13 (start-up output; OBS-21):** the image's start command, run on an empty data directory with sentinel model-key, eval-key, session-secret and demo-password values generated at test time as its environment (no Langfuse values), writes container log lines that each parse as one JSON record through AEA-23's allow-list formatter (IDs, statuses, timings and counts only; DO-6 *Content and redaction* step 3); no sentinel value appears in any log line or in the `deploy_record` row — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf13_startup_logs_allow_listed` (`-m deploy`) — evidence: 0 lines outside the allow-list; 0 sentinel hits.
- [ ] AC-19 [capture] **WF-13 (deploy status; OBS-13):** the `deploy_record` the start command writes takes only DO-6 *Status values* (`started`, `completed`, `failed`, `incomplete`): `completed` once the app answers `/healthz` 200; a start-up forced to fail after the record is begun (the index directory removed from a copy of the image, so `FastembedIndex` readiness fails) leaves its row `failed`, never `completed` — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf13_deploy_record_status` (`-m deploy`) — evidence: both rows' `status` printed. (cases.md §8's `DeployRecord` comment omits `status`; as for AC-6, a missing field is `blocked-on AEA-32`.)
- [ ] AC-20 [failure/refusal] **WF-13 (restart sweep at start-up; OBS-32):** the start command on a data directory holding a `turns` row left `running` (written before the container starts) marks it status `failed`, outcome `degraded_handoff`, `degrade_reason` `timeout` before the first request is served (web.md *Start-up restart sweep*, AEA-40's `core.turns.fail_running()` hunk), so M-24 counts it as a failure, and logs one `turn_sweep` line holding ids and a count only — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf13_startup_sweeps_running_turns` (`-m deploy`) — evidence: the row before and after start-up; the `turn_sweep` line.
- [ ] AC-21 [negative] **WF-14 (ingestion; OBS-24, OBS-29):** in the image built from AC-4's temp context (sentinel `.env` and `.env.local` present), no sentinel value appears in any of the six `/app/index/` artefacts; and the ingest CLI re-run inside the index-stage image under `docker run --network none` (the embedding model already cached) completes with the same `manifest_hash` and chunk count as the built `index_record.json`, so ingestion sends nothing out — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf14_index_clean_and_offline` (`-m deploy`) — evidence: 0 sentinel hits per artefact; the offline run's hash and count equal the build's.
- [ ] AC-22 [negative] **WF-15 (reset script; OBS-24):** with sentinel model-key, eval-key and demo-password values in the script's environment, AC-10's run leaves none of them in the `reset_event` row, the `seed_event` row, stdout or any log line — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf15_reset_holds_no_values` — evidence: 0 sentinel hits per row and stream.
- [ ] AC-23 [negative] **WF-16 (first boot; OBS-21, OBS-24, OBS-29):** first boot on an empty data directory under `docker run --network none`, with sentinel model-key, eval-key and demo-password values in the environment and no Langfuse values, completes (every `schema/*.sql` applied, the four seeds loaded, one `seed_event`); every boot log line is one allow-listed JSON record (IDs, counts, statuses); no sentinel appears in a log line, the `seed_event` row or any text column of the new working copy — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf16_first_boot_offline_and_clean` (`-m deploy`) — evidence: the `seed_event` row; 0 lines outside the allow-list; 0 sentinel hits.
- [ ] AC-24 [capture] **WF-17 (check and deploy ids; OBS-10, OBS-11):** over AC-12's forced-failure run every `health_event` row (`check_failed`, `restart`) carries a non-empty `health_check_id`, distinct per probe, and the `deploy_id` of the `deploy_record` written by the process that ran the probe (DO-6 WF-17 row, *Correlation*) — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf17_health_events_carry_ids` (`-m deploy`) — evidence: the rows with both ids printed. (cases.md §8's `HealthEvent` lists neither field; a missing field is `blocked-on AEA-32`.)
- [ ] AC-25 [negative] **WF-17 (restart path; OBS-24, OBS-29):** AC-12's run repeated under `docker run --network none --restart on-failure` with sentinel model-key, eval-key and demo-password values in the environment: the probes (loopback), the exit and the restart still happen, and no sentinel appears in any `health_event` row or container log line — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf17_restart_offline_and_clean` (`-m deploy`) — evidence: restart count 1 under `--network none`; 0 sentinel hits.
- [ ] AC-26 [failure/refusal] **WF-17 (open turn across a restart; OBS-32):** a `turns` row left `running` in the data directory when AC-12's forced failure ends the process is status `failed`, outcome `degraded_handoff`, `degrade_reason` `timeout` after the restart, before the restarted process serves its first request — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf17_restart_sweeps_open_turn` (`-m deploy`) — evidence: the row before the failure and after the restart.
- [ ] AC-27 [capture] **WF-17 (project check after a restart; OBS-39):** with AC-8's stub Langfuse holding another project's id, the process restarted by AC-12's forced failure runs the project check again: export stays `off`, it calls `on_alert("wrong_project")`, the stored `trace_export_failed` alert state reads firing after the restart, and the stub receives 0 spans across both processes — verify: `tests/capture/test_cap9_runtime_ops.py::test_wf17_restart_rechecks_project` (`-m deploy`) — evidence: export state and alert state per process; span count 0.
- [ ] AC-28 [regression/context] Context updated in the same change: the area-map A12 row (planned → actual with the commit), the `.claude/state/icm-progress.md` row for deploy/scaffold, DO-3 §3's `Dockerfile · railway.json · scripts/` line marked built — verify: `git diff --name-only` — evidence: those files only, beside this issue's owned files.

### Observability

- Responsibilities: preserve and prove the runtime-operation records for **WF-13** (`deploy_record`: deploy ID, commit
  SHA, `agent_version`, config hash, trace export on/off; the wrong-project alert), **WF-14** (`manifest.json` with 17 file
  rows, `index_record.json`, `ingest_run.json`, DAT-12), **WF-15** (`reset_event` from the script), **WF-16**
  (`seed_event`), **WF-17** (`health_event` per failed check and per restart). Redaction: ops output carries IDs, counts and
  statuses only (DO-6 *Content and redaction*, log column).
- Capture evidence: AC-6 and AC-8 (WF-13), AC-9 (WF-14), AC-10 (WF-15), AC-11 (WF-16), AC-12 (WF-17), AC-15 (no values in
  ops output); AC-19 (WF-13 status), AC-24 and AC-27 (WF-17 ids, project re-check), AC-20 and AC-26 (restart sweep),
  AC-18, AC-21, AC-22, AC-23 and AC-25 (allow-listed output, no values, no outbound connection per workflow).

### Evaluation

- Checks: no new suite. WF-14 inherits **E-2** (retrieval): the index this image builds is the one E-2 scores, so AC-1 and
  AC-9 keep E-2 runnable on the deployed build (`eval/run_retrieval.py --index-dir`, DAT-26; SDQ-4 A: the same image runs
  on the VPS for Stage 9). WF-13 stamps `agent_version` so CON-20 can label a stale run (AC-6, AC-7); the image carries
  `eval/reports/` so `load_eval_reports` serves the latest run (DAT-14). M-7's hard gate (0 answers from excluded files) is
  protected at its root by AC-9.
- Expected-answer authority: PRD §4.3a knowledge map and the R-10 exclusions (DEC-4) decide which files are current and
  which are excluded (DO-5 *Expected-answer authority*, retrieval row).

### Metrics

- References: **M-28** (restarts: `health_event`), **M-29** (trace export completeness: `off` until the route is opened),
  **M-6** and **M-7** (the index and its exclusions), **M-26** (the spend ledger survives a reset); WF-16 inherits **M-3,
  M-13, M-27** (seed cases are a named segment that each reports with and without).
- Acceptance conditions: each stays computable from the records this issue proves: M-28 from AC-12's restart rows, M-29's
  `off` state from AC-6, M-7's population free of excluded passages per AC-9, M-26's ledger kept across a reset per AC-10;
  the with-and-without-seed split of M-3, M-13 and M-27 from AC-11's `seed_event` and `run_tag = 'seed'`. No target is set
  here.

### Blocked by

- AEA-16 (manifest and ingest CLI), AEA-19 (Langfuse project check), AEA-23 (`create_app()` lifespan, `/healthz`,
  `ResetGate`), AEA-31 (`ResetService`, `seed_demo`), AEA-32 (`deploy_record`, health events, `Watchdog`,
  `load_eval_reports`), AEA-33 (`FastembedIndex` readiness) — slice plan row AEA-50 (DAT-23: AEA-19 and AEA-23 are in the
  row). AEA-10 (`migrate.py` first-boot copy and `restore_working_copy`, which AC-5 and AC-11 prove; R-19 WF-16) and
  AEA-40 (the start-up restart sweep, AC-20 and AC-26; OBS-32) added at the coverage repair 2026-10-21: AEA-10 is wave 1
  and already upstream through AEA-31 and AEA-32; AEA-40 is wave 2; AEA-50 stays wave 3.

### Agent handoff

- Area / owner: A12 Deploy (DO-3 §8; area map). Owns `Dockerfile`, `.dockerignore`, `railway.json`, `scripts/`
  (`agent_version.py`, `reset.py`, image checks), `tests/deploy/`, `tests/capture/test_cap9_runtime_ops.py`, and its
  `tests/journeys/` evidence record.
- Contracts and shared surfaces: consumes the ingest CLI and index layout (data.md §3), `ResetService.reset` and
  `seed_demo` (cases.md §7), `restore_working_copy` and `Checkpointer.clearing` (cases.md §1.4), `ResetGate` (web.md §7),
  `AlertSettings`, `Watchdog`, `load_eval_reports` and the `deploy_record` writer (cases.md §8), the Langfuse project check
  (models.md §4), `Settings` (graph-core §12) and `create_app()`. Produces the image AEA-54 documents and AEA-56 deploys,
  and the Railway variable names AEA-09 sets (data.md §7: every §9 item 1 name plus `MERIDIAN_COOKIE_SECURE`,
  `MERIDIAN_TRUST_PROXY_HEADERS`, `MERIDIAN_REQUIRE_FRONTEND` (all `true`) and `MERIDIAN_WEB_DIST_DIR=/app/apps/web/dist`).
  **Must not edit** `web/container.py`, `web/app.py` or any `src/meridian/` module: a start-up record that is missing or
  wrong is a small follow-up on its owner (32, 31, 19, 16, 23), recorded as `blocked-on AEA-NN`. Contract note for AEA-32:
  cases.md §8's `DeployRecord` comment lists `deploy_id, at_wall, agent_version, commit, image digest` while saying "every
  field DO-6 *Records* lists"; DO-6 WF-13 also names config hash and trace export on/off. AC-6 asserts DO-6's list; if
  AEA-32's row lacks a field, that is `blocked-on AEA-32`.
- Join amendment applied: AEA-50-1 (AC-17; the *What to build* `web` line). The web stage reads
  `docs/ux/03-structure/ui-contracts.openapi.yaml` into the build context only (so `.dockerignore` must not exclude it);
  nothing under `apps/web/**` or `docs/ux/**` is edited.
- Scope boundary / refusal: no deploy, no Railway project changes, no variables set, no Langfuse route opened (AEA-09 and
  AEA-56 are Innocent's; the route is his yes, Q-062). No deployment guide (AEA-54). Tests that build or run the image are
  marked `deploy` and excluded from the default run; they run in this issue and before every deploy. Check `df -h /home`
  before building (89% full on 2026-10-21) and remove test images after.
- Awaiting Innocent: DAT-4 — built on the recommended option A (the route is opened later through Railway variables; the
  image is identical either way); if he picks B, the deployed `deploy_record` reads export `off` for the life of the app and
  `trace_export_failed` fires (MC-24); nothing in this issue changes.
- Awaiting Innocent: DAT-2 — built on the recommended option B (held-out keys outside the repo, so never in the build
  context); if he picks A, the keys sit under `eval/cases/heldout/` and the `.dockerignore` exclusion of `eval/cases/` that
  AC-4 asserts is what keeps them out of the image.
- Wave and gates: wave 3; no human gate on this issue (the deploy's gate is on AEA-56).
- Lane: `lane::build-loop` — it changes the build, the runtime configuration and tests (ticket-lanes: config and CI are
  code-read).
- Risk: **`risk::security`** — what a bug here could expose: the repo-root `.env` (Anthropic, OpenRouter and demo-login
  values), `var/sp1-runs/` or held-out keys copied into a public image layer; a secret passed as a build `ARG`/`ENV` visible
  in `docker history`; the issued DB or a working copy with case data baked into the image; a fault-injection switch left
  reachable in production; `/healthz` or ops output echoing configuration; traces exported to the wrong Langfuse project.
  Frozen failing tests first (`test-writer-agent` from AC-4, AC-5, AC-8, AC-12, AC-13, AC-15, AC-18, AC-21, AC-22,
  AC-23, AC-25), and `security-privacy-agent`
  reviews this diff at the wave-3 merge.
- Entry points added or changed: WF-13, WF-14, WF-15, WF-16, WF-17 (the image build, start command, reset script, first
  boot and the health/restart path).
