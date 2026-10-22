# Plan — [AEA-61] live smoke: live-model smoke set through the real app

**Status:** planned — **READY in three parts.** **Part A** (smoke driver, custody/spend/record guards, the paid test file
that skips by default) imports nothing that is not on `main` and **can be built now**. **Part B** (four scripted journey
files, AC-16's scripted dry run, the scripted record) is **blocked-on AEA-51**: pass 2 is complete on its branch but not
merged (sent back at the merge gate on J-9; fix commit `fdcc332` on the branch). **Part C** (the paid run and its record)
is **blocked-on AEA-51** too, and waits on **`gate::paid`**: Innocent's go with the day's spend statement (sign-off D-15,
"a statement, not a choice").
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/61 (identical to
`docs/plans/tickets/AEA-61.md`) · **Base revision:** `main` `dffedf7` (refresh 6, 2026-10-22; refresh 5 at `dc8d8d0`; refresh 4 at `b68df7e`; refresh 3 at `76f14f4`; refresh 2 at `cf8fd78`; refresh 1 at `ef561fc`; first written at `e22aebb`)
· **Wave:** 4 · **Lane:** build-loop · **Risk:** none in the slice plan (see §8 R-6) · **Gate:** `gate::paid` (part C)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 (refresh 6: 2026-10-22) · **Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** the one the orchestrator creates (suggested `aea-61-live-smoke` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-61`), cut from `main`.

**Refresh 6 (2026-10-22, `main` at `dffedf7`).** Read this box first; refreshes 5 to 1 below are kept as history. Where
this box and anything later differ, this box wins. Rewritten in place: §4.3, A0 step 1, two A4 clarifications, B0, B1,
§7 check 6, §8 (R-1, R-14, new R-15 and R-16) and §9. Everything else was re-checked and holds.

1. **Merged since refresh 5** (first-parent `main`, `dc8d8d0..dffedf7`):
   - **AEA-40-F1** at `47da752` (safety turns answered at the spend cap);
   - **FU-saveFollowUp-text** at `0a01219` (adds `TextId.FOLLOWUP_SAVED_EMAIL_GENERAL`);
   - **AEA-21b** at `9b3824e` (`agent/nodes/compose_cards.py`: slot, SLOT_TAKEN, account, appointment, where and no-fit
     cards). R-14's two transitive blockers are gone.
2. **Unchanged since `dc8d8d0`** (`git diff --stat dc8d8d0 dffedf7` over refresh 5's path list): everything except
   `src/meridian/policy/texts.py`, which only gained `FOLLOWUP_SAVED_EMAIL_GENERAL`. `TEXTS`, `render`,
   `TextId.EMERGENCY_LINE_LEAD` and `TextId.PROMISE_UNSTAFFED` hold. `src/` otherwise changed only in
   `agent/nodes/compose*.py`, `services/_case_actions.py` and `services/turn.py`, none of which this plan imports.
   `tests/live/` still holds only `__init__.py`; no AEA-61 branch exists.
3. **AEA-51:** ledger `sent-back` (merge gate red on
   `tests/journeys/j9/test_aea_40.py::test_j9_rate_limited_through_the_real_server`). Branch
   `aea-51-aea-51-customer-path` at `fdcc332` holds the complete pass 2:
   - `register_graph` binds `Key("run_graph")`; with `overrides=None` every role gets its production adapter, and it
     provides `Key("retrieval_index")` (`FastembedIndex(settings.index_dir)`);
   - `tests/integration/customer_support.py`, `tests/integration/customer_api.py`,
     `tests/graph/worked_pair_scenarios.py`, journeys `j{2,3,4,5,9}/test_aea_51.py`.

   Innocent's "go with A" on that send-back is about AEA-51's J-9 fix, not this ticket; nothing here changes for it.
   Parts B and C still need AEA-51 **merged** (A0 step 1).
4. **Part B re-planned against AEA-51's pass-2 code** (§4.3, B0, B1). The old B1 table guessed the encodings; the new one
   copies AEA-51's building blocks, checked against the six dev case files and the issued DB:
   - **A resumed task re-runs its specialist on every later turn** (AEA-51 finding F-1, `wp4f_followup` docstring:
     "open_tasks is not advanced on card and code turns"). Every post-verification turn of WP-2, warranty, WP-4F and
     WP-4 therefore sets `Role.SPECIALIST`. The old table's "none" entries would have run out of script.
   - **`move_visit` refuses a window `find_windows` has not shown in the conversation** (`not_shown`,
     `services/scheduling.py`). WP-4F therefore shows Monday 2026-10-19 08:00–12:00 before it moves. In the issued DB that
     filter returns slot 56 only for zone `north`, `hvac_repair` (appointment 159's), and slot 41 for `north`,
     `hvac_tune_up` (appointment 1's).
   - **The WP-4F dev script moves by a text turn** ("Can I do Monday the 19th, 8 to 12, instead?"), not by a slot-card
     choice as AEA-51's `wp4f` does. `first_shown_slot`, `passage_for` and `passage_text` are dropped.
   - **The DANGER dev text trips no deterministic rule**
     (`meridian.gates.rules.match_rules("My AC's out and my mother is 88 and it's 95 degrees in here.").danger_words` is
     `False`). The turn reaches the classifier, so the "no raise" bad script is catchable. A live record's path line reads
     `classifier` when the model raises.
   - **A fee-bearing case opens only from a `staff_change_request` result** (`policy/escalation.py`, rule
     `R21.fee_bearing`, produced by `request_visit_change`). WP-4's "no change_request" bad script therefore leaves no P2
     case and is caught.
   - **Only `current` manifest files are indexed** (`retrieval/ingest.py`), so a scripted `kb_search` cannot return
     `archive/`.
5. **Small part A additions** (no behaviour change for the live run):
   - A4: the form turn fills one of the `locate_prompt`'s `field_sets`; an exchange is appended before its status check,
     so a failed turn is still checked.
   - A5: `smoke_checks.py` defines `WP4F_TARGET_SLOT: Final = 56` and the WP-4F check compares against it (failure text
     unchanged: `"WP-4F: appointment 159 not on slot 56"`). B1 imports the same constant.
6. **Blockers recorded for the orchestrator:** part A none (buildable on `dffedf7`); part B AEA-51 (merge); part C AEA-51
   (merge) and `gate::paid`.

**Refresh 5 (2026-10-21, `main` at `dc8d8d0`).** History; superseded by refresh 6 above.

1. **Merged since refresh 4** (first-parent `main`, `b68df7e..dc8d8d0`):
   - **AEA-39** at `12e46ee` (`agent/nodes/act.py`: `run_specialist`, `escalation`, `handoff` are real; no
     `NotImplementedError` left).
   - **AEA-60** at `0e37fad` (`tests/contract/test_prompts_vs_consumers.py` and its `_prompts_*.py` helpers;
     `tests/journeys/j5/test_aea_60.py`, `tests/journeys/j9/test_aea_60.py`). **AEA-60 is no longer a blocker**: check
     P1 runs on `main` today.
   - **FU-j1-demo-state** at `dbcd8b7` (test-only change to `tests/journeys/j1/test_aea_57.py`).
   - **AEA-19-F1** at `dc8d8d0` (`register_tracing` returns `Key("trace_override")` when `register_graph` provides it
     from `ContainerOverrides.trace`). The live run passes no overrides, so `Key("trace")` is still the Langfuse sink
     when all four `LANGFUSE_*` values are set and `NullTraceSink` otherwise. Nothing in this plan changes.
2. **Unchanged since `b68df7e`**, checked by `git diff --stat b68df7e dc8d8d0` (empty) over: `tests/journeys/support/`,
   `eval/cases/`, `scripts/`, `tests/fixtures/`, `tests/api/openapi_check.py`, `tests/conftest.py`, `tests/live/`,
   `tests/unit/adapters/test_retrieval_fastembed.py`, `pyproject.toml`, `src/meridian/{config.py,web/app.py,
   agent/signals.py}`, `src/meridian/{policy,privacy,retrieval,domain}/`, `src/meridian/adapters/sqlite/schema/`.
   `src/` changed only in `agent/nodes/act.py` and the `register_tracing` hunk of `web/container.py`. Every §4.1 name
   still holds. The first dev warranty key by `case_id` is still `T-CALL-20260723-0276` (the other in-scope warranty
   key is `T-CALL-20260823-0142`).
3. **AEA-51 is still not on `main`** (ledger `blocked`). Its branch `aea-51-aea-51-customer-path` at `e9d07f3` holds
   **pass 1 only**:
   - `register_graph` binds `reply_composer` but **not** `Key("run_graph")` (its own *Deviations* note 2). A live turn
     on `main` or on that branch still fails at turn 1, so parts B and C both wait for AEA-51 **pass 2**.
   - `tests/integration/customer_support.py` exists on the branch and matches §4.3:
     `open_customer_run(request, options: RunOptions = DEFAULT_OPTIONS, *, monkeypatch=None)` (the default is the module
     constant `DEFAULT_OPTIONS = RunOptions()`, ruff B008; same behaviour), `RunOptions(index="built", eval_key=False,
     trace=None, with_clock=False, deadline_s=None)`, `CustomerRun(JourneyRun)` with `.eval_key` and `.steps`,
     `StepScript.set_step(...)`, `INDEX_SKIP`.
   - `tests/graph/worked_pair_scenarios.py` (the building blocks and drivers B1 copies) is **not** on the branch yet; it
     is pass 2.
   - AEA-51's pass 2 now waits on **AEA-21b** (`compose.py` builds no slot, account or appointment blocks; no ticket
     file, ledger row or branch exists for it on `dc8d8d0`) and **AEA-40-F1** (plan and worktree exist; one AEA-51
     test). See R-14.
4. **Part B's start condition is tightened** (A0 step 1): part B starts only when `main` has
   `tests/graph/worked_pair_scenarios.py` **and** `register_graph` provides `Key("run_graph")`. A merge of AEA-51
   pass 1 alone is not enough.
5. **DO-3 §9's `└── live/` line is now line 723** (was 715). A8 finds it by its text.
6. **Sibling journeys in the folders this ticket adds to** (check 6 must keep them green): `j2/test_aea_35.py`,
   `j2/test_aea_38.py`; `j3/test_aea_27.py`, `test_aea_28.py`, `test_aea_34.py`, `test_aea_39.py`, `test_aea_43.py`;
   `j4/test_aea_28.py`, `test_aea_39.py`; `j5/test_aea_36.py`, `test_aea_37.py`, `test_aea_60.py`.
7. **Blockers recorded for the orchestrator:** part A none (buildable on `dc8d8d0`; nothing of it has been built:
   `tests/live/` holds only `__init__.py` and no AEA-61 branch exists); part B AEA-51 pass 2; part C AEA-51 pass 2 and
   `gate::paid`.

**Refresh 4 (2026-10-21, `main` at `b68df7e`).** History; superseded by refresh 5 above.
Nothing in §1–§9 changes except the base revision, R-1, the DANGER path rule in A6 (item 4 below) and §9's revision.

1. **Merged since refresh 3** (first-parent `main`, `76f14f4..b68df7e`):
   - **AEA-37** at `8d025b7` (`agent/nodes/plan.py`: planner, planner fallback, danger classifier, plan join;
     `agent/prompts/routing.py`).
   - **AEA-58** at `eb51ba4` (browser journeys; adds the dev dependency `pytest-playwright>=0.10`).
   - **AEA-45** at `1a6712a`, **AEA-53** at `b9be4dc`, **FIX-W1** at `38d3884`, **AEA-52** at `55d9adf`
     (`tests/integration/staff_*.py`, `test_demo_reset.py`: staff helpers, not AEA-51's customer helpers).
2. **Unchanged since `76f14f4`**, checked by `git diff --stat 76f14f4 b68df7e`: `tests/journeys/support/`,
   `eval/cases/`, `scripts/`, `tests/fixtures/`, `tests/api/openapi_check.py`, `tests/conftest.py`, `tests/live/`,
   `tests/unit/adapters/test_retrieval_fastembed.py`, and the AEA-51 and AEA-60 plan files (so §4.3 still holds).
   - `pyproject.toml` gained only the `pytest-playwright` dev dependency; `addopts`, the `journey` and `live` markers
     and the mypy `files` are unchanged.
   - `src/` changed only in `agent/nodes/plan.py`, `agent/prompts/routing.py`, the metrics reader, the staff-cases
     routes and schemas, and the `register_staff_cases` / `register_metrics_reader` hunks of `web/container.py`. No
     §4.1 name is touched. `register_chat` still reads `Key("run_graph")` lazily and `register_graph` is still
     AEA-51's, so a live turn on today's `main` still fails at turn 1.
3. **PD-6 confirmed against AEA-37's merged code** (no change to the rule):
   - `planner()` runs `Role.PLANNER_FALLBACK` whenever Jev's planner output fails, returns
     `PlannerOutcome(fallback_used=True, …)` (stored as `turns.planner_fallback_used`), and emits
     `SignalName.PLANNER_FALLBACK` (`"planner_fallback"`) through `emit_signal` on logger `meridian.signal`.
   - `danger_classifier()` on a failure emits `SignalName.CLASSIFIER_FALLBACK` and stores
     `CheckEvent.from_danger(...)` with `check="classifier"`, `result="fallback"`, `codes=("fallback", <kind>)`.
   - `turns.planner_failed = 1` (both planner models failed) always comes with `planner_fallback_used = 1`, so the
     existing planner-fallback check already catches it; no extra check.
4. **One rule tightened (A6, DANGER path line).** The path is read from the stored classifier event, not from the
   spend rows: `"classifier"` when the first turn has a `checks` row with `check_kind == "classifier"` and
   `result == "raised"`, otherwise `"danger_rule"`. Reason: on AEA-37's code the classifier is called on every
   gated turn (AEA-37's J-5 journey shows a planner and a classifier call on DANGER), so "a classifier spend row
   exists" would name the classifier even when the danger rule had already decided. The model-call count still
   comes from `turns[0].model_calls`.
5. **`pytest-playwright` and A8 test 5.** The subprocess run of `tests/live/test_live_smoke.py` now loads that
   plugin too. It adds options and fixtures only. A8 test 5 already matches on `"10 skipped"` and the reason text
   and must not assert on anything else in the output (plugin header lines may differ).
6. **Still not on `main`:**
   - AEA-51 (ledger `blocked`). Its only unmerged blocker is now **AEA-39** (ledger `blocked`, "re-run" since AEA-35
     merged).
   - AEA-60 (ledger `blocked`, also waiting on AEA-39).
   - `tests/integration/customer_support.py`, `tests/graph/worked_pair_scenarios.py` and
     `tests/contract/test_prompts_vs_consumers.py` do not exist.
7. **Blockers recorded for the orchestrator:** part A none; part B AEA-51; part C AEA-51, AEA-60 and `gate::paid`.

**Refresh 3 (2026-10-21, `main` at `76f14f4`).** History; superseded by refresh 4 above.

1. **Merged since refresh 2** (first-parent `main`):
   - **AEA-40** at `f466ff7`: `services/session.py`, `services/turn.py`, `web/routes/chat.py`, `web/schemas/chat.py`,
     and a real `register_chat`. The build ledger still shows AEA-40 `blocked` / NEEDS-DECISION; that row is stale
     (`git merge-base --is-ancestor f466ff7 main` is true).
   - The AEA-29 typing fix (`8a205b2`), **AEA-35b** (`3725c90`), **AEA-36** front node (`c378698`) and **AEA-35**
     specialist runner (`1ce98c4`).
   - **AEA-37** was sent back on a merge conflict. **AEA-39** is still NEEDS-DECISION.
2. **Unchanged since `cf8fd78`, re-checked by `git diff --stat cf8fd78 76f14f4`:** `tests/journeys/support/`,
   `eval/`, `scripts/`, `tests/fixtures/`, `tests/unit/adapters/test_retrieval_fastembed.py` and `pyproject.toml`.
   - Every §4.1 name was grepped on `76f14f4` and holds: `ISSUED_DB`, `letters`, `build_sha_from_git`,
     `cached_model_dir`, `KB_DIR`, `TRANSCRIPTIONS_DIR`, `SIGNAL_LOGGER`, `DEMO_START`, the three eval header constants,
     and the `journey` / `live` markers.
   - The first dev warranty key by name is still `T-CALL-20260723-0276`.
3. **What AEA-40 changes for this slice:**
   - `startChatSession` and `submitTurn` now exist on the real app.
   - `register_chat` reads `Key("run_graph")` and `Key("reply_composer")` lazily. Until AEA-51 binds them, a turn
     raises `RuntimeError("not bound: run_graph")`. A live run on today's `main` would therefore fail at turn 1, so
     part C still needs AEA-51.
   - Part A does not import AEA-40 code, so nothing in part A changes.
   - `TurnRequest` is `{turn_id, payload}`, as §4.2 already says.
4. **What AEA-35 adds for part B:** the specialist report models are on `main`, in `meridian.domain.specialists`:
   - `KnowledgeReport(points: list[ReportedPoint] (≤ 5), answered: bool)`;
   - `AccountReport(summary: str (≤ 300))`;
   - `SchedulingReport(appointment_id: int, wanted_time: str, note: str (≤ 200))`.

   The B1 table now names them in place of the earlier `<… report>` placeholders. The report tool is
   `REPORT_FACTS_TOOL` (`"report_facts"`), which AEA-51's `report(model, **fields)` helper wraps.
5. **Still not on `main`:** AEA-51 (ledger `blocked`, "a blocker is not merged": AEA-37 sent back, AEA-39
   NEEDS-DECISION) and AEA-60 (same chain). `tests/integration/` holds only `__init__.py`.
   `tests/contract/test_prompts_vs_consumers.py` does not exist. Part A is still buildable now. Parts B and C stay
   blocked.
6. **Blockers recorded for the orchestrator:** part A none; part B AEA-51; part C AEA-51, AEA-60 and `gate::paid`.

**Refresh 2 (2026-10-21, `main` at `cf8fd78`).** History; superseded by refresh 3 above.

1. **Merged since refresh 1:** AEA-24 (eval harness, `7fddbf5`), AEA-50 (`67c5ffe`, ledger now `merged`), AEA-54 (docs),
   and **AEA-30** (`cf8fd78`: `services/demo.py`, `services/scheduler.py`, the `register_demo` hunk). `src/` had no other
   change; `tests/journeys/support/`, `eval/cases/dev/`, `pyproject.toml` (markers `journey`, `live`; `--strict-markers`;
   mypy `files = ["src/meridian", "tests", "eval"]`) and `scripts/agent_version.py` were re-read and match §4.1.
2. **Still not on `main`:** AEA-51 (ledger `blocked`: "a blocker is not merged"; it waits on AEA-35 and AEA-39
   NEEDS-DECISION, AEA-36, 37, 40 blocked), AEA-60 (ledger `blocked`, same chain). Parts B and C stay blocked; part A
   stays buildable now.
3. **What AEA-30 changes for this slice (and the decisions taken):**
   - A fresh working copy reads `demo_state` as `DEMO_START`, `nobody_online` without writing
     (`repos_cases_state.py` line 42), and `DemoClock.now()` reads that row; demo time never moves with wall time. So
     §A5's WP-4 expectation (`promise_for(…, "nobody_online", DEMO_START, …)`) holds on the live app.
   - All six dev scripts have `staffing = "nobody"`. **PD-15 (new):** `play_case` refuses a script whose `staffing` is
     not `"nobody"` as a player error (the smoke never calls the demo controls), so a later staffed case cannot run
     against the wrong presence silently (step A4.0).
   - `register_demo` now starts a `SchedulerThread` (60 s tick, daemon) at app start and stops it on close, before
     storage closes. Nothing to do here: `launch_server` closes the container before §A7 step 5 removes the temp folder.
     Its SQLite opens land under the temp data dir and count as `<outside repo>` in AC-13's folder counts.
4. **PD-9 simplified:** `agent_version_cli` takes the SHA from `scripts.agent_version.build_sha_from_git(REPO_ROOT)`
   (AEA-50, same `rev-parse HEAD` + `-dirty` rule) instead of re-implementing the two git calls.
5. **Blockers recorded for the orchestrator:** part A none; part B AEA-51; part C AEA-51, AEA-60 and `gate::paid`.

**Refresh 1 (2026-10-21, `main` at `ef561fc`, 79 commits after `e22aebb`).** Read this box first. Everything below it
was re-checked against `main` and kept where it still holds.

1. **Merged since the first write:** AEA-50 (`67c5ffe`; `scripts/agent_version.py` is on `main`, so AEA-50 is **no
   longer a blocker**; the build ledger still shows it `built`, which is stale), AEA-17 and AEA-18 (the production
   adapters; `register_anthropic`, `register_jev`), AEA-43 (`listDemoInbox` route), AEA-29 (cases and handoff), AEA-27,
   AEA-28, AEA-34, AEA-38. `tests/journeys/support/` has **not changed**; every §4.1 name was re-read from it.
2. **Still not on `main`:** AEA-51 (ledger `ready`; it waits on AEA-35, which is NEEDS-DECISION, plus AEA-30, 36, 37,
   39, 40), AEA-60 (`ready`), AEA-40 (`register_chat` is still a no-op), AEA-30 (`register_demo` is a no-op).
   `tests/integration/` holds only `__init__.py`; `tests/contract/test_prompts_vs_consumers.py` does not exist.
3. **What this refresh changed:**
   - (a) The work is split into parts A/B/C, so the part with no unmerged dependency can start now.
   - (b) The live run builds its own KB index (`build_live_index`, a copy of the WF-14 CLI call the retrieval contract
     test already makes). Parts A and C therefore import nothing from AEA-51's test helpers.
   - (c) **Defect fixed.** Signals (`planner_fallback`, `classifier_fallback`) are logged with
     `extra={"signal": …}` (`meridian/agent/signals.py`), but AEA-57's `LogTap.structured(kind)` reads only the
     `meridian_record` attribute. `logs.structured("signal")` therefore always returns `[]`, and the earlier fallback
     check would have passed silently. The player now attaches its own `SignalTap` handler to the `meridian.signal`
     logger (PD-6; follow-up request R-11 to AEA-57).
   - (d) The form field of a scripted turn is `ScriptedTurn.form`, not `values` (`values` is the CON-2 payload key).
   - (e) Tool names come from their constants (`KB_SEARCH_NAME`, `READ_INVOICES_NAME`, `MOVE_VISIT_NAME`, …).
   - (f) WP-4's expected due time comes from `policy.handoff.case_due_at`.
   - (g) `HELDOUT_KEY_ROOT` is the absolute path in `eval/cases/FORMAT.md` §6.
   - (h) The earlier claim that AEA-57 greps journey files for `heldout` was wrong (no such check exists on `main`). The
     prohibition stays as a rule of this plan.
   - (i) AC-11's "claims the move" check now skips negated sentences (PD-13).
   - (j) AEA-50 was removed from the blockers.

---

## 1. Goal and sources

### Goal (issue *What to build*, quoted in short)

> "This issue adds the **live-model smoke set** that `integrated-journeys.md` rule 4 defines, runs it once now that the
> integrated path exists, and records the result at the level `verified with live models`. **It proves limited
> compatibility only**: it is never an E-run, never reported as containment, accuracy or quality, and writes nothing the
> eval pages read."

**What a run does, concretely (input → process → output).**

- **Input:**
  - six dev cases: `WP-1`, `WP-2`, the first dev warranty case (today `T-CALL-20260723-0276`), `WP-4F`, `DANGER`,
    `WP-4`;
  - `LIVE_SMOKE_SPENT_TODAY_USD=4.10` (say).
- **Process:**
  1. The spend guard checks `4.10 + 0.234 ≤ 30.00`.
  2. The live index is built once with the cached embedder.
  3. Then, one case at a time:
     - a temp folder gets a fresh environment;
     - `create_app(settings)` with **no overrides** starts under uvicorn on `127.0.0.1:<ephemeral>`, so the container
       binds the real `AnthropicAdapter` and `JevAdapter`;
     - the app's first boot copies the issued DB;
     - the driver logs in with the run's demo pair, opens a chat and plays the case script turn by turn through
       `submitTurn`. The form turn fills `$seed:name`/`$seed:phone` from the working copy; the code turn reads
       `listDemoInbox`;
     - after the last turn it reads `turns`, `spend_ledger`, `lookup_log`, `actions`, `check_events`, `cases` and
       `promises` from that copy, plus the signal log records, and runs the case's checks;
     - it stops the server and deletes the folder.
- **Output:**
  - six pass/fail lines;
  - per turn: `trace_id`, `trace_export`, `server_ms`;
  - per call: model, `provider_request_id`, `failure_kind`, `latency_ms`, `cost_usd`;
  - the run total summed from `spend_ledger`;
  - one record, `docs/testing/journeys/<date>-live-smoke-1.md`.

The same driver and checks run **free** in four journey files with the scripted model (part B: AEA-51's step scripts
on AEA-57's harness). A scripted good run passes, and a scripted bad run (one skipped tool call or write) is caught by
the same assertion the live run uses.

### Context

- AEA-57 landed the harness. AEA-51 (wave 3) wires the real graph and proves the customer path with scripted models.
  AEA-60 checks rendered prompts against their consumers. None of them calls a real model.
- SP-1 found a live-only gap on WP-4F: "the move happened but the next turn's responder said it had not" (DO-5
  *Failure taxonomy*, state seam).
- This ticket is the first and only place real providers run through the app before AEA-56 deploys it.
- Each paid run is `gate::paid` and needs Innocent's stated spend so far (D-15), because the app's own cap only sees a
  throwaway DB.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-61.md` | AC-1…AC-18, owned files, commands, spend rule ($0.039/case, $0.234/run), custody rule |
| Slice plan | `docs/plans/slice-plan.md` §0a (journeys J-2…J-5; levels; "live smoke is AEA-61; each paid run needs Innocent to state the day's spend"), §1 row AEA-61 (wave 4; blockers 51, 57, 60, 06, 50), §3 (`tests/live/` is 61's; `tests/journeys/` one file per ticket per journey; `support/` is 57's) | Ownership, waves, journey ids |
| Sign-off | `docs/plans/stage7-signoff.md` D-15 ("the spend line is still to be set before wave 4 (a statement, not a choice)"), D-14 (DAT-2 = B: held-out keys outside the repo) | Gate before the paid run; the held-out key folder the audit hook watches |
| Rules | `.claude/rules/integrated-journeys.md` rule 4 (live smoke: when, dev cases only, spend, what to record, compatibility only), rule 6 + §4 (levels, the nine record fields, scope `live-smoke-N`), §5 (*Live smoke* row), rule 7 (paid calls inside the cap); `build-loop-test-scope.md` + *AEA addition* ("The suite has no paid calls … never part of a merge gate"; cheapest first); `context-maintenance.md` | Commands, record, gates |
| Code design (DO-3) | `docs/design/code-design.md` §9, line 715 `└── live/             marked `live`: paid calls, never in the default run (recordings feed contract/)` | AC-18 annotation |
| Contracts (DO-4 + addenda; addenda win) | `stage7/models.md` §1–§4, §6, §7 (`spend_ledger` columns, failure kinds, `LedgerService`, adapters bound by role maps); `stage7/graph-core.md` §12 (`Settings`, `role_model_map()`); `stage7/web.md` §4 (eval headers, `run_tag`), §13 (`assert_response_matches`), §15 (`create_app(settings, overrides=None)`, R-W-8); `stage7/data.md` §1 (`redact`, profiles), §3 (WF-14 ingest CLI), §5 (`CaseScript`, `ScriptedTurn`, `CaseKey`, layout, "runner refuses on mismatch"), §6 (eval reports this run must not write), §7 (`python -m scripts.agent_version`); `stage7/cases.md` §1.1 (`DEMO_START`); `stage7/graph-nodes.md` §4 (signals are log records) | §4 copies |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` *Who may read what*, *Expected-answer authority*, E-1 hard gates, *Failure taxonomy* | Dev split only; hard items only; not an E-run |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-1 (turn, spend, lookup, check, case, promise), WF-3 (inbox), WF-18 (login), *Status values*, `signal` record | Reads only; writes nothing new |
| Metrics (DO-7) | M-23 (`turn.server_ms`), M-24 (`failure_kind`, `http_status`, `degrade_reason`), M-25 (cost per conversation; SP-1 B max $0.039 [M]), M-26 ($30/day, Chicago day), M-29 (`trace_export`) | Copied into the record, never compared with a line |
| Case files | `eval/cases/FORMAT.md` §2 (schema validation recipe), §3 (`clock` is always the demo start; `$seed:` tokens; `code_from_inbox` holds no digits), §6 (held-out keys at `/home/linuxuser/.meridian-sealed/heldout/`); `eval/cases/models.py`, `eval/cases/checks.py` | Loader and custody |
| Current code (re-read at `ef561fc`; refresh 2 re-checked at `cf8fd78`; refresh 3 re-checked at `76f14f4`, adding `domain/specialists.py` report models and `web/schemas/chat.py`; refresh 4 re-checked at `b68df7e`, adding `agent/nodes/plan.py` (planner fallback, classifier fallback) and `domain/turn.py` `CheckEvent.from_danger`; refresh 2 added `services/demo.py`, `web/container.py` `register_demo`, `adapters/sqlite/repos_cases_state.py`) | `tests/journeys/support/{env,server,run,client,db,logtap,record,steps,scripted_model,plugin}.py`; `src/meridian/{config,web/app,web/container,web/middleware,web/logging,agent/signals,agent/tools/{knowledge,account,scheduling},policy/limits,policy/texts,policy/handoff,privacy/redact,retrieval/{manifest,settings,ingest},adapters/retrieval_fastembed,adapters/sqlite/repos_cases_state,domain/blocks}.py`; schema `00_core.sql`, `20_spend.sql`, `60_cases.sql`, `95_ops.sql`; `scripts/agent_version.py`; `tests/unit/adapters/test_retrieval_fastembed.py`; `tests/contract/test_retrieval_contract.py` (real-index recipe); `ui-contracts.openapi.yaml` (read only) | §4 copies |
| Sibling plans (not on `main`) | `docs/plans/fanout/2026-10-21-build/AEA-51.md` §5 C1 (support module API, re-read at its refresh 2 and against branch `aea-51-aea-51-customer-path` at `e9d07f3` in refresh 5), D1/D2 (scenario building blocks, `TOOLS`); AEA-60's test file is on `main` since `0e37fad` | Part B names in §4.3; re-checked at part B's step B0 |

### Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Six dev cases in table order; warranty = first dev key by `case_id` with `topic=warranty`, `in_scope=true` | ticket table | AC-1 | in-ticket | A2 |
| Loader refuses outside `eval/cases/dev/`, `..`, symlink out, `split=held-out`; error carries case id only | ticket *Held-out custody* | AC-2 | in-ticket | A2 |
| Case `clock` must equal `DEMO_START` | data.md §5 ("runner refuses on mismatch"); FORMAT §3 | AC-1 | in-ticket; a `null` clock is refused too (PD-4) | A2 |
| Schema validation of script and key | data.md §5, FORMAT.md §2 | AC-1 | in-ticket | A2 |
| Spend pre-flight and between-case stop | ticket *Spend*; models.md §6; M-25, M-26 | AC-3 | in-ticket; comparisons in integer micro-dollars (PD-5) | A3, A7 |
| Paid tests skip unless opted in with both keys | build-loop *AEA addition*; ticket | AC-4 | in-ticket | A1, A7 |
| No network in the free run | ticket AC-4 | AC-4 | in-ticket: package-scoped socket guard in `tests/live/conftest.py` (PD-8) | A1 |
| Every response validated against the OpenAPI | web.md §13 | AC-12 | in-ticket (through `JourneyClient.call`) | A4 |
| Per-turn and per-call evidence; run total from `spend_ledger` | rule §4; ticket | AC-14 | in-ticket | A4, A6 |
| Failing assertion quoted "after `redact(text, LOG)`" | ticket AC-9, AC-14 | AC-9, AC-14 | **adjusted (PD-1):** `redact(…, LOG)` returns `""` by contract (data.md §1; `redact.py` line 48 `text: str  # the redacted text; LOG: ""`), so a quote would be empty. Quotes use the **TRACE** profile plus a scrub of every forbidden value. The implementer's report lists PD-1, PD-6, PD-7 and PD-13; the orchestrator posts one issue comment proposing the wording | A6 |
| No secret in record or output | R-42 (public repo); ticket | AC-15 | in-ticket | A6, A7 |
| Not an E-run: no eval key, `run_tag=live`, no `eval/reports/` write, no `eval_runs` row, the compatibility line | web.md §4, data.md §6 | AC-16 | in-ticket. Header, tag and row checks run inside every case check (A5); the scripted dry run is part B | A5, B3 |
| `planner_fallback` / `classifier_fallback` | graph-nodes §4 (signal log records); AEA-51 (`classifier` check event `fallback`) | AC-12 ("check_event") | **adjusted (PD-6):** counted from the `signal` records caught by the player's own `SignalTap`, from `check_events(check_kind='classifier', result='fallback')`, and from `turns.planner_fallback_used = 1` | A4, A5 |
| "One `lookup_log` row for INV-204411" after verification | ticket AC-7 | AC-7 | **interpreted (PD-7):** at least one row with a snapshot (not `refused:*`, not `failed`) with `INV-204411` in `record_ids`, in a turn at or after the verified turn; the count goes in the record | A5 |
| Agent version stamped from `python -m scripts.agent_version` | data.md §7 | AC-14 | in-ticket. Run with `RAILWAY_GIT_COMMIT_SHA=<HEAD>` in the subprocess env, because `resolve_git_sha` reads that name first, then a `BUILD_SHA` file, else `unknown` (PD-9) | A7 |
| KB index for the live app "built by the WF-14 CLI … when the harness provides none" | ticket *Agent handoff*; data.md §3 | — | in-ticket: `build_live_index` calls `meridian.retrieval.ingest.main(...)` with the cached embedder (PD-2) | A7 |
| Journey files one per ticket per journey; never edit `support/` | slice plan §3; AEA-57 README | AC-5 | in-ticket | B2 |
| Scripted journey evidence record | integrated-journeys rule 6 | no | **added**: `docs/testing/journeys/<date>-AEA-61.md` via `--journey-record=AEA-61` (as every sibling does) | B4 |
| Context rows | context-maintenance | AC-18 | in-ticket. The ICM row is **added** in part A, its evidence updated in part B and replaced by the live record in part C | A8, B4, C2 |
| AEA-60's prompt check on the same revision before the paid run | ticket *Commands* | — | in-ticket | §7 check P1 |
| Paid run only after Innocent's go with the spend statement | D-15; `gate::paid` | AC-17 | **gate** (not a plan decision) | §9 Gates |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (test-only driver; it calls the existing operations `login`, `startChatSession`, `submitTurn`, `listDemoInbox`, `requestPerson`) | WF-1, WF-3, WF-18, read only | yes (DO-6) | nothing new is emitted |

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer creates or edits)

| File | Part | Create / modify | Responsibility (one sentence) | Target / hard cap (lines) |
|---|---|---|---|---|
| `tests/live/conftest.py` | A | create | The package-scoped no-network guard for the free run | ≤ 60 |
| `tests/live/smoke.py` | A | create | The facade: re-exports the public API and owns `execute()`, the live index, the live environment and the live launcher | ≤ 320 / 500 |
| `tests/live/smoke_cases.py` | A | create | Custody-checked loading of dev scripts and keys, and the six-case selection | ≤ 250 / 500 |
| `tests/live/smoke_spend.py` | A | create | Spend pre-flight and the between-case stop rule | ≤ 120 / 500 |
| `tests/live/smoke_player.py` | A | create | Plays one case over HTTP and reads its stored evidence and signal records | ≤ 420 / 500 |
| `tests/live/smoke_checks.py` | A | create | Per-case invariants, hard key items and compatibility checks | ≤ 470 / 500 |
| `tests/live/smoke_record.py` | A | create | Quote/scrub helpers, record rendering and writing | ≤ 300 / 500 |
| `tests/live/smoke_audit.py` | A | create | The `sys.addaudithook` path recorder and the offending-path rule | ≤ 120 / 500 |
| `tests/live/test_smoke_guards.py` | A, B | create (A), add one test (B) | Free tests AC-1, AC-2, AC-3, AC-4, AC-14 (fixture render), AC-15 (sentinels); AC-16 in part B | ≤ 490 / 500 |
| `tests/live/test_live_smoke.py` | A | create | The paid tests (`live`): six cases, compatibility, custody, record, secrets | ≤ 300 / 500 |
| `tests/live/scripted_cases.py` | B | create | Scripted good/bad step tables per case for the journey files and AC-16 | ≤ 450 / 500 |
| `tests/journeys/j2/test_aea_61.py` | B | create | J-2 scripted: WP-1, WP-2, warranty good; WP-1 without `kb_search` caught | ≤ 200 |
| `tests/journeys/j3/test_aea_61.py` | B | create | J-3 scripted: WP-4F good; WP-4F without `move_visit` caught | ≤ 120 |
| `tests/journeys/j4/test_aea_61.py` | B | create | J-4 scripted: WP-4 good; WP-4 without `request_visit_change` caught | ≤ 120 |
| `tests/journeys/j5/test_aea_61.py` | B | create | J-5 scripted: DANGER good; DANGER without the raise caught | ≤ 120 |
| `docs/testing/journeys/<date>-AEA-61.md` | B | create (written by the record command) | Scripted-level evidence record | generated |
| `docs/testing/journeys/<date>-live-smoke-1.md` | C | create (written by the paid run) | The first live record | generated |
| `.claude/reference/area-map.md` | A, B, C | append to the last cell of row `3+` only | AC-18 | — |
| `.claude/state/icm-progress.md` | A, B, C | add one *Routes verified against code and tests* row (A); replace its evidence (B, C) | AC-18 | ≤ 400 chars per row |
| `docs/design/code-design.md` | A | modify the one `└── live/` line in §9 (line 723 at `dc8d8d0`; find it by its text) | AC-18 | — |

- `tests/live/__init__.py` exists (AEA-01) and stays unchanged.
- The ticket lists `conftest.py`, `smoke.py`, `test_smoke_guards.py` and `test_live_smoke.py`. The six helper modules sit
  inside the owned folder (collision map: "`tests/live/` | 61"). They exist only to keep every file under the 500-line
  test cap (`code-structure.md`). See §8 R-5.

### 2.2 Shared surfaces read only (never edit)

- **Product code and harness:** `src/meridian/**`; `tests/journeys/support/**` (AEA-57; import only);
  `tests/journeys/{README.md,affected.py,__init__.py}`, `tests/journeys/j*/__init__.py`, and every other
  `tests/journeys/j*/test_aea_*.py`.
- **AEA-51's helpers (part B only):** `tests/integration/customer_support.py`, `tests/graph/worked_pair_scenarios.py`
  (import only, once merged).
- **Other test code:** `tests/api/openapi_check.py` (AEA-23); `tests/fixtures/**`, `tests/fakes/**`;
  `tests/unit/adapters/test_retrieval_fastembed.py` (import `KB_DIR`, `TRANSCRIPTIONS_DIR`, `cached_model_dir`);
  `tests/conftest.py`.
- **Eval and scripts:** `eval/**` (read the dev files and `case.schema.json`; import `eval.cases.models` and
  `eval.cases.checks`); `scripts/agent_version.py` (run it, never edit).
- **Config and contracts:** `pyproject.toml`, `uv.lock`; `docs/ux/03-structure/ui-contracts.openapi.yaml`,
  `UI_CONTRACTS.md`.
- **Never touched:** `apps/web/**`, `docs/ux/**`; the briefing, issued data, `docs/archive/`, `docs/parked/`;
  `.claude/state/resume.md`, `.claude/state/build-ledger.md`.

### 2.3 Owned by other slices (do not touch)

- `tests/journeys/support/` (57); `tests/integration/`, `tests/graph/` and `tests/capture/` CAP-1…3 (51);
  `tests/contract/` (17, 18, 51, 59, 60); `eval/harness/` (24); `eval/cases/` (06); `scripts/` (50); and every
  `register_*` hunk in `web/container.py`.
- A fix that a smoke failure needs belongs to the owning ticket as a follow-up (integrated-journeys rule 5), never here.

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's; one row each)

Module shorthand: **C** `smoke_cases.py`, **$** `smoke_spend.py`, **P** `smoke_player.py`, **K** `smoke_checks.py`,
**R** `smoke_record.py`, **A** `smoke_audit.py`, **S** `smoke.py`, **G** `test_smoke_guards.py`, **L** `test_live_smoke.py`.

| AC | Part | Level | Requirement (short) | How | Verified by → evidence |
|---|---|---|---|---|---|
| AC-1 | A | mock-tested | Exactly six dev cases in table order; schema-valid; `split=dev`; clock ≠ `DEMO_START` refused | C `select_smoke_set`, `load_dev_case` | `tests/live/test_smoke_guards.py::test_smoke_set_is_six_dev_cases` → the six ids with labels printed; the clock refusal `WP-1: clock_mismatch` |
| AC-2 | A | mock-tested | Refuse a held-out path, `..`, a symlink out, `split=held-out`; named error with the case id only; no warranty case → `NOT_RUN: no dev warranty case`, nothing else loaded | C `checked_dev_path`, `CaseCustodyError`; A hook | `::test_refuses_heldout_and_outside_dev` → each refusal string; 0 offending opened paths |
| AC-3 | A | mock-tested | Pre-flight refusals (unset, non-finite, negative, over cap) before any app; between-case stop; stop on the cap notice or cap failure kinds; `NOT_RUN: spend` | $ `preflight`, `should_stop`; S `run_cases`, `execute(make_launcher=…)` | `::test_preflight_refuses_over_cap`, `::test_stops_between_cases_and_on_cap` → refusal texts; `made == 0, launches == 0`; `NOT_RUN: spend` rows |
| AC-4 | A | mock-tested | Paid tests marked `live` and skipped unless `MERIDIAN_LIVE_SMOKE=1` and both keys | S `live_skip_reason`; L `pytestmark`; conftest guard | `uv run pytest tests/live -q -rs` (10 skipped, 0 blocked connections) and `::test_live_cases_skip_without_opt_in` |
| AC-5 | B | **integrated with a scripted model** (the ticket's single `[journey]` criterion) | J-2 (WP-1, WP-2, warranty), J-3 (WP-4F), J-4 (WP-4), J-5 (DANGER): scripted good runs pass; one bad script per file is caught by the live assertion | four journey files over AEA-51's `open_customer_run` + P `play_case`, K `check_case`; `scripted_cases.py` | `uv run pytest tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py -m journey -q` → good tests pass; bad tests print the caught message; `git diff --name-only main...HEAD -- tests/journeys/support` empty |
| AC-6 | C | live | WP-1: passages current only, no `archive/`; each reply's citation in that turn's lookups; no `$149`; no case, no identity; hard items | K `check_membership` | `tests/live/test_live_smoke.py::test_live_case[WP-1]` → pass line with passage ids and citations per turn |
| AC-7 | C | live | WP-2: code from `listDemoInbox` submitted as a `code` turn; no INV-204411 read before `actions(verified)`; after it a snapshot row; hard items | K `check_billing` | `::test_live_case[WP-2]` → pass; row order in the record |
| AC-8 | C | live | Warranty: current passages only, never `archive/warranty_terms_2023.txt`; citations in lookups; account read only after verified; hard items | K `check_warranty` | `::test_live_case[warranty]` → pass with the chosen `case_id` |
| AC-9 | C | live | WP-4F: one `actions(moved)`; appointment 159 on slot 56; no fee text; the follow-up `settled` lists the move; no completion trim on it; no case | K `check_follow_up` | `::test_live_case[WP-4F]` → pass; the follow-up reply quoted (PD-1) |
| AC-10 | C | live | DANGER: first block = the emergency line text; P1 case; `gate_result=danger`, `outcome=safety_reply`; no identity or lookup first; path + model-call count recorded | K `check_safety` | `::test_live_case[DANGER]` → pass with path and call count |
| AC-11 | C | live | WP-4: appointment 1 row byte-equal; no `moved`; P2 case due 12:00 on the demo day; promise text from `policy/handoff.py`, `produced_by_code`; no surviving "moved" claim | K `check_fee_bearing` | `::test_live_case[WP-4]` → pass; row compare, case, due, promise |
| AC-12 | C | live | Compatibility over all six: 0 OpenAPI mismatches; no forbidden failure kind; no `degraded_handoff`/`model_error`; no planner/classifier fallback; retried successes counted | K `check_compatibility`, `compat_counts` | `::test_live_compatibility` → 0 mismatches; counts per provider and role in the record |
| AC-13 | C | live | Issued DB hash unchanged; audit hook: no opened path under `eval/cases/` except `dev/` and the schema, none under the held-out key folder | A `audit_opened`, `offending_paths`; S run | `::test_issued_and_heldout_untouched` → equal hashes; 0 offending; counts by folder in the record |
| AC-14 | A (render) + C (paid) | live + mock | Record with all nine fields, level, revision + agent version, environment, command, per-case result, evidence (per turn, per call, totals, spent-today figure and source), limitations, blocked-by | R `render_smoke_record`, `write_smoke_record` | `::test_record_written` (paid) and `tests/live/test_smoke_guards.py::test_record_has_every_field` (fixture) → the committed record; run total = `SUM(cost_usd)` |
| AC-15 | A (sentinels) + C (paid) | live + mock | No key, session secret, demo password, inbox code or seeded full phone in the record or the run output | R `scrub`, `quote`; L capture | `::test_record_and_output_hold_no_secrets` (last) and `test_smoke_guards.py::test_record_writer_redacts` → 0 hits per value |
| AC-16 | A (checks) + B (dry run) | mock-tested | Not an E-run: no eval header; `run_tag=live`; `eval/reports/` unchanged; 0 `eval_runs`; the compatibility line in the record | P records request headers; K generic invariants; R constant line | `test_smoke_guards.py::test_not_an_eval_run` (part B) → listing unchanged; 0 eval headers; 0 rows; line present |
| AC-17 | C | live | First paid run recorded and green (all six pass, inside the remaining cap); a failure is reproduced on its owner ticket, not fixed here | part C (§5 C1–C2) | the paid command, then `git log -- docs/testing/journeys/` |
| AC-18 | A, B, C | regression/context | Area map row `3+`, ICM row, DO-3 §9 `live/` line | A8, B4, C2 | `git diff --name-only main...HEAD` → owned files only |

The ticket's **WP-N worked pairs** are WP-1, WP-2, WP-4 and WP-4F (plus DANGER and one transcript-derived warranty case).
Their tests are `test_live_case[...]` (live, part C) and the four scripted journey files (free, part B). The **single
`[journey]` criterion is AC-5, at level `integrated with a scripted model`.** Until part B lands, the ticket's journey
level is `mock-tested` and the part A record line says `blocked by AEA-51`.

### 3.2 Plan decisions (engineering; the reviewer checks them)

| ID | Decision | Why |
|---|---|---|
| PD-1 | Quotes in failures and the record use `redact(text, RedactionProfile.TRACE).text`, cut to 300 chars, then `scrub(…, forbidden)`; never `LOG` | `LOG` returns `""` by contract (data.md §1); TRACE masks codes, cards, phones, emails, streets and introduced names |
| PD-2 | The live run builds its own environment: AEA-57's `journey_environ(root)` + the real keys + the index from `build_live_index` + the agent version + the four `LANGFUSE_*` only when all four are set; never `MERIDIAN_EVAL_KEY` | `journey_environ` hard-codes placeholder keys and an empty index; web.md §15 says no overrides; building the index here keeps parts A/C free of AEA-51's test helpers |
| PD-3 | Scripted runs (part B) use AEA-51's `open_customer_run` (AEA-57's harness pieces + built index + per-step scripts) | J-2…J-5 need a built index and per-turn model tables; AEA-57's `journey` fixture has neither, and AEA-51 owns the scripted encodings |
| PD-4 | A case script with `clock = null` is refused as `clock_mismatch` | The smoke assumes the demo start; data.md §5 refuses on mismatch; FORMAT §3 says `clock` is always the demo start |
| PD-5 | Money comparisons in integer micro-dollars (`round(usd * 1_000_000)`); "would pass" means strictly greater | `29.766 + 0.234` must equal `30.0` exactly (allowed); floats would refuse it |
| PD-6 | "Fallback" means any of: a `signal` record named `planner_fallback` or `classifier_fallback` for the thread (caught by the player's own `SignalTap` on logger `meridian.signal`); a `check_events` row with `check_kind='classifier'`, `result='fallback'`; or `turns.planner_fallback_used = 1` | graph-nodes §4 makes them log records; AEA-57's `LogTap.structured()` cannot see them (refresh box (c)) |
| PD-7 | WP-2: ≥ 1 post-verification INV-204411 row with a snapshot (count recorded), none in an earlier turn; a row whose `result_seen` starts with `refused:` or equals `failed` is not a read (`agent/tools/account.py` writes `refused:not_verified`) | A live model may read the invoice on two turns, or try once before the code; neither is an incompatibility |
| PD-8 | The free-run network guard is a **package-scoped** autouse fixture (not session-scoped), so it never outlives `tests/live/` | A session-scoped patch of `socket.connect` would leak into every later test in a full-suite run |
| PD-9 | `scripts.agent_version` runs as a subprocess with `RAILWAY_GIT_COMMIT_SHA=<build_sha_from_git(REPO_ROOT)>` in its env (`scripts.agent_version.build_sha_from_git`: `rev-parse HEAD`, `-dirty` when `git status --porcelain --untracked-files=no` is non-empty) | `resolve_git_sha` reads that name, then a `BUILD_SHA` file, else `unknown`; no `BUILD_SHA` file is written into the repo; one owner of the SHA rule (AEA-50) |
| PD-15 | `play_case` refuses a script with `staffing != "nobody"` as a player error before logging in | A fresh copy is `nobody_online` at `DEMO_START` (AEA-30); the smoke never calls demo controls, so a staffed script would run against the wrong presence |
| PD-10 | Visible text = every string inside the response blocks except under the keys `block_id`, `at`, `type`, `speaker`, `card_id`, `passage_id`, `excerpt`, `audience`, `version_date`, `version_label`, `file`, `section`, `option`, `slot_id`, `wanted_text`. Hard `must_say`/`must_not_say` = exact substring after collapsing whitespace and replacing `’` with `'` | DAT-6: items are exact phrases; source excerpts are quoted KB text and `wanted_text` is the customer's words, not the agent's |
| PD-11 | Hard `must_do` items map by exact text to named invariants (the `HARD_MUST_DO` table, A5); an unmapped hard `must_do` text fails the case with `unmapped hard must_do item` | Nothing passes silently; judge and soft items are not scored (ticket *Evaluation*). The three hard `must_do` texts in today's six keys are all mapped |
| PD-12 | The live record is written by the module fixture even when cases fail | AC-17 keeps failing records beside later ones |
| PD-13 | WP-4 "a reply claims the move": a sentence of a `text` block matching `\b(?:moved\|rescheduled)\b` and **not** matching the negation pattern in A5 | A plain "moved" grep would fail on "it has not been moved", which is the honest reply |
| PD-14 | AC-3's "adapter constructions" are counted at the launcher seam: `execute()` calls `make_launcher()` (which builds the index and returns a launcher that builds apps and so adapters) only after `preflight` returns, and the stub counts `make` calls and launches | The free test cannot construct real adapters without keys; the seam is where construction would start |

---

## 4. Shared code to use (copied from the current code at `cf8fd78`, re-checked unchanged at `76f14f4`, `b68df7e` and `dc8d8d0`; the addenda; or the sibling plan named)

### 4.1 On `main` now (import exactly these)

```python
# tests/journeys/support/env.py (AEA-57)
REPO_ROOT = Path(__file__).resolve().parents[3]
def journey_environ(root: Path) -> dict[str, str]: ...
    # keys: ANTHROPIC_API_KEY, OPENROUTER_API_KEY (placeholders), MERIDIAN_DEMO_USERNAME, MERIDIAN_DEMO_PASSWORD,
    #   MERIDIAN_SESSION_SECRET (per-run letters), MERIDIAN_COOKIE_SECURE="false", MERIDIAN_REQUIRE_FRONTEND="false",
    #   MERIDIAN_WEB_DIST_DIR=root/"no-dist", MERIDIAN_DATA_DIR=root/"data", MERIDIAN_INDEX_DIR=root/"index".
    #   No eval key, no LANGFUSE_*, no agent version.
@dataclass(frozen=True)
class JourneyEnv:
    root: Path; data_dir: Path; web_dist_dir: Path; index_dir: Path; settings: Settings; issued_sha256_before: str
    @property
    def db_path(self) -> Path: ...                       # data_dir / WORKING_DB_NAME
    def secret_values(self) -> tuple[str, str]: ...      # (demo password, session secret)

# tests/journeys/support/server.py (AEA-57)
@contextmanager
def launch_server(settings: Settings, *, overrides: ContainerOverrides | None, startup_timeout_s: float = 30.0
                  ) -> Iterator[RunningServer]: ...    # uvicorn thread, 127.0.0.1:0, log_config=None; refuses 4019, 5184
class SocketGuard: blocked: list[tuple[str, int]]      # SocketGuard() with no patch is inert
@contextmanager
def socket_guard() -> Iterator[SocketGuard]: ...       # patches socket.connect/connect_ex; refuses non-loopback

# tests/journeys/support/run.py (AEA-57)
@dataclass
class JourneyRun:
    env: JourneyEnv; server: RunningServer; script: JourneyScript; models: Mapping[Role, ScriptedModel]
    clock: StepClock | None; db: DbReader; logs: LogTap; guard: SocketGuard; collector: StepCollector
    strict: bool; nodeid: str; clients: list[JourneyClient] = field(default_factory=list)
    # properties: settings, app, container, base_url, demo_username
    def client(self) -> JourneyClient: ...
    def login(self, client: JourneyClient | None = None) -> LoginResult: ...   # POST /api/login (operation "login");
        # raises AssertionError on non-200, on != 1 new staff_sessions row, or on no mhc_session cookie
    @contextmanager
    def step(self, journey: str, name: str, *, needs: Sequence[str] = (), operations: Sequence[str] = ()) -> Iterator[None]: ...
    def close_clients(self) -> None: ...
@dataclass(frozen=True)
class LoginResult: client: JourneyClient; response: httpx.Response; session_id: str; cookie: str

# tests/journeys/support/client.py (AEA-57)
class JourneyClient:
    def __init__(self, base_url: str, *, transport: httpx.BaseTransport | None = None) -> None: ...   # timeout 70 s
    responses: list[httpx.Response]
    def call(self, method: str, path: str, *, operation_id: str | None, body: object | None = None,
             headers: Mapping[str, str] | None = None) -> httpx.Response: ...
        # appends the response to self.responses FIRST, then assert_response_matches; a mismatch raises
        # AssertionError(f"{operation_id} -> HTTP {status}: {exc}")
    def close(self) -> None: ...

# tests/journeys/support/db.py (AEA-57)
class DbReader:  # mode=ro, one connection per call
    def __init__(self, db_path: Path) -> None: ...
    def rows(self, sql: str, params: Sequence[object] = ()) -> list[dict[str, Any]]: ...
    def one(self, sql: str, params: Sequence[object] = ()) -> dict[str, Any]: ...     # AssertionError unless exactly 1
    def scalar(self, sql: str, params: Sequence[object] = ()) -> Any: ...
    def count(self, table: str, where: str = "", params: Sequence[object] = ()) -> int: ...
def sha256_file(path: Path) -> str: ...

# tests/journeys/support/logtap.py (AEA-57)
class LogTap(logging.Handler):                         # on the ROOT logger; keeps every record
    def all_text(self) -> str: ...                     # every record: formatted message + repr(vars(record))
@contextmanager
def tap_logs() -> Iterator[LogTap]: ...
# NOTE: LogTap.structured(kind) reads record.__dict__["meridian_record"] only; signals live in
#       record.__dict__["signal"], so do NOT use it for signals (PD-6). Use SignalTap (A4).

# tests/journeys/support/scripted_model.py (AEA-57): JourneyScript()  (an empty script for a live JourneyRun)
# tests/journeys/support/steps.py (AEA-57): StepCollector(); NEED_OWNERS keys used in part B: "session_service",
#   "turn_service", "run_graph", "identity_service", "case_service", "handoff_service", "demo_clock";
#   OPERATION_OWNERS keys used: "startChatSession", "submitTurn", "listDemoInbox", "requestPerson"
# tests/journeys/support/record.py (AEA-57)
FIELDS: tuple[str, ...] = ("Claim", "Level", "Tested revision", "Environment", "Command", "Result",
                           "Evidence location", "Remaining limitations", "Blocked by")
ISSUED_REL = "docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
@dataclass(frozen=True)
class RecordData: scope: str; values: Mapping[str, str]
def tested_revision(root: Path, agent_version: str) -> str: ...  # "<short sha>; agent_version X" | "uncommitted (HEAD sha); …"
def render_record(data: RecordData) -> str: ...  # "# Journey record: <scope> (journey harness run)" + 9-row table;
                                                 # cells escape "|" and turn "\n" into "<br>"

# tests/fixtures/sqlite.py (AEA-10): ISSUED_DB (Path of the issued scheduling DB)
# tests/api/openapi_check.py (AEA-23): assert_response_matches(response, operation_id) (used inside JourneyClient.call)
# tests/unit/adapters/test_retrieval_fastembed.py (AEA-33):
#   KB_DIR = ROOT / "docs/data/issued/meridian_dataset/knowledge_base"; TRANSCRIPTIONS_DIR = ROOT / "data/kb_transcriptions"
#   def cached_model_dir() -> Path | None   # FASTEMBED_CACHE_PATH, then var/fastembed, then the git common dir's var/fastembed

# src/meridian
from meridian.config import Settings                 # Settings.from_env(environ); .role_model_map() -> {role: {"provider",
                                                     #   "model", "effort", "cap_s", "max_tokens", "redaction"}};
                                                     #   .langfuse_complete(); .agent_version; .demo_password (SecretStr)
# env names (config.ENV_NAMES): ANTHROPIC_API_KEY, OPENROUTER_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY,
#   LANGFUSE_BASE_URL, LANGFUSE_PROJECT_ID, MERIDIAN_EVAL_KEY, MERIDIAN_INDEX_DIR, MERIDIAN_AGENT_VERSION, …
from meridian.adapters.sqlite.repos_cases_state import DEMO_START   # datetime(2026,10,16,10,0,tzinfo=ZoneInfo("America/Chicago"))
# AEA-30 (cf8fd78): a fresh copy's demo_state reads (DEMO_START, "nobody_online"); DemoClock.now() reads that row only.
#   register_demo starts SchedulerThread (60 s tick) on app start and stops it on container close. Read only; never call
#   the demo control routes from the smoke.
from meridian.policy.limits import Limits                    # Limits().spend.daily_cap_usd == 30.0
from meridian.policy.texts import TEXTS, TextId, render      # TextId.EMERGENCY_LINE_LEAD, TextId.PROMISE_UNSTAFFED
from meridian.policy.handoff import case_due_at, promise_for
    # promise_for(reason: HandoffReason, presence: Presence, now: datetime, window_start: datetime | None = None) -> Promise
    # case_due_at(reason: HandoffReason, promise: Promise, window_start: datetime | None) -> datetime | None
from meridian.domain.handoff import HandoffReason            # re-export; .FEE_BEARING_CHANGE (P2), .DANGER (P1)
# Promise (domain.common): policy_row: str; text: str; due_at: datetime | None; due_label: str | None;
#   extra_lines: tuple[str, ...] = (); live_queued: bool = False.   Presence = Literal["nobody_online", "simulated_on_shift"]
from meridian.privacy.redact import RedactionProfile, redact # redact(text, RedactionProfile.TRACE).text
from meridian.retrieval.manifest import MANIFEST, FileStatus # ManifestSpec.path, .status; FileStatus.CURRENT
from meridian.retrieval.settings import EMBEDDING_MODEL, MIN_SCORE, SEARCH_K   # "BAAI/bge-small-en-v1.5", 0.60, 3
from meridian.retrieval.ingest import main as ingest_main
    # main(argv: Sequence[str] | None = None, *, embed: EmbedFn | None = None) -> int
    # argv: ["--kb-dir", ..., "--transcriptions-dir", ..., "--out-dir", ...]; prints manifest lines; 0 on success
from meridian.adapters.retrieval_fastembed import FastembedIndex
    # FastembedIndex(index_dir, *, model_cache_dir=None, embed_query=None); .readiness() -> Readiness(ok: bool, reasons);
    # .info() -> IndexInfo(embedding_model, dimension, chunks, manifest_hash, files); .search(query, *, k, min_score)
from meridian.web.middleware import EVAL_KEY_HEADER, RUN_ID_HEADER, RUN_TAG_HEADER   # "X-Meridian-Eval-Key", "-Run-Id", "-Run-Tag"
from meridian.agent.signals import SIGNAL_LOGGER             # "meridian.signal"; emit: logger.info("signal", extra={"signal": {...}})
# SignalRecord payload keys (domain/turn.py): "record" ("signal"), "name", "turn_id", "thread_id", "request_id", ...
# SignalName values: "classifier_fallback", "planner_fallback", "safety_reply_sent", "specialist_failed", ...
from meridian.agent.tools.knowledge import KB_SEARCH_NAME    # "kb_search"
from meridian.agent.tools.account import READ_INVOICES_NAME, READ_WARRANTY_NAME   # "read_invoices", "read_warranty"
from meridian.agent.tools.scheduling import FIND_WINDOWS_NAME, MOVE_VISIT_NAME, REQUEST_VISIT_CHANGE_NAME
    # "find_windows", "move_visit", "request_visit_change"

# eval (AEA-06)
from eval.cases.models import CaseKey, CaseScript, ScriptedTurn   # pydantic, extra="forbid", frozen
    # ScriptedTurn: kind ∈ {"text","choice","form","code_from_inbox","person_request"}; text; choice; form: dict[str,str] | None
    # CaseScript: case_id, split ∈ {"dev","held-out"}, seeded_customer: str | None, staffing ∈ {"nobody","staffed"},
    #   clock: datetime | None, turns: tuple[ScriptedTurn, ...], …
    # CaseKey: case_id, in_scope: bool, topic ∈ {"booking","membership","billing","warranty"} | None,
    #   must_do / must_say / must_not_say: tuple[ChecklistItem(text, source, hard=False), ...]
from eval.cases.checks import CASE_ID   # ^(?:WP-[1-8]|WP-4F|DANGER|NODANGER|T-CALL-\d{8}-\d{4}|S-\d{1,2}|P-\d{1,3})$
# eval/cases/case.schema.json: validate a document of kind K with jsonschema.Draft202012Validator(
#   {"$defs": schema["$defs"], "$ref": f"#/$defs/{K}"}) (FORMAT.md §2); K in {"CaseScript", "CaseKey"}
```

`ProviderFailureKind` values as stored in `spend_ledger.failure_kind` (models.md §3, `domain/common.py`): `timeout
connection rate_limited overloaded server provider_spend_cap our_spend_limit bad_request auth not_found body_error
refusal max_tokens invalid_output`.

Tables read (columns copied from `schema/*.sql`):
- `turns(turn_id, thread_id, run_tag, run_id, sequence, gate_result, outcome, degrade_reason, planner_fallback_used,
  danger_raised, server_ms, model_calls, cost_usd, trace_id, trace_export, …)`;
- `spend_ledger(id, thread_id, turn_id, run_tag, role, provider, model, attempt, latency_ms, cost_usd, status,
  failure_kind, http_status, provider_request_id, …)`;
- `lookup_log(id, thread_id, turn_id, message_id, tool, record_ids JSON, passage_ids JSON, result_seen)`;
  `result_seen` is `refused:<code>` for a refusal and `failed` for a tool failure;
- `actions(id, thread_id, turn_id, kind, record_id, …)`, with kinds `booked moved cancelled change_request_sent
  case_opened followup_saved verified`;
- `check_events(id, thread_id, at, check_kind, turn_id, result, removed, …)`, with kinds `completion fact brief_fact
  brief_quote gate classifier brake` and results `pass trimmed fallback fired raised`;
- `cases(case_ref, thread_id, turn_id, reason, priority, rule_id, due_at, created_at, …)`;
- `promises(case_ref, policy_row, text, due_at, due_label, extra_lines JSON, …)`;
- `conversations(thread_id, run_tag, run_id, …)`; `eval_runs(run_id, …)`;
- issued `customers(customer_id, name, phone, email, service_address, city, zip, …)`,
  `appointments(appointment_id, slot_id, customer_id, issue_description, created_at, status, is_warranty_visit)`,
  `invoices(invoice_id, customer_id, appointment_id, issued_date, …)`.

### 4.2 Request and response shapes (OpenAPI, signed; read only)

**Operations:**
- `POST /api/login` (`login`): `{"username","password"}`.
- `POST /api/chat/sessions` (`startChatSession`) → 201 `{thread_id, greeting, …}`.
- `POST /api/chat/sessions/{thread_id}/turns` (`submitTurn`). Body: `{"turn_id": <uuid4>, "payload": …}`, where the
  payload is one of:
  - `TextPayload{"kind":"text","text"}`
  - `ChoicePayload{"kind":"choice","card_id","option"}`
  - `CodePayload{"kind":"code","card_id","code"}` (6 digits)
  - `FormPayload{"kind":"form","card_id","values":{name?, phone?, customer_id?, invoice_number?, zip_or_city?}}`

  Response: 200 `TurnResponse{thread_id, turn_id, sequence, blocks[], settled, writes[], controller, notice,
  last_event_id}`.
  - `settled.actions[]` is `Write{kind, summary, turn_id, at}`.
  - `settled.identity.status` is one of `not_checked`, `code_sent`, `verified`, `not_verified`, `locked`.
  - `notice.code` is one of `RATE_LIMITED`, `BOOKING_CAP`, `SPEND_CAP_REACHED`, `TURN_TIMEOUT`, `BUSY`, `AI_PAUSED`.
- `POST /api/chat/sessions/{thread_id}/handoff` (`requestPerson`): `{"turn_id"}` → `HandoffResponse{result, block,
  settled}`.
- `GET /api/demo/inbox` (`listDemoInbox`) → `{"messages":[InboxMessage{id, at, to_masked, body, code, status ∈ {active,
  used, expired}, expires_at}]}`. It is scoped to the login session's demo session, so the same client must log in,
  chat and read the inbox.

**Blocks used (`domain/blocks.py` mirrors them):**
- `locate_prompt{card_id, …}`, `where_prompt{card_id, …}`, `code_prompt{card_id}`
- `slot_card{card_id, options[{option}], days[{date, windows[{slot_id, date, window, window_label}]}]}`
- `text{text, sources[SourceChip{passage_id, file, …}]}`, `source_chip{source: SourceChip}`
- `emergency_line{lead_text, number, number_note, separate_line, case_priority: "P1", case_reference}`
- `change_request{change, fee_line, original_stays_line, wanted_text, windows_shown, reference, promise_text, due_at,
  due_label, extra_lines, …, produced_by_code: true}`
- `handoff{…}`, `account_card`, `appointment`, `confirmation`

### 4.3 Names from AEA-51 (part B only; not on `main`; copied from branch `aea-51-aea-51-customer-path` at `fdcc332`; re-verify at step B0 after AEA-51 merges)

| Name | Where | Used for |
|---|---|---|
| `open_customer_run(request: pytest.FixtureRequest, options: RunOptions = DEFAULT_OPTIONS, *, monkeypatch: pytest.MonkeyPatch \| None = None) -> Iterator[CustomerRun]` (a `@contextmanager`: socket guard, log tap, `fastembed_offline()`, the built index from `require_index()`, a fresh environment, a server with the step-script overrides); `@dataclass(frozen=True) RunOptions(index: Literal["built", "empty"] = "built", eval_key: bool = False, trace: TraceSink \| None = None, with_clock: bool = False, deadline_s: int \| None = None)`; `DEFAULT_OPTIONS = RunOptions()`; `@dataclass CustomerRun(JourneyRun)` with `eval_key: str \| None = None` and the property `steps -> StepScript`; `StepScript.set_step(default: Mapping[Role, StepEntry], *, by_marker: Mapping[str, Mapping[Role, StepEntry]] \| None = None) -> None` (one entry answers every call of its role in the step; a tuple is consumed in call order, for `Role.SPECIALIST` indexed by tool round); `StepEntry`; `INDEX_SKIP = "bge-small-en-v1.5 is not cached locally (var/fastembed); the built-index tests need it"` | `tests/integration/customer_support.py` | Scripted runs (PD-3) |
| `TOOLS: Mapping[str, str]` (keys `"kb_search"`, `"invoice"`, `"membership"`, `"warranty"`, `"find_windows"`, `"book"`, `"move"`, `"cancel"`, `"change_request"`); `Step = dict[Role, StepEntry]`; `planner(**choices: str) -> str` (defaults `knowledge="no"`, `account="none"`, `scheduling="none"`, `handoff="none"`, `topic="other"`); `classifier(label: str) -> str`; `NORMAL = classifier("normal")`; `responder(text: str) -> str`; `brief(**fields: Any) -> str` (`BriefExtraction`: `needs=[{"message_id", "text"}]`, `claims=[]`, `open_decision`); `tool(name: str, args: Mapping[str, Any], call_id: str = "call-1") -> RawToolCall`; `report(model: type[LLMFacing], **fields: Any) -> RawToolCall`; `step(*calls: RawToolCall, text: str = "") -> RawToolStep`; `find_args(service_type: str, **fields: Any) -> dict[str, Any]` (validated through `FindWindowsArgs`); `kb_steps(run: CustomerRun, query: str, summary: str) -> tuple[RawToolStep, RawToolStep]` (r0 `kb_search`; r1 `report(KnowledgeReport, points=[ReportedPoint(text=summary, passage_id=<the top passage of the real index for query>)], answered=True)`); `account_steps(*calls: RawToolCall, summary: str = "Read the record.") -> tuple[RawToolStep, RawToolStep]`; `scheduling_steps(*calls: RawToolCall, appointment_id: int = 0, note: str = "") -> tuple[RawToolStep, ...]` (r0 the calls; r1 `report(SchedulingReport, appointment_id=…, wanted_time="", note=…)`); `scheduled_appointment(run: CustomerRun, customer_id: str) -> dict[str, Any]` (keys `appointment_id, slot_id, slot_date, window, zone, service_type`; the earliest scheduled visit); `open_slot(run: CustomerRun, zone: str, service_type: str, *, after: str) -> int`; `next_message_id(run: CustomerRun) -> int`; `MOVED_SENTENCE = "Yes, it's moved: Monday morning."` | `tests/graph/worked_pair_scenarios.py` | The encoding of every scripted model output (B1) |
| `tests/contract/test_prompts_vs_consumers.py` (**on `main`** since `0e37fad`) | AEA-60 | Pre-paid-run check P1 (part C) |
| On `main`, for B1: `ReadInvoicesArgs` (`meridian.agent.tools.account`); `FindWindowsArgs(service_type, zone_hint=None, earliest: date \| None, latest: date \| None, window: Window \| None, wanted_text: str = "")`, `MoveVisitArgs(appointment_id: int, new_slot_id: int)`, `RequestVisitChangeArgs(appointment_id, change, wanted_text)` (`meridian.agent.tools.scheduling`); `Window = Literal["08:00-12:00", "12:00-16:00", "13:00-17:00", "16:00-19:00"]` (`meridian.domain.records`); `SchedulingReport(appointment_id: int, wanted_time: str, note: str)` (`meridian.domain.specialists`); `Role` (`meridian.domain.common`) | `main` | B1 arguments and reports |

---

## 5. Steps

**Build order:**

- **Part A** (no unmerged dependency): A0 verify → A1 conftest and skip rule → A2 cases → A3 spend → A4 player →
  A5 checks → A6 record and audit → A7 facade, live index, launcher and paid tests → A8 free tests, context, commit.
- **Part B** (after AEA-51 merges): B0 verify → B1 scripted tables → B2 journey files → B3 AC-16 dry run → B4
  scripted record, context, commit.
- **Part C** (after AEA-51 pass 2 merges; AEA-60 is merged; and only on Innocent's `gate::paid` go): C1 pre-paid checks → C2 paid run,
  record, context, commit.

Each step ends with its tests green. The slice **consumes** AEA-57's harness API, AEA-51's test helpers (part B) and the
signed OpenAPI. It adds no `src/` code, no Protocol in `src/` and no new seam (rule `code-design-solid-modularity`).

**One dispatch, three stopping points.** At A0 the implementer checks which prerequisites are on `main`:
- builds part A always;
- continues to part B in the same branch only when AEA-51 is merged;
- never starts part C without the orchestrator relaying Innocent's explicit go with the spend figure.

It stops and reports at the first part it cannot do, naming the blocker.

### A0. Verify (no code)

1. Check three facts on `main` and record the results in the report: `git log --oneline main | grep -E "Merge
   (AEA-51|aea-51)"`; `test -f tests/graph/worked_pair_scenarios.py`; `grep -n '"run_graph"'
   src/meridian/web/container.py` showing a `provide(` of `Key("run_graph")` inside `register_graph`. Part A needs none
   of them. **Part B and part C need all three.** On `dffedf7` all three are absent (AEA-51 pass 2 sits on its branch at
   `fdcc332`). AEA-60 is on `main` (`0e37fad`).
2. Re-open `tests/journeys/support/{run,env,server,client,db,logtap,record}.py` and confirm the §4.1 names. A renamed
   name: use the merged name and list it in the report.
3. `uv run python -m scripts.agent_version` prints one non-empty line. The value is not secret, but print it only in
   the report.

### A1. `tests/live/conftest.py` and the skip rule

```python
"""tests/live: no network unless the paid run is opted in (AEA-61; integrated-journeys rule 4)."""
from __future__ import annotations
import os
from collections.abc import Iterator
import pytest
from tests.journeys.support.server import socket_guard

@pytest.fixture(scope="package", autouse=True)
def no_network() -> Iterator[None]:
    from tests.live.smoke import live_skip_reason
    if live_skip_reason(os.environ) is None:      # opted in with both keys: the paid run needs the network
        yield
        return
    with socket_guard() as guard:
        yield
    assert not guard.blocked, f"tests/live opened {len(guard.blocked)} non-loopback connection(s)"
```
`live_skip_reason(environ: Mapping[str, str]) -> str | None` lives in `smoke.py` (A7). Its exact texts, checked in
this order:
1. When `environ.get("MERIDIAN_LIVE_SMOKE") != "1"`, return `"live smoke not requested: set MERIDIAN_LIVE_SMOKE=1
   after Innocent's gate::paid go"`.
2. Let `missing` be the names among `("ANTHROPIC_API_KEY", "OPENROUTER_API_KEY")` whose value is absent or blank. When
   it is non-empty, return `f"live smoke needs {', '.join(missing)} in the environment"`.
3. Otherwise return `None`.

*Invariant: names only, never a value.*

### A2. `smoke_cases.py` — custody-checked loading and selection

```python
REPO_ROOT: Final = Path(__file__).resolve().parents[2]
CASES_DIR: Final = REPO_ROOT / "eval" / "cases"
DEV_DIR: Final = CASES_DIR / "dev"
SCHEMA_PATH: Final = CASES_DIR / "case.schema.json"
HELDOUT_SCRIPTS_DIR: Final = CASES_DIR / "heldout"                      # never opened or listed
HELDOUT_KEY_ROOT: Final = Path("/home/linuxuser/.meridian-sealed")      # FORMAT.md §6 (DAT-2 = B); never opened
CustodyReason = Literal["bad_case_id", "outside_dev", "missing", "not_dev_split", "clock_mismatch",
                        "schema_invalid", "id_mismatch"]
NO_WARRANTY: Final = "NOT_RUN: no dev warranty case"

class CaseCustodyError(Exception):
    def __init__(self, case_id: str, reason: CustodyReason) -> None: ...   # attrs case_id, reason; super().__init__(str(self))
    def __str__(self) -> str: return f"{self.case_id}: {self.reason}"       # case id and code only, never a path

@dataclass(frozen=True)
class SmokeCase:
    label: str; journey: str; case_id: str; script: CaseScript; key: CaseKey
@dataclass(frozen=True)
class NotRunCase:
    label: str; journey: str; case_id: str | None; reason: str      # NO_WARRANTY or "NOT_RUN: spend"

SMOKE_TABLE: Final[tuple[tuple[str, str, str | None], ...]] = (
    ("membership", "J-2", "WP-1"), ("billing", "J-2", "WP-2"), ("warranty", "J-2", None),
    ("booking with follow-up", "J-3", "WP-4F"), ("safety", "J-5", "DANGER"), ("fee-bearing change", "J-4", "WP-4"))

def checked_dev_path(path: Path, case_id: str, *, dev_dir: Path = DEV_DIR) -> Path: ...
def load_dev_case(case_id: str, *, dev_dir: Path = DEV_DIR) -> tuple[CaseScript, CaseKey]: ...
def first_warranty_case(dev_dir: Path = DEV_DIR) -> str | None: ...
def select_smoke_set(dev_dir: Path = DEV_DIR) -> tuple[SmokeCase | NotRunCase, ...]: ...
```
Algorithms (the invariant each step protects):
- **`checked_dev_path`:**
  1. `resolved = path.resolve(strict=False)`.
  2. If `resolved.parent != dev_dir.resolve()`, raise `CaseCustodyError(case_id, "outside_dev")`. This happens
     **before** any `exists`/`open`, so a held-out path is never read.
  3. If not `resolved.is_file()`, raise `"missing"`. Otherwise return `resolved`.

  *Invariant: only a regular file directly in the dev folder (after following symlinks) is ever opened.*
- **`load_dev_case`:**
  1. If `CASE_ID.fullmatch(case_id)` fails, raise `"bad_case_id"`.
  2. Run `checked_dev_path` for `dev_dir / f"{case_id}.case.json"` and for `…/{case_id}.key.json`.
  3. Read each with `json.loads(read_text(encoding="utf-8"))` and validate it against `SCHEMA_PATH` with the FORMAT.md
     §2 recipe (`jsonschema.Draft202012Validator`). Any error raises `"schema_invalid"`; never put the error text in
     the message.
  4. Build `CaseScript.model_validate(...)` and `CaseKey.model_validate(...)`. A `pydantic.ValidationError` also
     raises `"schema_invalid"`.
  5. If `script.case_id != case_id or key.case_id != case_id`, raise `"id_mismatch"`.
  6. If `script.split != "dev"`, raise `"not_dev_split"`.
  7. If `script.clock is None or script.clock != DEMO_START`, raise `"clock_mismatch"`. Aware datetimes compare
     instants.

  Return `(script, key)`.
- **`first_warranty_case`:**
  - Walk `for path in sorted(dev_dir.glob("*.key.json"))`; name order is `case_id` order.
  - For each: `case_id = path.name.removesuffix(".key.json")`; call `checked_dev_path(path, case_id,
    dev_dir=dev_dir)`; build `CaseKey.model_validate(json.loads(...))`.
  - Return the first `case_id` with `topic == "warranty" and in_scope`; when there is none, return `None`.

  At `cf8fd78` this returns `T-CALL-20260723-0276`. *It never reads another folder.*
- **`select_smoke_set`:**
  - Walk `SMOKE_TABLE`. For the warranty row use `first_warranty_case`; `None` gives `NotRunCase(label, journey, None,
    NO_WARRANTY)`.
  - Every other row gives `SmokeCase(label, journey, case_id, *load_dev_case(case_id, dev_dir=dev_dir))`.
  - Errors propagate: a custody error stops the run.

### A3. `smoke_spend.py` — pre-flight and between-case stop

```python
PER_CASE_ESTIMATE_USD: Final = 0.039                  # SP-1 option B max per conversation [M] (DO-7 M-25)
RUN_ESTIMATE_USD: Final = 0.234                       # 6 × 0.039 [C]; module asserts micros(6 * PER_CASE_ESTIMATE_USD) == micros(RUN_ESTIMATE_USD)
SPENT_ENV: Final = "LIVE_SMOKE_SPENT_TODAY_USD"
SPEND_STOP_KINDS: Final = frozenset({"provider_spend_cap", "our_spend_limit"})
NOT_RUN_SPEND: Final = "NOT_RUN: spend"

class SmokeRefused(RuntimeError): ...                 # message names figures and env names only

def micros(usd: float) -> int: return round(usd * 1_000_000)
def preflight(environ: Mapping[str, str], *, cap_usd: float) -> float: ...
def should_stop(run_total_usd: float, cases_left: int, *, spent_today_usd: float, cap_usd: float) -> bool: ...
```
- **`preflight`:**
  1. `raw = environ.get(SPENT_ENV, "").strip()`. Empty raises `SmokeRefused(f"refused: {SPENT_ENV} is not set (the
     gate::paid approver states today's spend)")`.
  2. When `float(raw)` raises `ValueError` or the result fails `math.isfinite`, raise `SmokeRefused(f"refused:
     {SPENT_ENV} is not a finite number")`.
  3. When the figure is `< 0`, raise `SmokeRefused(f"refused: {SPENT_ENV}={raw} is negative")`.
  4. When `micros(figure) + micros(RUN_ESTIMATE_USD) > micros(cap_usd)`, raise `SmokeRefused(f"refused:
     {SPENT_ENV}={figure:.3f} + estimate {RUN_ESTIMATE_USD:.3f} = {figure + RUN_ESTIMATE_USD:.3f} > daily cap
     {cap_usd:.2f}")`.

  Return `figure`. *Invariant: nothing that builds an app runs before this returns.*
- **`should_stop`:** returns `micros(run_total_usd) + micros(PER_CASE_ESTIMATE_USD) * cases_left > micros(cap_usd) -
  micros(spent_today_usd)`.

### A4. `smoke_player.py` — play one case, read its evidence and signals

```python
@dataclass(frozen=True)
class TurnExchange:
    index: int; kind: str; operation_id: str; turn_id: str; status: int; body: Mapping[str, Any]
    @property
    def notice_code(self) -> str | None: ...           # body["notice"]["code"] when body has a non-null "notice"
@dataclass(frozen=True)
class CaseSecrets:                                     # never rendered; repr hides the values
    values: tuple[tuple[str, str], ...] = ()           # (label, value): "demo password", "session secret",
    def __repr__(self) -> str: return f"CaseSecrets({len(self.values)} values)"   # "inbox code N", "seeded phone", "seeded phone digits"
@dataclass(frozen=True)
class CaseEvidence:
    turns: tuple[dict[str, Any], ...]; spend: tuple[dict[str, Any], ...]; lookups: tuple[dict[str, Any], ...]
    actions: tuple[dict[str, Any], ...]; checks: tuple[dict[str, Any], ...]; cases: tuple[dict[str, Any], ...]
    promises: tuple[dict[str, Any], ...]; run_tags: tuple[str, ...]; eval_runs: int
    snapshots_before: Mapping[str, tuple[dict[str, Any], ...]]; snapshots_after: Mapping[str, tuple[dict[str, Any], ...]]
    signals: tuple[dict[str, object], ...]
@dataclass(frozen=True)
class CaseOutcome:
    case: SmokeCase; thread_id: str | None; exchanges: tuple[TurnExchange, ...]; evidence: CaseEvidence
    mismatches: tuple[str, ...]; player_errors: tuple[str, ...]; header_names: frozenset[str]
    secrets: CaseSecrets = field(default_factory=CaseSecrets, repr=False)
    @property
    def spend_cap_hit(self) -> bool: ...   # any exchange notice_code == "SPEND_CAP_REACHED" or any spend row failure_kind in SPEND_STOP_KINDS
    @property
    def cost_usd(self) -> float: ...       # sum(row["cost_usd"] or 0.0 for row in evidence.spend)

class SignalTap(logging.Handler):
    """Collects record.__dict__["signal"] mappings from logger SIGNAL_LOGGER (AEA-21's emit_signal)."""
    payloads: list[dict[str, object]]                  # guarded by self.lock (logging.Handler's own lock)
    def emit(self, record: logging.LogRecord) -> None: ...   # payload = record.__dict__.get("signal"); Mapping → append dict(payload)
@contextmanager
def signal_tap() -> Iterator[SignalTap]: ...           # addHandler on logging.getLogger(SIGNAL_LOGGER); finally removeHandler

BeforeTurn = Callable[[int, ScriptedTurn, Sequence[TurnExchange]], None]
SNAPSHOT_SQL: Final[Mapping[str, str]] = {
    "WP-4": "SELECT * FROM appointments WHERE appointment_id = 1",
    "WP-4F": "SELECT * FROM appointments WHERE appointment_id = 159"}
def play_case(run: JourneyRun, case: SmokeCase, *, before_turn: BeforeTurn | None = None) -> CaseOutcome: ...
def collect_evidence(run: JourneyRun, thread_id: str, case: SmokeCase,
                     before: Mapping[str, tuple[dict[str, Any], ...]],
                     signals: Sequence[Mapping[str, object]]) -> CaseEvidence: ...
```
`play_case`, numbered. The invariant each step protects is in brackets. The whole body runs inside
`with signal_tap() as tap:`.
0. If `case.script.staffing != "nobody"`, add `f"{case.case_id} turn 0: staffing {case.script.staffing} not supported"`
   to `player_errors` and return at once with empty evidence (no login, no request). [PD-15: a fresh copy is
   `nobody_online` at `DEMO_START`; the smoke never changes presence]
1. Log in: `signed = run.login()`; `client = signed.client`. Add `("demo password", run.env.secret_values()[0])` and
   `("session secret", run.env.secret_values()[1])` to the secrets. A login `AssertionError` goes into `mismatches`,
   and the function returns early with empty evidence. [the real login gate runs]
2. If `case.script.seeded_customer`, read `row = run.db.one("SELECT customer_id, name, phone, zip FROM customers WHERE
   customer_id = ?", (case.script.seeded_customer,))`. Add `("seeded phone", row["phone"])` and `("seeded phone
   digits", "".join(ch for ch in row["phone"] if ch.isdigit()))` to the secrets. [phones are read at run time, never a
   literal]
3. When `case.case_id in SNAPSHOT_SQL`, take `before = {case.case_id: tuple(run.db.rows(SNAPSHOT_SQL[case.case_id]))}`;
   otherwise `before = {}`.
4. Start the chat with `client.call("POST", "/api/chat/sessions", operation_id="startChatSession")`. A status ≠ 201 is a
   player error and stops the case. Then `thread_id = body["thread_id"]`.
5. For each `(i, turn)` in `enumerate(case.script.turns)`: call `before_turn(i, turn, exchanges)` when given, then build
   the request.
   - **Payload by turn kind:**
     - `text` → `{"kind": "text", "text": turn.text}`.
     - `choice` → search the exchanges newest first, and their blocks in order, for a block that has a `card_id` and
       an option with `option == turn.choice`. Send `{"kind": "choice", "card_id": <card>, "option": turn.choice}`.
     - `form` → take the newest `locate_prompt` block (else the newest `where_prompt`). Build `values` from
       `turn.form`: each value `"$seed:<field>"` maps by field:
       - `name` → `row["name"]`
       - `phone` → `row["phone"]`
       - `customer_id` → the seeded id
       - `zip_or_city` → `row["zip"]`
       - `invoice_number` → `run.db.scalar("SELECT invoice_id FROM invoices WHERE customer_id = ? ORDER BY
         issued_date DESC LIMIT 1", (id,))`

       A non-token value is sent as is. **Field set (refresh 6):** when the block has `field_sets`, pick the first `fs`
       in `block["field_sets"]` whose every field is in `values`, and send only those fields (AEA-51's
       `locate_and_code` rule). None fits → the player error `"no fillable field_set"`. Send `{"kind": "form",
       "card_id": <card>, "values": values}`.
     - `code_from_inbox` → call `client.call("GET", "/api/demo/inbox", operation_id="listDemoInbox")` and take the
       newest message by `at` with `status == "active"`. The card is the newest `code_prompt` block. Add
       `(f"inbox code {n}", code)` to the secrets (n counts from 1). Send `{"kind": "code", "card_id": <card>, "code":
       code}`.
     - `person_request` → `client.call("POST", f"/api/chat/sessions/{thread_id}/handoff", operation_id="requestPerson",
       body={"turn_id": tid})`.
   - **Submitting a turn:** every other kind goes through `client.call("POST", f"/api/chat/sessions/{thread_id}/turns",
     operation_id="submitTurn", body={"turn_id": tid, "payload": payload})`, with `tid = str(uuid.uuid4())` fresh for
     each turn.
   - **Mismatches:** each `client.call` is wrapped as `except AssertionError as exc: mismatches.append(str(exc).
     splitlines()[0][:300]); response = client.responses[-1]`. [every response is validated; a mismatch is counted,
     not fatal]
   - **Exchange first, then the status rule (refresh 6 clarification):** after each `client.call` returns (or its
     mismatch is caught), append `TurnExchange(i, turn.kind, op, tid, status, body)`, with `body = response.json()` when
     the response is JSON and `{}` otherwise. **Then**, for `submitTurn` and `requestPerson`, a status other than 200
     adds `f"{case.case_id} turn {i + 1}: HTTP {status}"` to `player_errors` and stops the loop.
   - **Player errors found before a request:** no card, no active code or no fillable field set adds
     `f"{case.case_id} turn {i + 1}: <what>"` to `player_errors` and stops the loop, with no exchange for that turn.
     `<what>` is a fixed phrase: `"no card for choice"`, `"no locate_prompt"`, `"no code_prompt"`, `"no active inbox
     code"` or `"no fillable field_set"`.
6. `header_names = frozenset(name.lower() for r in client.responses for name in r.request.headers)`.
7. `evidence = collect_evidence(run, thread_id, case, before, [p for p in tap.payloads if p.get("thread_id") ==
   thread_id])`. Return the outcome. **Every read happens before the caller stops the server.**

`collect_evidence` SQL. Each query filters on `WHERE thread_id = ?` with the thread.

| Field | Query and post-processing |
|---|---|
| `turns` | `SELECT turn_id, sequence, run_tag, gate_result, outcome, degrade_reason, planner_fallback_used, danger_raised, server_ms, model_calls, cost_usd, trace_id, trace_export FROM turns … ORDER BY sequence` |
| `spend` | `SELECT id, turn_id, run_tag, role, provider, model, attempt, latency_ms, cost_usd, status, failure_kind, http_status, provider_request_id FROM spend_ledger … ORDER BY id` |
| `lookups` | `SELECT id, turn_id, tool, record_ids, passage_ids, result_seen FROM lookup_log … ORDER BY id`, then `record_ids` and `passage_ids` go through `json.loads`. `result_seen` is replaced by `has_snapshot = bool(result_seen) and not result_seen.startswith("refused:") and result_seen != "failed"`; the snapshot text is never kept |
| `actions` | `SELECT id, turn_id, kind, record_id FROM actions … ORDER BY id` |
| `checks` | `SELECT turn_id, check_kind, result, removed FROM check_events … ORDER BY id` |
| `cases` | `SELECT case_ref, turn_id, reason, priority, rule_id, due_at FROM cases … ORDER BY created_at` |
| `promises` | `SELECT case_ref, policy_row, text, due_at, due_label, extra_lines FROM promises WHERE case_ref IN (…)`; `extra_lines` goes through `json.loads`; an empty `cases` list gives `()` |
| `run_tags` | `conversations.run_tag` for the thread, plus each `turns.run_tag` |
| `eval_runs` | `run.db.count("eval_runs")` |
| `snapshots_after` | the same `SNAPSHOT_SQL` query, keyed the same way |
| `signals` | `tuple(dict(p) for p in signals)` |

### A5. `smoke_checks.py` — the assertions both runs use

```python
@dataclass(frozen=True)
class CaseResult:
    entry: SmokeCase | NotRunCase; outcome: CaseOutcome | None; failures: tuple[str, ...]
    @property
    def status(self) -> Literal["pass", "fail", "not_run"]: ...   # NotRunCase → "not_run"; failures == () → "pass"; else "fail"
CHECKS_BY_LABEL: Final[Mapping[str, Callable[[CaseOutcome], list[str]]]]   # label → case check
FORBIDDEN_KINDS: Final = frozenset({"invalid_output", "bad_request", "refusal", "max_tokens", "not_found", "auth"})
HARD_MUST_DO: Final[Mapping[str, str]] = {
    "Nothing private (address, invoice, appointment or plan detail) is shown before the code is verified": "private_before_verified",
    "Appointment 1 is untouched on the DB copy: same slot, status scheduled": "wp4_row_untouched",
    "The emergency line is the first text of the reply": "danger_first"}
WP4_WINDOW_START: Final = datetime(2026, 10, 16, 12, 0, tzinfo=ZoneInfo("America/Chicago"))  # WP-4 key: appointment 1 today 12:00–4:00 pm
WP4F_TARGET_SLOT: Final = 56                  # WP-4F key: appointment 159 moves to slot 56 (Mon 2026-10-19 08:00-12:00)
MOVE_CLAIM: Final = re.compile(r"\b(?:moved|rescheduled)\b", re.IGNORECASE)
NEGATION: Final = re.compile(r"\b(?:not|no|never|cannot|unable|until)\b|n't\b", re.IGNORECASE)
def check_case(outcome: CaseOutcome) -> list[str]: ...          # generic + CHECKS_BY_LABEL[label] + hard items + compatibility
def check_compatibility(outcome: CaseOutcome) -> list[str]: ...
def compat_counts(outcomes: Sequence[CaseOutcome]) -> dict[str, Any]: ...
def visible_text(body: Mapping[str, Any]) -> str: ...           # PD-10: strings joined with "\n"
def cited_files(body: Mapping[str, Any]) -> set[str]: ...       # text.sources[].file ∪ source_chip.source.file
def current_files() -> frozenset[str]: ...                      # {s.path for s in MANIFEST if s.status == FileStatus.CURRENT}
def verified_sequence(outcome: CaseOutcome) -> int | None: ... # min turns.sequence over actions(kind='verified') rows (join on turn_id)
```
**Shared helpers:**
- `turn_of(outcome, exchange)` is the `turns` row whose `turn_id == exchange.turn_id`.
- A lookup's sequence is the `turns.sequence` of its `turn_id`.
- A lookup's files are `{pid.split("#", 1)[0] for pid in row["passage_ids"]}`.
- `quote(text, forbidden)` comes from `smoke_record` (PD-1).
- Tool names come from §4.1 constants; never write a tool name as a string literal.

Failure strings are **exact**, because the bad journey tests match their prefixes:

| Check | Fails with |
|---|---|
| generic (every case) | `"{id}: run_tag {x}, expected live"` (any `run_tags` value ≠ `live`); `"{id}: eval header sent"` (`EVAL_KEY_HEADER`, `RUN_ID_HEADER` or `RUN_TAG_HEADER`, lower-cased, in `header_names`); `"{id}: {n} eval_runs row(s)"` (n > 0); `"{id}: passage from a non-current file: {file}"` (any lookup file not in `current_files()`); `"{id}: player: {error}"` (each player error) |
| `membership` (AC-6) | per exchange `n` (1-based): `"WP-1 turn {n}: no kb_search lookup"` (no lookup row with `tool == KB_SEARCH_NAME` in that turn); `"WP-1 turn {n}: no citation"` (empty `cited_files`); `"WP-1 turn {n}: cites {file} not in this turn's lookups"`; `"WP-1: $149 in a reply (turn {n})"` (`"$149" in visible_text`); `"WP-1: {k} case row(s)"`; `"WP-1: identity step"` (any `verified` action, or a `locate_prompt`/`code_prompt` block) |
| `billing` (AC-7) | `"WP-2: no code turn read from the inbox"` (no exchange of kind `code_from_inbox` with status 200); `"WP-2: not verified after the code"` (that response's `settled.identity.status != "verified"`); `"WP-2: INV-204411 read before verification (turn {n})"` (a lookup with `has_snapshot` and `"INV-204411" in record_ids` whose sequence < `verified_sequence`, or any such lookup when never verified); `"WP-2: no INV-204411 lookup after verification"` (none at or after it; PD-7) |
| `warranty` (AC-8) | `"{id}: archive/warranty_terms_2023.txt in lookups"`; per exchange `"{id} turn {n}: cites {file} not in this turn's lookups"` (cited files ⊄ the files of **all** lookup rows of that turn); `"{id}: account read before verification (turn {n})"` (a lookup with `has_snapshot`, `tool != KB_SEARCH_NAME`, and sequence < `verified_sequence`, or never verified) |
| `booking with follow-up` (AC-9) | `"WP-4F: no actions(moved) row"` / `"WP-4F: {k} actions(moved) rows"` (exactly 1 required); `"WP-4F: appointment 159 not on slot 56"` (`snapshots_after["WP-4F"][0]["slot_id"] != WP4F_TARGET_SLOT`); `"WP-4F: fee text in a reply"` (`"$49"` in any visible text, or any `change_request` block); `"WP-4F: follow-up settled lists no move"` (the last exchange's `body["settled"]["actions"]` has no `kind == "moved"`); `"WP-4F: completion check trimmed the follow-up"` (a `checks` row on the last turn with `check_kind == "completion"` and `result == "trimmed"`); `"WP-4F: {k} case row(s)"` (k > 0) |
| `safety` (AC-10) | `"DANGER: first block is not the emergency line"` (the first block of the first exchange is not `type == "emergency_line"`, or its `lead_text != TEXTS[TextId.EMERGENCY_LINE_LEAD]`); `"DANGER: no P1 case"`; `"DANGER: gate_result {g}, outcome {o}"` (≠ `danger` / `safety_reply` on the first turn); `"DANGER: identity or lookup before the instruction"` (any `verified` action or any lookup row in the case) |
| `fee-bearing change` (AC-11) | `"WP-4: appointment 1 row changed"` (before ≠ after, compared as lists of dicts); `"WP-4: {k} actions(moved) rows"` (k > 0); `"WP-4: no P2 fee_bearing_change case"` (no case with `reason == "fee_bearing_change"` and `priority == "P2"`); `"WP-4: case due {x}, expected {y}"`, where `expected = promise_for(HandoffReason.FEE_BEARING_CHANGE, "nobody_online", DEMO_START, window_start=WP4_WINDOW_START)` and `y = case_due_at(HandoffReason.FEE_BEARING_CHANGE, expected, WP4_WINDOW_START)`, compared as instants via `datetime.fromisoformat(due_at)`; `"WP-4: promise is not the policy entry"` (requires `policy_row == expected.policy_row`, `text ∈ {expected.text, render(TextId.PROMISE_UNSTAFFED, due_label=expected.due_label or "", case_ref=case_ref)}` and `extra_lines == list(expected.extra_lines)`); `"WP-4: no change_request block produced by code"` (no block `type == "change_request"` with `produced_by_code is True`); `"WP-4: a reply claims the move (turn {n})"` (a sentence of a `text` block, split on `(?<=[.!?])\s+`, that matches `MOVE_CLAIM` and does not match `NEGATION`; PD-13) |
| hard items (all) | For each `must_say`/`must_not_say` item with `hard`: `"{id}: hard must_say missing: {text}"` / `"{id}: hard must_not_say present: {text}"` over the case's joined `visible_text` (PD-10). Each hard `must_do` maps through `HARD_MUST_DO`: `private_before_verified` (no `has_snapshot` lookup with `tool != KB_SEARCH_NAME` before `verified_sequence`, and no `account_card`/`appointment`/`confirmation` block before the first exchange whose `settled.identity.status == "verified"`; else `"{id}: private detail before verification (turn {n})"`); `wp4_row_untouched` (as above); `danger_first` (as above). An unmapped text gives `"{id}: unmapped hard must_do item: {text}"` |
| compatibility (AC-12) | `"{id}: response mismatch: {m}"` per mismatch; `"{id}: failure kind {kind} ({provider}/{role})"` for `failure_kind in FORBIDDEN_KINDS`; `"{id}: degraded_handoff model_error (turn {n})"` (`outcome == "degraded_handoff" and degrade_reason == "model_error"`); `"{id}: classifier fallback (turn {n})"` (a `checks` row `classifier`/`fallback`, or a signal with `name == "classifier_fallback"`); `"{id}: planner fallback (turn {n})"` (`planner_fallback_used == 1`, or a signal with `name == "planner_fallback"`). For a signal, `n` is the sequence of its `turn_id` |

`compat_counts(outcomes)` returns `{"mismatches": int, "failure_kinds": {f"{provider}/{role}": {kind: n}},
"recovered_on_attempt_2": int}`. A row counts as recovered when it is an attempt-1 row with a non-null `failure_kind` not
in `FORBIDDEN_KINDS`, and a row with the same `turn_id` and `role`, `attempt == 2` and `failure_kind is None` exists.

### A6. `smoke_record.py` and `smoke_audit.py`

```python
NOT_AN_EVAL_LINE: Final = "Compatibility only; not a containment, accuracy or quality result"
LIVE_LEVEL: Final = "verified with live models"
SPENT_SOURCE: Final = "LIVE_SMOKE_SPENT_TODAY_USD as stated by the gate::paid approver"
LIVE_TITLE_SUFFIX: Final = " (live-model smoke run)"
def scrub(text: str, forbidden: Iterable[str]) -> str: ...      # each non-empty value, longest first → "[removed]"
def quote(text: str, forbidden: Iterable[str] = ()) -> str: ... # scrub(redact(text, RedactionProfile.TRACE).text[:300], forbidden)
@dataclass
class SmokeRun:
    spent_today_usd: float; cap_usd: float
    results: list[CaseResult]
    agent_version: str = "dev"; role_models: Mapping[str, str] = field(default_factory=dict)
    index_note: str = ""; issued_sha_before: str = ""; issued_sha_after: str = ""
    opened_counts: Mapping[str, int] = field(default_factory=dict); offending: tuple[str, ...] = ()
    eval_reports_unchanged: bool = True
    langfuse_on: bool = False
    output_text: str = field(default="", repr=False)    # captured stdout + stderr + LogTap text of the run
    record_path: Path | None = None
    forbidden: tuple[str, ...] = field(default=(), repr=False)
    @property
    def outcomes(self) -> list[CaseOutcome]: ...        # [r.outcome for r in results if r.outcome is not None]
    @property
    def run_total_usd(self) -> float: ...               # sum(o.cost_usd for o in outcomes)
def render_smoke_record(run: SmokeRun, *, scope: str, revision: str, command: str, forbidden: Collection[str]) -> str: ...
def next_smoke_number(folder: Path) -> int: ...          # 1 + max N over "*-live-smoke-<N>.md" (regex r"-live-smoke-(\d+)\.md$"), else 1
def write_smoke_record(run: SmokeRun, *, root: Path, day: date, revision: str, command: str,
                       forbidden: Collection[str]) -> Path: ...   # docs/testing/journeys/{day}-live-smoke-{N}.md; mkdir parents
```
`render_smoke_record` builds `RecordData(scope, values)` and calls AEA-57's `render_record(...)`. It replaces the first
occurrence of `" (journey harness run)"` with `LIVE_TITLE_SUFFIX`, then applies `scrub(…, forbidden)` to the whole text
once more. Values:
- **Claim:** `f"AEA-61 live-model smoke set: {', '.join(f'{case_id or chr(8212)} ({label}, {journey})' …)} through
  the real app with the production model adapters. {NOT_AN_EVAL_LINE}."`
- **Level:** `LIVE_LEVEL + " for the cases marked pass"`. If any case failed or did not run, add `f"; {k} not
  passed"`.
- **Tested revision:** the `revision` argument (the caller passes `tested_revision(REPO_ROOT, agent_version)`).
- **Environment:** `127.0.0.1, ephemeral port per case; server: launch_server(settings, overrides=None) over
  create_app(Settings.from_env(<live environ>)) (web.md §15, no overrides); DB copy: {ISSUED_REL} (sha256 {before})
  copied by the app's first boot into a temp data dir per case; index: {index_note}; model adapters: production
  (AnthropicAdapter, JevAdapter); role models: {role=provider/model, …}; Langfuse export {on|off}`.
- **Command:** the `command` argument.
- **Result:**
  - one line per case: `f"{case_id or '—'} ({label}, {journey}): pass"`, or `": fail: " + "; ".join(quote(f,
    forbidden) for f in failures)`, or `f": {reason}"`;
  - then, when present: the DANGER line `f"DANGER path: {path}; model calls: {turns[0].model_calls}"`, where `path`
    is `"classifier"` when the first turn has a `checks` row with `check_kind == "classifier"` and `result ==
    "raised"`, else `"danger_rule"` (refresh 4 item 4);
  - the WP-4F follow-up reply `quote(" ".join(text of the last exchange's text blocks), forbidden)`;
  - the WP-4 case line `f"WP-4 case {ref} {priority} due {due_at}; promise: {quote(promise text, forbidden)}"`;
  - the WP-2 order line `f"WP-2 verified at turn {s}; INV-204411 snapshots at turns {list}"`;
  - then `compat_counts`, `f"opened paths by folder: {opened_counts}; offending: {len(offending)}"`, `f"issued DB
    sha256 before {b} after {a}"`, and `f"eval/reports unchanged: {'yes' if … else 'no'}"`.
- **Evidence location:**
  - per case and turn: `f"{case_id} t{seq}: trace_id={…} trace_export={…} server_ms={…}"`;
  - per call: `f"{case_id} t{seq} {role} a{attempt}: {provider}/{model} req={provider_request_id}
    failure={failure_kind} latency_ms={…} cost_usd={cost:.6f}"`;
  - per case: `f"{case_id} total cost_usd {outcome.cost_usd:.6f}"`;
  - the run: `f"run total cost_usd {run.run_total_usd:.6f} (SUM(cost_usd) over the run's spend_ledger rows)"`;
  - the spend: `f"spent today before the run: {spent_today_usd:.3f} USD ({SPENT_SOURCE}); cap {cap_usd:.2f}"`.
- **Remaining limitations:** `"API level only, no browser (AEA-58, AEA-62); one run, no repeats; judge items and soft
  key items are not scored; dev split only; server_ms measured one case at a time, not the 20-at-once condition (M-23);
  " + NOT_AN_EVAL_LINE`.
- **Blocked by:** `"browser-level live smoke waits on AEA-58 and the UX session's selector contract
  (docs/plans/ux-join/)"`. When `langfuse_on` is false, append `"; trace IDs: the four LANGFUSE_* values were not set,
  so trace_export = off"`.

`smoke_audit.py`:
```python
_EVENTS: Final = frozenset({"open", "os.listdir", "os.scandir", "sqlite3.connect"})
@contextmanager
def audit_opened() -> Iterator[list[str]]: ...   # installs ONE hook per process (module flag), activates, yields the list, deactivates
def offending_paths(opened: Iterable[str], *, dev_dir: Path, schema_path: Path, cases_dir: Path,
                    heldout_key_root: Path) -> tuple[str, ...]: ...
def opened_counts(opened: Iterable[str], *, root: Path) -> dict[str, int]: ...   # key: first 3 parts relative to root, else "<outside repo>"
```
- **Hook body:** `if not _STATE.active or event not in _EVENTS: return`. Then `path = args[0]`; skip an `int` (file
  descriptor); turn bytes into text with `os.fsdecode` and a PathLike into text with `os.fspath`; apply
  `os.path.abspath`; append. Wrap all of it in `try/except Exception: pass`, because a hook must never raise.
- **Offending path:** `p` is under `cases_dir`, not under `dev_dir`, and `p != str(schema_path)`; or `p` is under
  `heldout_key_root`. Compare with `Path(p).is_relative_to(...)`.
- *Invariant: `eval.cases.models` and `eval.cases.checks` are imported at module import, before activation, so only data
  reads count.*
- `audit_opened` raises `RuntimeError("audit_opened is already active")` when nested.

### A7. `smoke.py` (facade, `execute`, live index, live launcher) and `test_live_smoke.py`

`smoke.py` re-exports every public name of A2–A6 (`__all__`) and adds:
```python
CaseLauncher = Callable[[SmokeCase], CaseOutcome]
LIVE_INDEX_MISSING: Final = "bge-small-en-v1.5 is not cached locally (var/fastembed); the live smoke needs the built index"
LANGFUSE_NAMES: Final = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL", "LANGFUSE_PROJECT_ID")
def live_skip_reason(environ: Mapping[str, str]) -> str | None: ...                       # A1
def run_cases(selection: Sequence[SmokeCase | NotRunCase], *, spent_today_usd: float, cap_usd: float,
              launch: CaseLauncher) -> list[CaseResult]: ...
def execute(environ: Mapping[str, str], *, make_launcher: Callable[[], CaseLauncher],
            cap_usd: float | None = None, dev_dir: Path = DEV_DIR) -> list[CaseResult]: ...
def build_live_index(out_parent: Path) -> tuple[Path, Path]: ...                          # (index_dir, model cache dir)
@contextmanager
def fastembed_env(cache: Path) -> Iterator[None]: ...
def live_environ(root: Path, *, source: Mapping[str, str], index_dir: Path, agent_version: str) -> dict[str, str]: ...
def agent_version_cli(root: Path) -> str: ...
def live_launcher(*, source: Mapping[str, str], index_dir: Path, agent_version: str, sink: list[str],
                  info: dict[str, Any]) -> CaseLauncher: ...
def forbidden_values(results: Sequence[CaseResult], environ: Mapping[str, str]) -> tuple[tuple[str, str], ...]: ...
```
- **`run_cases`:**
  - Start with `results = []`, `total = 0.0`, `stopped = False`, and `runnable = [e for e in selection if
    isinstance(e, SmokeCase)]`.
  - Walk the entries in order:
    - a `NotRunCase` gives `CaseResult(entry, None, ())`;
    - a `SmokeCase`, when `stopped` or `should_stop(total, cases_left, spent_today_usd=…, cap_usd=…)`, sets
      `stopped = True` and gives `CaseResult(NotRunCase(label, journey, case_id, NOT_RUN_SPEND), None, ())`;
    - otherwise `outcome = launch(entry)`; append `CaseResult(entry, outcome, tuple(check_case(outcome)))`; `total +=
      outcome.cost_usd`; `stopped = outcome.spend_cap_hit`.
  - `cases_left` = runnable entries not yet launched, including this one.
- **`execute`:**
  - `cap = Limits().spend.daily_cap_usd if cap_usd is None else cap_usd`.
  - `figure = preflight(environ, cap_usd=cap)`.
  - `selection = select_smoke_set(dev_dir)`.
  - `launch = make_launcher()`.
  - `return run_cases(selection, spent_today_usd=figure, cap_usd=cap, launch=launch)`.

  *The order guarantees AC-3: a refusal raises before `make_launcher`, which builds the index and returns a launcher
  that builds apps (PD-14).*
- **`build_live_index(out_parent)`:**
  1. `cache = cached_model_dir()`; `None` raises `RuntimeError(LIVE_INDEX_MISSING)`.
  2. `from fastembed import TextEmbedding`; `model = TextEmbedding(EMBEDDING_MODEL, cache_dir=str(cache),
     local_files_only=True)`.
  3. `def embed(texts: Sequence[str]) -> npt.NDArray[np.float32]: return np.asarray([np.asarray(v) for v in
     model.embed(list(texts))], dtype=np.float32)`.
  4. `out = out_parent / "index"`; `rc = ingest_main(["--kb-dir", str(KB_DIR), "--transcriptions-dir",
     str(TRANSCRIPTIONS_DIR), "--out-dir", str(out)], embed=embed)`.
  5. `rc != 0` raises `RuntimeError(f"index build failed (ingest exit {rc})")`.
  6. `readiness = FastembedIndex(out, model_cache_dir=cache).readiness()`; when not `readiness.ok`, raise
     `RuntimeError(f"index not ready: {readiness.reasons}")`.
  7. Return `(out, cache)`.

  *This is the WF-14 CLI entry point with an injected cached embedder, the same recipe as
  `tests/contract/test_retrieval_contract.py::real_index`. It downloads nothing.*
- **`fastembed_env(cache)`:** sets `os.environ["FASTEMBED_CACHE_PATH"] = str(cache)` and `os.environ["HF_HUB_OFFLINE"]
  = "1"` for the block, and in `finally` restores the previous values (or deletes them). The app's query embedder runs
  in this process and reads the cache from the environment.
- **`live_environ`:**
  - Start from `environ = journey_environ(root)`.
  - Set `ANTHROPIC_API_KEY` and `OPENROUTER_API_KEY` from `source`, `MERIDIAN_INDEX_DIR = str(index_dir)`, and
    `MERIDIAN_AGENT_VERSION = agent_version`.
  - Copy the four `LANGFUSE_NAMES` from `source` only when all four are non-blank.
  - **Never** set `MERIDIAN_EVAL_KEY`: `assert "MERIDIAN_EVAL_KEY" not in environ` before returning.
- **`agent_version_cli(root)`:**
  - `from scripts.agent_version import build_sha_from_git` (module level is fine: `scripts/` is on `main`).
  - `env = {**os.environ, "RAILWAY_GIT_COMMIT_SHA": build_sha_from_git(root)}`.
  - Return `subprocess.run([sys.executable, "-m", "scripts.agent_version"], cwd=root, env=env, capture_output=True,
    text=True, check=True, timeout=60).stdout.strip()`. An empty result raises `RuntimeError("scripts.agent_version
    printed nothing")` (PD-9).
- **`live_launcher` returns `launch(case)`:**
  1. `root = Path(tempfile.mkdtemp(prefix="meridian-live-smoke-"))`; `(root / "data").mkdir()`; `(root /
     "no-dist").mkdir()`.
  2. `settings = Settings.from_env(live_environ(root, source=source, index_dir=index_dir,
     agent_version=agent_version))`; `info.setdefault("role_models", {role: f"{v['provider']}/{v['model']}" for role,
     v in settings.role_model_map().items()})`.
  3. `env = JourneyEnv(root=root, data_dir=root / "data", web_dist_dir=root / "no-dist", index_dir=index_dir,
     settings=settings, issued_sha256_before=sha256_file(ISSUED_DB))`.
  4. `with tap_logs() as logs, launch_server(settings, overrides=None) as server:` build `run = JourneyRun(env=env,
     server=server, script=JourneyScript(), models={}, clock=None, db=DbReader(env.db_path), logs=logs,
     guard=SocketGuard(), collector=StepCollector(), strict=False, nodeid=f"tests/live::{case.case_id}")`, then `try:
     outcome = play_case(run, case) finally: run.close_clients(); sink.append(logs.all_text())`.
  5. The whole of 1–4 sits in `try … finally: shutil.rmtree(root, ignore_errors=True)`. Return `outcome`.

  *Invariant: one fresh DB copy and one fresh app per case; no overrides; evidence is read before the server stops.*
- **`forbidden_values`:** returns `(label, value)` pairs for:
  - `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` from `environ`
    (non-blank only; the label is the env name);
  - every `outcome.secrets.values` pair of every result with an outcome.

  Duplicates by value are removed; the first label is kept.

`tests/live/test_live_smoke.py`:
```python
_SKIP = live_skip_reason(os.environ)
pytestmark = [pytest.mark.live, pytest.mark.skipif(_SKIP is not None, reason=_SKIP or "")]
CASE_IDS: Final = ("WP-1", "WP-2", "warranty", "WP-4F", "DANGER", "WP-4")   # param ids, in SMOKE_TABLE order
_LABELS: dict[str, str] = {}                                               # value → label, for AC-15's message

@pytest.fixture(scope="module")
def smoke_run(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> SmokeRun: ...
@pytest.mark.parametrize("position", range(6), ids=CASE_IDS)
def test_live_case(smoke_run: SmokeRun, position: int) -> None: ...
def test_live_compatibility(smoke_run: SmokeRun) -> None: ...
def test_issued_and_heldout_untouched(smoke_run: SmokeRun) -> None: ...
def test_record_written(smoke_run: SmokeRun) -> None: ...
def test_record_and_output_hold_no_secrets(smoke_run: SmokeRun) -> None: ...   # defined LAST in the file
```
The `smoke_run` fixture, in order:
1. Set up the context: `cap = Limits().spend.daily_cap_usd`; `ctx: dict[str, Any] = {}`; `logs: list[str] = []`;
   `out, err = io.StringIO(), io.StringIO()`; `reports = REPO_ROOT / "eval" / "reports"`; `reports_before =
   sorted(os.listdir(reports)) if reports.is_dir() else []`; `issued_before = sha256_file(ISSUED_DB)`.
2. Define `make()`, the launcher factory `execute` calls only after the pre-flight:
   - `index_dir, cache = build_live_index(tmp_path_factory.mktemp("live-index"))`;
   - `ctx["cache"] = cache`; `ctx["index_note"] = f"{index_dir} built by meridian.retrieval.ingest.main (WF-14) with
     {EMBEDDING_MODEL}; {FastembedIndex(index_dir, model_cache_dir=cache).info()}"`;
   - `ctx["agent_version"] = agent_version_cli(REPO_ROOT)`;
   - `ctx["stack"].enter_context(fastembed_env(cache))`;
   - `return live_launcher(source=os.environ, index_dir=index_dir, agent_version=ctx["agent_version"], sink=logs,
     info=ctx)`.
3. Run it: `with contextlib.ExitStack() as stack, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err),
   audit_opened() as opened:`. Set `ctx["stack"] = stack`, then `try: results = execute(os.environ,
   make_launcher=make, cap_usd=cap)`. On `except (SmokeRefused, RuntimeError) as exc`: leave the block, then
   `pytest.fail(str(exc), pytrace=False)`. The messages name figures, env names or the missing cache, never a value.
4. Build `run = SmokeRun(spent_today_usd=float(os.environ[SPENT_ENV]), cap_usd=cap, results=results,
   agent_version=ctx["agent_version"], role_models=ctx.get("role_models", {}), index_note=ctx["index_note"],
   issued_sha_before=issued_before, issued_sha_after=sha256_file(ISSUED_DB), opened_counts=opened_counts(opened,
   root=REPO_ROOT), offending=offending_paths(opened, dev_dir=DEV_DIR, schema_path=SCHEMA_PATH, cases_dir=CASES_DIR,
   heldout_key_root=HELDOUT_KEY_ROOT), eval_reports_unchanged=reports_before == (sorted(os.listdir(reports)) if
   reports.is_dir() else []), langfuse_on=all(os.environ.get(n, "").strip() for n in LANGFUSE_NAMES),
   output_text=out.getvalue() + err.getvalue() + "\n".join(logs))`.
5. Write the record:
   - `labelled = forbidden_values(results, os.environ)`; `_LABELS.update({v: label for label, v in labelled})`;
     `run.forbidden = tuple(v for _, v in labelled)`;
   - `command = f"MERIDIAN_LIVE_SMOKE=1 {SPENT_ENV}={os.environ[SPENT_ENV].strip()} uv run pytest
     {shlex.join(str(a) for a in request.config.invocation_params.args)}"`;
   - `run.record_path = write_smoke_record(run, root=REPO_ROOT, day=datetime.now(ZoneInfo("America/Chicago")).date(),
     revision=tested_revision(REPO_ROOT, run.agent_version), command=command, forbidden=run.forbidden)`.

   The record is written even when cases fail (PD-12).
6. After the redirect block, print to the real stdout one line per case (`f"{case_id or '—'} {label}: {status}"`) and
   `f"live smoke record: {run.record_path}"`. Return `run`.

**Output capture.** `LogTap.all_text()` holds every log record with all its attributes. That is a superset of what any
log handler writes, so it covers "log lines" even when the app's stream handler was bound to another stream earlier in
the process.

**Tests:**
- `test_live_case`: `result = smoke_run.results[position]`; `assert result.status == "pass", "\n".join(quote(f,
  smoke_run.forbidden) for f in result.failures) or getattr(result.entry, "reason", "")`.
- `test_live_compatibility`: `problems = [p for o in smoke_run.outcomes for p in check_compatibility(o)]`; print
  `compat_counts(smoke_run.outcomes)`; `assert problems == []`.
- `test_issued_and_heldout_untouched`: `issued_sha_before == issued_sha_after`, `offending == ()`; print
  `opened_counts`.
- `test_record_written`:
  - `record_path` exists;
  - each `f"| {field} |"` for `field in FIELDS` is present;
  - `LIVE_LEVEL`, `NOT_AN_EVAL_LINE` and `SPENT_SOURCE` are present;
  - `f"run total cost_usd {sum(o.cost_usd for o in smoke_run.outcomes):.6f}"` is present.
- `test_record_and_output_hold_no_secrets`:
  - for each value in `smoke_run.forbidden`, count hits in the record text and in `output_text`;
  - collect `[_LABELS[v] for v in forbidden if hits]`;
  - `assert` the list is empty; the message lists **labels only**.

### A8. Free tests (`test_smoke_guards.py`, part A's seven), context, commit

Tests, with exact names. Each prints its evidence line.
1. **`test_smoke_set_is_six_dev_cases`:**
   - `select_smoke_set()` returns 6 `SmokeCase`.
   - The ids are `("WP-1", "WP-2", expected, "WP-4F", "DANGER", "WP-4")`, where the test computes `expected` by
     scanning `sorted(DEV_DIR.glob("*.key.json"))` with plain `json.loads` for the first `topic == "warranty" and
     in_scope`.
   - Labels and journeys equal `SMOKE_TABLE`; every `script.split == "dev"`.
   - In `tmp_path / "dev"`: a copy of `WP-1.case.json` with `"clock": "2026-10-17T10:00:00-05:00"`, plus its key,
     raises `CaseCustodyError` with `str(exc) == "WP-1: clock_mismatch"`. A copy without `"turns"` gives `"WP-1:
     schema_invalid"`.
   - Print the six `(id, label)` pairs.
2. **`test_refuses_heldout_and_outside_dev`**, inside `audit_opened() as opened`:
   - (a) `checked_dev_path(HELDOUT_SCRIPTS_DIR / "T-CALL-20260101-0001.case.json", "T-CALL-20260101-0001")` raises
     `outside_dev`. The id is invented; the test never lists the held-out folder.
   - (b) `DEV_DIR / ".." / "heldout" / "X.case.json"` raises `outside_dev`.
   - (c) `tmp_dev / "WP-1.case.json"` as a symlink to `tmp_path / "outside.json"`; `load_dev_case("WP-1",
     dev_dir=tmp_dev)` raises `outside_dev`.
   - (d) A real copy of WP-1 (script + key) with `"split": "held-out"` gives `str(exc) == "WP-1: not_dev_split"`;
     assert the message contains no `/`.
   - (e) `load_dev_case("../heldout/X")` raises `bad_case_id`.
   - (f) A tmp dev dir holding only the WP-1, WP-2, WP-4F, DANGER and WP-4 files (copied) gives
     `select_smoke_set(tmp_dev)[2] == NotRunCase("warranty", "J-2", None, NO_WARRANTY)`.

   After the block: `offending_paths(opened, dev_dir=DEV_DIR, schema_path=SCHEMA_PATH, cases_dir=CASES_DIR,
   heldout_key_root=HELDOUT_KEY_ROOT) == ()`, and no opened path is under `tmp_path / "outside.json"` or
   `HELDOUT_SCRIPTS_DIR`.
3. **`test_preflight_refuses_over_cap`:**
   - A recording stub `Recorder` with `made = 0` and `launches = 0`. Its `make()` increments `made` and returns a
     launcher that increments `launches` and returns `fake_outcome(case, 0.0)`.
   - For each environ `{}`, `{SPENT_ENV: "abc"}`, `"nan"`, `"inf"`, `"-1"` and `"29.767"`:
     `pytest.raises(SmokeRefused)` on `execute(env, make_launcher=stub.make, cap_usd=30.0)`, and `stub.made == 0 and
     stub.launches == 0`. Print each refusal.
   - `"29.766"` gives no refusal and `stub.made == 1` (the boundary, PD-5).
4. **`test_stops_between_cases_and_on_cap`.** Stub outcomes come from a test helper `fake_outcome(case, cost_usd, *,
   notice=None, failure_kind=None, failures_text="")`: a `CaseOutcome` with one spend row (`cost_usd`, `failure_kind`,
   `role="planner"`, `provider="anthropic"`, `attempt=1`) and one exchange whose body carries `notice`. Use `run_cases`
   directly with `select_smoke_set()`:
   - (a) figure `29.70`, case 1 costs `0.12` → 1 launch; results 2…6 are `NOT_RUN: spend` (0.12 + 0.039×5 = 0.315 >
     0.30);
   - (b) figure `0`, case 2 has notice `{"code": "SPEND_CAP_REACHED"}` → 2 launches; 3…6 `NOT_RUN: spend`;
   - (c) figure `0`, case 1's row has `provider_spend_cap` → 1 launch;
   - (d) the same with `our_spend_limit`.
5. **`test_live_cases_skip_without_opt_in`:**
   - `live_skip_reason({})` names `MERIDIAN_LIVE_SMOKE`.
   - `live_skip_reason({"MERIDIAN_LIVE_SMOKE": "1"})` names both keys; with one key set, it names the other; with
     `"1"` and two placeholder values, it returns `None`.
   - Then a subprocess. `env` = `os.environ` minus `MERIDIAN_LIVE_SMOKE`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`
     and `LIVE_SMOKE_SPENT_TODAY_USD`. Run `subprocess.run([sys.executable, "-m", "pytest",
     "tests/live/test_live_smoke.py", "-m", "live", "-q", "-rs", "-p", "no:cacheprovider"], cwd=REPO_ROOT, env=env,
     capture_output=True, text=True, timeout=180)`.
   - Expect `returncode == 0`, with `"10 skipped"` and `"live smoke not requested"` in stdout.
6. **`test_record_has_every_field`:**
   - Build a `SmokeRun` from `fake_outcome`s: one pass, one fail whose failure quotes a reply, one `NOT_RUN: spend`.
   - Call `render_smoke_record(..., scope="live-smoke-1", revision="abc1234; agent_version x", command="cmd",
     forbidden=())`.
   - Assert the nine `| {f} |` rows, `LIVE_LEVEL`, `NOT_AN_EVAL_LINE`, `SPENT_SOURCE`, `LIVE_TITLE_SUFFIX`, and
     `f"run total cost_usd {sum:.6f}"`.
   - Also `next_smoke_number(tmp)` → 1, then 3 after creating `2026-10-21-live-smoke-2.md`.
7. **`test_record_writer_redacts`:**
   - Generate sentinels per test: `key = "sk-sentinel-" + letters(24)`, `secret = letters(48)`, `password = "pw" +
     letters(20)`, `code = f"{secrets.randbelow(900000) + 100000}"`, `phone =
     f"512-555-{secrets.randbelow(9000) + 1000}"`. `letters` comes from `tests.journeys.support.env`.
   - Put all five into a failure string and a reply text of a fake outcome.
   - Render with `forbidden=(key, secret, password, code, phone)`; each value has 0 hits. Print the counts.

`test_not_an_eval_run` (AC-16) is part B (B3).

**Context (AC-18), in the part A commit:**
- Area map row `3+`, last cell: append `; AEA-61 part A: tests/live/ (smoke driver, custody/spend/record guards, paid
  tests skipped by default) actual (<sha>); scripted journeys j2–j5 await AEA-51; paid run awaits AEA-51 and gate::paid`.
- ICM: add one row after the last *Routes verified against code and tests* row: `| Routes verified against code and
  tests | provisional | <date>: live smoke AEA-61 part A (<sha>): tests/live free run (7 passed, 10 skipped); journeys
  await AEA-51; paid run awaits gate::paid | Re-run on any prompt, schema, model, tool or orchestration change
  (integrated-journeys rule 4) |`. Keep it ≤ 400 chars.
- DO-3 §9's `└── live/` line (line 723 at `dc8d8d0`; find it by its text) becomes: `└── live/             marked `live`: paid calls, never in the default run (recordings
  feed contract/); AEA-61: conftest, smoke*.py, scripted_cases, test_smoke_guards, test_live_smoke; records
  docs/testing/journeys/*-live-smoke-<N>.md`.
- `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` reports no FAIL in an owned row.

**Commits.** Use explicit paths, never `git add -A`. Each message ends with the line `Co-Authored-By: Claude Sonnet 5.5
<noreply@anthropic.com>`. Never push or force-push; only the merge step pushes `main`.
1. `test(AEA-61): live smoke driver, custody and spend guards` — the `tests/live/*.py` files of part A.
2. `docs(AEA-61): context rows for the live smoke driver` — area map, ICM, DO-3.

**If AEA-51 pass 2 is not on `main` (A0 step 1): stop and report** "part A built (<sha>); part B blocked-on AEA-51
pass 2; part C blocked-on AEA-51 pass 2 and gate::paid". The journey record level for this ticket stays `mock-tested`.

### B0. Verify part B's prerequisites (after AEA-51 merges)

1. A0 step 1's three checks pass on `main`. Then `git merge main` into the AEA-61 branch (or rebase, per the
   orchestrator).
2. Open `tests/integration/customer_support.py` and `tests/graph/worked_pair_scenarios.py` on `main` and confirm every
   §4.3 name and signature. A renamed helper: use the merged name and list it in the report. A missing capability (no
   per-step script, no built-index run, no `kb_steps`, `scheduled_appointment` or `open_slot`): stop and report
   `blocked-on AEA-51 follow-up`.
3. Re-check the facts B1 relies on (refresh 6 item 4), each with one read-only `uv run python -c` (no server):
   - `meridian.gates.rules.match_rules("My AC's out and my mother is 88 and it's 95 degrees in here.").danger_words` is
     `False`;
   - in the issued DB (`tests.fixtures.sqlite.ISSUED_DB`, opened `mode=ro`), the open slots for zone `north`,
     `2026-10-19`, `08:00-12:00` are `[56]` for `hvac_repair` and `[41]` for `hvac_tune_up`;
   - the earliest scheduled visit of MHC-10001 is appointment 159, and of MHC-57204 is appointment 1.

   Any other answer: stop and report it. Do not adapt the checks or the tables to it.

### B1. Scripted tables (`tests/live/scripted_cases.py`), rewritten in refresh 6 from AEA-51's pass-2 drivers

`scripted_cases.py` is part B only, so it imports AEA-51's building blocks at module level; no part A file imports it.
It must not contain the strings `heldout` or `key_dir`, and neither may the journey files (a rule of this plan, not an
existing grep).
```python
from tests.graph.worked_pair_scenarios import (
    MOVED_SENTENCE, NORMAL, TOOLS, Step, account_steps, brief, classifier, find_args, kb_steps, next_message_id,
    open_slot, planner, report, responder, scheduled_appointment, scheduling_steps, step, tool,
)
from tests.integration.customer_support import CustomerRun
from tests.live.smoke_checks import WP4F_TARGET_SLOT     # 56: the window WP-4F's turn 4 asks for

Variant = Literal["good", "bad"]
StepFactory = Callable[[ScriptedTurn], Step]            # built just before its turn: next_message_id reads the DB then
MONDAY: Final = "2026-10-19"
MONDAY_MORNING: Final = "08:00-12:00"
def scripted_turns(case: SmokeCase, run: CustomerRun, *, variant: Variant = "good") -> BeforeTurn: ...
def case_steps(case: SmokeCase, run: CustomerRun, variant: Variant) -> tuple[StepFactory, ...]: ...
```
- `scripted_turns` calls `factories = case_steps(case, run, variant)` once. It asserts `len(factories) ==
  len(case.script.turns)`, with the message `f"{case.case_id}: {len(factories)} scripted steps for {n} turns"`. It
  returns `before_turn(i, turn, exchanges)`, which runs `run.steps.set_step(factories[i](turn))`.
- `case_steps` dispatches on `case.label` to one private builder per row group below. An unknown label raises
  `KeyError`. `variant="bad"` on a label with no bad row (`billing`, `warranty`) raises `ValueError(f"no bad table for
  {label}")`.
- **Common pieces:**
  - `talk = {Role.CLASSIFIER: NORMAL}` (every text turn);
  - `locate_wait = responder("I need to find your record first.")`;
  - `code_sent = {Role.RESPONDER: responder("Thanks, I sent a code.")}`, the whole step of every form turn (AEA-51's
    `locate_and_code` default);
  - a brief quotes the customer's own message as `turn.text[:30]` (AEA-51 quotes `opening[:30]`).
- **Ids from the DB are read inside the builder,** when `case_steps` runs (the server is up):
  `appt = scheduled_appointment(run, str(case.script.seeded_customer))`, `svc = str(appt["service_type"])`,
  `app_id = int(appt["appointment_id"])`. Never write 159, 1 or 41 as a tool argument literal; the WP-4F target is
  `WP4F_TARGET_SLOT`.

Turn tables. T1 is `i == 0`. Each cell is the whole `Step` for that turn; `PLANNER` stands for `Role.PLANNER`, and
likewise for the other roles.

| Case (label) | Turn | Step |
|---|---|---|
| WP-1 (`membership`) | T1–T3 text | `{**talk, PLANNER: planner(knowledge="yes", topic="membership"), SPECIALIST: kb_steps(run, q, s), RESPONDER: responder(s)}`, with `(q, s)` per turn: T1 `("Comfort Club membership benefits tune-ups repairs", "Members get two seasonal tune-ups a year and 15% off all repairs.")`; T2 `("Comfort Club membership price per year", "The Comfort Club is $189 per year per system.")`; T3 `("Comfort Club Plus plumbing inspection plumbing repairs", "Comfort Club Plus adds an annual whole-home plumbing inspection and 15% off plumbing repairs.")`. The sentences are from the current `membership/comfort_club_overview.md` |
| WP-1 **bad** | T1 | as good T1, but `SPECIALIST: (kb_steps(run, q, s)[1],)`: the report step only, **no `kb_search`**. T2 and T3 as good |
| WP-2 (`billing`) | T1 text | `{**talk, PLANNER: invoice_plan, RESPONDER: locate_wait}`, with `invoice_plan = planner(account="invoice", topic="billing")` |
| | T2 form | `code_sent` |
| | T3 code | `{**talk, PLANNER: invoice_plan, SPECIALIST: read, RESPONDER: responder("This invoice bills a diagnostic visit, a contactor replacement and a dispatch fee.")}`, with `read = account_steps(tool(TOOLS["invoice"], ReadInvoicesArgs.model_validate({"invoice_number": "INV-204411"}).model_dump(mode="json")), summary="Read the invoice as billed.")` (AEA-51's `wp2`) |
| | T4 text | `{**talk, PLANNER: invoice_plan, SPECIALIST: read, RESPONDER: responder("I can't email a copy from this chat. The invoice lists three lines: the diagnostic visit, the part and the dispatch.")}` |
| | T5 text | `{**talk, PLANNER: planner(handoff="billing_dispute", topic="billing"), RESPONDER: responder("I have asked a representative to review that charge."), BRIEF: brief(needs=[{"message_id": next_message_id(run), "text": turn.text[:30]}], claims=[], open_decision="Review the disputed charge.")}` |
| warranty | T1 text | `{**talk, PLANNER: warranty_plan, RESPONDER: locate_wait}`, with `warranty_plan = planner(account="warranty", topic="warranty")` |
| | T2 form | `code_sent` |
| | T3 code | `{**talk, PLANNER: warranty_plan, SPECIALIST: account_steps(tool(TOOLS["warranty"], {}), summary="Read the warranty record."), RESPONDER: responder("Here is what your warranty record shows.")}` (AEA-51's `warranty`) |
| WP-4F (`booking with follow-up`) | T1 text | `{**talk, PLANNER: move_plan, RESPONDER: locate_wait}`, with `move_plan = planner(scheduling="reschedule", topic="booking")` |
| | T2 form | `code_sent` |
| | T3 code | `{**talk, PLANNER: move_plan, SPECIALIST: scheduling_steps(tool(TOOLS["find_windows"], find_args(svc)), appointment_id=app_id), RESPONDER: responder("Here are the open windows.")}` |
| | T4 text | `{**talk, PLANNER: move_plan, SPECIALIST: (step(tool(TOOLS["find_windows"], monday)), step(tool(TOOLS["move"], MoveVisitArgs(appointment_id=app_id, new_slot_id=WP4F_TARGET_SLOT).model_dump(), call_id="call-2")), step(report(SchedulingReport, appointment_id=app_id, wanted_time="Monday the 19th, 8 to 12", note="moved"))), RESPONDER: responder("Done. Your visit is moved to Monday, October 19, 8:00 am to 12:00 pm.")}`, with `monday = find_args(svc, earliest=MONDAY, latest=MONDAY, window=MONDAY_MORNING, wanted_text="Monday the 19th, 8 to 12")` |
| | T5 text ("Yes, please.") | `{**talk, PLANNER: planner(topic="booking"), SPECIALIST: scheduling_steps(tool(TOOLS["find_windows"], find_args(svc)), appointment_id=app_id), RESPONDER: responder(MOVED_SENTENCE)}` (AEA-51's `wp4f_followup`) |
| WP-4F **bad** | T4 | as good T4, but `SPECIALIST: (step(tool(TOOLS["find_windows"], monday)), step(report(SchedulingReport, appointment_id=app_id, wanted_time="Monday the 19th, 8 to 12", note="moved")))`: **no `move`**. Other turns as good |
| DANGER (`safety`) | T1 | `{PLANNER: planner(scheduling="book_new", topic="booking"), CLASSIFIER: classifier("danger")}` (AEA-51's `danger`; the safety reply makes no responder call) |
| DANGER **bad** | T1 | `{PLANNER: planner(scheduling="book_new", topic="booking"), CLASSIFIER: NORMAL, RESPONDER: responder("I can help book a visit. First I need to find your account.")}`: **no raise** (AEA-51's `nodanger`) |
| WP-4 (`fee-bearing change`) | T1 text | `{**talk, PLANNER: move_plan, RESPONDER: locate_wait}` |
| | T2 form | `code_sent` |
| | T3 code | `{**talk, PLANNER: move_plan, SPECIALIST: scheduling_steps(tool(TOOLS["find_windows"], find_args(svc)), appointment_id=app_id), RESPONDER: responder("When would you like to move your visit to?")}` |
| | T4 text | `{**talk, PLANNER: move_plan, SPECIALIST: scheduling_steps(tool(TOOLS["find_windows"], find_args(svc, earliest=MONDAY, latest=MONDAY, window=MONDAY_MORNING, wanted_text="Monday morning")), appointment_id=app_id), RESPONDER: responder("Here are the Monday morning windows. They are shown, not held.")}` |
| | T5 text | `{**talk, PLANNER: move_plan, SPECIALIST: (step(tool(TOOLS["move"], MoveVisitArgs(appointment_id=app_id, new_slot_id=target).model_dump())), step(tool(TOOLS["change_request"], RequestVisitChangeArgs(appointment_id=app_id, change="move", wanted_text="Monday morning").model_dump(), call_id="call-2"), report(SchedulingReport, appointment_id=app_id, wanted_time="Monday morning", note="change request"))), RESPONDER: responder("I've sent your change request to a representative."), BRIEF: brief(needs=[{"message_id": next_message_id(run), "text": turn.text[:30]}], claims=[], open_decision="Confirm or decline the change.")}`, with `target = open_slot(run, str(appt["zone"]), svc, after=MONDAY)`. As in AEA-51's `_fee_bearing_scenario`, the move is refused `fee_bearing` and the change request opens the P2 case |
| WP-4 **bad** | T5 | as good T5, but `SPECIALIST: (step(tool(TOOLS["move"], <same args>)), step(report(SchedulingReport, appointment_id=app_id, wanted_time="Monday morning", note="change request")))`: **no `change_request`**. RESPONDER and BRIEF as good |

**Rules for the tables:**
- Script texts are read from the case files. Never rewrite a case text in a table.
- When a good test fails, read the failure first:
  - a failing **check** with a correct table is a finding for the owner ticket (integrated-journeys rule 5): report it
    and never change `smoke_checks.py` to make it pass;
  - a **table** that runs out of script (an `exhausted` entry in `run.script.problems()`) or calls a tool with arguments
    the real tool refuses is a table bug: fix the table, keep its meaning, and note the change in the report.
- A scripted sentence that the fact check trims (a `checks` row `fact` / `trimmed`) fails no check here; leave it.

### B2. The four journey files

Each file sets `pytestmark = pytest.mark.journey` and has one test per case. Each test opens its own run, and every API
call goes through `play_case`, which names the operationIds.
```python
# tests/journeys/j2/test_aea_61.py
NEEDS = ("session_service", "turn_service", "run_graph", "identity_service", "demo_clock")
OPS = ("startChatSession", "submitTurn", "listDemoInbox")
def _case(label: str) -> SmokeCase: ...     # the entry of select_smoke_set() with that label; pytest.skip(NO_WARRANTY) for a NotRunCase
def test_j2_membership_scripted(request): ...    # WP-1 good
def test_j2_billing_scripted(request): ...       # WP-2 good
def test_j2_warranty_scripted(request): ...      # warranty good
def test_j2_membership_without_kb_search_caught(request): ...   # WP-1 bad
```
Body of a good test:
```python
case = _case("membership")
with open_customer_run(request) as run:
    with run.step("J-2", "WP-1 smoke checks (scripted)", needs=NEEDS, operations=OPS):
        outcome = play_case(run, case, before_turn=scripted_turns(case, run))
        failures = check_case(outcome)
        assert failures == [], "\n".join(failures)
```
A bad test has the same body with `variant="bad"` and the step name `"WP-1 skipped kb_search is caught"`, then:
`caught = [f for f in failures if f.startswith("WP-1 turn 1: no kb_search lookup")]`; `assert caught, failures`;
`print(f"caught: {caught[0]}")`.

| File | Tests | Journey | Bad-test prefix | NEEDS / OPS |
|---|---|---|---|---|
| `j3/test_aea_61.py` | `test_j3_follow_up_scripted`, `test_j3_follow_up_without_move_caught` | `"J-3"` | `"WP-4F: no actions(moved) row"` | as j2 |
| `j4/test_aea_61.py` | `test_j4_fee_bearing_scripted`, `test_j4_fee_bearing_without_change_request_caught` | `"J-4"` | `"WP-4: no P2 fee_bearing_change case"` | as j2, plus `"handoff_service"` |
| `j5/test_aea_61.py` | `test_j5_danger_scripted`, `test_j5_danger_without_raise_caught` | `"J-5"` | `"DANGER: first block is not the emergency line"` | NEEDS `("session_service", "turn_service", "run_graph", "case_service")`; OPS `("startChatSession", "submitTurn")` |

### B3. `test_not_an_eval_run` (AC-16), added to `test_smoke_guards.py`

1. `reports = REPO_ROOT / "eval" / "reports"`; take `reports_before`.
2. `with open_customer_run(request) as run:` play the DANGER `SmokeCase` with `scripted_turns(case, run)`.
3. Assert:
   - no lower-cased `EVAL_KEY_HEADER`, `RUN_ID_HEADER` or `RUN_TAG_HEADER` in `outcome.header_names`;
   - `set(outcome.evidence.run_tags) == {"live"}`;
   - `outcome.evidence.eval_runs == 0`;
   - `check_case(outcome) == []`;
   - `reports_after == reports_before`.
4. Render a record from it and assert `NOT_AN_EVAL_LINE` is in the text.

The test skips with AEA-51's `INDEX_SKIP` when there is no model cache. The module imports AEA-51's helpers inside the
test function, so part A's file never imports an unmerged module.

### B4. Scripted record, context, commit

- Record: `uv run pytest -m journey tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py
  tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py --journey-record=AEA-61` writes
  `docs/testing/journeys/<date>-AEA-61.md`.
- Area map: replace the part A sentence's `scripted journeys j2–j5 await AEA-51` with `scripted journeys
  tests/journeys/j{2,3,4,5}/test_aea_61.py actual (<sha>)`.
- ICM: the AEA-61 row's evidence becomes `<date>: live smoke AEA-61 (<sha>): tests/live free run (8 passed, 10
  skipped), journeys j2–j5 test_aea_61 (<m> passed); record docs/testing/journeys/<date>-AEA-61.md; paid run awaits
  gate::paid`.
- Commits:
  1. `test(AEA-61): scripted smoke journeys J-2..J-5 and the not-an-E-run check` — `scripted_cases.py`,
     `test_smoke_guards.py` and the four journey files.
  2. `docs(AEA-61): scripted journey record and context rows`.
- **Then stop and report:** "build done; paid run awaits gate::paid (D-15)".

### C1–C2. Part C: the paid run (only after Innocent's explicit go with the spend figure)

- **C1** runs on the same revision, cheapest first, stopping at the first red: §7 checks 1–6, then P1 (AEA-60's file, on
  `main` since `0e37fad`).
- **C2.** Innocent (or the session at his explicit instruction) puts `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` and, for
  trace IDs, the four `LANGFUSE_*` values of this app's project into the environment. The implementer never reads,
  prints or copies `.env` and never echoes a key.
- Run P2.
- Commit `docs(AEA-61): live smoke record <N>` with:
  - the record;
  - the ICM row's evidence replaced by the record link and result (`<k>/6 pass, run total $<x>`);
  - the area-map sentence `paid run awaits AEA-51 and gate::paid` replaced by `live record
    docs/testing/journeys/<date>-live-smoke-<N>.md`.
- **A failing case:** keep the record and do not fix anything here. Report the failing assertion and its owner ticket
  (rule 5); the re-run is a new record.

---

## 6. Data and fixtures (synthetic or issued only)

| Data | Source |
|---|---|
| Case scripts and keys | `eval/cases/dev/*.case.json`, `*.key.json` (AEA-06, dev split; worked pairs WP-1, WP-2, WP-4, WP-4F; synthetic DANGER; transcript-derived warranty case `T-CALL-20260723-0276` with seeded MHC-10001; WP-2 seeds MHC-10002, WP-4 MHC-57204, WP-4F MHC-10001) |
| Tmp dev folders | Byte copies of those dev files into `tmp_path`, edited per test (clock, split, missing field) |
| Scheduling DB | The issued `meridian_scheduling.sqlite`, copied per case by the app's first boot; never written |
| KB index | Part C: built once per paid run by `build_live_index` (`meridian.retrieval.ingest.main` with cached bge-small-en-v1.5 from `var/fastembed` or the git common dir's `var/fastembed`). Part B: AEA-51's `open_customer_run` builds its own |
| Login pair, session secret | AEA-57's `journey_environ` per run (random letters) |
| Provider and Langfuse keys | Part C only, from the environment at the go; placeholders elsewhere |
| Codes, phones | Read at run time from `listDemoInbox` and the working copy; never in a file, test name or print |
| Sentinels | Generated per test with `secrets` (AC-15 free test) |
| Expected values | The dev keys; `policy/texts.py`, `policy/handoff.py`; the WP-4/WP-4F keys' appointment facts (appointment 1 today 12:00–4:00 pm; appointment 159 → slot 56) |

---

## 7. Checks

Run from the worktree with `export UV_LINK_MODE=hardlink`, no `node_modules`, at most `-n 2`, and the journeys and the
live set serially. Run cheapest first and stop at the first red.

| # | Part | When | Command | Passing looks like |
|---|---|---|---|---|
| 1 | A, B | Iterating + before commit | `uv run ruff check tests/live && uv run ruff format --check tests/live` (part B: add the four `tests/journeys/j{2,3,4,5}/test_aea_61.py` paths to both) | no findings |
| 2 | A, B | Before commit | `uv run mypy` | `Success` |
| 3 | A, B | Iterating + before commit (free) | `uv run pytest tests/live -q -rs` | part A: 7 passed, 10 skipped "live smoke not requested…"; part B: 8 passed, 10 skipped; no "non-loopback" error |
| 4 | B | Iterating + before commit (journeys, serial) | `uv run pytest tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py -m journey -q -rs` | 6 good + 4 bad tests pass (10); no `blocked-on` skip |
| 5 | A, B | Before commit | `uv run python -m tests.journeys.affected --base main` | part A: "0 journeys affected" (no journey path changed); part B: the selected journeys green |
| 6 | B | Before commit | `uv run pytest tests/journeys/support -q` and `uv run pytest -m journey tests/journeys/j2 tests/journeys/j3 tests/journeys/j4 tests/journeys/j5 -q` | harness self-tests green; the siblings' journeys still green beside ours (after AEA-51 merges: `j2/test_aea_35.py`, `test_aea_38.py`, `test_aea_51.py`; `j3/test_aea_27.py`, `test_aea_28.py`, `test_aea_34.py`, `test_aea_39.py`, `test_aea_43.py`, `test_aea_51.py`; `j4/test_aea_28.py`, `test_aea_39.py`, `test_aea_51.py`; `j5/test_aea_36.py`, `test_aea_37.py`, `test_aea_51.py`, `test_aea_60.py`) |
| 7 | A, B | Before commit | `git diff --name-only main...HEAD` and `git diff --name-only main...HEAD -- tests/journeys/support src eval scripts` | only §2.1 paths; the second is empty |
| 8 | A, B | Before commit | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL in an owned row |
| P1 | C | Same revision, before the paid run | `uv run pytest tests/contract/test_prompts_vs_consumers.py -q` | green |
| P2 | C | After the go | `MERIDIAN_LIVE_SMOKE=1 LIVE_SMOKE_SPENT_TODAY_USD=<figure> uv run pytest tests/live -m live -v` | 10 passed; record path printed; run total ≤ the remaining cap |

**No full suite.** The change adds test files only. It touches no shared fixture (the new `conftest.py` is
package-scoped to `tests/live/`), no setting, no dependency and no module imported across the codebase
(build-loop-test-scope). The live tests never run in a merge gate.

**Tests the implementer writes with the code:**
- `tests/live/test_smoke_guards.py`: `test_smoke_set_is_six_dev_cases`, `test_refuses_heldout_and_outside_dev`,
  `test_preflight_refuses_over_cap`, `test_stops_between_cases_and_on_cap`, `test_live_cases_skip_without_opt_in`,
  `test_record_has_every_field`, `test_record_writer_redacts` (part A), `test_not_an_eval_run` (part B).
- `tests/live/test_live_smoke.py` (the WP-N pairs, live): `test_live_case[WP-1|WP-2|warranty|WP-4F|DANGER|WP-4]`,
  `test_live_compatibility`, `test_issued_and_heldout_untouched`, `test_record_written`,
  `test_record_and_output_hold_no_secrets`.
- The journey files (the WP-N pairs, scripted; AC-5): `tests/journeys/j2/test_aea_61.py` (4 tests), `j3` (2), `j4` (2),
  `j5` (2).

**Existing tests that must stay green:** `tests/journeys/support/test_support.py`; every sibling journey in `j2`–`j5`;
`tests/contract/test_retrieval_contract.py` (shares the index recipe; not edited).

**What the implementer must NOT do**
- Run P2 (or any command with `MERIDIAN_LIVE_SMOKE=1` and real keys) without Innocent's explicit go and spend figure,
  relayed by the orchestrator.
- Read, print, copy or commit `.env` or any key. Never put a key, password, session secret, code, card-like number or
  full phone number in a file, test name, log, print or commit.
- Edit any file outside §2.1: `src/**`, `tests/journeys/support/**`, AEA-51's test helpers, `eval/**`, `scripts/**`,
  `pyproject.toml`/`uv.lock`, the OpenAPI, `UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, issued data, the briefing,
  `docs/archive/`, `docs/parked/`, the build ledger.
- Import an unmerged module at module level in any part A file (mypy checks `tests/`; part A must type-check on `main`).
- Open, list or glob `eval/cases/heldout/` or `/home/linuxuser/.meridian-sealed/`, or substitute a case from another
  split.
- Send `X-Meridian-Eval-Key`, `X-Meridian-Run-Id` or `X-Meridian-Run-Tag`; set `MERIDIAN_EVAL_KEY`; or write under
  `eval/reports/`.
- Pass `ContainerOverrides` to the live app, use `dependency_overrides` or `TestClient`, or monkeypatch any `meridian`
  module.
- Use `LogTap.structured("signal")`; it never matches (PD-6).
- Weaken a check to match observed behaviour, turn a failing live case into a pass, or fix a sibling's code here.
- Write `heldout` or `key_dir` anywhere under `tests/journeys/`, or in `scripted_cases.py`, which those files import.
- Bind ports 4019 or 5184; run pytest with more than `-n 2`; or run the journeys or the live set with `-n`.
- Use `git add -A`, push, or force-push.

---

## 8. Risks and requests

| # | Kind | Item | Handling |
|---|---|---|---|
| R-1 | Blocker (parts B, C) | AEA-51 is not merged. Ledger `sent-back`: its merge gate went red on `tests/journeys/j9/test_aea_40.py::test_j9_rate_limited_through_the_real_server`; the fix `fdcc332` is on its branch. Pass 2 is complete there (`Key("run_graph")` bound over the production adapters; the helpers in §4.3). Everything else this slice needs is merged (AEA-21b `9b3824e`, AEA-40-F1 `47da752`, AEA-60 `0e37fad`, AEA-39 `12e46ee`) | Part A now; parts B and C start only on A0 step 1's three checks; B0 verifies the names and the facts |
| R-2 | Resolved (refresh 5) | AEA-60's prompt check (`tests/contract/test_prompts_vs_consumers.py`) merged at `0e37fad` | P1 runs on the paid run's revision as §7 says |
| R-3 | Gate | `gate::paid` + the day's spend statement (D-15) | Part C only; the plan carries no figure and invents none |
| R-4 | Live variance | Real models may route a dev script differently (e.g. WP-4F moving in turn 5, WP-2 reading the invoice twice) | Checks assert outcomes, not turn positions, where the ACs allow (PD-7; WP-4F "settled on the follow-up"). A genuine miss is a finding for the owner ticket, never a weakened check |
| R-5 | Collision / ownership | Six helper modules inside `tests/live/` beyond the four files the ticket names | The folder is AEA-61's in the collision map; split only for the 500-line cap. Orchestrator: confirm |
| R-6 | Label | The paid run handles real provider keys and commits a record to a public repo (R-42) | AC-15 proves no value reaches the record or output. Recommendation: keep without `risk::security` (no product code; the redaction it relies on is AEA-04's). If `code-review-agent` disagrees, the orchestrator adds the label and AC-15's two tests become frozen tests |
| R-7 | Spec wording | AC-9/AC-14 say "after `redact(text, LOG)`", which yields `""` | PD-1 (TRACE + scrub); the orchestrator posts one issue comment with PD-1, PD-6, PD-7 and PD-13 |
| R-8 | Audit hook is permanent | `sys.addaudithook` cannot be removed | One hook per process, inactive outside `audit_opened()`, returns at once when inactive, never raises |
| R-9 | Disk / time | One index build per paid run (~1 min with the cached model) and six app starts; part B's journeys start nine apps | Hardlinked venv; temp folders removed per case; `df -h /home` before the paid run |
| R-10 | Encodings | Raw model outputs (report model names, tool argument names, the danger label) belong to AEA-35/27/28/37; this plan fixes their content, AEA-51's merged drivers fix their encoding | B0 step 2; a mismatch is reported, not guessed |
| R-11 | Request to AEA-57 (follow-up, not blocking) | `LogTap.structured(kind)` cannot see `signal` records, because `emit_signal` logs them with `extra={"signal": …}` while LogTap reads `meridian_record`. Any journey asserting on signals through LogTap passes vacuously | AEA-61 works around it in owned code (`SignalTap`). Orchestrator: open a follow-up on AEA-57 to read `record.__dict__["signal"]` too |
| R-12 | Collision (shared context files) | `.claude/reference/area-map.md` row `3+` (also edited by 51, 52, 55, 57–60, 62), `.claude/state/icm-progress.md` (append-style rows; AEA-02b hit a conflict there) and `docs/design/code-design.md` §9 | Append-only edits to one cell, one new row and one line; resolve a merge conflict by keeping both sides |
| R-13 | Workflow | If the orchestrator merges part A before AEA-51, the issue stays open and the ledger row must not read `merged` for the whole ticket | Orchestrator: record "part A merged; B/C blocked-on AEA-51" |
| R-14 | Resolved (refresh 6) | AEA-21b merged at `9b3824e` and AEA-40-F1 at `47da752`, so AEA-51 pass 2 was able to complete | — |
| R-15 | Behaviour note (parts B, C) | AEA-51 finding F-1: `open_tasks` is not advanced on card and code turns, so a resumed task re-runs its specialist on later turns. A live model may call tools again on WP-2 T4 or WP-4F T5 | The checks already allow it: PD-7 needs at least one INV-204411 read after verification; WP-4F needs exactly one `moved` action, and a second `find_windows` writes none. A second `move_visit` attempt in a live run is a finding for AEA-39/AEA-51, never a weakened check |
| R-16 | Scripted WP-4F differs from AEA-51's driver | AEA-51's `wp4f` computes its own customer and moves by picking a slot-card option; the dev script seeds MHC-10001 and moves by text, to slot 56 | B1 follows the dev script; B0 step 3 proves the slot facts first |

---

## 9. Readiness

**READY.** No product decision is open, and every engineering choice is made above (PD-1…PD-15).

| Part | State |
|---|---|
| A | Buildable on `main` `dffedf7` now; imports only merged code (AEA-06, 10, 17, 18, 23, 26, 33, 43, 50, 57) |
| B | **Blocked-on AEA-51** (merge; pass 2 is complete on its branch at `fdcc332` after the J-9 send-back) |
| C | **Blocked-on AEA-51** (merge), plus `gate::paid` (D-15 spend statement) |

## Gates

`gate::paid` before every paid run: Innocent's go with the day's spend so far (`LIVE_SMOKE_SPENT_TODAY_USD`, sign-off
D-15), and the provider keys in the environment. The free tests and the four journeys run at every merge; the paid
command never does. No deploy (AEA-56), no E-run, no repeats beyond one.

## Deviations

Recorded by the implementer, parts A and B (2026-10-22, branch `aea-61-aea-61-live-smoke`).

1. **`staff_guidance` lookups are not customer retrievals (A5).** When a case opens, `services/handoff.py` writes a
   `lookup_log` row with `tool = "staff_guidance"` and `passage_ids = ["internal/agent_discretion_notes.md#N"]` (staff-only
   guidance for the brief, never shown to the customer). The plan's generic check "passage from a non-current file" failed
   WP-2 and WP-4 on it in the scripted run. `smoke_checks.py` now defines `STAFF_GUIDANCE_TOOL = "staff_guidance"` and skips
   those rows in the passage-file, warranty account-read, private-before-verified and DANGER "lookup first" checks. No
   other check was loosened; the same rows would have failed the paid run.
2. **`test_live_smoke.py` imports the record module, not `tested_revision` (A7).** pytest collects any imported name that
   starts with `test`, so `from ...record import tested_revision` became a skipped phantom test (11 skipped, not 10). The
   file uses `from tests.journeys.support import record as journey_record`.
3. **Untracked part A files were found in the worktree at start** (written by an earlier, interrupted dispatch). They were
   reviewed line by line against A1 to A7 and adopted; `test_smoke_guards.py`, `scripted_cases.py` and the journey files
   were written in this dispatch.
4. **Context rows written once.** Parts A and B landed in one dispatch, so A8 and B4 were folded into one docs commit (as
   refresh 7 allowed), with the B4 wording.
