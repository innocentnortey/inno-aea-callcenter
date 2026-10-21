# Plan — [AEA-50] deploy: Dockerfile, Railway config, scripts

**Status:** planned (READY; ten criteria stay red until named siblings and follow-ups land, see §8 and §9)
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #50 (spec copy `docs/plans/tickets/AEA-50.md`) · **Base revision:** `0dedd59` (main)
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21. **Builders:** `test-writer-agent` (frozen tests first:
`risk::security`), then `fanout-implementer` (Sonnet). **Lane:** `lane::build-loop`, `risk::security`, wave 3.

Read this whole file before touching anything. Every name below is copied from the code on `main` at `0dedd59` or from
`docs/design/contracts/stage7/data.md` §3/§7, `cases.md` §1.3/§1.4/§7/§8, `models.md` §4, `web.md` §15. Where this
plan makes a decision the ticket left open, it is marked **[P-n]** and listed in §8 so the orchestrator can check it.

---

## 1. Goal and sources

**Goal (ticket *What to build*, verbatim in substance).** The deployable image and its Railway configuration, proven
locally, so AEA-56 (human) can deploy without editing anything: a three-stage `Dockerfile` (`web` → `index` →
`runtime`), the start command that exports `MERIDIAN_AGENT_VERSION` and runs one Uvicorn worker on `$PORT`,
`scripts/agent_version.py` (`compute_agent_version`), a `.dockerignore` that keeps every secret and run artefact out of
the build context, `railway.json`, `scripts/reset.py` (WF-15 operator path, stopped service only) and the CAP-9 capture
tests (`tests/capture/test_cap9_runtime_ops.py`) proving WF-13…WF-17 at their real entry points.

**Worked pair it protects: WP-1** (`docs/data/worked-pairs.md` §WP-1). The stale twin
`archive/comfort_club_overview.md` is excluded by the manifest (R-10); the image's index holds no passage from it.
Proven by AC-9 (`test_wf14_manifest_and_index_in_image`). Note: `$149` also appears in the *current*
`services/service_catalog.md`, and "prorated refund" in current files, so the check is on passage `file`/`passage_id`
and manifest rows, never a text grep.

**Sources read for this plan**

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-50.md` (AC-1…AC-28, *Seams*, *Agent handoff*) | Everything below; "Must not edit `web/container.py`, `web/app.py` or any `src/meridian/` module" |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-50 (wave 3; blockers 16, 31, 32, 33, 19, 23 — all merged), §3 collision map (`tests/capture/` one file per CAP; `pyproject.toml` is AEA-01's) | Owned files; CAP-9 file is ours |
| Deploy decision | `docs/design/contracts/stage7/data.md` §7 (railway.json values, stages, start command, `compute_agent_version`, reset script, Railway variables); §3 (ingest CLI, index layout, `manifest_hash`); §9 item 1 (env names), item 3 (`load_eval_reports` at start-up "beside the deploy_record write") | Exact values |
| Reset | `cases.md` §1.3 (restored / cleared / kept tables), §1.4 (`restore_working_copy(tx)`, `Checkpointer.clearing()`), §7 (`ResetService.reset(now, *, request_id, session_id, role)`; seed set MHC-C-0005…0008) | `scripts/reset.py`; AC-10 |
| Ops | `cases.md` §8 (`AlertSettings` probe 15 s × 3; `Watchdog`; `AlertWriter`; `load_eval_reports`; `DeployRecord`; consumers line "AEA-50 (deploy record; copies `eval/reports/` into the image)") | Start-up record; AC-6, AC-12, AC-19 |
| Tracing | `models.md` §4 MOD-6 (project check: `GET /api/public/projects`, one project id equal to `LANGFUSE_PROJECT_ID` → on; otherwise off + `on_alert("wrong_project")` once; missing values → `NullTraceSink`, no alert) | AC-8, AC-27 |
| App factory | `web.md` §15 ("The deployed start command runs uvicorn's factory with no arguments, so nothing is overridden"); §6–§7 (`/healthz` public; `ResetGate`) | `scripts/serve.py` calls `create_app()` with no arguments |
| Restart sweep | `web.md` *Start-up restart sweep* (AEA-40 hunk; `turn_sweep` count line) | AC-20, AC-26 (blocked-on AEA-40) |
| Code design | DO-3 `docs/design/code-design.md` §2.3 rules 3 and 7 (no sync SQLite on the loop; 65 s), §3 line 320 (`Dockerfile · railway.json · scripts/{agent_version,reset}.py`, A12), §8 | Module placement; AC-14; AC-28 |
| Observability | DO-6 `docs/design/observability-contract.md` WF-13…WF-17 rows (lines 88–92), *Status values* (`started`, `completed`, `failed`, `incomplete`), *Correlation* (`deploy_id` = Railway deployment ID; `health_check_id`), *Content and redaction* (logs: IDs only), CAP-9 (line 271) | Records and their fields |
| UX join | `docs/plans/ux-join/backend-amendments.md` AEA-50-1 (= AC-17); `audit-shell-reads-build.md` F2/F3/F4 | Web stage recipe; Node version |
| Sign-off | `docs/plans/stage7-signoff.md` (D-14: DAT-2 option B, DAT-4 option A as recommended; "`HealthEvent`/`DeployRecord` get the DO-6 fields"; "the deploy image copies the OpenAPI into the web stage") | No change needed; nothing here re-decides D-4…D-15 |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §4, `context-maintenance.md`, `gauntlet-hosting-default.md`; workspace `async-safety.md` rules 2–3, `code-design-solid-modularity.md` | Checks, evidence record, context rows |

---

## 2. Boundary

### 2.1 Owned files (the only files the test-writer and the implementer may create or edit)

| File | State | Who writes it | Change |
|---|---|---|---|
| `Dockerfile` | absent | implementer | create (§5 step I-2) |
| `.dockerignore` | absent | implementer | create (§5 step I-1) |
| `railway.json` | absent | implementer | create (§5 step I-3) |
| `scripts/__init__.py` | absent | implementer | create (one-line docstring) |
| `scripts/agent_version.py` | absent | implementer | create (§4.6, step I-4) |
| `scripts/serve.py` | absent | implementer | create **[P-1]** (§4.7, step I-6) |
| `scripts/reset.py` | absent | implementer | create (§4.8, step I-7) |
| `scripts/image_check.py` | absent | implementer | create (§4.9, step I-5) — the ticket's "image checks" |
| `scripts/log_config.json` | absent | implementer | create **[P-4]** (§4.10, step I-5) |
| `tests/deploy/__init__.py` | absent | test-writer (**frozen**) | create (empty) |
| `tests/deploy/conftest.py` | absent | test-writer (**frozen**) | create (§6.2) |
| `tests/deploy/support.py` | absent | test-writer (**frozen**) | create (§6.3) |
| `tests/deploy/fault_app.py` | absent | test-writer (**frozen**) | create (§6.4) — test-only, never in the image |
| `tests/deploy/langfuse_stub.py` | absent | test-writer (**frozen**) | create (§6.5) |
| `tests/deploy/test_agent_version.py` | absent | test-writer (**frozen**) | create (§6.6) |
| `tests/deploy/test_railway_config.py` | absent | test-writer (**frozen**) | create (§6.7) |
| `tests/deploy/test_image.py` | absent | test-writer (**frozen**) | create (§6.8) |
| `tests/capture/conftest.py` | absent | test-writer (**frozen**) | create **[P-5]** (§6.2) — new file in a shared folder, see §8 R-6 |
| `tests/capture/test_cap9_runtime_ops.py` | absent | test-writer (**frozen**) | create (§6.9) |
| `docs/testing/journeys/<run date>-AEA-50.md` | absent | implementer | create (step C-1; AC-16) |
| `.claude/reference/area-map.md` | exists | implementer | A12 row only (step C-2; AC-28) |
| `.claude/state/icm-progress.md` | exists | implementer | one new "Routes verified" row (step C-2; AC-28) |
| `docs/design/code-design.md` | exists | implementer | §3 line 320–321 only (step C-2; AC-28) |

The test-writer writes **every** test file and test helper in this table (all ACs, not only the eleven the ticket
lists), commits them as "frozen failing tests", and the implementer never edits them (file-level freeze, the same
convention AEA-19 and AEA-23 used). If a frozen test is wrong, the implementer stops and reports; it does not fix it.

### 2.2 Shared surfaces: read only (import, never edit)

`src/meridian/**` (all of it — ticket *Agent handoff*), in particular `web/app.py` (`create_app`), `web/container.py`
(`Container`, `Key`), `web/deps.py` (`UOW_FACTORY`, `WALL_CLOCK`), `web/middleware.py` (`HEALTHZ_PATH`), `web/logging.py`
(`AllowListFormatter`, `install_log_formatter`, `HANDLER_NAME`, `ALLOWED_FIELDS`), `config.py` (`Settings`,
`default_model_settings`, `SettingsError`, `ENV_NAMES`), `services/reset.py`, `services/reset_gate.py`,
`services/health.py`, `adapters/sqlite/{db,migrate,repos_ops}.py`, `adapters/checkpointer.py`,
`adapters/retrieval_fastembed.py`, `adapters/tracing_langfuse.py`, `retrieval/{ingest,settings,manifest}.py`.
Test helpers owned by others, imported read-only: `tests/fixtures/sqlite.py` (AEA-10), `tests/services/reset_support.py`
(AEA-31), `tests/services/ops_support.py` (AEA-32), `tests/journeys/affected.py` (AEA-01).
Read into the image only: `apps/web/**`, `docs/ux/03-structure/ui-contracts.openapi.yaml`,
`docs/data/issued/meridian_dataset/**`, `data/kb_transcriptions/**`, `eval/reports/**` (absent today).

### 2.3 Never touch

`pyproject.toml`, `uv.lock`, `tests/conftest.py` (AEA-01; editing them would also make the affected-journey command
select every journey and break AC-16); `web/container.py`, `web/app.py`, any `src/meridian/` file; `apps/web/**`,
`docs/ux/**`, `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`; the briefing, `docs/data/issued/**`, `docs/archive/`,
`docs/parked/`; `README.md`, `docs/deployment-guide.md` (AEA-54); `.gitignore`; any other ticket's test file;
`tests/journeys/**`. No Railway project, variable or deploy (AEA-09, AEA-56 are Innocent's). No Langfuse route.

---

## 3. Requirements table

Level column = the verification level the evidence record states (integrated-journeys §4). "Image" = the built image
run with its real start command on a mounted data directory; no model is called on any of these paths.
**F** = frozen test (the ticket's list: AC-4, 5, 8, 12, 13, 15, 18, 21, 22, 23, 25); all other tests are frozen too
(§2.1), the **F** column only mirrors the ticket. **B** = blocked marker (§6.3 `BLOCKED_*`), red until the named
dependency lands.

| AC | Requirement (ID-cited) | Implemented by | Verified by (test; `-m deploy` = docker) | F | B | Level |
|---|---|---|---|---|---|---|
| AC-1 | Clean-checkout build; `index` stage runs the ingest CLI; runtime holds `/app/index/` (6 files), `/app/eval/reports/`, `BUILD_SHA`, the issued dataset | `Dockerfile` stages `index`, `runtime` (§5 I-2) | `tests/deploy/test_image.py::test_index_built_in_image` (deploy) | | | image |
| AC-2 | `web` stage builds only when `apps/web/package.json` exists (DAT-21); dist present, no `node_modules`; without the file the build succeeds, no `dist` | `Dockerfile` stage `web` (`if [ -f package.json ]`) | `test_image.py::test_web_stage_conditional` (deploy) | | | image |
| AC-17 | Web stage = UX recipe (AEA-50-1): copies `apps/web/` + the one OpenAPI file; Node from `engines.node` or 24; `npm ci` with dev deps; `npm run build && npm run check:dist`, no `--mode`; only `dist/` reaches runtime | `Dockerfile` stage `web`, `ARG NODE_VERSION=24` **[P-6]** | `test_image.py::test_web_stage_recipe` (deploy) + `test_railway_config.py::test_dockerfile_static_rules` (default) | | | image |
| AC-3 | CAP-9 WF-13 readiness: `FastembedIndex` readiness passes and a knowledge search answers with **no network** | model cached at `/opt/fastembed`, `HF_HUB_OFFLINE=1`; `scripts/image_check.py` | `test_image.py::test_runs_without_network` (deploy, `--network none`) | | | image |
| AC-4 | No secret, run artefact or eval case in the image; sentinel `.env`, `.env.local`, `var/sp1-runs/ledger.jsonl`, `eval/cases/heldout/x.key.json`; `docker save` + `docker history --no-trunc` 0 hits; no secret-like `ARG`/`ENV`; `.dockerignore` lists `.env`, `.env.*`, `var/`, `.venv/`, `.git/`, `**/node_modules`, `eval/cases/` | `.dockerignore`; Dockerfile has no secret ARG/ENV | `test_image.py::test_no_secrets_in_image` (deploy) | F | | image |
| AC-5 | Issued data never written; working copy only in the data dir; issued SQLite SHA-256 identical before first boot, after first boot, after reset | `CMD` + `MERIDIAN_DATA_DIR=/data`; `scripts/reset.py` | `test_image.py::test_first_boot_writes_only_data_dir` (deploy) + plan-added `test_image.py::test_reset_leaves_issued_file_unchanged` (deploy) | F | reset leg: `BLOCKED_AEA_29_30` | image |
| AC-6 | WF-13: start command writes one `deploy_record` (non-empty `deploy_id`, commit SHA, `agent_version` `<12 hex>+<8 hex>` from the test's `BUILD_SHA`, config hash, trace export `off` with no Langfuse values) | `scripts/serve.py` `DeployStartup.begin` **[P-1]**; `scripts/agent_version.py` | `tests/capture/test_cap9_runtime_ops.py::test_wf13_startup_writes_deploy_record` (deploy) | | | image |
| AC-7 | `compute_agent_version` stable and sensitive (DAT-22); `RAILWAY_GIT_COMMIT_SHA` > `BUILD_SHA` > `"unknown"`; `-dirty` kept | `scripts/agent_version.py` | `tests/deploy/test_agent_version.py` (default) | | | mock-tested (pure functions) |
| AC-8 | MOD-6 against a stub Langfuse: right id → on; other id → off, `on_alert("wrong_project")` once, one `alert_fired` `trace_export_failed` row; missing value → `NullTraceSink`, no alert; **0 spans** to the stub when wrong | existing `register_tracing` (AEA-19) + `scripts/serve.py` | `test_cap9_runtime_ops.py::test_wf13_wrong_project_keys_turn_export_off` (default, in process) + plan-added `test_wf13_deploy_record_reads_export_state` (default) | F | plan-added test: `BLOCKED_AEA_19_FU` | integrated, in process (real app, real SQLite, loopback stub) |
| AC-9 | WF-14: built image's `manifest.json` 17 rows; non-current rows (incl. `archive/comfort_club_overview.md`, WP-1) `chunks` 0; no passage id under `archive/` or from `internal/agent_discretion_notes.md`; `ingest_run.json` matches `index_record.json` | `Dockerfile` `index` stage running AEA-16's CLI | `test_cap9_runtime_ops.py::test_wf14_manifest_and_index_in_image` (deploy) — **the WP-1 test** | | | image |
| AC-10 | WF-15: `scripts/reset.py` on a stopped dir with a live conversation, a case and spend rows writes one `reset_event` (both asked_by NULL, `checkpoints_cleared` 1) and one `seed_event` (reset_id set, 4, `demo seed`); issued tables equal the issued file; cleared tables empty apart from the 4 seeds; kept tables' counts unchanged | `scripts/reset.py` | `test_cap9_runtime_ops.py::test_wf15_reset_script` (default) | | `BLOCKED_AEA_29_30` | integrated, script entry point on a real SQLite copy |
| AC-11 | WF-16: first boot copies the issued DB, applies every `schema/*.sql`, loads the 4 seeds (`run_tag='seed'`), one `seed_event` with `deploy_id`, 4, `demo seed`; second start writes no second seed | existing `register_storage`/`register_reset`; `scripts/serve.py` sets `app.state.deploy_id` | `test_cap9_runtime_ops.py::test_wf16_first_boot_seed` (deploy) + plan-added `test_wf16_seed_event_carries_deploy_id` (deploy) | | `BLOCKED_AEA_29`; deploy_id test: `BLOCKED_AEA_31_FU` | image |
| AC-12 | WF-17: `/healthz` 200 without login; forced failure → `Watchdog` exits after 3 failed probes at 15 s; `--restart on-failure` brings it back (restart count 1); `check_failed` and `restart` rows; fault switch unreachable in deployed config | existing `register_ops` Watchdog; test-only `tests/deploy/fault_app.py` mounted at run time **[P-7]** | `test_cap9_runtime_ops.py::test_wf17_forced_failure_restarts` (deploy) | F | | image |
| AC-13 | `railway.json` exactly data.md §7; start command exports `MERIDIAN_AGENT_VERSION`, one worker on `0.0.0.0:$PORT`; no secret `ENV`; fault switch absent | `railway.json`, `Dockerfile` `CMD` | `tests/deploy/test_railway_config.py::test_railway_json_values` (default) + `::test_image_config_read_back` (deploy) | F | | image |
| AC-14 | No timeout below 65 s (DO-3 §2.3 rule 7); no hold-open endpoint; route list unchanged | `CMD` `--timeout-keep-alive 75` **[P-8]**; `serve.py` adds no route | `test_railway_config.py::test_no_timeout_below_65s` (default) | | | mock-tested (static + route list) |
| AC-15 | Reset script, agent-version script and image checks print IDs, counts, statuses only; sentinel name/phone/key/password in no stdout or log line | the three scripts' output formats (§4.6–§4.9) | `test_cap9_runtime_ops.py::test_ops_output_has_no_values` (default; parametrised) | F | `reset` param: `BLOCKED_AEA_29_30` | integrated, script entry points |
| AC-16 | [journey] No journey path imports `Dockerfile`, `railway.json` or `scripts/`; affected-journey command selects none, exits 0; evidence record states each CAP-9 claim's level and that the all-journeys pre-deploy run is AEA-56's | nothing to build; record file | `uv run python -m tests.journeys.affected --base main` → `0 journeys affected`; `docs/testing/journeys/<date>-AEA-50.md` | | | **no journey** (record level per claim, this column) |
| AC-18 | WF-13 start-up output: every container log line one allow-listed JSON record; sentinel model-key, eval-key, session-secret, demo-password in no log line and not in the `deploy_record` | `scripts/log_config.json` routes uvicorn and root through `AllowListFormatter`; `--no-access-log` | `test_cap9_runtime_ops.py::test_wf13_startup_logs_allow_listed` (deploy) | F | | image |
| AC-19 | `deploy_record.status` only DO-6 values: `completed` once `/healthz` answers 200; index removed from a copy of the image → readiness fails → row `failed`, never `completed` | `serve.py` `DeployStartup` (started → completed / failed / incomplete) | `test_cap9_runtime_ops.py::test_wf13_deploy_record_status` (deploy) | | | image |
| AC-20 | Start-up sweep: a `running` turn → `failed` / `degraded_handoff` / `timeout` before the first request; one `turn_sweep` line with ids and a count only | AEA-40's `register_chat` hunk (not built) | `test_cap9_runtime_ops.py::test_wf13_startup_sweeps_running_turns` (deploy) | | `BLOCKED_AEA_40` | image |
| AC-21 | WF-14: no sentinel in the six `/app/index/` artefacts; ingest re-run in the index-stage image under `--network none` gives the same `manifest_hash` and chunk count | `.dockerignore`; `FASTEMBED_CACHE_PATH=/opt/fastembed` in the image | `test_cap9_runtime_ops.py::test_wf14_index_clean_and_offline` (deploy) | F | | image |
| AC-22 | WF-15: sentinels in the reset script's env appear in neither event row, stdout nor any log line | `scripts/reset.py` output + `install_log_formatter()` | `test_cap9_runtime_ops.py::test_wf15_reset_holds_no_values` (default) | F | `BLOCKED_AEA_29_30` | integrated, script entry point |
| AC-23 | WF-16 first boot under `--network none` with sentinels, no Langfuse: completes (schemas, 4 seeds, one `seed_event`); every log line allow-listed JSON; no sentinel in logs, `seed_event` or any text column of the working copy | image + `log_config.json` | `test_cap9_runtime_ops.py::test_wf16_first_boot_offline_and_clean` (deploy) | F | `BLOCKED_AEA_29` | image |
| AC-24 | WF-17: every `health_event` (`check_failed`, `restart`) carries a distinct `health_check_id` and the process's `deploy_id` | AEA-10 DDL + AEA-32 follow-up (not built) | `test_cap9_runtime_ops.py::test_wf17_health_events_carry_ids` (deploy) | | `BLOCKED_AEA_32_FU` | image |
| AC-25 | AC-12 under `--network none --restart on-failure` with sentinels: probes, exit, restart still happen; no sentinel in any `health_event` row or log line | image | `test_cap9_runtime_ops.py::test_wf17_restart_offline_and_clean` (deploy) | F | | image |
| AC-26 | A `running` turn when the forced failure ends the process is swept after the restart, before the first request | AEA-40 (not built) | `test_cap9_runtime_ops.py::test_wf17_restart_sweeps_open_turn` (deploy) | | `BLOCKED_AEA_40` | image |
| AC-27 | Wrong-project stub + forced restart: the restarted process re-checks (stub sees 2 project checks), export off, stored `trace_export_failed` firing, 0 spans across both processes | existing `register_tracing` + `register_ops`; stub on an internal docker network | `test_cap9_runtime_ops.py::test_wf17_restart_rechecks_project` (deploy) + plan-added `test_wf17_restart_export_state_per_process` (deploy) | | plan-added test: `BLOCKED_AEA_19_FU` | image |
| AC-28 | Context rows in the same change (area map A12, ICM row, DO-3 §3 line) | step C-2 | `git diff --name-only main...HEAD` lists only §2.1 files | | | n/a |

**Source-contract reconciliation (obligations the ticket did not state):**

| Obligation | Source | Disposition | Where |
|---|---|---|---|
| The start-up `deploy_record` write and the `load_eval_reports` call | cases.md §8 consumers; data.md §9 item 3; AEA-32 plan §2.3 ("the start-up deploy-record write (AEA-50)"); ticket forbids `src/` edits | **added**: `scripts/serve.py` **[P-1]** | §4.7, I-6 |
| Index readiness failure stops the deploy ("readiness fails and the deploy does not go live") | DO-1 `system-design.md` line 408 | **added**: `DeployStartup.begin` raises `IndexNotReady` | §4.7 |
| `deploy_record.status` transitions | DO-6 *Status values*; `repos_ops.DeployRepo.set_status` (AEA-32 PA-1) | in-ticket AC-19 | §4.7 |
| `trace_export_on` in the deploy record needs a public export-state read on `LangfuseTraceSink` (only private `_state` exists) | DO-6 WF-13 | **blocked-on AEA-19 follow-up** (`export_on` property); `serve.py` writes NULL meanwhile, `False` for `NullTraceSink` | §8 R-2 |
| `seed_event.deploy_id` at first boot | DO-6 WF-16; `seed_first_boot(..., deploy_id=None)` from AEA-31's hunk | **blocked-on AEA-31 follow-up** (read `app.state.deploy_id`) | §8 R-3 |
| `health_check_id`, `deploy_id` on `health_events` | DO-6 WF-17 *Correlation*; sign-off "HealthEvent gets the DO-6 fields"; absent in `95_ops.sql` | **blocked-on AEA-10 + AEA-32 follow-up** | §8 R-4 |
| `turn_sweep` readable in the allow-listed logs | web.md *Start-up restart sweep*; AEA-40 plan R-5 | **blocked-on AEA-40** (+ its AEA-23 allow-list request) | §8 R-5 |
| Reset script needs the real `BriefAssembler` and `format_clock` | cases.md §7; AEA-31 plan line 1152 ("pass `format_clock=meridian.services.demo.format_clock`") | **blocked-on AEA-29, AEA-30** (wave 2, not merged at `0dedd59`) | §4.8 |
| Railway variables list | data.md §7 | other-ticket: AEA-09 sets, AEA-54 documents; image adds non-secret defaults (§4.2) | §8 R-10 |
| `BUILD_SHA` writer for the deploy step | data.md §7 ("written by the deploy step") | **added**: `python -m scripts.agent_version --write-build-sha` | §4.6 |

**Entry points (all registered in DO-6):** WF-13 (`CMD` → `scripts.serve:create_deployed_app`), WF-14 (`index` stage →
`python -m meridian.retrieval.ingest`), WF-15 (`python -m scripts.reset`), WF-16 (first boot inside `create_app`'s
lifespan), WF-17 (`/healthz` + `Watchdog` + Railway `ON_FAILURE`). Each inherits CAP-9; WF-14 inherits E-2.

---

## 4. Shared code to use (copied from `main` at `0dedd59`)

### 4.1 Imports and signatures

```python
# src/meridian/web/app.py (AEA-23)
def create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None) -> FastAPI
#   settings None → Settings.from_env(os.environ). Sets app.state.web_shell = WebShellState(settings=resolved, ...).
#   Its lifespan builds the container: app.state.container = build_container(app, resolved, overrides=overrides).
#   The lifespan is stored on app.router.lifespan_context (FastAPI 0.156.8 / Starlette 1.9.0; Starlette reads
#   `self.lifespan_context(app)` when the lifespan starts, so replacing the attribute before start-up works).

# src/meridian/web/container.py (AEA-01)
class Key[T]: name: str            # Key[Any]("trace") is the trace sink (AEA-19 register_tracing)
class Container: def get[T](self, key: Key[T]) -> T   # memoised; a plain dict read after build

# src/meridian/web/deps.py (AEA-23)
UOW_FACTORY: Key[UnitOfWorkFactory] = Key("uow_factory")
WALL_CLOCK: Key[Callable[[], datetime]] = Key("wall_clock")

# src/meridian/web/middleware.py
HEALTHZ_PATH  # "/healthz"

# src/meridian/web/logging.py (AEA-23)
HANDLER_NAME = "meridian-allow-list"; ROOT_LOGGER = "meridian"
class AllowListFormatter(logging.Formatter)   # non-allow-listed records → {"record":"log","logger","level","length"[,"exc_type"]}
ALLOWED_FIELDS: Mapping[str, frozenset[str]]   # keys today: "request", "auth_event", "stream_reconnect", "signal"
def install_log_formatter() -> None            # adds a handler to "meridian" only if none is named HANDLER_NAME

# src/meridian/config.py (AEA-02)
class Settings(MeridianModel):  # fields used here: agent_version: str = "dev"; data_dir: Path = Path("var");
    # index_dir: Path = Path("var/index"); issued_db_path: Path = Path("docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite");
    # cookie_secure, trust_proxy_headers, require_frontend: bool; models: ModelSettings = default_model_settings()
    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> Settings   # raises SettingsError (names only, never values)
    def role_model_map(self) -> Mapping[str, Any]              # plain JSON-safe, sorted, no secrets
    def langfuse_complete(self) -> bool
def default_model_settings() -> ModelSettings
class SettingsError(ValueError): problems: tuple[SafeError, ...]   # str(exc) names variables, codes, rules only
# Required env (no default): ANTHROPIC_API_KEY, OPENROUTER_API_KEY, MERIDIAN_DEMO_USERNAME, MERIDIAN_DEMO_PASSWORD,
# MERIDIAN_SESSION_SECRET. `models` has no env name (ENV_NAMES comment: "`models` and `issued_db_path` have none").

# src/meridian/adapters/sqlite/repos_ops.py (AEA-32)
RunStatus = Literal["started", "completed", "failed", "incomplete"]
class DeployRecord(MeridianModel):
    deploy_id: str; at_wall: datetime; agent_version: str
    git_commit: str | None = None; image_digest: str | None = None; config_hash: str | None = None
    trace_export_on: bool | None = None; status: RunStatus = "completed"
# tx.ops.deploy.insert(record: DeployRecord) -> None ; tx.ops.deploy.set_status(deploy_id: str, status: RunStatus) -> bool
# tx.ops.deploy.latest() -> DeployRecord | None ; tx.ops.health.latest_alert_states() -> dict[AlertType, AlertState]

# src/meridian/services/health.py (AEA-32)
def load_eval_reports(reports_dir: Path, uow: UnitOfWorkFactory, *, wall_clock: Callable[[], datetime] = _utc_now,
                      agent_version: str = "unknown") -> int        # returns 0 when reports_dir is not a directory
class Heartbeat: def fresh(self, mono: float) -> bool              # /healthz answers 503 {"status":"stale"} when False
# AlertSettings: probe_every_s=15, probe_timeout_s=5, failures_to_exit=3; Watchdog writes check_ok/check_failed rows,
# then kind="restart", reason_code=f"healthz_failed_{n}_in_a_row", then exit(1) via os._exit (register_ops)

# src/meridian/adapters/retrieval_fastembed.py (AEA-33)
class Readiness(MeridianModel): ok: bool; reasons: tuple[Literal["index_missing","dimension_mismatch","manifest_not_17","record_mismatch"], ...]
class FastembedIndex:
    def __init__(self, index_dir: Path, *, model_cache_dir: Path | None = None, embed_query: Callable[[str], np.ndarray] | None = None) -> None
    def readiness(self) -> Readiness            # never raises; does NOT load the embedding model
    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult   # loads fastembed lazily
# model_cache_dir None → fastembed's own default: $FASTEMBED_CACHE_PATH, else <tmp>/fastembed_cache (fastembed 0.9.0
# common/utils.py:81). HF_HUB_OFFLINE=1 makes fastembed use local files only (model_management.py:645).

# src/meridian/retrieval/settings.py: SEARCH_K = 3; MIN_SCORE = 0.60; EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
# src/meridian/retrieval/ingest.py (AEA-16)
def build_index(kb_dir: Path, out_dir: Path, *, transcriptions_dir: Path, embed: EmbedFn) -> IngestRun
# CLI: python -m meridian.retrieval.ingest --kb-dir PATH --transcriptions-dir PATH --out-dir PATH
#   last stdout line: "ingest_run_id=<id> status=completed files=17 chunks=<n> dimension=<d> manifest_hash=<h>"
# index_record.json keys: embedding_model, dimension, chunks, manifest_hash, files (+ every settings constant)
# passages.jsonl lines: Passage fields (passage_id "<file>#<n>", file, section, version_label, version_date, text) + embed_text

# src/meridian/adapters/tracing_langfuse.py (AEA-19)
class LangfuseTraceSink: ...                    # project check in start(); state private (_state); NO public export state
class NullTraceSink: ...

# src/meridian/services/reset.py (AEA-31)
class ResetService:
    def __init__(self, uow: UnitOfWorkFactory, gate: ResetGate,
                 restore_working_copy: Callable[[UnitOfWork], None],
                 clear_checkpoints: Callable[[], AbstractContextManager[None]],
                 seed_demo: Callable[[UnitOfWork], int], *,
                 format_clock: Callable[[datetime], tuple[str, str]]) -> None
    def reset(self, now: datetime, *, request_id: RequestId, session_id: LoginSessionId | None,
              role: DemoRole | None) -> ResetDone | ResetFailed   # raises ValueError for a naive `now`
class ResetDone: ok: Literal[True]; open_chats_ended: int; roles_reset: int; clock: ResetClock
class ResetFailed: code: Literal["RESET_FAILED"]
def seed_demo(tx: UnitOfWork, *, assembler: _BriefAssembler) -> int     # bind with functools.partial(seed_demo, assembler=...)
# src/meridian/services/reset_gate.py: class ResetGate: def __init__(self) -> None
# src/meridian/adapters/sqlite/migrate.py
WORKING_DB_NAME = "meridian.sqlite"; CLEARED_TABLES: tuple[str, ...]; KEPT_TABLES: tuple[str, ...]; ISSUED_TABLES
def migrate(db_path: Path, *, issued_path: Path) -> bool        # copies on first boot, applies every schema file
def restore_working_copy(tx: UnitOfWork, *, issued_path: Path) -> None   # bind issued_path with functools.partial
def schema_files() -> tuple[Path, ...]
# src/meridian/adapters/sqlite/db.py: class SqliteUnitOfWorkFactory: def __init__(self, db_path: Path, *, busy_timeout_ms: int = 5000)
# src/meridian/adapters/checkpointer.py: CHECKPOINTS_DB_NAME = "checkpoints.sqlite";
#   class Checkpointer: def __init__(self, path: Path, ...); def clearing(self) -> ContextManager[None]; def close(self) -> None
# src/meridian/domain/common.py: class RequestId(_PatternId)  — RequestId(str(uuid.uuid4())) is valid (tests do this)
```

Siblings not on `main` (called by name through `importlib`, never a static import, so mypy and the container keep
working before they land): `meridian.services.handoff.BriefAssembler` (AEA-29, constructor with no arguments, as
`register_reset` uses it), `meridian.services.demo.format_clock` (AEA-30, `Callable[[datetime], tuple[str, str]]`),
`meridian.services.turn` (AEA-40, presence only).

### 4.2 Image environment (non-secret; every name decided here or in data.md)

| Name | Value | Stage | Why |
|---|---|---|---|
| `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED` | `1` | base | no `.pyc` writes at run time; logs unbuffered |
| `UV_LINK_MODE` | `copy` | base | Docker layers cannot hardlink across mounts |
| `UV_COMPILE_BYTECODE` | `1` | base | compile at build, not at start |
| `UV_PYTHON_DOWNLOADS` | `never` | base | use the image's Python 3.12 (`requires-python ==3.12.*`) |
| `UV_PROJECT_ENVIRONMENT` | `/app/.venv` | base | fixed venv path |
| `FASTEMBED_CACHE_PATH` | `/opt/fastembed` | base | ingest (index stage) and `FastembedIndex` (runtime) share the cached model |
| `PATH` | `/app/.venv/bin:$PATH` | base | `python`, `uvicorn` are the venv's |
| `HF_HUB_OFFLINE` | `1` | runtime | AC-3: no download is ever attempted at run time |
| `MERIDIAN_DATA_DIR` | `/data` | runtime | data.md §9 item 1 (`/data` on Railway); a default, Railway may set it again |
| `MERIDIAN_INDEX_DIR` | `/app/index` | runtime | data.md §9 item 1 |
| `MERIDIAN_WEB_DIST_DIR` | `/app/apps/web/dist` | runtime | data.md §7 |
| `PORT` | `8080` | runtime | Railway overrides it; makes a local `docker run` work |

No `ARG` or `ENV` whose name matches `(?i)(KEY|SECRET|PASSWORD|PASSWD|TOKEN|CREDENTIAL)` (AC-4). `MERIDIAN_REQUIRE_FRONTEND`,
`MERIDIAN_COOKIE_SECURE`, `MERIDIAN_TRUST_PROXY_HEADERS` stay Railway variables (AEA-09), not image defaults.

### 4.3 `railway.json` (exact; data.md §7; no other keys)

```json
{
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile" },
  "deploy": {
    "healthcheckPath": "/healthz",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "numReplicas": 1
  }
}
```

### 4.4 `.dockerignore` (exact content, in this order; order matters, last match wins)

```
# AEA-50 (AC-4): local secrets, run artefacts and held-out eval material never enter the build context.
.env
.env.*
**/.env
**/.env.*
var/
.venv/
**/.venv
.git/
**/node_modules
**/__pycache__
**/*.pyc
.mypy_cache/
.pytest_cache/
.ruff_cache/
.claude/
tests/
# Eval: only committed reports reach the image (DAT-14); cases and held-out keys never do (DAT-2).
eval/cases/
eval/**
!eval/reports/
!eval/reports/**
# Frontend outputs and local tooling: the web stage rebuilds dist from source.
apps/web/dist/
apps/web/test-results/
apps/web/playwright-report/
apps/web/.tmp/
apps/web/*.tsbuildinfo
# Docs: only the issued dataset and the one OpenAPI file the web stage reads (AEA-50-1).
docs/**
!docs/data/issued/meridian_dataset/
!docs/data/issued/meridian_dataset/**
!docs/ux/03-structure/ui-contracts.openapi.yaml
```

Must stay in the context: `pyproject.toml`, `uv.lock`, `src/`, `scripts/`, `data/kb_transcriptions/`, `apps/web/`
(including `package-lock.json`, `scripts/`, `src/`, `tests/`, `tsconfig.json`, `vite.config.ts`), the two `docs/`
re-includes, `eval/reports/` (absent today), `BUILD_SHA` (written by the deploy step or the test).

### 4.5 `Dockerfile` (exact structure; the implementer types it as given)

```dockerfile
# Meridian image (AEA-50; docs/design/contracts/stage7/data.md section 7). Stages: web -> index -> runtime.
# No ARG or ENV holds a secret; secrets are Railway variables (gauntlet-hosting-default).
ARG NODE_VERSION=24
ARG PYTHON_VERSION=3.12

# --- web: apps/web's own build, only when apps/web/package.json exists (DAT-21, AEA-50-1). Reads apps/web and the
# one OpenAPI file; writes nothing back. Dev dependencies stay (tsc -b type-checks tests; prebuild regenerates types).
FROM node:${NODE_VERSION}-bookworm-slim AS web
WORKDIR /src/apps/web
COPY apps/web/ /src/apps/web/
COPY docs/ux/03-structure/ui-contracts.openapi.yaml /src/docs/ux/03-structure/ui-contracts.openapi.yaml
RUN mkdir -p /out \
 && if [ -f package.json ]; then \
      npm ci && npm run build && npm run check:dist && cp -a dist /out/dist; \
    else \
      echo "web stage: no apps/web/package.json, frontend build skipped"; \
    fi

# --- base: Python 3.12 and the locked dependencies (no dev group).
FROM python:${PYTHON_VERSION}-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.12.16 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    FASTEMBED_CACHE_PATH=/opt/fastembed \
    PATH=/app/.venv/bin:$PATH
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src/ ./src/
RUN uv sync --locked --no-dev

# --- index: WF-14. Builds /app/index with the ingest CLI (data.md section 3) and caches the embedding model.
FROM base AS index
COPY docs/data/issued/meridian_dataset/knowledge_base/ /build/knowledge_base/
COPY data/kb_transcriptions/ /build/kb_transcriptions/
RUN python -m meridian.retrieval.ingest \
      --kb-dir /build/knowledge_base \
      --transcriptions-dir /build/kb_transcriptions \
      --out-dir /app/index

# --- runtime: code, issued dataset (read-only), index, model cache, web dist when built, eval reports, BUILD_SHA.
FROM base AS runtime
ENV HF_HUB_OFFLINE=1 \
    MERIDIAN_DATA_DIR=/data \
    MERIDIAN_INDEX_DIR=/app/index \
    MERIDIAN_WEB_DIST_DIR=/app/apps/web/dist \
    PORT=8080
COPY docs/data/issued/meridian_dataset/ /app/docs/data/issued/meridian_dataset/
COPY --from=index /opt/fastembed /opt/fastembed
COPY --from=index /app/index /app/index
COPY --from=web /out/ /app/apps/web/
COPY scripts/ /app/scripts/
RUN --mount=type=bind,source=.,target=/ctx \
    mkdir -p /app/eval/reports /data \
 && if [ -d /ctx/eval/reports ]; then cp -a /ctx/eval/reports/. /app/eval/reports/; fi \
 && if [ -f /ctx/BUILD_SHA ]; then cp /ctx/BUILD_SHA /app/BUILD_SHA; fi \
 && chmod -R a-w /app/docs/data/issued
EXPOSE 8080
CMD ["sh", "-c", "MERIDIAN_AGENT_VERSION=\"$(python -m scripts.agent_version)\" && export MERIDIAN_AGENT_VERSION && exec uvicorn --factory scripts.serve:create_deployed_app --host 0.0.0.0 --port \"$PORT\" --workers 1 --log-config scripts/log_config.json --no-access-log --timeout-keep-alive 75"]
```

Notes the implementer must respect:
- No `USER` line: the process runs as root **[P-3]** (Railway volumes are root-owned; §8 R-7).
- No `# syntax=` line (Docker 29's built-in BuildKit frontend supports `RUN --mount`; avoids a frontend pull).
- If the `ghcr.io/astral-sh/uv:0.12.16` pull fails, replace that one line with
  `RUN pip install --no-cache-dir uv==0.12.16` (same version as the VPS) and say so in the report. Nothing else changes.
- If `uv sync` or the ingest step fails with a missing shared library (`libgomp.so.1` or similar) for onnxruntime, add
  `RUN apt-get update && apt-get install -y --no-install-recommends <that package> && rm -rf /var/lib/apt/lists/*` to the
  `base` stage right after `WORKDIR /app`, naming the package from the error, and say so in the report.
- The `CMD` assigns, then exports (`VAR="$(…)" && export VAR`): an assignment's exit status is the command
  substitution's, so a failing `agent_version` script stops the start instead of silently running as `"dev"`
  **[P-2]**. Everything else is data.md §7's line.

### 4.6 `scripts/agent_version.py` (DAT-22; data.md §7 signature unchanged)

```python
ROOT: Final = Path(__file__).resolve().parents[1]          # repo root locally; /app in the image
BUILD_SHA_FILE: Final = ROOT / "BUILD_SHA"
PROMPT_GLOBS: Final = ("src/meridian/agent/prompts/*.py", "src/meridian/policy/texts.py")

def prompt_files(root: Path = ROOT) -> tuple[Path, ...]      # sorted union of root.glob(each pattern)
def resolve_git_sha(environ: Mapping[str, str], build_sha_file: Path = BUILD_SHA_FILE) -> str
def compute_agent_version(git_sha: str, model_config: Mapping[str, Any], prompt_files: Iterable[Path]) -> str
def model_config() -> Mapping[str, Any]
def build_sha_from_git(repo: Path = ROOT) -> str
def main(argv: Sequence[str] | None = None) -> int
```

Algorithm (each step's invariant in brackets):
1. `resolve_git_sha`: `v = environ.get("RAILWAY_GIT_COMMIT_SHA", "").strip()`; if `v` → return `v`. Else if
   `build_sha_file.is_file()` and its stripped text is non-empty → return that text unchanged (a `-dirty` suffix is
   kept). Else return `"unknown"`. [Railway's SHA wins; the file is the `railway up` path; never raises on a missing file.]
2. `compute_agent_version`:
   a. `prompts = {_key(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in prompt_files}` where
      `_key(p)` = `p.resolve().relative_to(ROOT).as_posix()` when `p` is under `ROOT`, else `p.resolve().as_posix()`.
      [Same relative keys locally and in the image, so host and image agree.]
   b. `payload = {"models": dict(model_config), "prompts": dict(sorted(prompts.items()))}`.
   c. `canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
   d. `h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()`; return `f"{git_sha[:12]}+{h[:8]}"`.
      [Pure: same inputs → same value; any byte change in a prompt or the map changes `h[:8]` only.]
3. `model_config()`: `return Settings.model_construct(models=default_model_settings()).role_model_map()`.
   [`models` has no env name, so the default *is* the deployed map; `model_construct` needs no secret, so this script
   never reads a key value.] (**[P-9]**)
4. `build_sha_from_git(repo)`: `git -C <repo> rev-parse HEAD` (strip); dirty when
   `git -C <repo> status --porcelain --untracked-files=no` prints anything → append `"-dirty"`. Use
   `shutil.which("git")` for the absolute path; `subprocess.run([...], check=True, capture_output=True, text=True)`
   with `# noqa: S603 - fixed argv, no shell`. [Untracked files, including `BUILD_SHA` itself, never mark it dirty.]
5. `main(argv)`: `argparse` with one optional flag `--write-build-sha [PATH]` (`nargs="?"`, `const=str(BUILD_SHA_FILE)`).
   - Without the flag: print exactly one line, `compute_agent_version(resolve_git_sha(os.environ), model_config(),
     prompt_files())`; return 0.
   - With the flag: `sha = build_sha_from_git()`; write `sha + "\n"` to PATH; print `build_sha=<sha>`; return 0.
   - Any exception: print nothing to stdout, print `agent_version_error=<ExceptionClassName>` to stderr, return 1.
   `if __name__ == "__main__": raise SystemExit(main())`.

### 4.7 `scripts/serve.py` — the deployed factory **[P-1]**

```python
REPORTS_DIR: Final = ROOT / "eval" / "reports"     # ROOT from scripts.agent_version
COMPLETE_WITHIN_S: Final = 60.0                    # [A] /healthz must answer 200 within this, else status "incomplete"
POLL_EVERY_S: Final = 0.5                          # [A]
TRACE_KEY: Final = Key[Any]("trace")               # AEA-19's register_tracing key

class IndexNotReady(RuntimeError): ...             # message: "retrieval index not ready: " + ",".join(reasons)

@runtime_checkable
class _ExportStateReader(Protocol):                # AEA-19 follow-up adds `export_on` to LangfuseTraceSink (§8 R-2)
    @property
    def export_on(self) -> bool: ...

def trace_export_on(sink: object) -> bool | None   # NullTraceSink → False; _ExportStateReader → bool(sink.export_on); else None
def config_hash(settings: Settings, index_dir: Path) -> str
def deploy_id_from(environ: Mapping[str, str]) -> str     # RAILWAY_DEPLOYMENT_ID (stripped) or str(uuid.uuid4())

class DeployStartup:
    def __init__(self, container: Container, settings: Settings, deploy_id: str, environ: Mapping[str, str]) -> None
    def begin(self) -> None                                # sync; run in a worker thread
    def set_status(self, status: RunStatus) -> None        # sync; one short write unit of work
    async def complete_when_healthy(self, app: FastAPI) -> None

def create_deployed_app() -> FastAPI                       # uvicorn --factory target; takes no arguments
```

Algorithm:
1. `config_hash(settings, index_dir)`: read `index_dir / "index_record.json"` → `manifest_hash` (any `OSError`,
   `ValueError` or missing key → `None`). `payload = {"models": dict(settings.role_model_map()), "cookie_secure":
   settings.cookie_secure, "trust_proxy_headers": settings.trust_proxy_headers, "require_frontend":
   settings.require_frontend, "langfuse_configured": settings.langfuse_complete(), "index_manifest_hash": <hash or None>}`;
   return the full SHA-256 hex of the canonical JSON (same `json.dumps` arguments as §4.6 step 2c).
   [Only non-secret values and booleans enter; no `SecretStr` is ever unwrapped.]
2. `DeployStartup.begin()`:
   a. `uow = container.get(deps.UOW_FACTORY)`; `wall = container.get(deps.WALL_CLOCK)`; `sink = container.get(TRACE_KEY)`.
   b. Insert `DeployRecord(deploy_id=self.deploy_id, at_wall=wall(), agent_version=settings.agent_version,
      git_commit=resolve_git_sha(environ), image_digest=None, config_hash=config_hash(settings, Path(settings.index_dir)),
      trace_export_on=trace_export_on(sink), status="started")` in `with uow(write=True) as tx:` then `tx.commit()`.
      [The row exists before anything that can fail, so a failed start leaves `failed`, never nothing.]
   c. In `try:` — `readiness = FastembedIndex(Path(settings.index_dir)).readiness()`; if not `readiness.ok`:
      `raise IndexNotReady(...)`. Then `load_eval_reports(REPORTS_DIR, uow, wall_clock=wall,
      agent_version=settings.agent_version)`.
      `except BaseException:` → `self.set_status("failed")` (itself wrapped in `contextlib.suppress(Exception)`), then
      `raise`. [DO-1 §8.2: a missing index stops the deploy; status is never left `started` on a known failure.]
3. `set_status(status)`: `with uow(write=True) as tx: tx.ops.deploy.set_status(self.deploy_id, status); tx.commit()`.
4. `complete_when_healthy(app)`: `loop = asyncio.get_running_loop()`; `deadline = loop.time() + COMPLETE_WITHIN_S`;
   `async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://deploy.local") as client:`
   loop while `loop.time() < deadline`: `GET HEALTHZ_PATH` (catch `httpx.HTTPError` → treat as not ready); on status 200
   → `await asyncio.to_thread(self.set_status, "completed")`; `return`. Else `await asyncio.sleep(POLL_EVERY_S)`.
   After the loop: `await asyncio.to_thread(self.set_status, "incomplete")`.
   [No sync SQLite on the event loop (DO-3 §2.3 rule 3); the probe goes through the real middleware, unsigned.]
5. `create_deployed_app()`:
   a. `logging.captureWarnings(True)` (Python warnings become `py.warnings` log records → allow-listed JSON).
   b. `app = create_app()` — **no arguments** (web.md §15: nothing is overridden; it builds `Settings.from_env`).
   c. `settings = app.state.web_shell.settings`; `deploy_id = deploy_id_from(os.environ)`;
      `app.state.deploy_id = deploy_id` (read by the R-3/R-4 follow-ups; nothing reads it today).
   d. `inner = app.router.lifespan_context`; define

      ```python
      @asynccontextmanager
      async def lifespan(a: FastAPI) -> AsyncIterator[None]:
          async with inner(a):                      # builds the container: migrate, first-boot seed, trace check, watchdog
              startup = DeployStartup(a.state.container, settings, deploy_id, os.environ)
              await asyncio.to_thread(startup.begin)   # raises IndexNotReady → uvicorn start-up fails → exit code 3
              task = asyncio.create_task(startup.complete_when_healthy(a), name="meridian-deploy-complete")
              try:
                  yield
              finally:
                  task.cancel()
                  with contextlib.suppress(asyncio.CancelledError):
                      await task
      app.router.lifespan_context = lifespan
      ```
      [The task's closer is named (async-safety rule 2); `inner`'s own `finally` closes the container on every path.]
   e. `return app`. No route is added (AC-14).

### 4.8 `scripts/reset.py` (WF-15, stopped service only)

`def main(argv: Sequence[str] | None = None) -> int`; module guard `raise SystemExit(main())`. Steps:
1. `install_log_formatter()` (from `meridian.web.logging`) — every log line it causes is allow-listed JSON.
2. `settings = Settings.from_env(os.environ)`; on `SettingsError as exc`: print
   `reset status=refused reason=settings variables=<comma list of p.field for p in exc.problems>` to stdout, return 2.
   [Names only; never `str(exc)`'s inputs — `SettingsError` already holds no values, but print only the fields.]
3. `data_dir = Path(settings.data_dir)`; `db_path = data_dir / WORKING_DB_NAME`; if not `db_path.exists()`: print
   `reset status=refused reason=no_working_copy`, return 2. [The operator path never performs a first boot.]
4. `migrate(db_path, issued_path=Path(settings.issued_db_path))` — DDL only here (the copy branch cannot run, step 3).
5. Resolve siblings: `handoff = importlib.import_module("meridian.services.handoff")`,
   `demo = importlib.import_module("meridian.services.demo")`; on `ImportError`: print
   `reset status=refused reason=missing_module`, return 3.
6. `checkpointer = Checkpointer(data_dir / CHECKPOINTS_DB_NAME)`; in `try/finally` (`checkpointer.close()`):
   `service = ResetService(SqliteUnitOfWorkFactory(db_path), ResetGate(),
   functools.partial(restore_working_copy, issued_path=Path(settings.issued_db_path)), checkpointer.clearing,
   functools.partial(seed_demo, assembler=handoff.BriefAssembler()), format_clock=demo.format_clock)`;
   `request_id = RequestId(str(uuid.uuid4()))`;
   `result = service.reset(datetime.now(UTC), request_id=request_id, session_id=None, role=None)`.
7. `ResetDone` → print `reset status=done request_id=<id> open_chats_ended=<n> roles_reset=<n>`, return 0.
   `ResetFailed` → print `reset status=failed request_id=<id> code=RESET_FAILED`, return 1.
Output: exactly one stdout line per run. Never print a row, a name, a phone, a message or a setting value.

### 4.9 `scripts/image_check.py`

`def main(argv: Sequence[str] | None = None) -> int`. Args: `--index-dir PATH` (default
`Path(os.environ.get("MERIDIAN_INDEX_DIR", "/app/index"))`), optional `--search QUERY`.
1. `index = FastembedIndex(index_dir)`; `r = index.readiness()`; print
   `readiness ok=<true|false> reasons=<comma list or ->`. If not ok → return 1.
2. With `--search`: `res = index.search(query, k=SEARCH_K, min_score=MIN_SCORE)`; print
   `search status=ok passages=<len(res.passages)> below_floor=<true|false> files=<comma list of p.file or ->`; any
   exception → print `search status=error error=<ExceptionClassName>`, return 1.
3. Return 0. [KB file paths are document ids, not customer data; the query and passage text are never printed.]

### 4.10 `scripts/log_config.json` (uvicorn `--log-config`; exact) **[P-4]**

```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": { "allow_list": { "()": "meridian.web.logging.AllowListFormatter" } },
  "handlers": {
    "meridian-allow-list": { "class": "logging.StreamHandler", "formatter": "allow_list", "stream": "ext://sys.stderr" }
  },
  "loggers": {
    "uvicorn": { "handlers": ["meridian-allow-list"], "level": "INFO", "propagate": false },
    "uvicorn.error": { "level": "INFO", "propagate": true },
    "uvicorn.access": { "level": "WARNING", "propagate": false },
    "meridian": { "handlers": ["meridian-allow-list"], "level": "INFO", "propagate": false }
  },
  "root": { "handlers": ["meridian-allow-list"], "level": "WARNING" }
}
```

Why the handler key is `meridian-allow-list`: `dictConfig` sets `handler.name` to its key, and
`install_log_formatter()` adds no second handler when one with `HANDLER_NAME` exists (no duplicate lines).

---

## 5. Steps

Every shell: `cd <worktree>`; `export UV_LINK_MODE=hardlink`; `uv sync` once (never copy a venv; no `node_modules`
in the worktree — the web stage runs `npm ci` *inside* Docker). `df -h /home` before any image build (stop if under
4 GB free). Never `git add -A`; add the paths listed. Last line of every commit message:
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

### Phase T — test-writer (frozen failing tests, `risk::security`)

T-1. Create every file marked test-writer in §2.1, exactly as §6 specifies.
T-2. Red for the right reason: `uv run pytest -q tests/deploy tests/capture/test_cap9_runtime_ops.py` → collection
     succeeds; default-run tests fail with `ModuleNotFoundError: scripts.agent_version` / `scripts.serve` /
     `FileNotFoundError` for `railway.json`, `Dockerfile`; deploy tests are skipped (no `-m deploy`).
     `uv run pytest --collect-only -q tests/capture tests/deploy` exits 0.
T-3. `uv run ruff check tests/deploy tests/capture/conftest.py tests/capture/test_cap9_runtime_ops.py` and
     `uv run ruff format --check` on the same paths pass. Type check `uv run mypy src/meridian` only: the tests import
     `scripts.*`, which does not exist until Phase I, so the full `uv run mypy` is the implementer's gate (§7 check 3).
     Never add `# type: ignore` for a missing `scripts` module.
T-4. Commit: `test(deploy): frozen failing tests for AEA-50 image, Railway config and CAP-9` listing the files.

### Phase I — implementer (production files only; never edit a Phase T file)

I-1. `.dockerignore` exactly §4.4. Check: `uv run pytest -q tests/deploy/test_railway_config.py -k dockerignore`.
I-2. `Dockerfile` exactly §4.5. Check: `uv run pytest -q tests/deploy/test_railway_config.py -k "dockerfile"`.
I-3. `railway.json` exactly §4.3. Check: `uv run pytest -q tests/deploy/test_railway_config.py`.
I-4. `scripts/__init__.py` (docstring `"""Deploy and operator scripts (AEA-50; A12). Not part of the meridian package."""`)
     and `scripts/agent_version.py` per §4.6. Check: `uv run pytest -q tests/deploy/test_agent_version.py`;
     `uv run python -m scripts.agent_version` prints one `<12>+<8>` line (or `unknown+<8>` without BUILD_SHA).
I-5. `scripts/log_config.json` (§4.10) and `scripts/image_check.py` (§4.9). Check:
     `uv run pytest -q tests/capture/test_cap9_runtime_ops.py -k "ops_output"`.
I-6. `scripts/serve.py` per §4.7. Check: `uv run pytest -q tests/capture/test_cap9_runtime_ops.py -k "wf13"` and
     `tests/deploy/test_railway_config.py::test_no_timeout_below_65s`.
I-7. `scripts/reset.py` per §4.8. Check: `uv run pytest -q tests/capture/test_cap9_runtime_ops.py -k "wf15"` (xfail
     while AEA-29/30 are absent; must turn green, i.e. XPASS-strict-fail → report, once they land: see §8 R-13).
I-8. Image: `uv run pytest -q -m deploy tests/deploy tests/capture/test_cap9_runtime_ops.py` (serial; no `-n`; first
     run builds the images, ~10–20 min). Fix production files until every non-blocked test passes and every blocked
     one reports `xfail`.
I-9. Fast gates and affected tests (§7, in order). Commit:
     `feat(deploy): image, Railway config, deploy start-up record and operator scripts (AEA-50)`.

### Phase C — context and evidence (same branch, after Phase I is green)

C-1. Write `docs/testing/journeys/<run date>-AEA-50.md` with the integrated-journeys §4 table:
     Claim (AEA-50 CAP-9 WF-13…WF-17, AC-1…AC-27); Level (per claim, from §3's Level column; "no journey: 0 affected");
     Tested revision (commit SHA + the `agent_version` the image printed); Environment (VPS, Docker 29.8.1, image tags,
     `--network none` / internal network, data dirs under `tempfile`, no model adapter, no model call); Command (the
     §7 commands); Result (pass / xfail per test, with the blocked-on reason quoted); Evidence location (this file +
     the report); Remaining limitations (Railway itself not exercised; image digest not recorded; the ten blocked
     criteria and their blockers); Blocked by (AEA-29, AEA-30, AEA-40, and the R-2…R-5 follow-ups; "the all-journeys
     pre-deploy run and the full suite are AEA-56's").
C-2. AC-28 rows (each changes only its own text):
     - `.claude/reference/area-map.md` A12 row: paths become `` `Dockerfile`, `.dockerignore`, `railway.json`,
       `scripts/{agent_version,serve,reset,image_check}.py`, `scripts/log_config.json` `` and status
       `actual (AEA-50, <sha>)`.
     - `.claude/state/icm-progress.md`: add one row "Routes verified against code and tests | provisional |
       2026-10-21: area map A12 → Dockerfile, railway.json, scripts/ checked by tests/deploy/, tests/capture/test_cap9_runtime_ops.py
       (AEA-50, `<sha>`; <n> passed, <m> xfail blocked) | Deployed level at AEA-56" (≤400 characters).
     - `docs/design/code-design.md` lines 320–321: replace with
       `Dockerfile · .dockerignore · railway.json · scripts/{agent_version,serve,reset,image_check}.py · scripts/log_config.json`
       `   image build (index built here), deploy start-up record, agent version stamp, reset command   A12  2` and the
       second line `(built AEA-50, <sha>; stage7/data.md §7, DAT-22; scripts/ is top level, not under src/meridian/)`.
C-3. `uv run python -m tests.journeys.affected --base main` → paste output into the record. Commit
     `docs(AEA-50): journey record and context rows` with only those four files.

### What the implementer must NOT do

- Edit any test file, `tests/capture/conftest.py`, `tests/deploy/*` (frozen), `pyproject.toml`, `uv.lock`,
  `tests/conftest.py`, any `src/meridian/` file, `web/container.py`, `web/app.py`, `apps/web/**`, `docs/ux/**`.
- Read, print, copy or mount the repo-root `.env` or `/home/linuxuser/workspaces/.env`; pass a real key to any
  container or subprocess; add a secret-named `ARG`/`ENV`; add a `USER`, `VOLUME` or `HEALTHCHECK` line not in §4.5.
- Add a route, an env switch, a file switch or any code path in `scripts/` that forces `/healthz` to fail (the only
  fault switch is the mounted test module, AC-13).
- Pass arguments to `create_app()` inside `serve.py`, or construct `ContainerOverrides`.
- Bind a host port (no `-p`), use ports 4019 or 5184, run pytest with more than `-n 2` (deploy tests: no `-n`), push,
  deploy, touch Railway, open a Langfuse route.
- Make a paid model call (nothing here calls a model).
- Leave test images behind: the session teardown removes them; check `docker images | grep aea50` is empty after.

---

## 6. Data and fixtures (synthetic only)

### 6.1 Values

- **Sentinels** (generated per test session, never literals): `support.sentinel(kind)` returns
  `f"aea50-{kind}-{secrets.token_hex(12)}"` for `kind` in `model-key`, `openrouter-key`, `eval-key`,
  `session-secret`, `demo-user`, `demo-password`, `langfuse-pk`, `langfuse-sk`, `name`, `phone`, `env-file`,
  `env-local`, `ledger`, `heldout`. Phone and name sentinels contain no digit run (token_hex is hex, prefixed with
  letters) so nothing phone- or card-like is ever written. No real phone, card, code or key appears in any test.
- **BUILD_SHA** in test contexts: `secrets.token_hex(20)` (40 hex) written to `<ctx>/BUILD_SHA`.
- **Project ids** for the Langfuse stub: `"proj-aea50"` (ours) and `"proj-other"`.
- **Data** comes only from the issued dataset (through the image / `migrate`) and AEA-31's `make_dirty_demo`
  (synthetic, `tests/services/reset_support.py`), with its `customer_message` set to
  `f"My name is {name}, call me on {phone}"` (sentinels).
- **Process env for host subprocesses** is built from scratch: `{"PATH": os.environ["PATH"], "HOME": str(tmp),
  "LANG": "C.UTF-8", **sentinel settings, "MERIDIAN_DATA_DIR": ...}` — never `os.environ` copied (the shell may have
  sourced the workspace `.env`). Docker runs get the same mapping through `--env-file <tmp file, mode 0600>`.

### 6.2 `tests/deploy/conftest.py` and `tests/capture/conftest.py` (identical bodies)

```python
from tests.deploy.support import configure_deploy_marker, skip_deploy_unless_selected, cleanup_session
def pytest_configure(config: pytest.Config) -> None: configure_deploy_marker(config)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    skip_deploy_unless_selected(config, items)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None: cleanup_session()
```
`configure_deploy_marker` adds `"deploy: builds or runs the Docker image (AEA-50); excluded unless -m selects it; runs
before every deploy"` with `config.addinivalue_line("markers", ...)`. `skip_deploy_unless_selected`: selected when
`re.search(r"(?<!not )\bdeploy\b", config.getoption("markexpr") or "")`; when not selected, add
`pytest.mark.skip(reason="deploy test: run with -m deploy")` to every item with `get_closest_marker("deploy")`; when
selected and `shutil.which("docker") is None` → `raise pytest.UsageError("deploy tests need docker")`; when selected
and `shutil.disk_usage("/").free < 4 * 2**30` → `raise pytest.UsageError("deploy tests need 4 GB free disk")`. Both
functions are idempotent (two conftests may call them in one session).

### 6.3 `tests/deploy/support.py` (frozen; exact public API)

```python
ROOT: Path                          # repo root (parents[2] of this file)
IMAGE, IMAGE_NOWEB, IMAGE_INDEX, IMAGE_WEB, IMAGE_NOINDEX = (
    "meridian:aea50-test", "meridian:aea50-noweb", "meridian:aea50-index", "meridian:aea50-web", "meridian:aea50-noindex")
ISSUED_IN_IMAGE = "/app/docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
SECRET_NAME = re.compile(r"(?i)(KEY|SECRET|PASSWORD|PASSWD|TOKEN|CREDENTIAL)")

def sentinel(kind: str) -> str
def session_sentinels() -> dict[str, str]                 # memoised per session; the kinds of §6.1
def module_present(name: str) -> bool                     # importlib.util.find_spec, False on ModuleNotFoundError
BLOCKED_AEA_29: pytest.MarkDecorator     # xfail(not module_present("meridian.services.handoff"), strict=True,
                                         #   reason="blocked-on AEA-29: BriefAssembler (meridian.services.handoff) not merged")
BLOCKED_AEA_29_30: pytest.MarkDecorator  # xfail(not (handoff and meridian.services.demo present), strict=True, reason=...)
BLOCKED_AEA_40: pytest.MarkDecorator     # xfail(not (module_present("meridian.services.turn") and "turn_sweep" in ALLOWED_FIELDS),
                                         #   strict=True, reason="blocked-on AEA-40 (+ AEA-23 allow-list): start-up restart sweep")
BLOCKED_AEA_19_FU: pytest.MarkDecorator  # xfail(not hasattr(LangfuseTraceSink, "export_on"), strict=True,
                                         #   reason="blocked-on AEA-19 follow-up: LangfuseTraceSink.export_on")
BLOCKED_AEA_32_FU: pytest.MarkDecorator  # xfail("health_check_id" not in HealthEvent.model_fields, strict=True,
                                         #   reason="blocked-on AEA-10 + AEA-32 follow-up: health_check_id and deploy_id on health_events")
BLOCKED_AEA_31_FU: pytest.MarkDecorator  # xfail(True, strict=True, reason="blocked-on AEA-31 follow-up: first-boot seed_event.deploy_id")

def sentinel_env(*, langfuse: Mapping[str, str] | None = None) -> dict[str, str]
    # ANTHROPIC_API_KEY, OPENROUTER_API_KEY, MERIDIAN_DEMO_USERNAME, MERIDIAN_DEMO_PASSWORD, MERIDIAN_SESSION_SECRET,
    # MERIDIAN_EVAL_KEY = sentinels; PORT=8080; plus `langfuse` items when given. Never reads os.environ.
def host_env(data_dir: Path, *, index_dir: Path | None = None, langfuse: Mapping[str, str] | None = None) -> dict[str, str]
def make_context(dst: Path, *, with_sentinels: bool, drop: Sequence[str] = ()) -> Path
    # copies every path from `git -C ROOT ls-files -co --exclude-standard` (tracked + untracked-not-ignored; this is the
    # working tree a clean checkout would hold) into dst, skipping `drop` paths; writes BUILD_SHA (40 hex); with
    # sentinels writes .env, .env.local, var/sp1-runs/ledger.jsonl, eval/cases/heldout/x.key.json holding them.
def build_sha_value() -> str                               # the BUILD_SHA written into every test context (memoised)
def docker(*args: str, timeout: float = 600, check: bool = True, input: str | None = None) -> subprocess.CompletedProcess[str]
def build(tag: str, ctx: Path, *extra: str, timeout: float = 1800) -> str      # `docker build --progress=plain --label aea50.test=1 -t tag *extra ctx`; returns combined log
def built_images() -> ImageSet       # memoised: builds IMAGE from a sentinel context (log kept), IMAGE_NOWEB from a
                                     # context with apps/web/package.json dropped, IMAGE_INDEX (--target index),
                                     # IMAGE_NOINDEX (`FROM meridian:aea50-test` + `RUN rm -rf /app/index`, built from stdin)
@dataclass(frozen=True)
class ImageSet: main_log: str; noweb_log: str; context: Path
def image_cmd(image: str) -> list[str]                     # docker inspect .Config.Cmd
def image_env(image: str) -> dict[str, str]                # docker inspect .Config.Env
def run_in_image(image: str, *cmd: str, network: str = "none", env: Mapping[str, str] | None = None,
                 volumes: Mapping[Path, str] | None = None) -> subprocess.CompletedProcess[str]   # docker run --rm
def new_data_dir() -> Path                                 # tempfile.mkdtemp(prefix="aea50-data-"), registered for cleanup
@dataclass
class Running: name: str; data_dir: Path
    def logs(self) -> list[str]                            # docker logs (stdout+stderr), non-empty lines
    def exec(self, *cmd: str) -> subprocess.CompletedProcess[str]
    def restart_count(self) -> int                         # docker inspect .RestartCount
    def stop(self) -> None
def start(image: str = IMAGE, *, data_dir: Path, network: str = "none", restart: str = "no",
          env: Mapping[str, str], fault_once: bool = False, extra_volumes: Mapping[Path, str] | None = None) -> Running
    # docker run -d --name aea50-<hex> --network <network> --restart <restart> --env-file <0600 file> -v <data_dir>:/data
    # never `-p`. fault_once=True: creates <data_dir>/aea50-fault-once, mounts tests/deploy/fault_app.py read-only at
    # /fault/aea50_fault_app.py, sets PYTHONPATH=/fault and AEA50_FAULT_ONCE_FILE=/data/aea50-fault-once, and passes the
    # image's own Cmd with "scripts.serve:create_deployed_app" replaced by "aea50_fault_app:create_faulty_app"
    # (assert exactly one replacement), so the start command is otherwise byte-identical.
def db_rows(data_dir: Path, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]   # read-only sqlite3 (mode=ro)
def wait_for(predicate: Callable[[], bool], *, timeout: float, every: float = 1.0, what: str) -> None  # fails with `what`
def wait_deploy_status(data_dir: Path, status: str, *, count: int = 1, timeout: float = 120) -> None
def json_lines(lines: Sequence[str]) -> list[dict[str, Any]]   # each line must parse to a dict, else AssertionError naming the line number only
ALLOWED_LOG_KEYS: Mapping[str, frozenset[str]]  # ALLOWED_FIELDS ∪ {"log": {"record","logger","level","length","exc_type"}}
def scan_saved_image(image: str, needles: Sequence[str]) -> list[str]
    # docker save -o <tmp>.tar; walk the outer tar; for each member stream the bytes, gunzip when it starts with 1f 8b,
    # fail the test on zstd magic 28 b5 2f fd ("unsupported layer compression"), scan in 1 MiB chunks with
    # (max needle length − 1) overlap; returns "member: needle-kind" strings (never the needle value)
def build_stand_in_index(out_dir: Path) -> Path
    # meridian.retrieval.ingest.build_index(ROOT/"docs/data/issued/meridian_dataset/knowledge_base", out_dir,
    #   transcriptions_dir=ROOT/"data/kb_transcriptions", embed=stand_in_embed) — no model download
def stand_in_embed(texts: Sequence[str]) -> np.ndarray     # sha256 of each text → 8 floats + 1.0 (AEA-16's test pattern)
def release_dir(path: Path) -> None   # docker run --rm -v path:/d IMAGE chown -R <uid>:<gid> /d, then shutil.rmtree
def cleanup_session() -> None         # idempotent: docker rm -f every started container, docker network rm every
                                      # created network, docker image rm -f the five tags, release_dir every data dir
```
Every helper that runs docker passes `timeout=` and asserts the return code with a message holding the command name
and exit code only (never stdout that might hold a value).

### 6.4 `tests/deploy/fault_app.py` (test-only; mounted, never in the image)

```python
"""Test-only (AEA-50 AC-12): the first process started with AEA50_FAULT_ONCE_FILE present answers /healthz 503."""
def create_faulty_app() -> FastAPI:
    once = Path(os.environ["AEA50_FAULT_ONCE_FILE"])
    if once.exists():
        once.unlink()
        Heartbeat.fresh = _never_fresh   # type: ignore[method-assign]   (meridian.services.health.Heartbeat)
    return create_deployed_app()         # from scripts.serve
def _never_fresh(self: Heartbeat, mono: float) -> bool: return False
```
The real `/healthz` handler then answers 503 `stale`; the real `Watchdog` probes it, writes three `check_failed`
rows and a `restart` row, and exits(1). The restarted process finds no once-file and is healthy.

### 6.5 `tests/deploy/langfuse_stub.py`

A `ThreadingHTTPServer` with `--host` (default `127.0.0.1`), `--port` (default 0), `--project-id`, `--counts PATH`.
`GET /api/public/projects` → 200 `{"data": [{"id": <project-id>, "name": "stub"}]}` and `project_checks += 1`.
`POST` to a path containing `/otel/` or `/ingestion` → 200 `{}` and `spans += 1`. Anything else → 404 and
`other += 1`. After each request it writes `{"project_checks", "spans", "other"}` to `--counts` (atomic replace).
Also `start_stub(project_id: str, counts: Path) -> StubHandle` (in-process thread on 127.0.0.1:0, `.base_url`,
`.counts() -> dict[str, int]`, `.close()`). The container use passes `--host 0.0.0.0 --port 8000` on the command line
(no `0.0.0.0` literal in code: ruff S104).

### 6.6 `tests/deploy/test_agent_version.py` (default run; AC-7)

- `test_same_inputs_same_value`: two calls with identical sha, map, files → equal; matches `^[0-9a-f]{12}\+[0-9a-f]{8}$`.
- `test_prompt_byte_changes_suffix_only`: tmp prompt files; flip one byte → prefix equal, suffix differs.
- `test_model_map_change_changes_suffix_only`: change one `max_tokens` in a copy of `model_config()` → suffix differs.
- `test_sha_precedence`: `resolve_git_sha({"RAILWAY_GIT_COMMIT_SHA": a}, file_with_b) == a`; `({}, file_with_b) == b`;
  `({}, missing) == "unknown"`; `({"RAILWAY_GIT_COMMIT_SHA": "  "}, file_with_b) == b`.
- `test_dirty_sha_kept`: file holds `<40 hex>-dirty` → returned unchanged; the version prefix is its first 12 chars.
- `test_cli_prints_one_line`: `main([])` with `capsys` → one line matching the regex or `^unknown\+[0-9a-f]{8}$`.
- `test_prompt_files_cover_both_globs`: `prompt_files()` includes `src/meridian/policy/texts.py` and every
  `src/meridian/agent/prompts/*.py`.
- `test_build_sha_from_git` (tmp git repo: init, commit, then modify a tracked file → `-dirty`; an untracked file alone
  → not dirty). Skip with reason if `git` is missing.

### 6.7 `tests/deploy/test_railway_config.py`

- `test_railway_json_values` (default; AC-13): `json.loads(railway.json) == ` the §4.3 object exactly.
- `test_dockerignore_lists_required_patterns` (default; AC-4 read-back): lines include `.env`, `.env.*`, `var/`, `.venv/`,
  `.git/`, `**/node_modules`, `eval/cases/`; and do not exclude `docs/ux/03-structure/ui-contracts.openapi.yaml`
  (a `!` line for it exists).
- `test_dockerfile_static_rules` (default; AC-4, AC-13, AC-17): stage names in order `web`, `base`, `index`,
  `runtime`; no `ARG`/`ENV` name matching `SECRET_NAME`; the `CMD` contains `export MERIDIAN_AGENT_VERSION`,
  `python -m scripts.agent_version`, `uvicorn --factory scripts.serve:create_deployed_app`, `--host 0.0.0.0`,
  `--port "$PORT"`, `--workers 1`; the web `RUN` contains `npm ci`, `npm run build`, `npm run check:dist`, and contains
  neither `--omit=dev`, `NODE_ENV=production` nor `--mode`; `ARG NODE_VERSION=` equals the major of
  `apps/web/package.json` `engines.node` when that key exists, else `24`; the file has no `USER`, `VOLUME` or
  `HEALTHCHECK` line ([P-3]).
- `test_image_config_read_back` (deploy; AC-13): `image_cmd(IMAGE)` equals the Dockerfile `CMD`; `image_env(IMAGE)`
  names: none matches `SECRET_NAME`, none is `PYTHONPATH` or `AEA50_FAULT_ONCE_FILE`; `run_in_image(IMAGE, "sh", "-c",
  "test ! -e /app/tests && ! python -c 'import aea50_fault_app'")` exits 0; railway.json has no `startCommand`.
- `test_no_timeout_below_65s` (default; AC-14): every `--timeout-*` value in the `CMD` is ≥ 65; no key containing
  `timeout` (case-insensitive) in railway.json; with `host_env` env monkeypatched, the set of route paths of
  `scripts.serve.create_deployed_app()` equals that of `meridian.web.app.create_app()` (both before any lifespan).

### 6.8 `tests/deploy/test_image.py` (all `pytestmark = pytest.mark.deploy`)

- `test_index_built_in_image` (AC-1): `built_images().main_log` contains `python -m meridian.retrieval.ingest`; via
  `docker create` + `docker cp` read `/app/index/` → the six files exist; `index_record.json` `embedding_model ==
  "BAAI/bge-small-en-v1.5"`, `files == 17`, `chunks > 0`, `manifest_hash` 64 hex; `ingest_run.json` `status ==
  "completed"`; `/app/eval/reports` is a directory; `/app/BUILD_SHA` text == `build_sha_value()`;
  `/app/docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite` exists.
- `test_web_stage_conditional` (AC-2): in `IMAGE`, `/app/apps/web/dist/index.html` exists and
  `find /app /usr/local/lib -name node_modules` is empty; in `IMAGE_NOWEB`, `/app/apps/web/dist` does not exist and the
  noweb build log contains `frontend build skipped`.
- `test_web_stage_recipe` (AC-17): `build(IMAGE_WEB, ctx, "--target", "web", "--no-cache-filter", "web")` log contains
  `openapi-typescript` (the `prebuild` → `gen:types` step) and `dist is clean`; in `IMAGE`, no file named
  `ui-contracts.openapi.yaml` anywhere (`find / -xdev -name ui-contracts.openapi.yaml` empty).
- `test_runs_without_network` (AC-3): `run_in_image(IMAGE, "python", "-m", "scripts.image_check", "--search",
  "What does the Comfort Club membership include?", network="none")` exits 0; stdout has `readiness ok=true` and
  `search status=ok`; output contains none of `Downloading`, `huggingface.co`, `Fetching`.
- `test_no_secrets_in_image` (AC-4): `scan_saved_image(IMAGE, the four context sentinels)` → `[]`; `docker history
  --no-trunc --format '{{.CreatedBy}}' IMAGE` contains no sentinel; plus the static checks of §6.7 repeated on
  `image_env`.
- `test_first_boot_writes_only_data_dir` (AC-5): `before = sha256 of ROOT/<issued sqlite>` (host) and
  `run_in_image(IMAGE, "sha256sum", ISSUED_IN_IMAGE)` equal; `start(data_dir=new_data_dir(), env=sentinel_env())`,
  `wait_deploy_status(..., "completed")`; `exec("sha256sum", ISSUED_IN_IMAGE)` equals `before`; the data dir holds
  `meridian.sqlite` and `checkpoints.sqlite`; `exec("sh", "-c", "find / -xdev -name meridian.sqlite -not -path '/data/*'")`
  is empty.
- `test_reset_leaves_issued_file_unchanged` (plan-added, `BLOCKED_AEA_29_30`): after the run above, `stop()`, then
  `run_in_image(IMAGE, "sh", "-c", f"python -m scripts.reset && sha256sum {ISSUED_IN_IMAGE}", env=sentinel_env(),
  volumes={data_dir: "/data"})` exits 0, prints `reset status=done`, and the sha equals `before`.

### 6.9 `tests/capture/test_cap9_runtime_ops.py`

Module-level memoised runs (in `support`-style helpers inside this file, each started once and shared):
- **R0 first boot** (`--network none`, `sentinel_env()`, empty data dir): wait `completed`. Used by AC-6, 11, 12 (200
  part), 18, 19 (completed part), 23.
- **R1 offline restart** (`--network none`, `--restart on-failure`, `sentinel_env()`, `fault_once=True`; before start,
  host-`migrate` the data dir and insert one `running` turn with `tests.services.ops_support.add_conversation` +
  `add_turn(status="running", trace_export=None)` through a `TempStore` built on that dir): wait until
  `restart_count() == 1` and two `deploy_records` exist with the newest `completed` (timeout 180 s). Used by AC-12,
  24, 25, 26.
- **R2 stub restart**: `docker network create --internal aea50-net-<hex>`; stub container from `IMAGE` running
  `python /stub/langfuse_stub.py --host 0.0.0.0 --port 8000 --project-id proj-other --counts /stub/counts.json`
  (stub file + counts dir mounted at `/stub`); app container on that network with `sentinel_env(langfuse={
  "LANGFUSE_PUBLIC_KEY": s, "LANGFUSE_SECRET_KEY": s, "LANGFUSE_BASE_URL": "http://<stub name>:8000",
  "LANGFUSE_PROJECT_ID": "proj-aea50"})`, `--restart on-failure`, `fault_once=True`. Used by AC-27.
- **R3 sweep**: like R1's preparation but no fault, `--network none`. Used by AC-20.

Tests:
- `test_wf13_startup_writes_deploy_record` (deploy; AC-6): one row in R0; `deploy_id` non-empty; `git_commit ==
  build_sha_value()`; `agent_version == compute_agent_version(build_sha_value(), model_config(), prompt_files())` and
  matches `^[0-9a-f]{12}\+[0-9a-f]{8}$`; `config_hash` 64 hex; `trace_export_on == 0`; `status == "completed"`.
- `test_wf13_wrong_project_keys_turn_export_off` (default; AC-8): in process. For each case `right`, `wrong`,
  `missing_project_id`: `start_stub("proj-aea50" if right else "proj-other")`; `tmp` data dir;
  `build_stand_in_index(tmp/index)`; `monkeypatch` the env to exactly `host_env(...)` (+ the four Langfuse values, minus
  `LANGFUSE_PROJECT_ID` for the missing case); `with TestClient(create_deployed_app()):` wait (≤10 s) for the deploy
  record `completed`; then read rows. Assert: `right` → no `alert_fired` row; `wrong` → exactly one `alert_fired` row
  with `alert_type == "trace_export_failed"` and `reason_code == "wrong_project"`, and stub `spans == 0`; `missing` →
  no alert row and stub `project_checks == 0`. Teardown: `logging.captureWarnings(False)`; stub closed.
- `test_wf13_deploy_record_reads_export_state` (default; plan-added; `BLOCKED_AEA_19_FU`): same three cases →
  `trace_export_on` is `1`, `0`, `0`.
- `test_wf14_manifest_and_index_in_image` (deploy; AC-9; **WP-1**): from `IMAGE`'s `/app/index`: `manifest.json` has 17
  rows each with `status` and `parse_method`; every row with `status != "current"` has `chunks == 0`, including
  `archive/comfort_club_overview.md` (status `excluded`); no `passages.jsonl` line has `file` or `passage_id` starting
  `archive/` or `file == "internal/agent_discretion_notes.md"`; every `staff_notes.json` entry has
  `file == "internal/agent_discretion_notes.md"`; `ingest_run.json` `ingest_run_id` non-empty and its `manifest_hash`
  and `chunks` equal `index_record.json`'s.
- `test_wf14_index_clean_and_offline` (deploy; AC-21): each of the six artefacts contains no context sentinel; then
  `run_in_image(IMAGE_INDEX, "sh", "-c", "python -m meridian.retrieval.ingest --kb-dir /build/knowledge_base
  --transcriptions-dir /build/kb_transcriptions --out-dir /tmp/reindex", env={"HF_HUB_OFFLINE": "1"}, network="none")`
  exits 0 and its last line's `manifest_hash=` and `chunks=` equal the built `index_record.json`.
- `test_wf15_reset_script` (default; AC-10; `BLOCKED_AEA_29_30`): `with demo_store() as (store, cp):`
  `make_dirty_demo(store, cp, open_chats=1, customer_message=...)`; record kept-table counts (`spend_ledger`,
  `health_events`, `deploy_records`, `eval_runs`, `job_runs`); `cp.close()`; run
  `subprocess.run([sys.executable, "-m", "scripts.reset"], cwd=ROOT, env=host_env(store.data_dir), capture_output=True,
  text=True, timeout=120)`; assert exit 0 and one stdout line `reset status=done request_id=<uuid> open_chats_ended=1
  roles_reset=<n>`; newest `reset_events` row: `asked_by_role IS NULL`, `asked_by_session IS NULL`, `request_id` ==
  printed id, `checkpoints_cleared == 1`, `restored_json` non-empty; newest `seed_events` row: `reset_id` == that
  reset's id, `seed_count == 4`, `label == "demo seed"`; each of the five issued tables equals
  `reset_support.issued_rows(store.issued_path, table)` row for row; `conversations` has no row with
  `run_tag != 'seed'`, `cases` no row with `seed = 0`, and `flags`, `identity_codes`, `demo_inbox`,
  `identity_threads` are empty; kept counts unchanged.
- `test_wf15_reset_holds_no_values` (default; AC-22; `BLOCKED_AEA_29_30`): same run (shared fixture) with
  `host_env` sentinels; no sentinel in `json.dumps` of the `reset_event` and `seed_event` rows, stdout or stderr.
- `test_ops_output_has_no_values` (default; AC-15): parametrised `script` in `agent_version` (`[sys.executable, "-m",
  "scripts.agent_version"]`), `image_check` (`… "scripts.image_check", "--index-dir", <stand-in index>`), and
  `pytest.param("reset", marks=BLOCKED_AEA_29_30)` (the AC-10 setup with name/phone sentinels in the data): each
  run with `host_env` sentinels; exit 0; no sentinel (name, phone, every key, password) in stdout or stderr; stderr
  lines, if any, each parse as JSON.
- `test_wf13_startup_logs_allow_listed` (deploy; AC-18): R0 `logs()`; `json_lines(...)` succeeds; each record's keys ⊆
  `ALLOWED_LOG_KEYS[record["record"]]`; no sentinel in any line or in `json.dumps` of the `deploy_records` row.
- `test_wf13_deploy_record_status` (deploy; AC-19): R0's row `completed`; then `start(IMAGE_NOINDEX,
  data_dir=new_data_dir(), env=sentinel_env())`, wait until the container has exited (≤ 90 s, `--restart no`); its
  single `deploy_records` row has `status == "failed"`; every status seen ∈ {started, completed, failed, incomplete}.
- `test_wf13_startup_sweeps_running_turns` (deploy; AC-20; `BLOCKED_AEA_40`): R3: the turn row after start-up is
  `status='failed'`, `outcome='degraded_handoff'`, `degrade_reason='timeout'`; exactly one log record with
  `record == "turn_sweep"` and `count == 1`, holding no key outside its allow-list.
- `test_wf16_first_boot_seed` (deploy; AC-11; `BLOCKED_AEA_29`): R0's data dir: every `CREATE TABLE IF NOT EXISTS
  <name>` in `schema_files()` exists; `cases` with `seed = 1` are exactly MHC-C-0005…MHC-C-0008 and their conversations
  have `run_tag = 'seed'`; one `seed_events` row, `seed_count == 4`, `label == "demo seed"`, `reset_id IS NULL`; then
  `docker restart`, wait for a second `completed` deploy record → still one `seed_events` row.
- `test_wf16_seed_event_carries_deploy_id` (deploy; plan-added; `BLOCKED_AEA_31_FU`): that row's `deploy_id` equals
  the first `deploy_records` row's `deploy_id`.
- `test_wf16_first_boot_offline_and_clean` (deploy; AC-23; `BLOCKED_AEA_29`): R0 (offline, sentinels, no Langfuse):
  completed; one `seed_events` row; all log lines allow-listed JSON; no sentinel in any log line, the `seed_events` row
  or any TEXT column of any table of the working copy (iterate `sqlite_master`).
- `test_wf17_forced_failure_restarts` (deploy; AC-12): R0 `exec("python", "-c", "import urllib.request,sys;
  sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz').status == 200 else 1)")` exits 0 (no cookie);
  R1: `restart_count() == 1`; `health_events` ordered by id hold ≥ 3 `check_failed` before one `restart` row whose
  `reason_code` starts with `healthz_failed_`; consecutive `check_failed` `at_wall` gaps ≥ 10 s (15 s cadence with
  slack); the newest deploy record `completed`.
- `test_wf17_health_events_carry_ids` (deploy; AC-24; `BLOCKED_AEA_32_FU`): R1: every `check_failed`/`restart` row has
  a non-empty `health_check_id`, distinct per probe, and `deploy_id` equal to the first process's `deploy_records` row.
- `test_wf17_restart_offline_and_clean` (deploy; AC-25): R1 ran with `--network none`: restart count 1; no sentinel in
  any `health_events` row or log line.
- `test_wf17_restart_sweeps_open_turn` (deploy; AC-26; `BLOCKED_AEA_40`): R1's pre-inserted `running` turn is
  `failed` / `degraded_handoff` / `timeout` after the restart.
- `test_wf17_restart_rechecks_project` (deploy; AC-27): R2: restart count 1; stub counts `project_checks == 2`,
  `spans == 0`; `latest_alert_states()["trace_export_failed"].state == "firing"` (read through a host
  `SqliteUnitOfWorkFactory` on the data dir); exactly one `alert_fired` row with `reason_code == "wrong_project"`.
- `test_wf17_restart_export_state_per_process` (deploy; plan-added; `BLOCKED_AEA_19_FU`): R2's two deploy records both
  `trace_export_on == 0`.

---

## 7. Checks

Cheapest first; stop at the first red. Paths: `P = scripts tests/deploy tests/capture/conftest.py tests/capture/test_cap9_runtime_ops.py`.

| # | Check | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check $P` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check $P` | all already formatted |
| 3 | Type check | `uv run mypy` then `uv run mypy scripts` | `Success: no issues found` (twice) |
| 4 | Affected tests, default run | `uv run pytest -q tests/deploy tests/capture` | all pass; the blocked tests report `xfailed`; deploy tests `skipped` |
| 5 | Collection still whole | `uv run pytest --collect-only -q` | exit 0 (the two new conftests break nothing) |
| 6 | Deploy tests (this ticket; before every deploy) | `df -h /home` then `uv run pytest -q -m deploy tests/deploy tests/capture/test_cap9_runtime_ops.py` (serial, no `-n`) | every non-blocked test passes; blocked ones `xfailed` with their `blocked-on` reason; afterwards `docker images | grep aea50` and `docker ps -a | grep aea50` print nothing |
| 7 | Affected journeys | `uv run python -m tests.journeys.affected --base main` | `0 journeys affected`, exit 0 (AC-16) |
| 8 | Context check | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL |
| 9 | Diff scope (AC-28) | `git diff --name-only main...HEAD` | only §2.1 paths |

**Full suite: not required.** The change reaches no shared fixture (`tests/conftest.py` untouched), no settings, no
dependency or lockfile, no module imported across the codebase (`scripts/` is imported only by its own tests). The
two new directory conftests affect `tests/capture` and `tests/deploy` only, both run in check 4. The full suite and all
journeys run before the deploy (AEA-56).

**Report back:** each check's command and result line; the `-m deploy` summary line; the list of `xfailed` tests with
their reasons; the built image size (`docker image inspect meridian:aea50-test --format '{{.Size}}'` before cleanup);
the `agent_version` the image printed; `df -h /home` before and after.

---

## 8. Risks and requests

| # | Risk / request | What to do |
|---|---|---|
| R-1 **[P-1]** | **Where the start-up deploy record lives.** Nobody owned it: AEA-32's merged plan §2.3 gives "the start-up deploy-record write" and the `load_eval_reports` call to AEA-50; AEA-50's ticket forbids editing `web/container.py` and `src/`. The only AEA-50-owned home is `scripts/serve.py`, a factory that calls `create_app()` with **no arguments** (so web.md §15's "factory with no arguments, nothing is overridden" still holds) and wraps its lifespan. Consequence: the deploy record exists only when started through the image's `CMD` (journeys and local `create_app` runs write none — correct for a deploy fact). It is a second start-up hook beside the container, not a new interface. | **Orchestrator: confirm before dispatch.** Alternative: a follow-up on AEA-32 (`register_ops` writes the record) plus an AEA-02 follow-up (`Settings` fields for commit and deploy id); AEA-50 would then drop `serve.py` and use `--factory meridian.web.app:create_app`, and AC-6/AC-19 would be blocked on those. Recommended: keep `serve.py`. DO-3 §3 line gains it in step C-2. |
| R-2 | `LangfuseTraceSink` has no public export state (only `_state`), so `deploy_record.trace_export_on` cannot read on/off for a Langfuse sink. | **Request AEA-19 follow-up:** a read-only `export_on: bool` property, `True` only in state `"on"`. Until then `serve.py` writes `NULL` for a Langfuse sink (honest "unknown") and `False` for `NullTraceSink`. Tests: `BLOCKED_AEA_19_FU`. |
| R-3 | `register_reset` calls `seed_first_boot(..., deploy_id=None)`; DO-6 WF-16 wants the first-boot `seed_event` tied to the deploy. | **Request AEA-31 follow-up:** in `register_reset.first_boot`, pass `deploy_id=getattr(app.state, "deploy_id", None)` (set by `serve.py` before the lifespan). Test: `BLOCKED_AEA_31_FU` (unconditional strict xfail; the follow-up removes the marker in its own diff). |
| R-4 | `health_events` has no `health_check_id` / `deploy_id` (DO-6 WF-17; sign-off "HealthEvent gets the DO-6 fields"). Already raised as AEA-32 plan R-4. | **Request AEA-10 (two nullable TEXT columns) + AEA-32 follow-up** (`HealthEvent` fields; `Watchdog` sets a UUID4 per probe and `app.state.deploy_id`). Test: `BLOCKED_AEA_32_FU`. |
| R-5 | The `turn_sweep` count line is formatted as `{"record":"log","length":N}` until AEA-23 allow-lists it (AEA-40 plan R-5). | Covered by `BLOCKED_AEA_40` (needs AEA-40 **and** `"turn_sweep"` in `ALLOWED_FIELDS`). |
| R-6 **[P-5]** | `tests/capture/conftest.py` is a new file in a folder four other tickets write into (24, 51, 52, 53). It only registers the `deploy` marker and its default skip; `pyproject.toml` (AEA-01) cannot be used because changing it selects every journey and breaks AC-16. | Collision note for the orchestrator: later CAP tickets **extend** this conftest (append hooks), never replace it. |
| R-7 **[P-3]** | The container runs as root. Railway mounts volumes root-owned; a non-root `USER` would need `RAILWAY_RUN_UID=0` (a variable outside data.md §7's list) and so runs as root anyway [A: check Railway's volume docs at AEA-56]. The image holds no secret; the issued file is protected by code (`immutable` read-only connection, copy on first boot) and proven by AC-5's SHA checks. | For `security-privacy-agent` at the wave-3 merge. If Innocent prefers non-root, add `USER` + `RAILWAY_RUN_UID=0` in AEA-09/54 (small follow-up). |
| R-8 **[P-2]** | The `CMD` uses `VAR="$(…)" && export VAR && exec uvicorn …` instead of data.md's literal `export VAR="$(…)" && exec …`, so a failing version script stops the start (the literal would export an empty value and every stamp would read `"dev"`). Same effect otherwise. | Recorded deviation; DO-3 §3 line notes the start command. |
| R-9 **[P-8]** | `--timeout-keep-alive 75`: uvicorn's default 5 s idle keep-alive is not a request timeout, but setting it above the 65 s line keeps AC-14's rule literal and avoids a proxy reusing a connection the server just closed [A]. | None; revisit with M-28 or a 502 seen at AEA-56. |
| R-10 | Image defaults `MERIDIAN_DATA_DIR=/data`, `MERIDIAN_INDEX_DIR=/app/index`, `MERIDIAN_WEB_DIST_DIR=/app/apps/web/dist`, `PORT=8080`, `HF_HUB_OFFLINE=1`. Railway variables (AEA-09) may set the first three again; `PORT` is Railway's. | AEA-54's guide should list them as image defaults. |
| R-11 | `BUILD_SHA` is written by the deploy step: `python -m scripts.agent_version --write-build-sha` (git HEAD, `-dirty` for tracked changes only). It is not in `.gitignore`, so it shows as untracked in the repo after that command. | AEA-54/AEA-56: run it right before `railway up`; delete it after (or a `.gitignore` line via the owner of `.gitignore`). |
| R-12 | Disk: four test images (~0.8–1 GB each, layers shared) plus BuildKit cache (npm + uv). 16 GB free at planning time. | `cleanup_session()` removes images and containers; the build cache is left (other projects share the daemon). Check `df -h /home` before and after. |
| R-13 | Strict-xfail markers flip to failures (XPASS) under `-m deploy` / default run once their blocker lands. AEA-29/30/40 are conditional (module presence) and flip on their own; R-3's marker is unconditional. | Whoever lands R-2…R-4 removes the matching marker in `tests/deploy/support.py` in their own diff (a frozen file: that ticket's test-writer does it). |
| R-14 **[P-6]** | No `engines.node` in `apps/web/package.json` yet (shell audit F4); Node 24 is the VPS version the UX build used. | `test_dockerfile_static_rules` switches to `engines.node` automatically when the UX session adds it. |
| R-15 **[P-7]** | The AC-12 fault is a test module mounted at run time with the image's own `CMD` (one factory name swapped). Nothing in the image or `railway.json` can select it (AC-13 read-back). | None. |
| R-16 | The Langfuse SDK might call a path on the stub that is neither the project check nor ingestion. | The stub counts it as `other`, never as a span; AC-8/AC-27 assert `spans == 0` and report `other`. |
| R-17 **[P-9]** | `model_config()` uses `Settings.model_construct(models=default_model_settings())`, not `from_env`: `models` has no env name, so this is the deployed map, and the script never needs or reads a key. If a later ticket adds an env override for models, this must switch to `Settings.from_env(os.environ).role_model_map()`. | Note in the plan; the AEA-02 owner would flag it. |
| R-19 | When AEA-51 wires `FastembedIndex` readiness into the container build (data.md §9 item 6), a readiness check that *raises* there would stop start-up before `serve.py` begins the record, and AC-19 would find no row. | **Note to AEA-51's planner:** report readiness (log/flag) inside the container; `serve.py` already stops the deploy on a failed readiness after the record is begun. |
| R-18 | AEA-29, AEA-30, AEA-40 are wave-2 tickets not merged at `0dedd59`. Ten criteria (AC-5 reset leg, 10, 11, 15 reset leg, 20, 22, 23, 26 and the plan-added deploy_id/export-state/id tests) stay `xfail` until they and the follow-ups land. | `blockedOn` below. Everything else is buildable now. |

---

## 9. Readiness

**READY.** Every file this slice owns can be built and tested now against `main` at `0dedd59`; no signed contract
changes; no decision D-4…D-15 is re-answered; nothing needs Innocent. The orchestrator checks R-1 (the
`scripts/serve.py` start-up hook) and R-6 (new `tests/capture/conftest.py`) before dispatch.

**Blocked criteria (strict xfail until the dependency lands):** AEA-29 (`BriefAssembler`), AEA-30 (`format_clock`),
AEA-40 (start-up restart sweep, with its AEA-23 allow-list request), and three follow-ups this plan requests:
AEA-19 (`LangfuseTraceSink.export_on`), AEA-31 (first-boot `seed_event.deploy_id`), AEA-10 + AEA-32
(`health_check_id`, `deploy_id` on `health_events`).

## Gates

None on this ticket (`risk::security`: frozen tests first; `security-privacy-agent` reads this diff at the wave-3
merge). The deploy gate is AEA-56's (`gate::live`).

## Deviations from the ticket text (all marked [P-n] above)

P-1 `scripts/serve.py` as the deployed factory; P-2 assign-then-export start command; P-3 no `USER`; P-4
`scripts/log_config.json`; P-5 `tests/capture/conftest.py`; P-6 `ARG NODE_VERSION=24`; P-7 mounted fault module; P-8
`--timeout-keep-alive 75`; P-9 `model_construct` for the model map. Plan-added tests: `test_reset_leaves_issued_file_unchanged`,
`test_wf13_deploy_record_reads_export_state`, `test_wf16_seed_event_carries_deploy_id`,
`test_wf17_restart_export_state_per_process`, plus the static `test_dockerignore_lists_required_patterns` and
`test_dockerfile_static_rules`.

## Deviations (implementer, 2026-10-21)

- D-1 Dockerfile `base` stage: the official `python:3.12-slim-bookworm` image sets `ENV GPG_KEY` (a public key id), which the
  frozen `test_no_secrets_in_image` (name regex `KEY`) rejects and no later stage can unset. The `base` stage is now
  `debian:bookworm-slim` + the shared libraries python links against + `COPY --from=python:3.12-slim-bookworm /usr/local/`
  + `ldconfig`. The frozen stage-name test forbids an extra stage, so the python image is a `COPY --from` reference and
  `ARG PYTHON_VERSION` was dropped. Nothing else in §4.5 changed.
- D-2 `scripts/agent_version.py` `model_config()` calls `model_construct` through `cast(Any, Settings)`: the pydantic mypy plugin
  demands the five required secrets as keyword arguments, which this script must never read.
- D-3 `uv run mypy scripts` alone reports `import-untyped` for `meridian.*` (the package is installed without `py.typed`);
  `uv run mypy` (project config, `tests` import `scripts`) is clean and covers it. `pyproject.toml` is not ours.
- D-4 Frozen-test defect (reported, not edited): `test_wf13_deploy_record_reads_export_state[missing_project_id-0]` carries the
  strict `BLOCKED_AEA_19_FU` xfail on all three params, but the missing-value case reads `0` today (NullTraceSink -> False,
  as §4.7 says), so it XPASSes and fails the default run. Fix belongs to the test-writer: apply the marker to the `right` and
  `wrong` params only.
