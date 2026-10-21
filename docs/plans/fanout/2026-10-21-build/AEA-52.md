# Plan — [AEA-52] integration B: staff and demo end to end

**Status:** READY as a plan, **BLOCKED-ON** before the implementer starts: pass 1 waits on AEA-30 and AEA-45 merging
to `main` (AEA-29 and AEA-43 merged since the second pass); pass 2 also waits on AEA-40 and AEA-51; one AC-6 sub-check
waits on AEA-53 (§9).
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/52 (spec copy:
`docs/plans/tickets/AEA-52.md`) · **Base revision:** `main` at `c9b17ea` (third pass; earlier passes against `cf74674` and `68b1412`)
· **Wave:** 3 · **Lane:** `lane::build-loop` · **Risk:** none (no `risk::security`: plan → implement code + named tests →
test → `code-review-agent`; no test-writer, no frozen tests, no security agent) · **Planner model:** claude-opus-5-5 ·
**Implementer:** Sonnet (`fanout-implementer`)

**Refresh log (2026-10-21, third planner pass, against `main` `c9b17ea`).** What still holds: everything below this
log. `git diff --stat 68b1412 main` touches, among the surfaces this plan reads, only AEA-29's service files
(`services/cases.py`, `handoff.py`, `_case_actions.py`, `_case_views.py`, `_case_rules.py`) and `web/container.py`;
`tests/journeys/support/`, `tests/api/openapi_check.py`, `tests/conftest.py`, `web/deps.py`, `web/logging.py` and
`services/{live_chat,reset,reset_gate,staff,health}.py` are unchanged. What changed:
1. **Merged since the second pass:** AEA-29 (`ef561fc`) and AEA-43 (`03f5334`), plus AEA-24, AEA-50, AEA-54 (not read
   here). AEA-29's names are now **confirmed on main**: `kind=f"action:{name}"` (`_case_actions.py` line 152);
   `source_id, log_id = f"src-{r.id}", f"ll-{r.id}"` (`_case_views.py` line 228); `f"invoices/{ident}"` (line 179);
   "No change since the snapshot" / "Changed since the AI saw it" (lines 245, 275); `CaseService(uow, clock, *,
   handoff_block=None, settled_view=None)`; `register_cases` provides `deps.CASE_SERVICE`, `deps.HANDOFF_SERVICE` and
   `Key("brief_assembler")`, reading `Key("demo_clock")`, `deps.DEMO_SERVICE` and `deps.REPLY_COMPOSER` through
   forwarders that raise `RuntimeError("not bound: <key>")` until their owners bind them.
2. **Still not on main:** AEA-30 (branch `aea-30-aea-30-demo-clock-sched` still at `e5c4ce4`, unchanged since the
   second pass; ledger `blocked`, its send-back unfinished): `register_demo` is still a no-op, so `Key("demo_clock")`
   is unbound and a real login answers 500 on the assembled app. AEA-45: now **built** on `aea-45-staff-cases-api` at
   `ea00827` (`web/routes/staff_cases.py` with operationIds `getQueue`, `getCase`, `applyCaseAction`,
   `recordContactActivity`, `createFlag`, `listFlags`, `reviewFlag`, `getOversight`; `register_staff_cases` includes
   the router and provides nothing; the routes read the demo clock through `DemoService`, so they also need AEA-30);
   ledger `blocked`. AEA-40 (branch at `8fc2d33`, ledger NEEDS-DECISION). AEA-51 not started (`register_graph` still a
   no-op). AEA-53 ledger NEEDS-DECISION, not started.
3. **Journey files on main corrected** in §7's must-stay-green list to what exists at `c9b17ea`; AEA-30's branch adds
   `j6/test_aea_30.py` and `j7/test_aea_30.py`, AEA-45's adds `j6/test_aea_45.py`.
4. **Imports:** `CaseService` and `HandoffService` now import from main; only `meridian.services.demo` and
   `meridian.services.scheduler` remain branch-only (Step 0.4). `DEMO_START` is defined in
   `adapters/sqlite/repos_cases_state.py` and re-exported through `repos_cases.__all__`, so §4's import line stands
   under mypy strict.
5. **Context rows:** the area map still has the duplicate A6 rows (lines 31 and 32); AEA-30 and AEA-45 also edit the
   area map, `icm-progress.md` and `code-design.md` on their branches, so Step 1.13 matches rows by name, never by line.
6. No decision changed: AC-25's failure seam (R-5), AC-17's speaker name and D-12 in AC-19 stand.

**Refresh log (2026-10-21, second planner pass, against `main` `68b1412`).** What still holds: the whole structure,
every owned file, the harness signatures (`tests/journeys/support/` is byte-identical to `cf74674`), the reset, staff,
live-chat, health and logging signatures (unchanged on main), the OpenAPI paths and x-roles (re-read), the seed dues
(recomputed from `policy/handoff.py`: 0005 Thu Oct 15 19:00; 0006 and 0007 Mon Oct 19 19:00; 0008 none). What changed:
1. **Blockers.** Merged since the first pass: AEA-02b, 03b, 17, 18, 21, 27, 28, 34, 38. Still **not on main**: AEA-29
   (built on branch `aea-29-aea-29-cases-handoff` at `b54fed9`), AEA-30 (branch `aea-30-aea-30-demo-clock-sched` at
   `e5c4ce4`), AEA-43 (branch `aea-43-aea-43-demo-routes` at `4b1645e`), AEA-40 (branch at `23bd73e`), AEA-45 (no
   branch yet), AEA-51 (not started; `register_graph` on main is still a no-op, so `reply_composer` and `run_graph` are
   unbound). AEA-53 not started.
2. **R-1 settled from AEA-30's branch:** `Key("scheduler_job")` → `SchedulerJob`, `Key("scheduler_thread")` →
   `SchedulerThread` (property `alive`, method `stop()`), thread name `"meridian-scheduler"`, missed-promise event kind
   `PROMISE_MISSED_KIND = "promise_missed"`, failed-tick `error_kind` in `ERROR_KINDS = ("alerts_failed", "sweep_failed",
   "prune_failed")`. Step 0.4 now only *confirms* these on main.
3. **AC-25 failure seam changed.** `SchedulerJob.tick()` calls no `CaseService` method (cases.md §6 lists none; AEA-30
   R-7: the `cases` slot is stored and unused). The forced failure now goes through the contract-named
   `prune_checkpoints` dependency (§3 reconciliation, Step 1.11). AC-1's seam row 7 is proven through `DemoService`'s
   deferred case-service lookup instead (Step 1.3).
4. **AC-9 field formats corrected** from AEA-29's code: the invoice source's `ref` is `"invoices/INV-200037"`,
   `lookup_log_id` is `"ll-<lookup_log.id>"`, `changed_note` is `"No change since the snapshot"` / `"Changed since the
   AI saw it"` (never null for a record source).
5. **Two race fixes** against the real background runner: `stale_check` reads the run's wall clock at evaluate time;
   AC-12 writes its rows before it moves the wall clock a day (Step 1.11).
6. AEA-29's and AEA-43's branches add `tests/journeys/j6/test_aea_29.py`, `j7/test_aea_29.py`, `j8/test_aea_43.py`; they
   join the must-stay-green list once merged (§7).

---

## 1. Goal and sources

**Goal (from the issue's *What to build*).** Wire nothing new; *prove*, through the HTTP API of the app `create_app()`
builds on AEA-57's harness (real container, disposable DB copy, scripted model, socket guard), that the real services
sit behind CON-7…CON-17 and CON-21, that the CON-3 events those services write arrive, and that the reviewer's staff
story works end to end: sign in → switch to Riley → queue with the four seeds → open a case → claim → join, reply, hand
back → record a contact attempt → flag → as supervisor advance the clock past a due time → the scheduler writes
`overdue` and oversight shows it → reset the demo. AEA-52 writes **tests, journey files, one evidence record and
context rows only**. It writes no production code and registers nothing (each service's own `register_<area>()` hunk
binds it).

**What this slice delivers, concretely.** Example: in `test_reset_all_or_nothing` the test signs in twice (Riley and
the supervisor), claims MHC-C-0006, flags MHC-C-0005, advances the clock one hour and turns staffing on; it then posts
`POST /api/demo/reset {"confirm": true}` and checks, against the disposable DB copy, that the five issued tables equal
the issued file row for row, the cases table holds exactly MHC-C-0005…0008, the flags table is empty, the clock reads
Fri 2026-10-16 10:00, Riley's next `GET /api/staff/queue` answers 403 `ROLE_NOT_ALLOWED` with `reason: role_reset`,
and exactly one `reset_events` and one `seed_events` row were written.

**Sources read (governing, by section):**

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-52.md` AC-1…AC-28, *Blocked by*, *Agent handoff* | Every criterion, test path and test name below |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-52, §0a Amendment 1 (J-6, J-7, J-8 journey map), §3 collision map | Owned folders `tests/integration/`, `tests/capture/` (CAP-4, CAP-5), `tests/journeys/j{6,7,8}/test_aea_52.py`; run on the harness, never on fakes |
| Component contracts (DO-4) | `docs/design/contracts/internal-components.md` §11 (`ApiErrorCode`), §13 (`CaseService`, "staff routes never call `open_case`"), §14, §16 | Signatures consumed; §16 addenda win |
| Addenda | `stage7/cases.md` §1.1–§1.4, §3.2–§3.3, §5, §6, §7, §8, §10; `stage7/staff.md` §1–§8, §10, §11; `stage7/web.md` §3, §4, §6, §7, §10, §11, §13, §14, §15 | Seed set, reset contents, lanes, dues, live-chat checks, CON-21 start rule (MC-8), reset gate set, log records |
| UI contracts (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` (operationIds, x-roles, schemas); `docs/design/contracts/api-con-mapping.md` §0–§1 | Every response checked with `assert_response_matches`; every SSE frame with `assert_sse_frames_match` |
| Residuals and amendments | `docs/plans/7b-decisions/residuals-web.md` R-W-13, R-W-14, R-W-16; `docs/plans/ux-join/backend-amendments.md` AEA-52-1…5 | AC-16…AC-18; `CUSTOMER_SPEAKER_NAME` |
| Evaluation plan (DO-5) | WF-4 note: flags never enter the eval set unreviewed | AC-11 |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-4, WF-5, WF-7, WF-15 rows; CAP-4, CAP-5; *Status values* | AC-2, AC-3, AC-6, AC-12, AC-22…AC-27 |
| Metrics (DO-7) | M-13, M-18, M-27, M-3 input | Rows those metrics read exist (promise status, `job_runs`, `abandoned`, `flags`) |
| Rules | `.claude/rules/integrated-journeys.md` §3–§5; `.claude/rules/build-loop-test-scope.md` (+ AEA addition); `context-maintenance.md` | Journey record, levels, affected tests and journeys, context rows |
| Harness (on main) | `tests/journeys/support/` (README, `run.py`, `env.py`, `server.py`, `client.py`, `db.py`, `logtap.py`, `steps.py`, `scripted_model.py`) | The `journey` / `journey_clock` fixtures and building blocks this slice uses |

**Entry points (all registered in DO-6):** WF-4 (staff console), WF-5 (demo controls), WF-7 (scheduler job), WF-15
(CON-9 entry point only). AEA-52 adds none; it proves them.

**Context (template *Context*).** Wave 2 built the staff console API (AEA-44…47) and the demo services (AEA-29…32,
AEA-43) each against DO-4 signatures with doubles. Nothing yet proves that the real objects are bound behind the
routes and work together. AEA-52 is that proof for the staff side, as AEA-51 is for the customer side. The plan stays
relevant while those signatures and the harness (`tests/journeys/support/`) are unchanged; Step 0 re-checks both.

**Entry-point registration (template).**

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| Staff console routes CON-10…CON-17, CON-21 | WF-4 | DO-6 `docs/design/observability-contract.md` WF-4 row; CAP-4 | Evaluation: none scored (DO-5 WF-4 note: flags never enter the eval set unreviewed, AC-11); metrics M-13, M-27, M-3 flag input |
| Demo controls CON-7, CON-8 | WF-5 | DO-6 WF-5 row; CAP-5 | No suite of its own (measured through WF-1, WF-6) |
| Scheduler job (`SchedulerJob.tick`, 60 s runner) | WF-7 | DO-6 WF-7 row; CAP-5 | M-18 (abandoned), M-27 (overdue, `job_runs`), M-13 (missed) |
| CON-9 reset | WF-15 (entry point only) | DO-6 WF-15 row | `reset_event`, `seed_event` |

AEA-52 adds no entry point and changes none; every row above already exists in DO-6.

**Gates (template).** None: no human, paid, live or external gate. No test calls a model provider (the scripted
adapter only), and nothing binds 4019 or 5184 (the harness binds port 0). The wave-3 merge runs `seam-audit-agent`
with all journeys (integrated-journeys §5). No `risk::security` label, so no test-writer and no security agent.

---

## 2. Boundary

### Owned files (create unless noted)

| File | Pass | Content |
|---|---|---|
| `tests/integration/staff_support.py` | 1 | **Plan-added** shared helpers for AEA-52's tests (sign-in, role switch, calls, own-server runner, seed facts, digests). New file, AEA-52-only name; no other ticket writes it |
| `tests/integration/staff_streams_support.py` | 1 | **Plan-added** SSE reader (`read_stream`, `BackgroundStream`) |
| `tests/integration/test_staff_composition.py` | 1 (+2) | AC-1, AC-5, AC-13 twin, AC-21 |
| `tests/integration/test_staff_streams.py` | 1 (+2) | AC-14, AC-20 (pass 1); AC-4, AC-7, AC-17, AC-18 (pass 2) |
| `tests/integration/test_staff_cases.py` | 1 (+2) | AC-9, AC-10, AC-11 (pass 1); AC-19 and the WP variants (pass 2) |
| `tests/integration/test_demo_reset.py` | 1 (+2) | AC-8, AC-27 (pass 1); AC-8 open-chat half (pass 2) |
| `tests/integration/test_staff_allowed_actions.py` | 1 (+2) | AC-16 seed variant (pass 1); live and WP-7 variants (pass 2) |
| `tests/capture/test_cap4_staff_console.py` | 2 | AC-2, AC-3, AC-22, AC-23 |
| `tests/capture/test_cap5_clock_and_scheduler.py` | 1 (+2) | AC-6, AC-12, AC-24, AC-25, AC-26 (pass 1); CON-3 and CON-19 halves and WP-4 variants (pass 2) |
| `tests/journeys/j6/test_aea_52.py` | 1 (+2) | J-6 seed leg (pass 1); WP-7/WP-8 leg (pass 2) |
| `tests/journeys/j7/test_aea_52.py` | 2 | J-7 |
| `tests/journeys/j8/test_aea_52.py` | 1 | J-8 |
| `docs/testing/journeys/2026-10-21-AEA-52.md` (date = run day) | 1, 2 | Written by `--journey-record=AEA-52`, then two cells edited by hand (Step 1.12) |
| `.claude/reference/area-map.md` | 1, 2 | **Modify** only the A6 row (line 31, the fuller of the two A6 rows) and the A9 row |
| `.claude/state/icm-progress.md` | 1, 2 | **Modify**: add one "Routes verified against code and tests" row |
| `docs/design/code-design.md` | 1, 2 | **Modify** only the §6 rows S-7, S-11, S-19, S-20 (append the proving test) |

### Shared surfaces: read and import, never edit

`src/meridian/**` (every module), `tests/journeys/support/**` (AEA-57's), `tests/api/openapi_check.py` (AEA-23's),
`tests/fixtures/sqlite.py`, `tests/conftest.py`, `pyproject.toml`, `uv.lock`, `tests/contract/**`, other tickets'
journey files (`tests/journeys/j*/test_aea_<other>.py`), `docs/ux/**`, `apps/web/**`, the OpenAPI, the briefing, issued
data, `docs/archive/`, `docs/parked/`.

### Other slices' files this slice must not touch

`web/container.py` (every `register_*` hunk is its owner's), `web/deps.py` (AEA-23), `web/routes/*` and
`web/schemas/*` (40–48), `services/*` (29, 30, 31, 32, 44, 46), `tests/integration/test_reads_composition.py`
(AEA-53), `tests/capture/test_cap1…3/6…9*` (51, 53, 24, 50), `.claude/state/build-ledger.md` (orchestrator).

---

## 3. Requirements table

Verbatim text of each criterion: `docs/plans/tickets/AEA-52.md` lines 88–115 (AC-1…AC-28). **P** = pass (§9).

| AC | Requirement (ID-cited, condensed) | P | How it is implemented | How it is verified |
|---|---|---|---|---|
| AC-1 | Real objects bound, no overrides; scheduler thread alive after start-up, gone after shutdown | 1 (+2 rows for AEA-40) | `open_staff_run` (own server so shutdown can be observed); key → class table; `SchedulerThread.alive`; staffing on → off reaches `case_service` (Step 1.3) | `tests/integration/test_staff_composition.py::test_real_objects_bound` |
| AC-2 | CAP-4: claim (`result_line` "Claimed · Riley (demo)"), join, send, hand back, flag; `case_event` per action with role; message in same thread, STORE-redacted; `flags` row; `request` records with role | 2 | `run_cap4_flow` on a CON-4 live case; WP-7 variant when AEA-51's script lands | `tests/capture/test_cap4_staff_console.py::test_staff_actions_recorded` |
| AC-3 | No customer name / Riley text in logs; card-like sentinel stored as "[card number removed]" | 2 | Same flow; values read at run time | `…::test_no_customer_pii_in_logs` |
| AC-4 | CON-3 joined/paused/staff_message/resumed/closed; CON-3 closes on `chat_closed`, CON-21 stays open; CON-21 `controller_changed` ×2 and no `case_changed` from live actions; pre-join version accepted by `resolve`; `Last-Event-ID` replay exact; `stream_reconnect` record | 2 | Two live cases (A: join, send, hand back, resolve; B: join, close) | `tests/integration/test_staff_streams.py::test_takeover_events_and_replay` |
| AC-5 | Role and state refusals at the real routes | 1 | Seeds MHC-C-0005/6/7 + four sessions | `tests/integration/test_staff_composition.py::test_role_and_state_refusals` |
| AC-6 | CAP-5: CON-8 past a case due → `demo_events` row, tick → `job_runs`, `overdue` with `job_run_id`, CON-17 Overdue lane, promise missed after its due, stale tick → `scheduler_stale` `health_event` (CON-19 tile, not an alert), `clock_changed` on CON-3 | 1 (seed variant), 2 (WP-4 variant; CON-3 half; CON-19 half needs AEA-53) | Seeds 0006/0007 (case due = promise due Mon 19:00) in pass 1 | `tests/capture/test_cap5_clock_and_scheduler.py::test_clock_past_due_and_scheduler` (+ `::test_clock_changed_reaches_open_chat`, `::test_stale_tick_shows_as_health_tile` in pass 2) |
| AC-7 | Staffing default, on → `demo_events` + `staffing_changed`, staffed handoff live-queued with `R26.staffed`, off → converted (same ref, same `created_at`), `shift_ended`, same mode writes nothing | 2 | CON-1 + CON-4 + CON-7 | `tests/integration/test_staff_streams.py::test_staffing_on_and_shift_end` |
| AC-8 | CON-9 all-or-nothing, issued tables equal, seeds only, flags gone (`FLAG_NOT_FOUND`), clock at `DEMO_START`, roles reset (`role_reset`, `roles_reset`), gate held → `submitTurn` 503 / second CON-9 409, one `reset_event` + `seed_event`, kept tables kept, forced failure → `RESET_FAILED` | 1 (+2 open-chat half) | Steps 1.6 | `tests/integration/test_demo_reset.py::test_reset_all_or_nothing` (+ `::test_reset_ends_open_chats` in pass 2) |
| AC-9 | Case view: both dues, sources snapshot vs current, "changed since" after a working-copy change, every fact links to `lookup_log` | 1 (seed invoice), 2 (WP-4 appointment) | MHC-C-0005 invoice source (`ref == "invoices/INV-200037"`) | `tests/integration/test_staff_cases.py::test_case_view_snapshot_vs_current` |
| AC-10 | Contact attempt recorded not sent; `left_message` before due → promise `kept`; `no_answer` → open; no network | 1 (seeds), 2 (WP-7) | Seeds 0006, 0007 | `…::test_contact_attempt_recorded_not_sent` |
| AC-11 | Flags on review list newest first; review changes no eval, prompt or KB file | 1 | Directory digests before/after | `…::test_flag_review_changes_nothing_else` |
| AC-12 | Daily prune to 2 per thread with `pruned` recorded; messages untouched; live idle ≥ 30 min → `abandoned` at last + 30 min; seed/eval/load never | 1 | Synthetic conversations + checkpoints through the real repos and the real `Checkpointer` | `tests/capture/test_cap5_clock_and_scheduler.py::test_daily_prune_and_abandonment` |
| AC-13 | No staff route module calls `open_case` | 1 | Grep, plus a durable test twin | `grep -rn "open_case" src/meridian/web/routes/staff_*.py` (no output); `test_staff_composition.py::test_staff_routes_never_open_cases` |
| AC-14 | After CON-9, CON-21 with no `Last-Event-ID` gets no `demo_reset` and stays open; resumed from before gets `demo_reset` and closes | 1 | Seed MHC-C-0005 | `tests/integration/test_staff_streams.py::test_case_stream_after_reset` |
| AC-15 | `[journey]` J-6, J-7, J-8 at level `integrated with a scripted model`; record filled | 1 (J-8, J-6 seed leg), 2 (J-7, J-6 WP leg) | Harness steps | `uv run pytest -m journey tests/journeys/j6 tests/journeys/j7 tests/journeys/j8` + `docs/testing/journeys/<date>-AEA-52.md` |
| AC-16 | `allowed_actions` listed ⇔ accepted per role; one unlisted per operation refused; owner `[]`; supervisor never live/contact keys | 1 (seed 0007), 2 (live claimed+joined; WP-7) | Fresh state per action (reset for seeds, a new live case for live) | `tests/integration/test_staff_allowed_actions.py::test_listed_iff_accepted_per_role` |
| AC-17 | Relayed customer line equal on CON-21 and in `getCase` | 2 (needs `run_graph`) | CON-4 live case + `submitTurn` | `tests/integration/test_staff_streams.py::test_relayed_message_same_on_stream_and_case_view` |
| AC-18 | Reload after takeover shows joined, paused, Riley's line, resumed; `last_event_id` = newest; 0 replayed | 2 | CON-4 live case | `…::test_reload_after_takeover_shows_staff_lines` |
| AC-19 | WP-4 fee-bearing case reaches oversight (Due soon) and case view at once | 2 (needs AEA-51 WP-4 script) | — | `tests/integration/test_staff_cases.py::test_fee_bearing_request_reaches_staff_at_once` |
| AC-20 | Queue and oversight follow staffing (mode, banner, `live` empty, `live_queue_length` 0) | 1 | CON-7 on/off | `tests/integration/test_staff_streams.py::test_staff_banner_follows_staffing` |
| AC-21 | Least-privilege matrix; no seeded contact value in queue/oversight | 1 | Probe requests (Step 1.5) | `tests/integration/test_staff_composition.py::test_least_privilege_matrix` |
| AC-22 | WF-4 status values: `request.status` = HTTP status; forced 500 has `error_kind`, body `ApiError` | 2 | CAP-4 flow + patched `CaseService.apply` | `tests/capture/test_cap4_staff_console.py::test_wf4_status_values` |
| AC-23 | Key sentinels and raw cookie nowhere (logs, bodies, frames, DB) | 2 | `open_staff_run(extra_env=…)` | `…::test_no_key_values_anywhere` |
| AC-24 | Demo controls: sentinels absent; 0 outbound | 1 | `open_staff_run(extra_env=…)` | `tests/capture/test_cap5_clock_and_scheduler.py::test_wf5_no_key_values_or_outbound` |
| AC-25 | Scheduler entry point: `job_runs` started→completed, `overdue` with `job_run_id`, promise missed, forced failure → `failed` + `error_kind`, next tick runs, stale → one `scheduler_stale` | 1 (seeds), 2 (WP-4) | Container-built `SchedulerJob`; forced failure through the container's `Checkpointer.prune` on a new wall day (§3 reconciliation) | `…::test_wf7_ticks` |
| AC-26 | Scheduler logs within allow-list; sentinels absent from logs and `job_runs`; 0 outbound | 1 | `open_staff_run(extra_env=…)` | `…::test_wf7_logs_keys_and_network` |
| AC-27 | CON-9 opens 0 outbound connections | 1 | Harness socket guard | `tests/integration/test_demo_reset.py::test_reset_makes_no_outbound_connection` |
| AC-28 | Context rows: area-map A6, A9 "integrated (AEA-52)"; icm-progress row; DO-3 §6 S-7, S-11, S-19, S-20 | 1, 2 | Step 1.13 | `git diff --name-only` shows only owned files |

### Source-contract reconciliation (obligations the issue words differently or omits)

| Obligation | Governing source | In ticket | Disposition | Where |
|---|---|---|---|---|
| Customer speaker on CON-21 `customer_message` and CON-12 is `display_name: "Customer"` (`CUSTOMER_SPEAKER_NAME`), not `null` | staff.md §1, §7; cases.md §5 rules; R-W-14 (addendum wins, DO-4 §16; AEA-29 plan made the same call) | AC-17 says "(customer `display_name` null)" | **in-ticket, contract wording followed**: assert equality of the two objects and `display_name == CUSTOMER_SPEAKER_NAME` | AC-17 test; report it |
| A flag writes a `flags` row only, never a `case_event` | staff.md §2 *Flags* ("Nothing here touches any table but `flags`", R-37); `services/staff.py` | AC-2 evidence lists "flagged" among event rows | **in-ticket, contract wording followed**: `case_events` for claim/join/send/hand back; the flag is proven by its `flags` row | AC-2 test |
| Live actions write `case_event` kinds `live_join`, `live_send`, `live_hand_back`, `live_close`; claim writes `action:claim` | `services/live_chat.py` `CASE_EVENT_KIND`; AEA-29 frozen test `tests/services/test_cases.py` line 307 | not named | **added** (exact strings) | AC-2 test |
| "Ticks stopped for more than 180 s" | cases.md §8 (`scheduler_stale_after_s` 180); `services/health.py` (age = now − `job_runs.latest().started_wall_at`) | AC-6, AC-25 | **added interpretation**: the real runner cannot be paused from a test, so the test builds an `AlertEvaluator` over the container's own unit of work and ledger whose wall clock reads *the run's wall clock + 181 s at the moment `evaluate()` runs* (every tick stamps `started_wall_at` from that same clock, so no runner tick can be newer) | AC-6, AC-25 tests |
| "Scheduler log records within web.md §10's allow-list" | `web/logging.py` `ALLOWED_FIELDS`, `AllowListFormatter` | AC-26 | **added interpretation**: every record the scheduler emits, run through `AllowListFormatter`, yields only allow-listed keys or the formatter's fixed fallback keys; and the raw record (`repr(vars(record))`) holds no sentinel | AC-26 test |
| "Eight case operations" | OpenAPI x-roles | AC-21 | **added list**: `getQueue`, `getCase`, `applyCaseAction`, `recordContactActivity`, `createFlag`, `listFlags`, `reviewFlag`, `getOversight` (CON-11, 12, 13, 15, 16×3, 17); `liveChatAction` is checked in the same matrix | AC-21 test |
| `submitTurn` 503 while the gate is held | web.md §7 (`RESET_503_OPERATIONS`, answered by middleware before the route) | AC-8 | **in-ticket, pass 1**: works without AEA-40's route | AC-8 test |
| Live cases "through CON-2 or CON-4 with the scripted model" | ticket *What to build*; web.md §14 (`SessionService` needs `settled_view`); `container.register_person_request` needs `reply_composer` | implied | **blocked-on AEA-51** (it binds `reply_composer` and `run_graph`) and **AEA-40** (CON-1); not in the ticket's *Blocked by* | §8 R-4 |
| CON-19 "Overdue job last ran" tile | cases.md §9 (`MetricsReader`, tile id `scheduler_last_run`) | AC-6 | **blocked-on AEA-53** for that sub-check only (AEA-48's route is merged) | `test_stale_tick_shows_as_health_tile` (pass 2) |
| Contact values never in queue/oversight | AC-21 (D2) | in-ticket | Read phone, email and `service_address` of the seed customers from the working copy at run time; nothing hard-coded | AC-21 test |
| AC-25 "a tick whose `CaseService` call is patched to raise" | cases.md §6 `SchedulerJob.tick()` (works only through the unit of work; names no `CaseService` call); AEA-30 plan R-7 (`cases` slot stored, never called) | AC-25 | **in-ticket, contract followed** (no contract change, no product decision): there is no `CaseService` call to patch. The test forces the failure through `prune_checkpoints`, the tick dependency cases.md §6 does name: patch the container's `Checkpointer` instance `prune` to raise, move the wall clock one day so the tick prunes → that tick's `JobRun.status == "failed"`, `error_kind == "prune_failed"`; undo; the next tick `completed`. The OBS-13 obligation (failed status, `error_kind`, next tick still runs) is proven unchanged. Report it to the orchestrator as a ticket-wording deviation | `test_wf7_ticks` step 3 |
| AC-1 seam row 7 "`SchedulerJob` (30) ← `CaseService` (29)" | cases.md §6 (`DemoService` calls `cases.convert_live_queued` on → off; the tick calls none); AEA-30 `register_demo` (`DeferredCases` resolves `deps.CASE_SERVICE` at a shift end) | AC-1 | **in-ticket, contract followed**: the binding is proven by behaviour, not by reading private attributes: a staffing on → off through CON-7 answers 200 (an unbound case service answers 500 "not bound: case_service"); pass 2's AC-7 proves the conversion itself | `test_real_objects_bound` step 6 |
| AC-9 source fields | AEA-29 `services/_case_views.py` `case_sources` (on its branch; the OpenAPI `CaseSource` shape) | AC-9 | **exact values added**: invoice source `ref == "invoices/INV-200037"`; `lookup_log_id == f"ll-{lookup_log.id}"`; `changed_note` `"No change since the snapshot"` before and `"Changed since the AI saw it"` after; `current_unavailable is False` | `test_case_view_snapshot_vs_current` |
| AC-19 "reaches the staff console at once" | `docs/plans/stage7-signoff.md` D-12 (accept the limit: no contract field for a P2 case booked more than 4 h ahead) | AC-19 | **in-ticket**: assert only the lane cases.md §5's lane rule gives (WP-4's 12:00 due is within `DUE_SOON_WINDOW` of 10:00 → Due soon); assert nothing for a later-booked P2 | AC-19 test (pass 2) |

---

## 4. Shared code to use (copied from the current code; exact names)

### Harness (main, `tests/journeys/support/`)

```python
# fixtures (registered by tests/conftest.py → tests.journeys.support.plugin)
journey: JourneyRun            # tests/journeys/support/run.py
journey_clock: StepClock       # the run's WALL clock; .advance(seconds); the demo clock does not move

# run.py
@dataclass(frozen=True)
class LoginResult:
    client: JourneyClient; response: httpx.Response; session_id: str; cookie: str
@dataclass
class JourneyRun:
    env: JourneyEnv; server: RunningServer; script: JourneyScript; models: Mapping[Role, ScriptedModel]
    clock: StepClock | None; db: DbReader; logs: LogTap; guard: SocketGuard; collector: StepCollector
    strict: bool; nodeid: str; clients: list[JourneyClient] = field(default_factory=list)
    # properties: settings, app, container, base_url, demo_username
    def secret_values(self) -> tuple[str, str]: ...            # (demo password, session secret)
    def client(self) -> JourneyClient: ...
    def login(self, client: JourneyClient | None = None) -> LoginResult: ...
    def step(self, journey: str, name: str, *, needs: Sequence[str] = (), operations: Sequence[str] = ()) -> ContextManager[None]
    def files_containing(self, value: str) -> list[str]: ...   # files under data_dir holding the bytes
    def close_clients(self) -> None: ...

# client.py
class JourneyClient:
    def __init__(self, base_url: str, *, transport: httpx.BaseTransport | None = None) -> None
    def call(self, method: str, path: str, *, operation_id: str | None, body: object | None = None,
             headers: Mapping[str, str] | None = None) -> httpx.Response   # runs assert_response_matches(response, operation_id)
    def cookie(self, name: str = "mhc_session") -> str | None
    responses: list[httpx.Response]

# env.py
PLACEHOLDER_ANTHROPIC_KEY = "journey-placeholder-anthropic-not-a-key"
PLACEHOLDER_OPENROUTER_KEY = "journey-placeholder-openrouter-not-a-key"
def journey_environ(root: Path) -> dict[str, str]: ...          # needs root/"data", root/"no-dist", root/"index"
@dataclass(frozen=True)
class JourneyEnv:
    root: Path; data_dir: Path; web_dist_dir: Path; index_dir: Path; settings: Settings; issued_sha256_before: str
    db_path: Path  # property = data_dir / WORKING_DB_NAME

# server.py
class StepClock: __call__() -> datetime; advance(seconds: float) -> None
def launch_server(settings: Settings, *, overrides: ContainerOverrides | None, startup_timeout_s: float = 30.0) -> ContextManager[RunningServer]
def socket_guard() -> ContextManager[SocketGuard]                # SocketGuard.blocked: list[tuple[str, int]]

# scripted_model.py
class JourneyScript: ...
def scripted_overrides(settings: Settings, script: JourneyScript, *, wall_clock: Callable[[], datetime] | None
                       ) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]

# db.py
class DbReader: rows(sql, params=()) / one / scalar / count(table, where="", params=()) / table_rows(table)
def issued_rows(table: str, issued_path: Path = ISSUED_DB) -> list[tuple[Any, ...]]
def sha256_file(path: Path) -> str

# logtap.py
class LogTap: structured(kind: str) -> list[dict]; wait_for(kind, predicate, *, timeout_s=2.0) -> dict; all_text() -> str
def tap_logs() -> ContextManager[LogTap]

# steps.py
NEED_OWNERS, OPERATION_OWNERS                                     # Mapping[str, str]
def missing_needs(container, app, needs: Sequence[str], operations: Sequence[str]) -> tuple[Missing, ...]
def blocked_message(missing: Sequence[Missing]) -> str
class StepCollector                                               # dataclass, no-arg constructor
```

### OpenAPI checks (`tests/api/openapi_check.py`, AEA-23)

```python
CONTRACT_URI = "urn:meridian:ui-contracts"
@dataclass(frozen=True)
class SseFrame: event: str | None; id: str | None; data: str
def assert_response_matches(response, operation_id: str) -> None
def assert_sse_frames_match(frames: Sequence[SseFrame], operation_id: str) -> None
def load_contract() -> Contract                                   # .registry for a "$ref" validator
```
ApiError body check for an undocumented 500: `Draft202012Validator({"$ref": f"{CONTRACT_URI}#/components/schemas/ApiError"},
registry=load_contract().registry)` (the same pattern `assert_sse_frames_match` uses; `jsonschema` is a dev dependency).

### Production names imported by the tests (read only)

```python
from meridian.adapters.sqlite.repos_cases import DEMO_START        # Fri 2026-10-16 10:00 America/Chicago
from meridian.adapters.sqlite.repos_cases_state import RecordsRepo  # .seed_event(row) — patched in AC-8's forced failure
from meridian.adapters.sqlite.rows import ConversationRow           # thread_id, demo_session, run_tag, agent_version,
                                                                    # started_at, started_wall_at, outcome, last_customer_wall_at, …
from meridian.adapters.checkpointer import Checkpointer             # .saver (SqliteSaver), .path, .prune(keep=2)
from meridian.config import Settings                                # Settings.from_env(environ)
from meridian.domain.common import ThreadId                         # ThreadId(str(uuid.uuid4()))
from meridian.domain.staff import CUSTOMER_SPEAKER_NAME, STAFF_PERSONAS, StaffRole   # "Customer"; Riley / Demo supervisor
from meridian.policy.handoff import PROMISE_TABLE, DUE_SOON_WINDOW   # PROMISE_TABLE["R26.staffed"], ["R26.unstaffed"]
from meridian.policy.texts import TEXTS, TextId                     # TextId.STAFFING_BANNER, RECORDED_NOT_SENT, DEMO_RESET
from meridian.services.health import AlertEvaluator, AlertSettings
from meridian.services.live_chat import CASE_EVENT_KIND, LiveChatService
from meridian.services.reset import SEED_CASES, ResetService        # SeedCase.ref, .customer_id
from meridian.services.reset_gate import ResetGate
from meridian.services.staff import FlagService, StaffSessionStore
from meridian.web.container import Container, ContainerError, Key
from meridian.web.deps import (CASE_SERVICE, DEMO_SERVICE, FLAG_SERVICE, HANDOFF_SERVICE, LIVE_CHAT, LOGIN_SESSIONS,
                               RESET_GATE, RESET_SERVICE, STAFF_ACCESS, UOW_FACTORY)
from meridian.web.logging import ALLOWED_FIELDS, RECORD_ATTR, AllowListFormatter
from meridian.services.cases import CaseService                 # on main since ef561fc (AEA-29)
from meridian.services.handoff import HandoffService            # on main since ef561fc (AEA-29)
# after AEA-30 merges (pass 1 starts only then):
from meridian.services.demo import DemoClock, DemoService
from meridian.services.scheduler import ERROR_KINDS, PROMISE_MISSED_KIND, SchedulerJob, SchedulerThread
```

### Sibling code read on the unmerged branches (confirm on `main` at Step 0.4; do not import from a branch)

Read 2026-10-21 from `aea-30-aea-30-demo-clock-sched` `e5c4ce4` (unchanged at the third pass) and
`aea-29-aea-29-cases-handoff` `b54fed9` (the AEA-29 lines below are now confirmed on main `c9b17ea`):

```python
# services/scheduler.py (AEA-30)
TICK_INTERVAL_S = 60.0; ABANDON_AFTER = timedelta(minutes=30)
ALERT_KINDS = ("overdue", "due_soon", "stuck_waiting", "unowned"); PROMISE_MISSED_KIND = "promise_missed"
ERROR_KINDS = ("alerts_failed", "sweep_failed", "prune_failed")
class JobRun(MeridianModel):  job_run_id: str; started_wall_at: datetime; finished_wall_at: datetime | None
    demo_now: datetime; status: Literal["started", "completed", "failed"]; error_kind: str | None
    overdue: int; promises_missed: int; due_soon: int; stuck_waiting: int; unowned: int; abandoned: int; pruned: int | None
class SchedulerJob:
    def __init__(self, uow, cases: object, clock: Clock, prune_checkpoints: Callable[[], int],
                 wall_clock: Callable[[], datetime] = _utc_now) -> None
    def tick(self) -> JobRun      # never raises for a step failure: status "failed", error_kind f"{step}_failed";
                                  # prunes once per Chicago wall day (self._pruned_on; the first tick of a process prunes)
class SchedulerThread:            # name="meridian-scheduler", daemon; ticks at once on start, then every 60 s
    def start(self) -> None; def stop(self, timeout_s: float = 5.0) -> None; alive: bool (property)
# overdue case_event: kind "overdue", key = due_at, actor_role "system", job_run_id set, detail {"due_at": key}
# missed promise: promises.status "missed" (reason "past_due") + case_event kind "promise_missed" with job_run_id

# web/container.py register_demo (AEA-30)
Key[DemoClock]("demo_clock") -> DemoClock(uow); deps.DEMO_SERVICE -> DemoService(uow, clock, DeferredCases(...),
  wall_clock=WALL_CLOCK); Key[SchedulerJob]("scheduler_job") -> SchedulerJob(uow, DeferredCases, clock,
  lambda: checkpointer.prune(keep=2), WALL_CLOCK); Key[SchedulerThread]("scheduler_thread") -> SchedulerThread(job.tick)
  # the thread starts in container.on_start and stops in container.on_close (before the checkpointer closes)

# services/demo.py (AEA-30)
BUSINESS_MORNING = time(7, 0)    # next_business_morning → 07:00 on the next business day (Chicago)
# advance_clock: became_overdue = open cases with old <= case due < new; one demo_events row
#   (kind "clock_advanced", step, demo_before/demo_after = format_wall(...), became_overdue, request_id, role)
# set_staffing: same mode → no row; else one demo_events row (kind "staffing_changed", mode, demo_before = old mode,
#   demo_after = new mode, converted_cases, request_id, role); on → off calls cases.convert_live_queued(now, tx)

# services/_case_actions.py (AEA-29): CON-13 case_event kind = f"action:{name}" → claim is "action:claim"
# services/_case_views.py (AEA-29): CaseSource.source_id = f"src-{lookup_log.id}", .lookup_log_id = f"ll-{lookup_log.id}";
#   invoice ref f"invoices/{invoice_id}"; current = {amount_cents, balance_cents, issued_date, due_date, appointment_id};
#   changed_note "No change since the snapshot" | "Changed since the AI saw it" (None only when current is None)
# CaseService(uow, clock, *, handoff_block=None, settled_view=None): both forwarders reach deps.REPLY_COMPOSER (AEA-51)
#   and are called only by convert_live_queued, i.e. only when a live-queued case exists (pass 2).
```

`AlertEvaluator` constructor on main (copy exactly):
`AlertEvaluator(uow, ledger, settings: AlertSettings, wall_clock: Callable[[], datetime], daily_cap_usd: float, *, agent_version: str)`;
the test passes `run.container.get(UOW_FACTORY)`, `run.container.get(Key[Any]("ledger"))`, `AlertSettings()`, its own
clock, `run.container.limits.spend.daily_cap_usd`, `agent_version=run.settings.agent_version`. Its stale rule writes
`health_events(kind="alert_fired", alert_type="scheduler_stale", reason_code="scheduler_tick_missed")` once.

### Wire paths and bodies (OpenAPI; every call names its operationId)

| op | method, path | body / note |
|---|---|---|
| `login` / `logout` | POST `/api/login` / POST `/api/logout` | `journey.login()` does login; logout 204 |
| `getSession` | GET `/api/session` | |
| `switchRole` | PUT `/api/session/role` | `{"role": "representative" \| "supervisor" \| "owner" \| "customer"}` |
| `startChatSession` | POST `/api/chat/sessions` | → 201 `thread_id` (pass 2) |
| `getChatThread` | GET `/api/chat/sessions/{thread_id}` | pass 2 |
| `submitTurn` | POST `/api/chat/sessions/{thread_id}/turns` | `{"turn_id": uuid4, "payload": {"kind": "text", "text": "…"}}` |
| `streamChatEvents` | GET `/api/chat/sessions/{thread_id}/events` | SSE; `Last-Event-ID` header |
| `requestPerson` | POST `/api/chat/sessions/{thread_id}/handoff` | `{"turn_id": uuid4}` → `result` `live_queued` / `case_created`, `block.reference` |
| `getStaffing` / `setStaffing` | GET / PUT `/api/demo/staffing` | `{"mode": "nobody_online" \| "simulated_on_shift"}` → `mode, label, converted_cases` |
| `getDemoClock` / `advanceDemoClock` | GET / POST `/api/demo/clock` | `{"step": "plus_1h" \| "plus_4h" \| "next_business_morning"}` → `now, label, became_overdue` |
| `resetDemo` | POST `/api/demo/reset` | `{"confirm": true}` → `ok, open_chats_ended, roles_reset, clock` |
| `getQueue` | GET `/api/staff/queue` | `as_of, staffing{mode,label,banner}, live[], needs_my_action[]` |
| `getCase` | GET `/api/staff/cases/{reference}` | `case` (CaseSummary: `version`, `due_at`, `promise_status`, `allowed_actions`, …), `promise`, `brief{status, headings}`, `sources[]`, `conversation[]`, `live`, … |
| `applyCaseAction` | POST `/api/staff/cases/{reference}/actions` | `{"action", "expected_version", "reason"?, "wake_up_at"?, "outcome"?, "assignee"?, "priority"?}` → `case`, `result_line` |
| `liveChatAction` | POST `/api/staff/cases/{reference}/live` | `{"action": "join"\|"send"\|"hand_back"\|"close", "text"?}` |
| `streamCaseEvents` | GET `/api/staff/cases/{reference}/events` | SSE |
| `recordContactActivity` | POST `/api/staff/cases/{reference}/activities` | `{"kind": "call"\|"email", "outcome": "reached"\|"no_answer"\|"left_message", "note": null, "expected_version"}` → 201 |
| `createFlag` | POST `/api/staff/flags` | `{"case_ref", "target": "answer"\|"brief"\|"escalation", "message_id"?, "note"?, "reason"?}` → 201 `Flag` |
| `listFlags` | GET `/api/staff/flags` | `as_of, flags[]` |
| `reviewFlag` | PATCH `/api/staff/flags/{flag_id}` | `{"status": "reviewed", "note"?}` |
| `getOversight` | GET `/api/staff/oversight` | `staffing, alerts, lanes{p0_p1, overdue, due_soon, unowned, stuck_waiting}{count, rows}, live_queue_length, new_flags_count` |
| `getMonitoring` | GET `/api/monitoring` | `health[]` Tile `id` (pass 2, AEA-53) |

x-roles in their order (for `details.needs`): `getQueue` [representative, supervisor]; `getCase` [representative,
supervisor, owner]; `applyCaseAction` [representative, supervisor]; `liveChatAction` [representative];
`streamCaseEvents` [representative, supervisor, owner]; `recordContactActivity` [representative]; `createFlag`
[representative, supervisor]; `listFlags` [representative, supervisor, owner]; `reviewFlag` [supervisor];
`getOversight` [supervisor]; `advanceDemoClock` [supervisor]. `assign`/`change_priority` by a representative →
`needs: ["supervisor"]`.

Persona strings: Riley = `STAFF_PERSONAS[StaffRole.REPRESENTATIVE].name` ("Riley"), signature "Riley (demo)";
supervisor name and signature "Demo supervisor".

### Seed facts (cases.md §7; `meridian.services.reset.SEED_CASES`)

| Ref | Reason, priority | Customer | Case due = promise due | State at `DEMO_START` |
|---|---|---|---|---|
| MHC-C-0005 | refund, P3; lookup INV-200037 | MHC-94339 | Thu 2026-10-15 19:00 | unassigned, Overdue lane |
| MHC-C-0006 | complaint_or_manager, P3 | MHC-39394 | Mon 2026-10-19 19:00 | unassigned, Unowned lane |
| MHC-C-0007 | billing_dispute, P3; INV-204411 | MHC-10002 | Mon 2026-10-19 19:00 | unassigned, Unowned lane |
| MHC-C-0008 | safety, P0 | none | no due | P0 and P1 lane |

Live cases number from MHC-C-0009.

---

## 5. Steps

The slice stays in the test tree. Interfaces consumed: the HTTP API (CON-1…CON-22), the container keys in
`web/deps.py`, and the DO-4/addendum service signatures above. No seam or abstraction is added to `src/`.

### Step 0 — readiness checks (before any file is written; stop and report if one fails)

0.1 `git -C /home/linuxuser/workspaces/inno-aea-callcenter log --oneline -1 main`; branch from main as
   `aea-52-aea-52-staff-demo-integ` (worktree per the orchestrator). `export UV_LINK_MODE=hardlink`; never copy a venv.

0.2 **Pass 1 is buildable** only when all exist on main: `src/meridian/services/cases.py`, `services/handoff.py`,
   `services/demo.py`, `services/scheduler.py`, `web/routes/staff_cases.py`, `web/routes/demo.py`. Check with
   `ls` on each path. Missing → report `blocked-on` the owner (29, 29, 30, 30, 45, 43) and stop. (At `68b1412` all six
   are missing: 29, 30 and 43 are built on branches, 45 is not started. At `c9b17ea` three are missing:
   `services/demo.py` and `services/scheduler.py` (AEA-30, branch `e5c4ce4`) and `web/routes/staff_cases.py` (AEA-45,
   branch `ea00827`).) Also confirm both registrations are live, not stubs:
   `sed -n '/^def register_demo(/,/^def register_reset(/p' src/meridian/web/container.py | grep -c 'container.provide('`
   ≥ 1 (0 at `c9b17ea`: AEA-30's no-op) and `grep -c 'staff_cases_routes_included' src/meridian/web/container.py` ≥ 1
   (0 at `c9b17ea`). Either 0 → stop: blocked-on AEA-30 / AEA-45.

0.3 **Pass 2 is buildable** only when additionally: `src/meridian/services/session.py` exists (AEA-40 CON-1), and the
   body of `register_graph` in `src/meridian/web/container.py` contains `container.provide(` for the keys
   `reply_composer` and `run_graph` (AEA-51). Check with
   `sed -n '/^def register_graph/,/^def register_frontend/p' src/meridian/web/container.py | grep -n 'provide\|reply_composer\|run_graph'`.
   WP-7 / WP-4 variants also need AEA-51's script module (§8 R-3); `test_stale_tick_shows_as_health_tile` needs
   `metrics_reads` bound (AEA-53). Build only the tests whose needs pass; list the rest as `not built: blocked-on …`.

0.4 Confirm on `main` the sibling names §4 lists (they were read from unmerged branches). Run:
   `grep -n 'Key\[SchedulerJob\]("scheduler_job")\|Key\[SchedulerThread\]("scheduler_thread")' src/meridian/web/container.py`
   (2 hits); `grep -n 'PROMISE_MISSED_KIND\|ERROR_KINDS\|name: str = "meridian-scheduler"' src/meridian/services/scheduler.py`
   (3+ hits); `grep -n 'kind=f"action:{name}"' src/meridian/services/_case_actions.py` (1 hit);
   `grep -n 'f"ll-{r.id}"\|"Changed since the AI saw it"' src/meridian/services/_case_views.py` (2+ hits). (The two
   AEA-29 greps already pass at `c9b17ea`; the AEA-30 greps are the ones that matter.)
   A miss means the owner changed the name before merging: use main's name, say so in the report, and keep the
   assertion's meaning. If `register_demo` provides **no** key for `SchedulerJob` or `SchedulerThread`, stop:
   blocked-on AEA-30. If `SchedulerJob.tick()` re-raises step failures instead of returning `status="failed"`, wrap the
   AC-25 failure tick in `pytest.raises` and read the `failed` row from `job_runs`; report it.

### Step 1 — pass 1 (seeds, demo controls, scheduler, reset, J-8, J-6 seed leg)

**1.1 `tests/integration/staff_support.py`** (≤ 300 lines; split into a second helper file if it grows). Module
docstring: "AEA-52 helpers: real app on AEA-57's harness; no doubles, no dependency overrides." Contents, exactly:

```python
CHICAGO = ZoneInfo("America/Chicago")
SEED_REFS: tuple[str, ...] = ("MHC-C-0005", "MHC-C-0006", "MHC-C-0007", "MHC-C-0008")
ISSUED_TABLES: tuple[str, ...] = ("customers", "technicians", "appointment_slots", "appointments", "invoices")
KEPT_TABLES: tuple[str, ...] = ("spend_ledger", "health_events", "deploy_records", "eval_runs", "job_runs", "demo_events")
SCHEDULER_JOB: Key[Any] = Key("scheduler_job")            # AEA-30 register_demo (Step 0.4 confirms)
SCHEDULER_THREAD_KEY: Key[Any] = Key("scheduler_thread")  # AEA-30 register_demo → SchedulerThread (.alive, .stop())
SCHEDULER_THREAD = "meridian-scheduler"                    # SchedulerThread's default thread name
OVERDUE_KIND = "overdue"; CLAIM_KIND = "action:claim"      # PROMISE_MISSED_KIND is imported from meridian.services.scheduler
X_ROLES: Mapping[str, tuple[str, ...]] = {...}            # the x-roles table in §4, keyed by operationId
P1_NEEDS = ("login_sessions", "staff_access", "flag_service", "case_service", "handoff_service", "demo_service",
            "demo_clock", "live_chat", "reset_service", "reset_gate", "checkpointer", "uow_factory", "wall_clock", "ledger")
P1_OPERATIONS = ("getSession", "switchRole", "getQueue", "getCase", "applyCaseAction", "liveChatAction",
                 "streamCaseEvents", "recordContactActivity", "createFlag", "listFlags", "reviewFlag", "getOversight",
                 "getStaffing", "setStaffing", "getDemoClock", "advanceDemoClock", "resetDemo")
P2_NEEDS = ("session_service", "person_requests", "reply_composer")
P2_OPERATIONS = ("startChatSession", "getChatThread", "requestPerson", "streamChatEvents")

@dataclass(frozen=True)
class Actor:
    client: JourneyClient; session_id: str; cookie: str; role: str

def assert_bound(run: JourneyRun, needs: Sequence[str], operations: Sequence[str]) -> None:
    """FAILS (never skips) with blocked_message(missing) when a need or route is missing; also gets SCHEDULER_JOB and
    SCHEDULER_THREAD_KEY directly (they are not in AEA-57's NEED_OWNERS) and fails "blocked-on AEA-30" if either is unbound."""
def sign_in(run: JourneyRun, role: str = "customer") -> Actor          # run.login(); switch_role when role != customer
def switch_role(actor: Actor, role: str) -> Actor                       # PUT /api/session/role; assert 200 and body role
def call(actor: Actor, method: str, path: str, op: str, body: object | None = None,
         headers: Mapping[str, str] | None = None) -> httpx.Response     # actor.client.call(..., operation_id=op)
def error_of(response: httpx.Response) -> dict[str, Any]                # response.json()["error"]
def case_view(actor: Actor, ref: str) -> dict[str, Any]                 # getCase; assert 200
def version_of(actor: Actor, ref: str) -> int                           # case_view(...)["case"]["version"]
def act(actor: Actor, ref: str, action: str, *, version: int | None = None, **fields: object) -> httpx.Response
def live(actor: Actor, ref: str, action: str, text: str | None = None) -> httpx.Response
def set_staffing(actor: Actor, mode: str) -> httpx.Response             # setStaffing; assert 200
def advance(actor: Actor, step: str) -> httpx.Response                  # advanceDemoClock
def reset_demo(actor: Actor) -> httpx.Response                          # resetDemo {"confirm": True}
def demo_now(actor: Actor) -> datetime                                  # getDemoClock → parse "now"
def parse_dt(value: str) -> datetime                                    # datetime.fromisoformat; assert tz-aware
def scheduler_job(run: JourneyRun) -> Any                               # run.container.get(SCHEDULER_JOB)
def seed_contact_values(run: JourneyRun) -> tuple[str, ...]             # phone, email, service_address of SEED_CASES customers
def seed_customer_names(run: JourneyRun) -> tuple[str, ...]             # name of SEED_CASES customers
def write_working_copy(run: JourneyRun, sql: str, params: Sequence[object] = ()) -> None
    """Test-only edit of the DISPOSABLE working copy (simulates an outside change). sqlite3.connect(run.env.db_path,
    timeout=5.0); execute; commit; close. Never used on the issued file."""
def tree_digest(path: Path) -> str                                      # sha256 over sorted (relative path, bytes); skips
                                                                        # __pycache__; a missing dir hashes "missing:<path>"
def sentinel(label: str) -> str                                         # f"aea52-{label}-{secrets.token_hex(8)}"
def card_like_number() -> str                                           # 16 random digits from secrets, grouped "dddd dddd dddd dddd"
@contextmanager
def open_staff_run(*, extra_env: Mapping[str, str] = MappingProxyType({}), strict: bool, nodeid: str
                   ) -> Iterator[JourneyRun]: ...
```

`open_staff_run` body, in order (it reproduces `open_journey` with an environment extension, because AC-1 must see the
server stop and AC-23/24/26 need sentinel key values; it never edits `support/`):
1. `with socket_guard() as guard, tap_logs() as logs:` (both from support).
2. `root = Path(tempfile.mkdtemp(prefix="meridian-aea52-"))`; make `root/"data"`, `root/"no-dist"`, `root/"index"`.
3. `settings = Settings.from_env({**journey_environ(root), **extra_env})`; if
   `Path(settings.issued_db_path).resolve() != ISSUED_DB.resolve()` raise `RuntimeError` (same text as support/env.py).
4. `before = sha256_file(ISSUED_DB)`; `env = JourneyEnv(root, root/"data", root/"no-dist", root/"index", settings, before)`.
5. `script = JourneyScript()`; `clock = StepClock()`; `overrides, models = scripted_overrides(settings, script, wall_clock=clock)`.
6. `with launch_server(settings, overrides=overrides) as server:` build `JourneyRun(env=env, server=server,
   script=script, models=models, clock=clock, db=DbReader(env.db_path), logs=logs, guard=guard,
   collector=StepCollector(), strict=strict, nodeid=nodeid)`; `yield run`; `finally: run.close_clients()`.
7. After the server block: `assert sha256_file(ISSUED_DB) == before`; `finally: shutil.rmtree(root, ignore_errors=True)`.
8. After the guard block: `assert not guard.blocked` (same rule as `open_journey`).

**1.2 `tests/integration/staff_streams_support.py`** (≤ 200 lines):

```python
@dataclass(frozen=True)
class StreamRead:
    status: int; frames: tuple[SseFrame, ...]; closed_by_server: bool; response: httpx.Response
def parse_sse(lines: Iterable[str]) -> Iterator[SseFrame]
    # "id: X" → id; "event: Y" → event; "data: Z" → data (several data lines joined by "\n"); a line starting with ":"
    # is a comment (heartbeat) and is ignored; a blank line ends a frame (emit only when data was seen).
def read_stream(base_url: str, cookie: str, path: str, *, last_event_id: str | None = None,
                idle_s: float = 3.0, max_s: float = 20.0) -> StreamRead
    # httpx.Client(base_url, cookies={"mhc_session": cookie}, timeout=httpx.Timeout(connect=5.0, read=idle_s,
    # write=5.0, pool=5.0)); headers {"Last-Event-ID": last_event_id} when given; client.stream("GET", path).
    # status != 200 → resp.read(); return StreamRead(status, (), True, resp).
    # 200 → iterate resp.iter_lines() through parse_sse; end of iteration → closed_by_server=True;
    # httpx.ReadTimeout → closed_by_server=False (the server kept it open for idle_s with nothing new);
    # stop after max_s wall seconds → closed_by_server=False.
class BackgroundStream:
    def __init__(self, base_url: str, cookie: str, path: str, *, last_event_id: str | None = None, max_s: float = 30.0)
    def start(self) -> None          # daemon thread calling read_stream(..., idle_s=max_s, max_s=max_s)
    def join(self, timeout: float = 15.0) -> StreamRead
```
Callers validate: `assert_response_matches(read.response, op)` when `read.status != 200`, and
`assert_sse_frames_match(read.frames, op)` when 200 (`op` = `"streamCaseEvents"` or `"streamChatEvents"`).

**1.3 `test_staff_composition.py::test_real_objects_bound` (AC-1).**
1. `with open_staff_run(strict=…, nodeid=request.node.nodeid) as run:` (`request` fixture for the nodeid; `strict`
   from `request.config.getoption("--journeys-strict")`).
2. `assert_bound(run, P1_NEEDS, P1_OPERATIONS)`; `assert run.app.dependency_overrides == {}`.
3. Table check (print each row): `LOGIN_SESSIONS` and `STAFF_ACCESS` → the **same** `StaffSessionStore` instance;
   `FLAG_SERVICE` → `FlagService`; `CASE_SERVICE` → `CaseService`; `HANDOFF_SERVICE` → `HandoffService`; `LIVE_CHAT`
   → `LiveChatService`; `DEMO_SERVICE` → `DemoService`; `Key("demo_clock")` → `DemoClock`; `SCHEDULER_JOB` →
   `SchedulerJob`; `SCHEDULER_THREAD_KEY` → `SchedulerThread`; `RESET_SERVICE` → `ResetService`; `RESET_GATE` →
   `ResetGate`; `Key("checkpointer")` → `Checkpointer`. Use `type(obj) is Cls` (not a double, not a subclass).
4. Thread: `thread = run.container.get(SCHEDULER_THREAD_KEY)`; `thread.alive is True`; exactly one alive thread named
   `SCHEDULER_THREAD` in `threading.enumerate()`.
5. Seam row 7 by behaviour (§3 reconciliation): `sup = sign_in(run, "supervisor")`; `set_staffing(sup,
   "simulated_on_shift")` → 200; `set_staffing(sup, "nobody_online")` → 200 with `converted_cases == 0` (the on → off
   path resolves `case_service`; unbound it answers 500).
6. After the `with` block (keep `thread` from step 4): poll up to 5 s until `thread.alive is False` and no alive thread
   named `SCHEDULER_THREAD` remains; assert both.
Pass 2 adds rows `Key("session_service")` → `SessionService`, `Key("turn_service")` → `TurnService`.

**1.4 `test_staff_composition.py::test_role_and_state_refusals` (AC-5).** Uses `journey`. `assert_bound`. Sessions:
`rep = sign_in(journey, "representative")`, `sup = sign_in(journey, "supervisor")`, `owner = sign_in(journey,
"owner")`, `cust = sign_in(journey)`, `anon = journey.client()`. Every call goes through `call(...)` (OpenAPI-checked).
1. Owner: `getCase MHC-C-0006` → 200 and `case.allowed_actions == []`. Owner on `applyCaseAction` (claim, current
   version), `liveChatAction` (join), `recordContactActivity` (call/no_answer, current version), `createFlag`
   (MHC-C-0006, target brief), `reviewFlag` (`flg-1`, status reviewed), `advanceDemoClock` (plus_1h) → each 403
   `ROLE_NOT_ALLOWED`, `details == {"role": "owner", "needs": list(X_ROLES[op]), "reason": "wrong_role"}`.
2. Representative: `advanceDemoClock` plus_1h and `reviewFlag flg-1` → 403, `needs == ["supervisor"]`.
3. Customer on every staff route (`getQueue`, `getCase`, `applyCaseAction`, `liveChatAction`, `streamCaseEvents`,
   `recordContactActivity`, `createFlag`, `listFlags`, `reviewFlag`, `getOversight`, `advanceDemoClock`) → 403,
   `details == {"role": "customer", "needs": list(X_ROLES[op]), "reason": "wrong_role"}`. (`streamCaseEvents` answers
   403 as JSON before any stream starts, so `call` works.)
4. Version conflict: `v = version_of(sup, "MHC-C-0006")`; supervisor `change_priority` (`priority "P2"`, reason
   "Synthetic priority reason.", version v) → 200; Riley `claim` with `expected_version=v` → 409
   `VERSION_CONFLICT`; `set(details) == {"changed_by", "changed_at", "current_version"}`, `changed_by == "Demo
   supervisor"`, `current_version == v + 1`.
5. Supervisor claims MHC-C-0007 → 200; Riley claims MHC-C-0007 (fresh version) → 409 `CASE_ALREADY_CLAIMED`,
   `details.claimed_by == "Demo supervisor"`.
6. Riley `join` MHC-C-0005 (unowned) → 403 `NOT_CLAIMED_BY_YOU`, `details == {"owner": None}`.
7. Riley `join` MHC-C-0007 (supervisor's) → 409 `CASE_ALREADY_CLAIMED`, `details.claimed_by == "Demo supervisor"`.
8. Riley `send` on MHC-C-0005 with `text="   "` → 400 `VALIDATION_ERROR`, `field == "text"`; with
   `text = "x" * 2001` → 400, `field == "text"`, and the 2001-character string is **not** in `response.text`.
9. `anon` `getQueue` → 401 `UNAUTHENTICATED`, `details == {"reason": "none"}`.

**1.5 `test_staff_composition.py::test_least_privilege_matrix` (AC-21).** Uses `journey`. Four sessions (rep, sup,
owner, customer). Probe requests that leave no lasting state change except a flag (all bodies valid):

| op | probe |
|---|---|
| getQueue | GET |
| getCase | GET MHC-C-0006 |
| applyCaseAction | MHC-C-0006 `{"action": "claim", "expected_version": 999999}` |
| liveChatAction | MHC-C-0006 `{"action": "join"}` |
| recordContactActivity | MHC-C-0006 `{"kind": "call", "outcome": "no_answer", "note": null, "expected_version": 999999}` |
| createFlag | `{"case_ref": "MHC-C-0006", "target": "brief"}` |
| listFlags | GET |
| reviewFlag | PATCH `flg-999999` `{"status": "reviewed"}` |
| getOversight | GET |

For each role × op: `refused = status == 403 and error code == "ROLE_NOT_ALLOWED"`. Assert `refused == (role not in
X_ROLES[op])`. Additionally assert: owner `getCase` and `listFlags` are 200; representative is refused on
`getOversight` and `reviewFlag`; customer refused on the eight case operations of §3. Print the role × op status table
(`print`, shown with `-s`/`-rA`). Contact values: `values = seed_contact_values(journey)`; none appears in the
`response.text` of `getQueue` (rep and sup) or `getOversight` (sup); print "0 contact-value hits".

**1.6 `test_staff_composition.py::test_staff_routes_never_open_cases` (AC-13 twin).** For every file matching
`src/meridian/web/routes/staff_*.py`, assert `"open_case"` not in its text. (Also run the AC-13 grep command in §7.)

**1.7 `test_demo_reset.py`.**

`test_reset_all_or_nothing` (AC-8, uses `journey`, `monkeypatch`):
1. Sessions rep, sup. Riley claims MHC-C-0006; Riley `createFlag` MHC-C-0005 target brief → keep `flag_id`;
   supervisor `advance plus_1h`; supervisor `set_staffing("simulated_on_shift")`.
2. Before counts: `{t: journey.db.count(t) for t in KEPT_TABLES}`; `reset_events` and `seed_events` counts;
   `staff_sessions` row count; `non_customer = journey.db.count("staff_sessions", "role != 'customer'")`.
3. Gate held: `gate = journey.container.get(RESET_GATE)`; `with gate.hold():` (a) customer client `submitTurn` on
   path `/api/chat/sessions/{uuid4}/turns` with body `{"turn_id": str(uuid4()), "payload": {"kind": "text", "text":
   "hello"}}` → 503 `RESET_IN_PROGRESS`, `details.retry_after_ms == 5000`; (b) Riley `reset_demo` → 409
   `RESET_IN_PROGRESS`.
4. Riley `reset_demo` → 200: `ok is True`, `roles_reset == non_customer`, `open_chats_ended == 0`,
   `parse_dt(clock["now"]) == DEMO_START`. Keep `rid = response.headers["X-Request-ID"]`.
5. After: for each `t` in `ISSUED_TABLES`: `journey.db.table_rows(t) == issued_rows(t)`. `cases` refs (sorted) ==
   `SEED_REFS`; `flags` count 0; `activities` count 0; `demo_state`: `demo_now` parses to `DEMO_START`, `staffing ==
   "nobody_online"`; `getDemoClock` now == `DEMO_START`; `conversations` rows all `run_tag == 'seed'`.
6. Riley `getQueue` → 403 `ROLE_NOT_ALLOWED`, `details.reason == "role_reset"`, `details.role == "customer"`;
   `getSession` → 200 role customer; `staff_sessions` row count unchanged.
7. Supervisor: `getQueue` → 403 `role_reset`; `switch_role(sup, "supervisor")`; `reviewFlag {flag_id}` → 404
   `FLAG_NOT_FOUND`.
8. `reset_events`: one new row; `asked_by_role == "representative"`, `asked_by_session == rep.session_id`,
   `request_id == rid`. `seed_events`: one new row with `reset_id` equal to it and `seed_count == 4`.
9. Kept tables: `spend_ledger`, `deploy_records`, `eval_runs`, `demo_events` counts equal before; `job_runs` and
   `health_events` counts `>=` before (background threads may add rows; none is deleted).
10. Forced failure: `switch_role(rep, "representative")`; supervisor `advance plus_1h` → note `demo_now`; Riley flags
    MHC-C-0005 again; `write_working_copy(run, "UPDATE invoices SET balance_cents = balance_cents + 1000 WHERE
    invoice_id = ?", ("INV-200037",))`; note counts of `cases`, `flags`, `reset_events`, and the invoice row.
    `monkeypatch.setattr(RecordsRepo, "seed_event", boom)` where `boom` raises `RuntimeError("forced reset failure")`.
    Riley `reset_demo` → 500 `RESET_FAILED` (documented). Then: invoice row still has the +1000 (restore rolled back);
    flags, cases and `reset_events` counts unchanged; `demo_state.demo_now` unchanged; Riley `getQueue` → 200 (role
    not reset). `monkeypatch.undo()`.

`test_reset_makes_no_outbound_connection` (AC-27): sessions rep; Riley claims MHC-C-0006 (so the reset has work);
`before = list(journey.guard.blocked)`; `reset_demo` → 200; `assert journey.guard.blocked == before == []`; print "0
connection attempts".

**1.8 `test_staff_streams.py` (pass 1 tests).**

`test_case_stream_after_reset` (AC-14): rep; Riley claims MHC-C-0005 (a `case_changed` lands on `case:MHC-C-0005`).
`first = read_stream(base, rep.cookie, "/api/staff/cases/MHC-C-0005/events")` → 200, frames contain one
`case_changed`; `last_id = first.frames[-1].id`. Riley `reset_demo` → 200. Riley `switch_role(rep,
"representative")` (the reset made it customer). `fresh = read_stream(..., last_event_id=None)` → 200, no frame with
`event == "demo_reset"`, `closed_by_server is False`. `resumed = read_stream(..., last_event_id=last_id)` → frames ==
exactly one `demo_reset`, `closed_by_server is True`; `journey.logs.wait_for("stream_reconnect", lambda r:
r.get("case_ref") == "MHC-C-0005")`. Validate frames with `assert_sse_frames_match(..., "streamCaseEvents")`. Print
both frame lists.

`test_staff_banner_follows_staffing` (AC-20): rep, sup. Supervisor `set_staffing("simulated_on_shift")`; `banner =
getStaffing(...)["banner"]`; assert `banner == TEXTS[TextId.STAFFING_BANNER]`. Riley `getQueue` →
`staffing.mode == "simulated_on_shift"`, `staffing.banner == banner`; supervisor `getOversight` → same. Supervisor
`set_staffing("nobody_online")` → Riley `getQueue`: `staffing.banner is None`, `live == []`; supervisor
`getOversight`: `staffing.banner is None`, `live_queue_length == 0`; no row in `needs_my_action` or any lane has
`lifecycle == "live_queued"`. Print the `staffing` objects, `live`, `live_queue_length` per mode.

**1.9 `test_staff_cases.py` (pass 1 tests).**

`test_case_view_snapshot_vs_current` (AC-9), `@pytest.mark.parametrize("variant", ["seed_invoice"])` (pass 2 adds
`"wp4_appointment"`): rep. `view = case_view(rep, "MHC-C-0005")`: `view["case"]["due_at"]` and
`view["promise"]["due_at"]` both present and both parse to Thu 2026-10-15 19:00 Chicago (refund: case due = promise
due); the source `s` with `s["ref"] == "invoices/INV-200037"` has dict `snapshot`, dict `current`, `changed_since is
False`, `changed_note == "No change since the snapshot"`, `current_unavailable is False`. Every `source_ids` entry of
every brief item (`view["brief"]["headings"][*]["items"][*]["source_ids"]`) is in `{x["source_id"] for x in
view["sources"]}`; every source those entries name has `lookup_log_id` of the form `"ll-<n>"` and
`journey.db.count("lookup_log", "id = ?", (int(lookup_log_id.removeprefix("ll-")),)) == 1`. Then
`write_working_copy(journey, "UPDATE invoices SET balance_cents = balance_cents + 1000 WHERE invoice_id = ?",
("INV-200037",))`; re-read: same source `changed_since is True`, `changed_note == "Changed since the AI saw it"`,
`current["balance_cents"] == before_current["balance_cents"] + 1000`, `snapshot == before_snapshot`. Print snapshot,
current, marker.

`test_contact_attempt_recorded_not_sent` (AC-10), `parametrize("variant", ["seeds"])` (pass 2 adds `"wp7"`): rep.
Riley claims MHC-C-0006 and MHC-C-0007. Riley `recordContactActivity` MHC-C-0006 `{"kind": "call", "outcome":
"left_message", "note": None, "expected_version": version_of(...)}` → 201: `activity.label ==
TEXTS[TextId.RECORDED_NOT_SENT]` ("Demo: recorded, not sent"), `activity.outcome == "left_message"`,
`case.promise_status == "kept"`; DB `promises` row for MHC-C-0006 `status == 'kept'`; `activities` row `actor_role ==
'representative'`. MHC-C-0007 with `"no_answer"` → 201, `case.promise_status == "open"`, DB promise `open`. Demo now
(Fri 10:00) is before the promise due (Mon 19:00). `assert journey.guard.blocked == []`. Print activity rows.

`test_flag_review_changes_nothing_else` (AC-11): dirs = `eval/cases`, `src/meridian/agent/prompts`,
`docs/data/issued/meridian_dataset/knowledge_base`, `journey.env.index_dir` (repo-root relative via
`Path(__file__).resolve().parents[2]`). `before = {d: tree_digest(d)}`; `staff_rows = journey.db.count("case_events",
"actor_role IN ('representative','supervisor')")`. Riley `createFlag` MHC-C-0005 target brief reason "Synthetic reason
one" → 201 (`f1`); Riley `createFlag` MHC-C-0006 target escalation → 201 (`f2`). Supervisor `listFlags` → `flags[0].flag_id
== f2`, `flags[1].flag_id == f1`. Supervisor `reviewFlag f1 {"status": "reviewed", "note": "Reviewed in test"}` → 200,
`status == "reviewed"`, `reviewed_by == "Demo supervisor"`. After: digests equal; `flags` count 2; staff
`case_events` count unchanged. Print the review list.

**1.10 `test_staff_allowed_actions.py::test_listed_iff_accepted_per_role` (AC-16)**,
`parametrize("source", ["seed_mhc_c_0007"])` (pass 2 adds `"live_claimed_joined"`, `"wp7_claimed_joined"`).

Constants in the test file:
```python
OPERATION_KEYS = {"applyCaseAction": ("claim", "release", "start", "wait", "resolve", "close_unresolved", "assign", "change_priority"),
                  "liveChatAction": ("join_chat", "send_live_message", "hand_back", "close_chat"),
                  "recordContactActivity": ("log_call", "log_email"), "createFlag": ("flag",)}
LIVE_OR_CONTACT = {"claim_and_join", "join_chat", "send_live_message", "hand_back", "close_chat", "log_call", "log_email"}
REFUSAL_CODES = {"ROLE_NOT_ALLOWED", "NOT_ALLOWED_IN_STATE", "CASE_ALREADY_CLAIMED", "NOT_CLAIMED_BY_YOU", "NOT_LIVE"}
```
`send_key(actor, ref, key, *, version, now) -> list[httpx.Response]` maps a key to its request(s):
claim/start → `act(…, action)`; release, close_unresolved → `reason="Synthetic reason."`; wait → `wake_up_at = (now +
timedelta(days=1)).isoformat()`; resolve → `outcome="Resolved by the integration test."`; assign → `assignee="riley",
reason=…`; change_priority → `priority="P2", reason=…`; join_chat/send_live_message/hand_back/close_chat → `live(…,
"join"/"send" with text "Synthetic staff reply."/"hand_back"/"close")`; log_call/log_email → activity
`{"kind": "call"/"email", "outcome": "reached", "note": None, "expected_version": version}`; flag → `createFlag
{"case_ref": ref, "target": "brief"}`; claim_and_join → claim then join (two responses).

Algorithm for `seed_mhc_c_0007`, per role in (representative, supervisor, owner):
1. `fresh()` = Riley `reset_demo` (→ 200), then `switch_role` every session back to its role. (≤ 6 resets per test,
   under `resets_per_ip` = 10.)
2. `fresh()`; `listed = case_view(role_actor, "MHC-C-0007")["case"]["allowed_actions"]`. Owner: `listed == []`.
   Supervisor: `not (set(listed) & LIVE_OR_CONTACT)`.
3. For each key in `listed`: `fresh()`; read version and `demo_now`; `send_key` → every response 2xx (print key ✓).
4. For each op in `OPERATION_KEYS`: the first key of that op not in `listed` (skip the op if none): `fresh()`;
   `send_key` → status in (403, 409) and `error.code in REFUSAL_CODES` (print key ✗ with code).

**1.11 `tests/capture/test_cap5_clock_and_scheduler.py` (pass 1 tests).** Module helper
`drive_seed_clock(sup: Actor) -> list[httpx.Response]`: advances `next_business_morning`, `plus_4h`, `plus_4h`,
`plus_4h`, `plus_1h` (Fri 10:00 → Mon 07:00 → 11:00 → 15:00 → 19:00 → 20:00) and returns the five responses. Module
helper `stale_check(run) -> int`: `now_fn = run.clock if run.clock is not None else (lambda: datetime.now(UTC))`;
build `AlertEvaluator(run.container.get(UOW_FACTORY), run.container.get(Key[Any]("ledger")), AlertSettings(),
lambda: now_fn() + timedelta(seconds=181), run.container.limits.spend.daily_cap_usd,
agent_version=run.settings.agent_version)` (§4); `evaluate()`; return `run.db.count("health_events", "kind =
'alert_fired' AND alert_type = 'scheduler_stale'")`. (The lambda reads the clock when `evaluate()` runs, so a runner tick
between our last tick and the evaluation cannot make the newest run look fresh.)

`test_clock_past_due_and_scheduler` (AC-6), `parametrize("variant", ["seeds"])` (pass 2 adds `"wp4"`):
1. sup. `responses = drive_seed_clock(sup)`: `became_overdue` == `[0, 0, 0, 0, 2]`; the last `now` parses to Mon
   2026-10-19 20:00 Chicago.
2. `demo_events` rows (`ORDER BY at_wall, rowid`): 5 rows, `kind == 'clock_advanced'`, `step` in order,
   `demo_before`/`demo_after` chained, `became_overdue` as above, `request_id` == each response's `X-Request-ID`,
   `role == 'supervisor'`.
3. `job = scheduler_job(journey)`; `run1 = job.tick()`; `run1.status == "completed"`; its `job_runs` row has
   `status == 'completed'`, `finished_wall_at` not null.
4. For MHC-C-0006 and MHC-C-0007: a `case_events` row with `kind == OVERDUE_KIND` and a non-null `job_run_id` that
   names a `job_runs` row with `status == 'completed'` (the background runner may have written it first; either is
   correct). Their `promises.status == 'missed'` (promise due Mon 19:00 < 20:00), each with a `case_events` row of
   `kind == PROMISE_MISSED_KIND` and a non-null `job_run_id`. MHC-C-0008 has no `overdue` row.
5. Supervisor `getOversight`: `lanes.overdue.rows` references ⊇ {MHC-C-0005, MHC-C-0006, MHC-C-0007};
   `lanes.p0_p1.rows` holds MHC-C-0008.
6. `stale_check(journey) == 1`.
Print the `demo_events` rows, the `job_runs` row and the lane references.

`test_wf7_ticks` (AC-25), `parametrize("variant", ["seeds"])`, uses `journey`, `journey_clock`, `monkeypatch`:
1. sup; `drive_seed_clock(sup)`; `job = scheduler_job(journey)`; `r1 = job.tick()` → `completed`; row as in 1.11 step 3;
   overdue and missed rows as in step 4.
2. Idempotent: `n = count of case_events kind OVERDUE_KIND`; `r2 = job.tick()` → `completed`; count unchanged;
   `job_runs` has `r2.job_run_id`.
3. Forced failure (§3 reconciliation: the tick has no `CaseService` call; the seam is `prune_checkpoints`):
   `cp = journey.container.get(Key[Any]("checkpointer"))`; `monkeypatch.setattr(cp, "prune", boom)` where `boom(*a, **k)`
   raises `RuntimeError("forced tick failure")`; **then** `journey_clock.advance(86_400)` (a new Chicago wall day, so the
   tick prunes); `r_fail = job.tick()` → `r_fail.status == "failed"`, `r_fail.error_kind == "prune_failed"` (in
   `ERROR_KINDS`, without the word "forced"); its `job_runs` row (by `r_fail.job_run_id`) has `status = 'failed'`, the
   same `error_kind`, `finished_wall_at` not null. `monkeypatch.undo()`; `r3 = job.tick()` → `r3.status ==
   "completed"`, `r3.error_kind is None` (the next tick still runs; it prunes, because the failed prune did not mark the
   day done). The background runner shares this `SchedulerJob` instance; assert only on the returned `job_run_id`s.
4. `stale_check(journey) == 1`.
Print each `job_runs` row (`job_run_id`, `status`, `error_kind`) and the overdue rows with `job_run_id`.

`test_daily_prune_and_abandonment` (AC-12), uses `journey`, `journey_clock`. Order matters: the background runner
ticks at start-up and every 60 s on the same `SchedulerJob`, so every row is written **before** the wall clock moves to
the next day, and our tick follows the move at once.
1. `job = scheduler_job(journey)`; `job.tick()` (today's prune is now done, by us or by the runner).
2. `t = journey_clock() + timedelta(seconds=86_400)` (tomorrow's wall time; do **not** advance yet).
3. Insert through `uow = journey.container.get(UOW_FACTORY)`, `with uow(write=True) as tx: …; tx.commit()`, five
   conversations with `tx.core.conversations.insert(ConversationRow(thread_id=ThreadId(str(uuid4())),
   demo_session="aea52-sweep", run_tag=…, agent_version="test", started_at=DEMO_START, started_wall_at=t -
   timedelta(minutes=40), outcome="open", last_customer_wall_at=…))` and one customer message each
   (`tx.core.messages.append(tid, "customer", "Synthetic sweep message.", DEMO_START)`): A `live`, last customer
   message `t - 31 min`; B `live`, `t - 29 min`; E `eval`, `t - 31 min`; L `load`, `t - 31 min`; S `seed`, `t - 31 min`.
   (All of these lie in the future of today's wall clock, so a runner tick before step 5 cannot sweep them.) Record the
   `messages` count per thread.
4. Checkpoints: `cp = journey.container.get(Key[Any]("checkpointer"))`; put 5 checkpoints for A and 3 for B the way
   `tests/unit/adapters/test_checkpointer.py::_put` does (`cfg = {"configurable": {"thread_id": tid, "checkpoint_ns":
   ""}}`; `cfg = cp.saver.put(cfg, empty_checkpoint(), {"source": "loop", "step": i, "parents": {}}, {})`; import
   `empty_checkpoint` from `langgraph.checkpoint.base`; copy the pattern, do not import the test helper). Note
   `extra = sum(n - 2 for each other thread_id with n > 2 checkpoints)` (`SELECT thread_id, COUNT(*) FROM checkpoints
   GROUP BY thread_id`, A and B excluded; expected 0).
5. `journey_clock.advance(86_400)`; immediately `r = job.tick()`.
6. Assert: checkpoint count per thread in `cp.path` (sqlite3 read, `SELECT COUNT(*) FROM checkpoints WHERE thread_id =
   ?`) is 2 for A and 2 for B; across `job_runs` rows with `started_wall_at >= t - 1 min`, exactly one has
   `counts_json["pruned"]` not null and it equals `4 + extra` (5→2 and 3→2; with
   `extra == 0` that is 4); the summed `counts_json["abandoned"]` over those rows is 1. A: `outcome ==
   'abandoned'`, `ended_wall_at` parses to A's `last_customer_wall_at + 30 min`. B, E, L, S: `outcome == 'open'`.
   `messages` counts unchanged. The four seed threads' outcomes are unchanged.
Print per-thread checkpoint counts, message counts and outcomes.

`test_wf5_no_key_values_or_outbound` (AC-24): `extra_env = {"MERIDIAN_EVAL_KEY": sentinel("eval"),
"LANGFUSE_PUBLIC_KEY": sentinel("lfpk"), "LANGFUSE_SECRET_KEY": sentinel("lfsk")}` (two of four Langfuse values: the
null trace sink stays, so nothing is exported). `with open_staff_run(extra_env=…, …) as run:` sup; `set_staffing on`,
`set_staffing off`, `advance plus_4h`. `secrets_ = (*extra_env.values(), PLACEHOLDER_ANTHROPIC_KEY,
PLACEHOLDER_OPENROUTER_KEY, *run.secret_values(), sup.cookie)`. For each value: not in any `demo_events` row
(`str(row)` of `run.db.rows("SELECT * FROM demo_events")`), not in the three responses' `.text`, not in
`run.logs.all_text()`. `run.guard.blocked == []`. Print "0 sentinel hits; 0 connection attempts".

`test_wf7_logs_keys_and_network` (AC-26): same `extra_env` plus `phrase = sentinel("phrase")`. In `open_staff_run`:
insert one live conversation whose last customer message is `run.clock() + 1 day - 31 min` and whose customer message
text contains `phrase` (as in AC-12 step 3); run `drive_seed_clock(sup)`, `job.tick()` ×2, `run.clock.advance(86_400)`,
`job.tick()`. Scheduler records: the test
file defines `class _Keep(logging.Handler)` (appends every `LogRecord` to a list; never touch `LogTap`'s private
`_snapshot`), attaches it to the root logger at `logging.DEBUG` for the test's duration (remove it in `finally`), and
keeps records with `record.threadName == SCHEDULER_THREAD` or `record.name.startswith("meridian.services.scheduler")`; for each, `keys = set(json.loads(AllowListFormatter().format(rec)))`;
assert `keys <= set().union(*ALLOWED_FIELDS.values()) | {"record", "logger", "level", "length", "exc_type"}`; print the
key sets. `phrase` and every key sentinel: not in `run.logs.all_text()`, not in any `job_runs` row text.
`run.guard.blocked == []`.

**1.12 Journeys (pass 1).** Each file: `pytestmark = pytest.mark.journey`; every API call through
`journey.client()`/`journey.login()` with its operationId; no `TestClient`, no `dependency_overrides`, no monkeypatch;
each block is `with journey.step("J-n", "<k> <name>", needs=…, operations=…):`; assert what the client sees **and** a
stored row.

`tests/journeys/j8/test_aea_52.py`:
- `test_j8_role_switch_seen_by_second_client(journey)`: `a = journey.login()`; client B = `journey.client()` calling
  with `headers={"Cookie": f"mhc_session={a.cookie}"}`. Step 1: A `switchRole representative` → B `getSession` role
  representative; B `getQueue` 200; stored `staff_sessions.role == 'representative'` for `a.session_id`. Step 2: A
  `switchRole customer` → B `getQueue` 403 `wrong_role`.
- `test_j8_reset_sends_both_clients_to_role_reset(journey)`: A supervisor; second login R resets (`resetDemo`); A and B
  `getQueue` → 403 `role_reset`; stored `role_reset_pending == 1`; A `switchRole representative` → A and B `getQueue`
  200; stored `role_reset_pending == 0`.
- `test_j8_refresh_signed_out_and_expired(journey, journey_clock)`: `getSession` twice → same `signed_in_at` (refresh);
  `logout` → 204, then `getSession` → 401 `UNAUTHENTICATED` reason `none`, row deleted; new login,
  `journey_clock.advance(43_201)` → `getSession` 401 reason `expired`, row deleted.

`tests/journeys/j6/test_aea_52.py`:
- `test_j6_seeded_cases_in_queue_with_brief(journey)`: Riley `getQueue` → the four `SEED_REFS` appear (in
  `needs_my_action`); `getCase MHC-C-0005` → `len(brief.headings) == 8`, `promise.policy_row == "R26.refund"`,
  `promise.text` non-empty, every brief `source_ids` entry resolves to a `sources[].source_id`; stored: `cases` has the
  four refs with `seed == 1`, a `case_briefs` row for MHC-C-0005.

Run with `--journey-record=AEA-52` (§7). Then edit the generated record by hand in exactly two cells: *Remaining
limitations* append "J-7 and the J-6 WP-7/WP-8 escalation leg not built in pass 1 (need CON-1, CON-4 and CON-2 through
AEA-40 and AEA-51)"; *Blocked by* append "AEA-40, AEA-51 (pass 2)".

**1.13 Context rows (AC-28).** Only these lines:
- `.claude/reference/area-map.md` the first `**A6 Cases and handoff**` row (line 31 at `c9b17ea`; match by name, the
  line moves when AEA-30/45 merge; leave a duplicate A6 row alone, §8): append to the
  status cell "; integrated (AEA-52, `<commit>`): CON-7…9 and the scheduler proven in `tests/integration/`,
  `tests/capture/test_cap5_clock_and_scheduler.py`". The `**A9 Staff console**` row: append "; integrated (AEA-52, `<commit>`)".
- `.claude/state/icm-progress.md`: add one row after the last "Routes verified against code and tests" row, same
  columns, ≤ 400 characters: "provisional | 2026-10-21: areas A6, A9 (integration, AEA-52 `<commit>`):
  `tests/integration/test_staff_*.py`, `test_demo_reset.py`, `tests/capture/test_cap5_*` pass (`<n>` passed), J-6
  seed leg and J-8 at integrated level | J-7 and CAP-4 after AEA-40/51".
- `docs/design/code-design.md` §6 rows S-7, S-11, S-19, S-20: append to the last cell " Proven: `<test path>` (AEA-52)."
  — S-7 `tests/integration/test_staff_composition.py::test_real_objects_bound`; S-11
  `tests/integration/test_staff_streams.py::test_case_stream_after_reset`; S-19
  `tests/capture/test_cap5_clock_and_scheduler.py::test_wf7_ticks`; S-20
  `tests/integration/test_demo_reset.py::test_reset_all_or_nothing`.
Then `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` → no FAIL.

**1.14 Commit (pass 1).** Gates in §7 green first. `git add` each owned path explicitly (never `-A`). Message:
`test(integration): AEA-52 pass 1 - staff and demo seams on the real app` + body listing ACs built and ACs blocked, last
line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push; do not touch the ledger.

### Step 2 — pass 2 (after AEA-40 and AEA-51; Step 0.3)

**2.1 `staff_support.py` additions:**
```python
@dataclass(frozen=True)
class LiveCase: thread_id: str; ref: str; result: str
def open_live_case(run: JourneyRun, customer: Actor, staff: Actor, *, staffed: bool = True) -> LiveCase
    # staffed → set_staffing(staff, "simulated_on_shift"); customer startChatSession → 201 thread_id;
    # customer requestPerson {"turn_id": str(uuid4())} → 200; result "live_queued" (staffed) or "case_created";
    # ref = body["block"]["reference"].
def greeting_message_id(run: JourneyRun, thread_id: str) -> int   # SELECT id FROM messages WHERE thread_id=? AND role='assistant' ORDER BY id LIMIT 1
def run_cap4_flow(run: JourneyRun, rep: Actor, cust: Actor, *, text: str) -> tuple[LiveCase, dict[str, httpx.Response]]
    # live case; claim (result_line == "Claimed · Riley (demo)"); join; send(text); hand_back;
    # createFlag {"case_ref": ref, "target": "answer", "message_id": str(greeting_message_id), "reason": "Synthetic flag reason."}
```
AC-1 gains the `SessionService` / `TurnService` rows.

**2.2 `test_cap4_staff_console.py`** (`parametrize("variant", ["person_request"])`; `"wp7"` added with R-3):
- `test_staff_actions_recorded` (AC-2): `rep = sign_in(…, "representative")`, `cust = sign_in(…)`;
  `run_cap4_flow(text=sentinel("riley"))`. Stored: `case_events` for the ref with `actor_role = 'representative'`
  ordered by id → kinds `[CLAIM_KIND, CASE_EVENT_KIND["join"], CASE_EVENT_KIND["send"], CASE_EVENT_KIND["hand_back"]]`,
  each `detail_json` a JSON object; the representative `messages` row is in `thread_id` with `text == text`; the
  `flags` row has `case_ref`, `flagged_by_role == 'representative'`, `target == 'answer'`; `journey.logs.structured("request")`
  records whose `request_id` is one of the staff responses' `X-Request-ID` all have `caller_role == "representative"`.
  Print the rows.
- `test_no_customer_pii_in_logs` (AC-3): `card = card_like_number()`; `text = f"{sentinel('riley')} card {card}"`;
  flow; stored message text contains "[card number removed]" and not `card`; `journey.logs.all_text()` contains
  neither `text`, `card`, its 16 digits, nor any `seed_customer_names(journey)` entry (WP-7 variant: also the WP-7
  customer's name read from the issued `customers` row). Print "0 hits" and the stored text.
- `test_wf4_status_values` (AC-22): flow; `by_id = {r.headers["X-Request-ID"]: r.status_code for c in journey.clients
  for r in c.responses}`; every `request` record with `request_id in by_id` has `status == by_id[...]` (int). Then
  `monkeypatch.setattr(journey.container.get(CASE_SERVICE), "apply", boom)`; post `applyCaseAction` with a **raw**
  `httpx.Client(base_url=journey.base_url, cookies={"mhc_session": rep.cookie})` (a 500 is undocumented, so not
  through `call`) → 500; body validates against `ApiError` (§4); the `request` record for its `X-Request-ID` has
  `status == 500`, `error_kind == "RuntimeError"`. `monkeypatch.undo()`. Print (`route`, `status`, `error_kind`).
- `test_no_key_values_anywhere` (AC-23): `open_staff_run(extra_env=…)` as AC-24; run the flow; collect `frames =
  read_stream(…, "/api/staff/cases/{ref}/events")`; values = key sentinels, placeholders, `run.secret_values()`,
  `rep.cookie`, `cust.cookie`. None in `run.logs.all_text()`, in any CON-11…CON-17 response `.text` from
  `rep.client.responses`, in any frame's `data`, or in `run.files_containing(value)` (all DB files). `staff_sessions`
  `token_hash` values differ from both cookies. Print 0 hits per sentinel.

**2.3 `test_staff_streams.py` additions:** `test_takeover_events_and_replay` (AC-4), `test_staffing_on_and_shift_end`
(AC-7), `test_reload_after_takeover_shows_staff_lines` (AC-18), `test_relayed_message_same_on_stream_and_case_view`
(AC-17), exactly as specified in §3 and these rules:
- AC-4: case A (claim → `v_claimed`; join; send S; hand_back) and case B (claim; join; close). CON-3 A (customer
  cookie): the subsequence of types in {`representative_joined`, `ai_paused`, `staff_message`, `ai_resumed`} is exactly
  that order; `staff_message` data `text == S`. CON-21 A (Riley cookie, no header): types == [`case_changed`,
  `controller_changed`, `controller_changed`] (claim, join, hand back). Riley `resolve` A with `version=v_claimed`,
  `outcome="Resolved in the live chat."` → 200; CON-21 A now ends with `case_changed`. CON-3 B ends with `chat_closed`
  and `closed_by_server is True`; CON-21 B contains `chat_closed` and `closed_by_server is False`. Replay: `F` = CON-3
  A frames; `k` = index of `representative_joined`; `R = read_stream(…, last_event_id=F[k].id)`; `[f.id for f in
  R.frames] == [f.id for f in F.frames[k+1:]]`; `logs.wait_for("stream_reconnect", lambda r: r.get("thread_id") ==
  A.thread_id)`. Same for CON-21 A with `case_ref`.
- AC-7: fresh app → `getStaffing.mode == "nobody_online"`, `demo_events` count 0. Customer opens a chat (T1) first;
  supervisor on → `converted_cases == 0`, one `demo_events` row (`kind 'staffing_changed'`, `mode
  'simulated_on_shift'`, `role 'supervisor'`); CON-3 T1 has `staffing_changed`. On again → `demo_events` count
  unchanged. Customer `requestPerson` on T1 → `result == "live_queued"`, `block.promise_text ==
  PROMISE_TABLE["R26.staffed"]`; note `ref`, `created_at` from `getCase`. Off → `converted_cases == 1`; CON-3 T1 has
  `shift_ended` with `handoff.reference == ref`, `handoff.promise_text == PROMISE_TABLE["R26.unstaffed"]`, `settled`
  present; `getCase` → same `reference`, same `created_at`, `promise.text == PROMISE_TABLE["R26.unstaffed"]`. Off again
  → no new row.
- AC-18: join, send S, hand_back; customer `getChatThread` → `turns` contains, in this order, an `event` entry whose
  `text` is the joined line, an `event` entry for the paused line, an entry with `speaker == {"kind":
  "representative", "display_name": "Riley"}` and `text == S`, an `event` entry for the resumed line; `last_event_id ==
  int(F.frames[-1].id)` (CON-3 read from start); `read_stream(…, last_event_id=str(last_event_id))` → 0 frames,
  `closed_by_server is False`. Print the entries.
- AC-17 (needs `run_graph`, `turn_service`): Riley joined on a live case; customer `submitTurn` `{"kind": "text",
  "text": "Synthetic customer reply."}` → 200; CON-21 frames: exactly one `customer_message`; `m = data["message"]`;
  `getCase` `conversation` line with `message_id == m["message_id"]` equals `m` field for field; `m["speaker"] ==
  {"kind": "customer", "display_name": CUSTOMER_SPEAKER_NAME}` (§3 reconciliation); customer `getChatThread` has that
  text and Riley's reply in order. Print both objects.

**2.4 Remaining pass-2 tests:** `test_demo_reset.py::test_reset_ends_open_chats` (a `BackgroundStream` on the
customer's CON-3 started before Riley's reset → last frame `demo_reset`, `closed_by_server is True`; then
`getChatThread` → 410 `SESSION_ENDED` `details.reason == "demo_reset"`; `open_chats_ended >= 1`);
`test_staff_allowed_actions.py` `"live_claimed_joined"` (a **new** live case per action instead of a reset:
`open_live_case`, claim, join, then the action); `test_cap5_clock_and_scheduler.py::test_clock_changed_reaches_open_chat`
(customer chat open; supervisor `advance plus_1h`; CON-3 has `clock_changed` whose `demo_clock.now` equals the advance
response's `now`); `test_stale_tick_shows_as_health_tile` (needs `metrics_reads`; after `stale_check == 1`,
`getMonitoring` `health` has a Tile with `id == "scheduler_last_run"` and no alert with `type == "scheduler_stale"`);
`tests/journeys/j7/test_aea_52.py::test_j7_person_request_takeover_and_reload` (steps: open chat and request a person;
Riley sees it in `getQueue.live`, claims, joins; relayed customer line identical on CON-21 and `getCase` (step needs
`run_graph`); Riley sends; customer reload `getChatThread` shows Riley's line; hand back; resolve with the pre-join
version accepted; stored: representative message row in the thread, case `lifecycle == 'resolved'`).

**2.5 WP-7 / WP-4 variants** (need R-3): add `"wp7"` / `"wp4"` / `"wp4_appointment"` / `"wp7_claimed_joined"`
parameters, `test_fee_bearing_request_reaches_staff_at_once` (AC-19: right after WP-4's `request_change` case opens,
supervisor `getOversight` lists it in `lanes.due_soon`; `getCase` priority `{"level": "P2", "word": "Time-sensitive"}`,
`case.due_at` = 12:00 window start ≠ `promise.due_at` (Mon 19:00); the appointment row unchanged; the wanted windows
shown with "Windows are shown, not held."; none of "charged", "waived", "sent" in the body text), and the J-6
WP-7/WP-8 step. AC-6/AC-25 `"wp4"`: `plus_4h` 10:00 → 14:00 → `became_overdue == 1`; tick → WP-4 `overdue`, its
promise still `open`; advance past Mon 19:00 → next tick marks it `missed`.

**2.6** Re-run every gate in §7, regenerate the journey record (remove the two hand-added pass-1 notes that no longer
apply), update the three context rows with the pass-2 commit, commit as in 1.14 with "pass 2".

---

## 6. Data and fixtures

Synthetic only; nothing hard-coded that is personal.
- **Seeds:** MHC-C-0005…0008 loaded by the app's own first boot (AEA-31 `seed_demo`, customers from the issued DB).
- **Contact values and names** (AC-3, AC-21): read at run time from the working copy `customers` rows of
  `SEED_CASES[*].customer_id`; never written into a test file.
- **Sentinels:** `sentinel(label)` → `aea52-<label>-<16 hex>` from `secrets`; the card-like value is 16 random digits
  from `secrets` (no checksum: the STORE redactor matches 13–19 digits, `privacy/redact.py` `_CARD`).
- **Synthetic conversations and checkpoints** (AC-12, AC-26): written through the real `UnitOfWork` repositories and
  the real `Checkpointer.saver`; texts "Synthetic sweep message." / the phrase sentinel.
- **Working-copy edits** (AC-8 forced failure, AC-9): `UPDATE invoices SET balance_cents = balance_cents + 1000 WHERE
  invoice_id = 'INV-200037'` on the disposable copy only; the harness asserts the issued file's hash is unchanged.
- **Customer chat turns** (pass 2): "hello", "Synthetic customer reply."; WP-7/WP-4 turns come from AEA-51's scripts
  (R-3), sourced from `docs/data/worked-pairs.md`.

---

## 7. Checks

No production code changes, no shared fixture, settings or dependency change: **no full suite** (build-loop-test-scope).

While iterating (one file at a time):
`cd <worktree> && UV_LINK_MODE=hardlink uv run pytest tests/integration/test_demo_reset.py -q -rs -x`

Before the final commit, cheapest first, stop at the first red:
1. `uv run ruff format tests/integration tests/capture/test_cap4_staff_console.py tests/capture/test_cap5_clock_and_scheduler.py tests/journeys/j6/test_aea_52.py tests/journeys/j7/test_aea_52.py tests/journeys/j8/test_aea_52.py`
   then the same with `--check` → "N files already formatted".
2. `uv run ruff check` on the same paths → "All checks passed!".
3. `uv run mypy` on the same paths → "Success: no issues found".
4. Affected tests: `uv run pytest tests/integration tests/capture/test_cap5_clock_and_scheduler.py tests/capture/test_cap4_staff_console.py -q -rs`
   (serial; `-n 2` at most) → all pass, 0 skipped (pass 1: only pass-1 files exist).
5. Journeys + record: `uv run pytest -m journey tests/journeys/j6 tests/journeys/j7 tests/journeys/j8 -v -rs --journey-record=AEA-52`
   → AEA-52 steps pass; record written to `docs/testing/journeys/<date>-AEA-52.md` (then Step 1.12's two hand edits).
6. Affected-journey gate: `uv run python -m tests.journeys.affected --base "$(git merge-base main HEAD)"` → exit 0.
7. AC-13: `grep -rn "open_case" src/meridian/web/routes/staff_*.py` → no output.
8. `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` → no FAIL.
9. `git diff --name-only main...HEAD` → only §2 owned files.

Report: each AC → test → result (pass / not built: blocked-on …), the printed evidence lines, the gate outputs, the
journey record path and its level line.

**Tests the implementer writes (with the code):** every test named in §3 for the pass being built. The WP-N worked
pairs: **WP-7** (`test_staff_actions_recorded[wp7]`, `test_contact_attempt_recorded_not_sent[wp7]`,
`test_listed_iff_accepted_per_role[wp7_claimed_joined]`, J-6 WP-7 step) and **WP-4**
(`test_fee_bearing_request_reaches_staff_at_once`, `test_clock_past_due_and_scheduler[wp4]`, `test_wf7_ticks[wp4]`,
`test_case_view_snapshot_vs_current[wp4_appointment]`), all pass 2. The single `[journey]` criterion is **AC-15** at
level `integrated with a scripted model`. Existing tests that must stay green: `tests/journeys/support/test_support.py`, every other file under
`tests/journeys/j6`, `j7`, `j8` (on `c9b17ea`: `j6/test_aea_{29,47}.py`, `j7/test_aea_{29,41,42,46}.py`,
`j8/test_aea_{31,43,44}.py`; after the blockers merge also `j6/test_aea_30.py`, `j7/test_aea_30.py` (AEA-30) and
`j6/test_aea_45.py` (AEA-45)),
`tests/unit/test_affected_journeys.py` (its `test_no_journey_yet_prints_zero_and_exits_0` is red on main since AEA-57,
ledger rows AEA-06/44/47/57: not this slice's to fix; report it, do not edit it).

**Must not:** edit anything outside §2; add a `register_*` binding or any `src/` change (a missing binding is
`blocked-on` its owner); use `TestClient`, `app.dependency_overrides` or doubles above the model ports; monkeypatch
anything except `RecordsRepo.seed_event` (AC-8), the container's `CaseService` instance `apply` (AC-22) and the
container's `Checkpointer` instance `prune` (AC-25); put a
real-looking phone, email, address, code or card number in a file; print a secret, cookie or the demo password; call
a paid model; bind 4019 or 5184 (the harness uses port 0); `git add -A`; push; force-push.

---

## 8. Risks and requests

- **R-1 (settled from AEA-30's branch `e5c4ce4`; was a request):** `register_demo` provides `Key("demo_clock")`,
  `deps.DEMO_SERVICE`, `Key("scheduler_job")` and `Key("scheduler_thread")`, names the thread `"meridian-scheduler"`,
  stops it in `on_close`, stores `counts_json` under the `JobRun` field names and records `error_kind` per failed step
  while the runner keeps going. The one part that did not land as requested: `tick()` calls no `CaseService` method
  (cases.md §6 never said it would; AEA-30 R-7). AC-25's failure seam moved to `prune_checkpoints` (§3). Step 0.4
  re-confirms all of it on main.
- **R-2 (note to AEA-57's owner, optional):** `NEED_OWNERS` lacks `scheduler_job`; this plan avoids it in journey steps.
- **R-3 (request to AEA-51):** publish the WP-7 and WP-4 customer conversations (customer turns + scripted raw
  outputs) as importable functions in an AEA-51-owned module (proposed `tests/integration/customer_scripts.py`:
  `open_wp7_case(run) -> (Actor, LiveCase)`, `open_wp4_case(run) -> (Actor, LiveCase)`), so AEA-52 drives the same
  conversations rather than inventing scripts. If AEA-51 lands without it, the WP variants go back to the planner.
- **R-4 (to the orchestrator; ledger row):** the ticket's *Blocked by* omits **AEA-51**: CON-1 (`SessionService` needs
  `ReplyComposer.settled_view`), CON-4 (`register_person_request` needs `reply_composer`) and CON-2 (`run_graph`) all
  go through objects only AEA-51's `register_graph` binds (and AEA-21 builds). So every live-chat criterion (AC-2, 3,
  4, 7, 17, 18, 19, 22, 23, the J-7 journey, the open-chat halves of AC-6/AC-8, and the WP variants) is pass 2. The
  AC-6 CON-19 tile also needs **AEA-53**. AEA-59 is **not** needed (`assert_response_matches` is AEA-23's, merged).
  Recommendation: dispatch pass 1 as soon as AEA-30 and AEA-45 merge (AEA-29 and AEA-43 are merged) (it proves seams S-7, S-8, S-11,
  S-18, S-19, S-20 early), keep the ticket open, dispatch pass 2 after AEA-40 and AEA-51.
- **R-5 (to the orchestrator, ticket wording):** AC-25 names "a tick whose `CaseService` call is patched to raise". There
  is no such call under the signed contract, so this plan proves the same obligation through `prune_checkpoints`. No
  contract, decision or other ticket changes. Note it on issue #52 when the result is posted.
- **R-6 (from AEA-30 R-17 / AEA-29 R-7, no action here):** a promise converted at a shift end is stored `changed`. AC-7
  asserts the converted promise's *text* and the case's reference and creation time, never its status, so either
  resolution of that open item leaves AC-7 green.
- **Area map has two A6 rows** (lines 31 and 32, a merge artefact). This slice appends to line 31 only; the duplicate
  is for the orchestrator to remove (AEA-29/30 will also edit the A6 row).
- **Background threads:** the scheduler runner (ticks at start-up, then every 60 s, on the same `SchedulerJob` instance
  the tests drive) and the watchdog run during tests. Every scheduler assertion keys on returned `job_run_id`s or "a
  completed run wrote it", never on a total count; AC-12 writes its rows before moving the wall clock; `stale_check`
  reads the clock at evaluate time (refresh log item 5).
- **Timing:** each test starts its own uvicorn app (~1–3 s); SSE reads wait `idle_s` (3 s). Expect pass 1 at a few
  minutes serial.
- **Collisions:** `tests/integration/` is shared with AEA-53 (`test_reads_composition.py`) and `tests/capture/` with
  51, 53, 24, 50; all AEA-52 files have distinct names (`tests/capture/conftest.py` is AEA-50's: never edit it; it only
  registers the `deploy` marker). AEA-45's branch adds `tests/api/staff_cases_support.py`: a different helper in a
  different folder; do not import it (AEA-52 tests run on the harness, AEA-45's on its own fixtures). Context files:
  AEA-29 (merged), AEA-30 and AEA-45 (branches) also append to the A6/A9 area-map rows, `icm-progress.md` and DO-3 §6;
  AEA-52 appends to its own cells after theirs and never rewrites their text.

---

## 9. Readiness

**READY as a plan; BLOCKED-ON before implementation** (no product decision needed; no signed contract change; no
D-4…D-15 answer differs from its recommendation; D-12 is followed in AC-19).
- Pass 1 waits on **AEA-30** (DemoService, DemoClock, SchedulerJob, SchedulerThread; it also binds `demo_clock`,
  without which a real login answers 500) and **AEA-45** (CON-11…13, 15…17 routes) reaching `main`. At `c9b17ea` both
  are built on branches (`e5c4ce4`, ledger `blocked`, send-back unfinished; `ea00827`, ledger `blocked`). Already
  merged: AEA-29 (CaseService, HandoffService), AEA-43 (CON-6…CON-9 routes), AEA-57 (harness), 23, 31, 32, 41, 44, 46,
  47, 48, 59. AEA-52 is an integration ticket: its criteria require the real objects through the real app
  (slice plan Amendment 1: "on the harness, not on fakes"), so a double cannot stand in for these four.
- Pass 2 also waits on **AEA-40** (CON-1, CON-2, `getChatThread`; built on its branch at `8fc2d33`, ledger
  NEEDS-DECISION) and **AEA-51** (binds `reply_composer` and `run_graph` in `register_graph`, still a no-op on main;
  not started; WP scripts, R-3); the CON-19 tile check waits on **AEA-53** (ledger NEEDS-DECISION, not started). AEA-51 is not in the ticket's *Blocked by* (R-4).
