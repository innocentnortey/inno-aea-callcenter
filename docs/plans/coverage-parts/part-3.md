# Coverage audit — part 3 (requirement rows R-40 … OBS-13, audit lines 68–89)

## Scope fixes

| Req | Replacement Applies-to cell | Reason |
|---|---|---|
| R-41 | WF-1, WF-2, WF-3, WF-5, WF-6, WF-15, WF-18; excludes WF-4 (staff operations are never rate-limited by web §5's table and make no model call or booking), WF-19 (page and asset files are not among the API operations web §5 limits, and serving them spends no model or booking budget), WF-7, WF-13, WF-14, WF-16, WF-17 (no public request reaches them), WF-8, WF-9, WF-10, WF-12 (harness runs drive the chat turn's own limits and their spend counts on its cap), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | WF-18 (login) has its own limit, `LOGIN_RATE_LIMITED` with an `auth_event` `rate_limited` (web §5; AEA-23 AC-7, AEA-58 AC-6/AC-11). WF-4 was included, but web §5 says every staff operation is "never limited" and WF-4 makes no model call or booking, so no R-41 limit applies there. WF-19 was unaccounted for (registered 2026-10-21). |
| NFR-1 | WF-1, WF-2; excludes WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17, WF-18, WF-19 (no model or tool call runs in them), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("every"); WF-18 and WF-19, registered at §7, make no model or tool call. |
| NFR-3 | WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-18; excludes WF-19 (it serves the built files; each screen's accessibility is judged under the user workflow that shows it), WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (no screen: jobs, runs and operations), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("never"). WF-18 has a screen (SCR-12 login, AEA-58 AC-6 asserts its refusal line), so the accessibility rule applies to it. |
| NFR-5 | WF-1, WF-2; excludes WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17, WF-18, WF-19 (no model call is made outside chat turns and handoff briefs), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("always"); login and page serving call no model. |
| OBS-1 | WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-15, WF-17, WF-18, WF-19; excludes WF-7, WF-13, WF-14, WF-16 (they make no HTTP call; the registry correlates them by job, deploy, ingest or reset IDs), WF-8, WF-9, WF-10, WF-12 (their HTTP calls are WF-1 calls, tagged by run), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("Every"). The old exclusion was untrue for three HTTP entry points: WF-15 is CON-9 `resetDemo` (AEA-43 AC-13 records its `request`), WF-17 is `GET /healthz` (AEA-23 AC-26 records its `request`), WF-18 / WF-19 rows name `request_id` in DO-6. |
| OBS-2 | WF-1, WF-2, WF-3, WF-4, WF-9, WF-10; excludes WF-5, WF-6, WF-7, WF-8, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17, WF-18, WF-19 (no conversation is involved), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("every"); login and page loads open no conversation. |
| OBS-3 | WF-1, WF-2; excludes WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17, WF-18, WF-19 (no customer turn is taken), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("every"). |
| OBS-4 | WF-1, WF-2, WF-4, WF-7; excludes WF-3, WF-5, WF-6, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17, WF-18, WF-19 (no case is created, acted on or touched), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("each"). |
| OBS-5 | WF-1, WF-8, WF-9, WF-10; excludes WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (no run-tagged traffic passes through them), WF-18, WF-19 (a run's login and page loads create no conversation or case result for its run ID to link), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("every"). The harness logs in once per run with the eval headers (AEA-24 AC-1), so "no run-tagged traffic" would be untrue for WF-18; the reason given is the true one. |
| OBS-6 | WF-12; excludes WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-13, WF-14, WF-15, WF-16, WF-17, WF-18, WF-19 (only experiments carry an experiment ID), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("Every"). |
| OBS-7 | WF-7; excludes WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17, WF-18, WF-19 (only the due-soon and overdue job writes job runs), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("every"). |
| OBS-8 | WF-14; excludes WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-15, WF-16, WF-17, WF-18, WF-19 (only ingestion writes ingest runs), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("Each"). |
| OBS-9 | WF-15, WF-16; excludes WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-17, WF-18, WF-19 (only reset and the seed load carry a reset ID), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("Each"). |
| OBS-10 | WF-17; excludes WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-18, WF-19 (only the health check writes check IDs), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("Each"). |
| OBS-11 | WF-1, WF-2, WF-8, WF-9, WF-10, WF-13, WF-16, WF-17; excludes WF-3, WF-4, WF-5, WF-6, WF-7, WF-12, WF-14, WF-15, WF-18, WF-19 (they write no conversation, turn, eval run or deploy-correlated record), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | Checker: narrowed guarantee ("every"). |
| OBS-13 | WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-17, WF-18, WF-19; excludes WF-16 (the seed load writes only a seed event, which has none of these status fields), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | The old reason ("their records carry none of these status fields") is untrue: DO-6 *Status values* lists `request.status` (the HTTP status, plus `error_kind` on 5xx), and every HTTP workflow writes `request` records: WF-3…WF-6, WF-15 (CON-9), WF-17 (`/healthz`), WF-18, WF-19. WF-4 also writes `turn.outcome = to_staff` (AEA-51 AC-23). |

## Matrix rows

| R-40 | WF-13 | Image, `railway.json`, start command (AEA-50) deployed to the dedicated Railway project | AEA-50 | AEA-56 | AEA-56 AC-6 | Live service's CON-20 `current_agent_version` from `BUILD_SHA`; runtime records on the public URL |
| R-41 | WF-18 | Login limiter `LOGIN_IP` (web §5) in middleware and `routes/auth.py` | AEA-23 | AEA-58 | AEA-58 AC-11 | Browser run: `auth_event` `rejected` then `rate_limited` in AC-6's run |
| NFR-2 | WF-15 | `ResetService` (the demo resets instead of retaining) | AEA-31 | AEA-52 | AEA-52 AC-8 | CON-9 reset: cleared tables hold only the 4 seeds; flags gone |
| OBS-1 | WF-1 | Request-ID middleware (`web/middleware.py`) | AEA-23 | AEA-51 | AEA-51 AC-17 | CAP-1: `request` record per call, `request_id` returned in `X-Request-ID` |
| OBS-1 | WF-2 | Request-ID middleware | AEA-23 | AEA-42 | AEA-42 AC-19 | One `request` per CON-4/CON-5 call, `request_id` = `X-Request-ID` |
| OBS-1 | WF-3 | Request-ID middleware | AEA-23 | AEA-43 | AEA-43 AC-13 | `listDemoInbox` `request` record, `request_id` = `X-Request-ID` |
| OBS-1 | WF-4 | Request-ID middleware | AEA-23 | AEA-45 | AEA-45 AC-17 | Eight staff entry points, one `request` each, `request_id` = header |
| OBS-1 | WF-5 | Request-ID middleware | AEA-23 | AEA-47 | AEA-47 AC-9 | `POST /api/demo/clock` `request` record; same id reaches `demo_events` |
| OBS-1 | WF-6 | Request-ID middleware | AEA-23 | AEA-48 | AEA-48 AC-9 | One `request` per read, `request_id` = `X-Request-ID` |
| OBS-1 | WF-15 | Request-ID middleware; `request_id` passed to `ResetService` | AEA-23 | AEA-31 | AEA-31 AC-12 | `reset_events` row carries the request's `request_id` |
| OBS-1 | WF-17 | Request-ID middleware on `/healthz` | AEA-23 | AEA-23 | AEA-23 AC-26 | One `request` record for `/healthz`, status 200 |
| OBS-1 | WF-18 | Request-ID middleware on login/logout | AEA-23 | AEA-57 | AEA-57 AC-12 | J-1: `request` per call, `request_id` = `X-Request-ID` |
| OBS-1 | WF-19 | Request-ID middleware on page serving | AEA-23 | AEA-49 | AEA-49 AC-7 | CAP-11: six `request` records, `request_id` = header |
| OBS-2 | WF-2 | `HandoffService` writes the case with the request's `thread_id` | AEA-29 | AEA-29 | AEA-29 AC-17 | `cases` row carries the request's `thread_id` and `turn_id` |
| OBS-2 | WF-3 | `thread_id` minted at CON-1, carried to the CON-6 `request` record | AEA-40 | AEA-51 | AEA-51 AC-31 | Each CON-6 `request` carries the code request's `thread_id` |
| OBS-2 | WF-4 | `request` record `thread_id` field (middleware) on the CON-3 stream | AEA-23 | AEA-41 | AEA-41 AC-14 | Stream `request` record with `thread_id` (WF-4) |
| OBS-3 | WF-1 | `turn_id` minted at CON-2 receipt (`TurnService`); one trace per turn | AEA-40 | AEA-51 | AEA-51 AC-17 | One trace per turn, node/model/tool spans nested |
| OBS-3 | WF-2 | CON-4 `turn` row and its span (`routes/handoff.py`) | AEA-42 | AEA-42 | AEA-42 AC-19 | CON-4 `turn` row with `trace_id` from the span |
| OBS-4 | WF-1 | `case_ref` minted at handoff (`HandoffService`) | AEA-29 | AEA-51 | AEA-51 AC-30 | 0 `handed_off` turns without a case over the dev set |
| OBS-4 | WF-2 | `case_ref` minted at handoff | AEA-29 | AEA-29 | AEA-29 AC-17 | `cases` with `case_ref`, `thread_id`, `turn_id` |
| OBS-4 | WF-4 | Case events per staff action on the case | AEA-29 | AEA-52 | AEA-52 AC-2 | CAP-4: one `case_event` per action with role and reason |
| OBS-4 | WF-7 | `SchedulerJob` stamps `case_ref` on alert events | AEA-30 | AEA-30 | AEA-30 AC-12 | Every alert `case_event` has `case_ref` and `job_run_id` |
| OBS-7 | WF-7 | `SchedulerJob.tick()` `job_runs` + stamped `case_event`s | AEA-30 | AEA-52 | AEA-52 AC-6 | CAP-5: `job_run_id` on every `case_event` the tick writes |
| OBS-8 | WF-14 | Ingest CLI `ingest_run.json` and manifest hash | AEA-16 | AEA-50 | AEA-50 AC-9 | CAP-9: `ingest_run_id`, manifest hash in the built image |
| OBS-9 | WF-15 | `ResetService` `reset_event` and seed stamped with `reset_id` | AEA-31 | AEA-50 | AEA-50 AC-10 | Reset script: `reset_event` + `seed_event` with `reset_id` set |
| OBS-9 | WF-16 | Seed loader stamps `reset_id` | AEA-31 | AEA-31 | AEA-31 AC-12 | `seed_events.reset_id` set inside a reset, NULL at first boot |
| OBS-11 | WF-1 | `agent_version` stamped on `conversation` and `turn` (`TurnService`) | AEA-40 | AEA-51 | AEA-51 AC-30 | Every turn and conversation carries `Settings.agent_version` |
| OBS-11 | WF-13 | `deploy_record` writer with `deploy_id`, `agent_version` | AEA-32 | AEA-50 | AEA-50 AC-6 | CAP-9: `deploy_record` fields non-empty, `agent_version` form |
| OBS-11 | WF-16 | Seed loader stamps `deploy_id` on first boot | AEA-31 | AEA-50 | AEA-50 AC-11 | First boot `seed_event` with `deploy_id` set |
| OBS-12 | WF-1 | CON-1/CON-2 records (`TurnService` and its writers) | AEA-40 | AEA-51 | AEA-51 AC-17 | CAP-1: request, conversation, turn, trace, lookup_log, check_event, spend_ledger |
| OBS-12 | WF-2 | Handoff records (case, case_event, promise) | AEA-29 | AEA-51 | AEA-51 AC-22 | CAP-3: case, events, promise, CON-4 `turn` row |
| OBS-12 | WF-3 | Inbox route records | AEA-43 | AEA-51 | AEA-51 AC-31 | CAP-1 WF-3: `request` per read; code row hash and expiry only |
| OBS-12 | WF-4 | Staff case routes and their writers | AEA-45 | AEA-52 | AEA-52 AC-2 | CAP-4: case_events, same-thread message, flag, `request` per call |
| OBS-12 | WF-5 | Demo clock / staffing `demo_events` | AEA-30 | AEA-52 | AEA-52 AC-6 | CAP-5: `demo_events` row with request id and role |
| OBS-12 | WF-6 | Request records on the read pages | AEA-23 | AEA-48 | AEA-48 AC-9 | One `request` per read and no other record kind |
| OBS-12 | WF-7 | `SchedulerJob` job runs, case events, promise changes | AEA-30 | AEA-30 | AEA-30 AC-12 | `job_runs` per tick; alert and promise `case_event`s |
| OBS-12 | WF-13 | `deploy_record` writer | AEA-32 | AEA-50 | AEA-50 AC-6 | CAP-9: one `deploy_record` with every DO-6 field |
| OBS-12 | WF-14 | Ingest manifest, index record, ingest run | AEA-16 | AEA-50 | AEA-50 AC-9 | CAP-9: 17 manifest rows; ingest run and index record |
| OBS-12 | WF-15 | `ResetService` records | AEA-31 | AEA-52 | AEA-52 AC-8 | CON-9: one `reset_event` and one `seed_event` |
| OBS-12 | WF-16 | Seed loader `seed_event` | AEA-31 | AEA-50 | AEA-50 AC-11 | First boot: one `seed_event`, `seed_count` 4 |
| OBS-12 | WF-17 | Health events and watchdog | AEA-32 | AEA-50 | AEA-50 AC-12 | CAP-9: `health_event` per failed check and the restart |
| OBS-12 | WF-18 | Login route `auth_event` and request records | AEA-23 | AEA-23 | AEA-23 AC-25 | CAP-10: four `request` records, three `auth_event`s in order |
| OBS-12 | WF-19 | Request records on page serving | AEA-23 | AEA-49 | AEA-49 AC-7 | CAP-11: six records with route templates |
| OBS-13 | WF-14 | `IngestRun.status` | AEA-16 | AEA-16 | AEA-16 AC-9 | `ingest_run.json` `completed`; a failing run `failed` |

## Gaps

| Requirement | Workflow | Proposed ticket | Proposed AC wording |
|---|---|---|---|
| R-41 | WF-1 | AEA-51 | Name the workflow in AC-24: "Spend cap through the real ledger (R-41, **WF-1**) …". Brakes (AC-25) and the 31st-turn `BUSY` / `RATE_LIMITED` notices (AEA-40 AC-4, AC-6) already exist; AC-24 is the integration proof. |
| R-41 | WF-2 | AEA-51 | New `[failure/refusal]`: "**WF-2**: with the spend cap reached and every read bucket exhausted, CON-4 `requestPerson` is never refused and still opens a case with its promise; CON-5 is never answered 429 (web §5)" — verify `tests/integration/test_limits.py::test_person_request_never_limited`. |
| R-41 | WF-3 | AEA-43 | Split AC-11: "**WF-3**: with the read buckets exhausted, `listDemoInbox` answers 429 `REQUEST_RATE_LIMITED` with `details.retry_after_ms`". |
| R-41 | WF-5 | AEA-43 | The other half of AC-11: "**WF-5**: `getStaffing` and `getDemoClock` answer 429 `REQUEST_RATE_LIMITED`; `setStaffing` does not". |
| R-41 | WF-6 | AEA-48 | Name the workflow in AC-8: "Through AEA-23's real middleware (**WF-6**) …". |
| R-41 | WF-15 | AEA-43 | Name the workflow in AC-8: "Reset throttle (WEB-27, **WF-15**) …". |
| R-42 | WF-13 | AEA-56 | New `[invariant]`: "**WF-13**: the GitLab project's `visibility` reads `public` from the API, and the deployed `BUILD_SHA` is on `origin/main`" — evidence: API response and `git branch -r --contains`. |
| R-42 | WF-9 | AEA-06 | New `[invariant]`: "**WF-9**: the dev split, retrieval cases and held-out case inputs that WF-9 reads, and the issued dataset, are tracked in the public repo (`git ls-files`); held-out answer keys follow DAT-2". |
| R-43 | WF-13 | AEA-54 | Name the workflow in AC-1: "All 13 sections of the deployment guide for **WF-13** exist …". |
| R-43 | WF-9 | none (Stage 9) | The test results and the README containment number come from Stage 9 E-runs, which the slice plan says are not tickets. Add a Stage 9 ticket with AC: "**WF-9**: the held-out run's report is committed under `eval/reports/` and the README number equals its headline". |
| NFR-1 | WF-1 | AEA-51 | Name the workflow in AC-25: "Brakes and the deadline through the real graph (**WF-1**) …"; add a scripted model error and tool error, each ending `degraded_handoff` with a case. |
| NFR-1 | WF-2 | AEA-51 | New `[failure/refusal]`: "**WF-2**: a scripted brief-model failure on CON-4 still opens the case with its promise and the fallback brief". |
| NFR-2 | WF-1 | AEA-51 | New `[negative]`: "**WF-1**: each lookup snapshot stored over the dev set holds only the fields the turn used (field allow-list per tool)". |
| NFR-2 | WF-4 | AEA-52 | New `[failure/refusal]`: "**WF-4**: least privilege: representative sees only queue and case views; owner gets no actions; customer role gets 403 `ROLE_NOT_ALLOWED` on every staff operation". |
| NFR-3 | WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-18 | AEA-55 | AC-4 runs axe and Lighthouse on every screen but names no workflow. Split it into one `[invariant]` per workflow: "**WF-n**: axe on SCR-x… reports no WCAG 2.2 AA contrast violation; no state is shown by colour alone; the safety card passes" (seven ACs, one per workflow). |
| NFR-4 | WF-1 | AEA-51 | New `[invariant]`: "**WF-1**: 20 concurrent conversations through the real app with a scripted model are never queued or limited; booking writes serialize (one transaction)". The components are already in AEA-23 AC-13 and AEA-40 AC-4. |
| NFR-4 | WF-10 | none (Stage 9) | AEA-24 AC-9 proves the load suite against a stub only. The deployed re-measure is Stage 9. Add a Stage 9 ticket with AC: "**WF-10**: the load run of 20 conversations reports p50/p95 and zero `BUSY` / `RATE_LIMITED` notices". |
| NFR-5 | WF-1 | AEA-51 | Extend AC-19: "… every Jev request body over the run carries `provider.data_collection = deny` (**WF-1**)". |
| NFR-5 | WF-2 | AEA-51 | New `[negative]`: "**WF-2**: the CON-4 brief call goes only to the configured paid provider, and any Jev call carries `data_collection: deny`". |
| OBS-2 | WF-1 | AEA-51 | Extend AC-17: "… every `turn`, `lookup_log` and case row carries the CON-1 `thread_id`, the checkpointer key equals it, and the trace's `session_id` equals it (**WF-1**)". |
| OBS-2 | WF-9 | AEA-24 | Split AC-14 (CAP-7) per workflow: "**WF-9**: each dev case starts its own `thread_id`". |
| OBS-2 | WF-10 | AEA-24 | Split AC-14: "**WF-10**: each scripted load conversation has its own `thread_id`". |
| OBS-5 | WF-1 | AEA-51 | New `[failure/refusal]`: "**WF-1**: through the real app, a `run_id` header without the eval key yields `run_tag = live` and no `run_id` on the conversation; with the key, the conversation carries the `run_id`" (component: AEA-23 AC-15). |
| OBS-5 | WF-8 | AEA-24 | Split AC-14: "**WF-8**: the retrieval run's report and every case result carry its `run_id`". |
| OBS-5 | WF-9 | AEA-24 | Split AC-14: "**WF-9**: every dev-case result and every conversation it created carry the `run_id`, tagged `eval`". |
| OBS-5 | WF-10 | AEA-24 | Split AC-14: "**WF-10**: the load run's timings and conversations carry its `run_id`, tagged `load`". |
| OBS-6 | WF-12 | AEA-24 | Name the workflow in AC-15: "CAP-8 (**WF-12**) …". |
| OBS-10 | WF-17 | AEA-50 | Extend AC-12: "… each `health_event` carries a `health_check_id` (**WF-17**)". No AC asserts the ID today. |
| OBS-11 | WF-2 | AEA-51 | Extend AC-22: "… the CON-4 `turn` row carries `Settings.agent_version` (**WF-2**)". |
| OBS-11 | WF-8, WF-9, WF-10 | AEA-24 | Split AC-14 into one capture AC per workflow, each asserting the report's `agent_version` (**WF-8**, **WF-9**, **WF-10**). |
| OBS-11 | WF-17 | AEA-50 | Extend AC-12: "… each `health_event` carries the `deploy_id` (**WF-17**)". |
| OBS-12 | WF-8, WF-9, WF-10 | AEA-24 | AC-14 proves CAP-7 for all three without naming them. Split it into three capture ACs, one per workflow. |
| OBS-12 | WF-12 | AEA-24 | Name the workflow in AC-15 (CAP-8, **WF-12**); same fix as OBS-6. |
| OBS-13 | WF-1 | AEA-51 | New `[invariant]`: "**WF-1**: over the dev set every stored `turn.gate_result`, `turn.outcome`, `turn.degrade_reason` (only with `degraded_handoff`), `conversation.outcome` and `request.status` (with `error_kind` on a forced 5xx) is within DO-6 *Status values*". AEA-51 AC-21 shows single values only. |
| OBS-13 | WF-2 | AEA-51 | Same check for the CON-4/CON-5 rows (**WF-2**). AC-22 shows only `person_requested` / `handed_off`. |
| OBS-13 | WF-3, WF-5, WF-15 | AEA-43 | Extend AC-13: the `request.status` of each call equals the HTTP status, and a forced 5xx records `error_kind`. One AC per workflow. |
| OBS-13 | WF-4 | AEA-52 | Extend AC-2: `request.status` per call, `error_kind` on a forced 5xx, and the relayed `turn.outcome = to_staff` within the list (**WF-4**). |
| OBS-13 | WF-6 | AEA-48 | Extend AC-9: a forced 500 (AC-5's case) records `error_kind` (**WF-6**). |
| OBS-13 | WF-7 | AEA-52 | `job_runs.status` `started` → `completed` / `failed` with `error_kind` is in AEA-30 AC-7, which names no workflow. Add it to AEA-52 AC-6 (**WF-7**). |
| OBS-13 | WF-8, WF-9, WF-10, WF-12 | AEA-24 | `eval_run.status` (`incomplete` in AC-7, `failed` in AC-5) names no workflow. Add a status assertion to each per-workflow CAP-7 / CAP-8 AC. |
| OBS-13 | WF-13 | AEA-50 | Extend AC-6: "`deploy_record.status` is `completed`, and a start-up that fails writes `failed` (**WF-13**)". |
| OBS-13 | WF-17 | AEA-23 | Extend AC-26: the `/healthz` `request.status` is recorded, and a forced 5xx carries `error_kind` (**WF-17**). |
| OBS-13 | WF-18 | AEA-23 | Extend AC-25: each `request.status` equals the response's HTTP status (**WF-18**). |
| OBS-13 | WF-19 | AEA-49 | Extend AC-7: a forced 5xx on page serving records `error_kind` (**WF-19**). |

## Notes

Rows with a workflow list in the Gaps table are one gap per workflow. Checker residuals are exactly these gaps: 59 requirement × workflow cells have no coverage row. Most of them are not missing tests. The criterion exists but never names its workflow: the checker can only trace a criterion that says which workflow it drives. AEA-24 has no criterion that names WF-8, WF-9, WF-10 or WF-12, and no other ticket does either. Its CAP-7 criterion (AC-14) needs splitting per workflow. Stage 9 (WF-9 and WF-10 real runs) has no ticket.
