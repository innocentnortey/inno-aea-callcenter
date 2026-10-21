# Coverage repair — group svc

Group **svc** owns AEA-23, AEA-28, AEA-30, AEA-31, AEA-49, AEA-50 and AEA-62. It also owns the pool tickets that a
missing-row gap names as the proposed owner: AEA-16, AEA-32, AEA-54, AEA-55 and AEA-56. Source of the problems:
`full-check.txt` (338 problems). Gap wording comes from `part-1.md` … `part-8.md`. Every AC number below is the **final**
number after these edits.

## Matrix rows

These are new rows for the coverage matrix in `coverage-audit.md`, in its seven-column format. Each one closes a
"no coverage row" problem. Every integration owner is directly blocked by the implementing ticket (AEA-50's new AEA-40
edge is listed under *Blocked-by edits*).

| Req | Workflow | Component / contract | Implementing ticket | Integration owner | Acceptance criterion | Evidence |
|---|---|---|---|---|---|---|
| OBS-10 | WF-17 | `health_check_id` on every `health_event` (`Watchdog`, `repos_ops`) | AEA-32 | AEA-50 | AEA-50 AC-24 | `test_wf17_health_events_carry_ids` (`-m deploy`): every `check_failed` / `restart` row has a distinct non-empty `health_check_id` |
| OBS-11 | WF-17 | `deploy_id` stamped on every `health_event` | AEA-32 | AEA-50 | AEA-50 AC-24 | `test_wf17_health_events_carry_ids`: each row carries the `deploy_id` of the process that ran the probe |
| OBS-13 | WF-13 | `deploy_record.status` written at start-up | AEA-32 | AEA-50 | AEA-50 AC-19 | `test_wf13_deploy_record_status` (`-m deploy`): `completed` after `/healthz` 200; `failed` after a forced readiness failure |
| OBS-13 | WF-17 | `request.status` and `error_kind` on `/healthz` (middleware record) | AEA-23 | AEA-23 | AEA-23 AC-33 | `test_healthz_status_values`: 200, stale non-200, and 500 with `error_kind` |
| OBS-13 | WF-18 | `request.status` and `error_kind` on `login` / `logout` | AEA-23 | AEA-23 | AEA-23 AC-32 | `test_wf18_status_values_and_no_outbound`: record status equals response status per call; 500 carries `error_kind` |
| OBS-13 | WF-19 | `request.status` and `error_kind` on page serving (AEA-23 middleware) | AEA-23 | AEA-49 | AEA-49 AC-11 | `test_wf19_status_values_and_no_outbound`: 200, 303, 404 without `error_kind`; forced 500 with it |
| OBS-18 | WF-1 | Deployed configuration with no Langfuse values → `NullTraceSink`, so every `turn.trace_export` reads `off` | AEA-50 | AEA-56 | AEA-56 AC-11 | S-7 CON-19 body: export off (0 of N) over the S-4 and S-5 turns, both answered; or "N/A: route opened <date>" |
| OBS-20 | WF-13 | VPS Langfuse project retention ≤ 90 days (D6), set with the route | AEA-09 | AEA-56 | AEA-56 AC-12 | Retention value or screenshot on the issue; "N/A: no traces leave" when declined |
| OBS-21 | WF-13 | Allow-list log formatter on the image's start command | AEA-23 | AEA-50 | AEA-50 AC-18 | `test_wf13_startup_logs_allow_listed` (`-m deploy`): 0 log lines outside the allow-list; 0 sentinel hits |
| OBS-21 | WF-14 | Ingest CLI output: IDs, counts and statuses only | AEA-16 | AEA-16 | AEA-16 AC-8 | `test_excluded_text_absent` through the entry point's `main`: sentinels absent from artefacts and captured output |
| OBS-21 | WF-16 | Allow-list log formatter on first boot | AEA-23 | AEA-50 | AEA-50 AC-23 | `test_wf16_first_boot_offline_and_clean` (`-m deploy`): 0 boot lines outside the allow-list |
| OBS-24 | WF-13 | Image build context exclusions (`.dockerignore`; no secret `ARG` / `ENV`) | AEA-50 | AEA-50 | AEA-50 AC-4 | `test_no_secrets_in_image`: 0 sentinel hits in `docker save` and `docker history --no-trunc` |
| OBS-24 | WF-14 | Index artefacts built by the ingest CLI in the image | AEA-16 | AEA-50 | AEA-50 AC-21 | `test_wf14_index_clean_and_offline` (`-m deploy`): 0 sentinel hits over the six `/app/index/` artefacts |
| OBS-24 | WF-15 | `reset_event` / `seed_event` from `scripts/reset.py` | AEA-31 | AEA-50 | AEA-50 AC-22 | `test_wf15_reset_holds_no_values`: 0 sentinel hits per row and stream |
| OBS-24 | WF-16 | Seed loader `seed_event`, boot output and the new working copy | AEA-31 | AEA-50 | AEA-50 AC-23 | `test_wf16_first_boot_offline_and_clean`: 0 sentinel hits in logs, `seed_event` and text columns |
| OBS-24 | WF-17 | `health_event` rows and watchdog / container output | AEA-32 | AEA-50 | AEA-50 AC-25 | `test_wf17_restart_offline_and_clean` (`-m deploy`): 0 sentinel hits |
| OBS-29 | WF-14 | Ingest CLI with the embedding model cached in the image | AEA-16 | AEA-50 | AEA-50 AC-21 | `test_wf14_index_clean_and_offline`: offline re-run gives the build's `manifest_hash` and chunk count |
| OBS-29 | WF-16 | First boot and seed load with no network | AEA-31 | AEA-50 | AEA-50 AC-23 | `test_wf16_first_boot_offline_and_clean`: first boot completes under `--network none` |
| OBS-29 | WF-17 | Watchdog probe (loopback), exit and restart with no network | AEA-32 | AEA-50 | AEA-50 AC-25 | `test_wf17_restart_offline_and_clean`: restart count 1 under `--network none` |
| OBS-29 | WF-18 | `login` / `logout` routes open no outbound connection | AEA-23 | AEA-23 | AEA-23 AC-32 | `test_wf18_status_values_and_no_outbound`: 0 non-loopback connects |
| OBS-29 | WF-19 | Page serving opens no outbound connection | AEA-49 | AEA-49 | AEA-49 AC-11 | `test_wf19_status_values_and_no_outbound`: 0 non-loopback connects |
| OBS-31 | WF-17 | `AlertEvaluator` `zero_traffic` (4 h, quiet 22:00–06:00 Chicago) evaluated by the running `Watchdog` | AEA-32 | AEA-32 | AEA-32 AC-14 | `test_watchdog_raises_zero_traffic_and_restart_alerts`: one `alert_fired` at 14:00 + 5 h; none in the quiet case |
| OBS-32 | WF-13 | Start-up restart sweep `core.turns.fail_running()` (web.md; AEA-40's hunk) | AEA-40 | AEA-50 | AEA-50 AC-20 | `test_wf13_startup_sweeps_running_turns` (`-m deploy`): `running` row → `degraded_handoff` / `timeout`; one `turn_sweep` line |
| OBS-32 | WF-17 | The same sweep run by the restarted process | AEA-40 | AEA-50 | AEA-50 AC-26 | `test_wf17_restart_sweeps_open_turn` (`-m deploy`): the row before the failure and after the restart |
| OBS-39 | WF-17 | MOD-6 Langfuse project check re-run on the restarted process | AEA-19 | AEA-50 | AEA-50 AC-27 | `test_wf17_restart_rechecks_project` (`-m deploy`): export `off` and alert firing per process; 0 spans |
| OBS-40 | WF-17 | `health_check_restart` alert written by the restarted `Watchdog`; `latest_alert_states()` (the read CON-19 shows) | AEA-32 | AEA-32 | AEA-32 AC-14 | `test_watchdog_raises_zero_traffic_and_restart_alerts`: one `alert_fired` `health_check_restart`; state `firing` |
| R-42 | WF-13 | Public GitLab project 2318 holding the deployed SHA, the eval set and the issued dataset | AEA-56 | AEA-56 | AEA-56 AC-10 | `visibility` `public`; `origin/main` contains `$SHA`; `eval/cases` and the issued dataset listed at `$SHA` |
| R-43 | WF-13 | Deployment guide `docs/deployment-guide.md` | AEA-54 | AEA-54 | AEA-54 AC-1 | 13 headings matching the table, each citing its sources |
| NFR-3 | WF-1 | UX-4 screens in `apps/web` run against the real backend: SCR-1 customer chat | AEA-55 | AEA-55 | AEA-55 AC-16 | AC-4 run's axe and Lighthouse rows for SCR-1: 0 AA violations per state; grayscale review row |
| NFR-3 | WF-2 | SCR-1 handoff card and follow-up preference | AEA-55 | AEA-55 | AEA-55 AC-17 | axe and Lighthouse rows for those states: 0 AA violations; grayscale review row |
| NFR-3 | WF-3 | SCR-2 demo delivery inbox | AEA-55 | AEA-55 | AEA-55 AC-18 | axe and Lighthouse rows for SCR-2: 0 AA violations; grayscale review row (expired state) |
| NFR-3 | WF-4 | SCR-4…SCR-8 staff console | AEA-55 | AEA-55 | AEA-55 AC-19 | axe and Lighthouse rows per screen: 0 AA violations; grayscale review row |
| NFR-3 | WF-5 | SCR-3 demo guide and controls | AEA-55 | AEA-55 | AEA-55 AC-20 | axe and Lighthouse rows for SCR-3 in both staffing modes: 0 AA violations; grayscale review row |
| NFR-3 | WF-6 | SCR-9…SCR-11 measure pages | AEA-55 | AEA-55 | AEA-55 AC-21 | axe and Lighthouse rows per page: 0 AA violations; grayscale review row |
| NFR-3 | WF-18 | SCR-12 demo login | AEA-55 | AEA-55 | AEA-55 AC-22 | axe and Lighthouse rows for SCR-12 (empty, refused, expired): 0 AA violations; grayscale review row |

## Reworded

Each AC below already drives the workflow's entry point. The edit adds the workflow id (plus, where noted, one clause
that makes the test's path explicit). Existing matrix rows that cite these ACs stand unchanged.

| Ticket AC | Added | Clears |
|---|---|---|
| AEA-16 AC-8 | **WF-14** and "run through the ingest entry point's `main`, as AC-9's" | OBS-21 WF-14 (new row above) |
| AEA-23 AC-6 | **WF-18 (`login`)** | DC-1 WF-18 (line 470) |
| AEA-30 AC-8 | **WF-7 (`SchedulerJob.tick()`)** | R-3 WF-7 (line 212), R-33 WF-7 (line 274) |
| AEA-30 AC-14 | **WF-2 (J-7's `requestPerson`)** | R-30 WF-2 (line 254) |
| AEA-31 AC-2 | **WF-15 and WF-16** (the seed load inside a reset, which DO-6's WF-16 row stamps with `reset_id`), plus "for each step after `seed_demo` the real `seed_demo` runs first, so its rows must roll back too" | DC-19 WF-16 (line 503) |
| AEA-31 AC-7 | **WF-15 (`ResetService.reset`)** | R-30 WF-15 (line 256) |
| AEA-31 AC-9 | **WF-16 (the seed loader)** | R-26 WF-16 (line 246) |
| AEA-31 AC-10 | **WF-16 (seed load, timed against `DEMO_START`)** | R-3 WF-16 (line 214) |
| AEA-49 AC-3 | **WF-19 (page gate)** | R-48 WF-19 (line 267) |
| AEA-50 AC-3 | **CAP-9, WF-13 (readiness)** | DC-15 WF-13 (line 493) |
| AEA-50 AC-4 | **WF-13 (image)** | OBS-24 WF-13 (new row above) |
| AEA-54 AC-1 | **WF-13 (the deployment guide R-43 requires)** | R-43 WF-13 (new row above) |
| AEA-62 AC-6 | **WF-1 (CON-2 from the browser)** | R-20 WF-1 (line 237) |
| AEA-62 AC-11 | **WF-4 (CON-12 `getCase` from the staff console)** | R-28 WF-4 (line 249) |

New ACs, all placed just before each ticket's regression/context AC (which stays last and was renumbered; no other AC
moved):

| Ticket | New ACs | Regression AC now |
|---|---|---|
| AEA-23 | AC-32 (WF-18: OBS-13, OBS-29), AC-33 (WF-17: OBS-13) | AC-34 (was AC-32) |
| AEA-32 | AC-14 (WF-17: OBS-31, OBS-40) | AC-15 (was AC-14) |
| AEA-49 | AC-11 (WF-19: OBS-13, OBS-29) | AC-12 (was AC-11) |
| AEA-50 | AC-18 (WF-13: OBS-21), AC-19 (WF-13: OBS-13), AC-20 (WF-13: OBS-32), AC-21 (WF-14: OBS-24, OBS-29), AC-22 (WF-15: OBS-24), AC-23 (WF-16: OBS-21, OBS-24, OBS-29), AC-24 (WF-17: OBS-10, OBS-11), AC-25 (WF-17: OBS-24, OBS-29), AC-26 (WF-17: OBS-32), AC-27 (WF-17: OBS-39) | AC-28 (was AC-18) |
| AEA-55 | AC-16 … AC-22 (NFR-3, one per workflow: WF-1, 2, 3, 4, 5, 6, 18) | AC-23 (was AC-16); AC-12's "plus the AC-16 context files" now reads AC-23 |
| AEA-56 | AC-10 (WF-13: R-42), AC-11 (WF-1: OBS-18), AC-12 (WF-13: OBS-20) | AC-13 (was AC-10) |

Matching section edits: each ticket's Observability *Capture evidence* line names the new ACs. AEA-50's frozen-test
list (it is `risk::security`) adds its new negative ACs 18, 21, 22, 23 and 25.

**Audit rows citing a renumbered regression AC:** none. A search of `coverage-audit.md`, the part files, the slice plan
and every ticket for AEA-23 AC-32, AEA-32 AC-14, AEA-49 AC-11, AEA-50 AC-18, AEA-55 AC-16 and AEA-56 AC-10 found no
citation outside the tickets themselves (the one internal reference, AEA-55 AC-12, was updated).

## Blocked-by edits

| Ticket | Added | Why | Wave |
|---|---|---|---|
| AEA-50 | AEA-10 | R-19 WF-16 row (line 236): AEA-50 AC-11 proves AEA-10's `migrate.py` first-boot copy | AEA-10 is wave 1, already upstream via AEA-31 and AEA-32; AEA-50 stays wave 3 |
| AEA-50 | AEA-40 | New OBS-32 WF-13 and WF-17 rows: AC-20 and AC-26 prove AEA-40's start-up restart sweep | AEA-40 is wave 2; AEA-50 stays wave 3; no cycle (AEA-40 depends on 03, 10, 11, 12, 23) |
| AEA-62 | AEA-28 | R-20 WF-1 row (line 237): AC-6 proves `SchedulingService.book` and its `fee_note` | AEA-28 is wave 2, already upstream via AEA-51; AEA-62 stays wave 4 |

## Decisions

These were not applied as product changes. Each needs Innocent's call or an owner's confirmation.

1. **Two observability fields are missing from the signed DO-4 contract.** DO-6's WF-17 row names `health_check_id`
   and `deploy_id` as the health check's correlation ids, and its *Status values* table gives `deploy_record` a `status`.
   cases.md §8's `HealthEvent` model has none of them, and its `DeployRecord` comment omits `status`. The new AEA-50
   AC-19 and AC-24 follow DO-6. They are written the way existing AC-6 already handles the same gap: a missing field is
   recorded as `blocked-on AEA-32`. AEA-32's scope was not widened.
   **Decision needed:** Should AEA-32 add `health_check_id` and `deploy_id` to `HealthEvent` and `status` to
   `DeployRecord` (DO-6 wins), or should OBS-10, OBS-11 and OBS-13 drop WF-17 / WF-13?
2. **Stage 9 rows outside this group.** These were seen but are not svc's: R-43 WF-9 and NFR-4 WF-10 propose a Stage 9
   ticket, and the slice plan says Stage 9 runs are not tickets. They are listed so they are not lost.

## Not fixed

| Item | Reason |
|---|---|
| OBS-29 WF-15 | The gap names AEA-52 (staff group). Not svc's. |
| OBS-31 WF-6, OBS-18 WF-6, OBS-40 WF-6 | AEA-53 (staff group). |
| OBS-32 WF-1 | AEA-40 (cust group). |
| R-12 WF-8 partial (a new AEA-50 AC that runs `eval.run_retrieval` on the built index) | Not a checker problem: the R-12 WF-8 row exists (AEA-24 AC-10, eval group). Adding it would also add AEA-24 and AEA-06 as AEA-50 blockers, which is the eval group's call. |
| EV-7 WF-10 partial ("the deploy refuses while the latest eval or load run has a DB-copy finding" on AEA-56) | Not a checker problem, and it would add a new deploy gate. That is a scope change for Innocent, not a coverage fix. |
| OBS-36 WF-1 / WF-2 partial (a hand comparison with the providers' usage pages on AEA-56) | Not a checker problem; the gap itself offers the checklist §9 record as the alternative. |
| AEA-28 | No problem in `full-check.txt` names an AEA-28 AC. Its only finding is the AEA-62 blocker above. |
