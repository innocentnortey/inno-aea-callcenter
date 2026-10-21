# Coverage repair: eval group (AEA-24, AEA-06)

Owner of this part: the `eval` repair agent, 2026-10-21. Tickets edited: `docs/plans/tickets/AEA-24.md`,
`docs/plans/tickets/AEA-06.md`. Nothing else was edited.

**What changed, in one paragraph.** AEA-24's old AC-14 proved three workflows (WF-8, WF-9, WF-10) in one criterion, which
the checker cannot accept (one criterion proves one workflow per requirement). It is now one capture criterion per
workflow: AC-17 (WF-8 retrieval, new), AC-14 (WF-9 dev case, rewritten in place), AC-22 (WF-10 load, new), and AC-15
(WF-12 experiment, extended). Each capture criterion also carries that workflow's record, header, status, log-hygiene and
outbound-traffic assertions, so one test file per workflow proves the OBS-/CAP- pairs together. A failure/refusal
criterion per workflow (AC-18 WF-8, AC-23 WF-10, AC-24 WF-12; WF-9 already had AC-5/AC-7) carries the hard-gate,
incomplete-run and tamper pairs. The fixture-level criteria AC-1…AC-11 were reworded to name the workflow they drive.
AEA-24's regression criterion moved from AC-17 to AC-25; AEA-06's from AC-14 to AC-17. No other criterion was renumbered.

## Matrix rows

New rows, in the audit's 7-column format. AC numbers are the final ones after the edits.

| Req | Workflow | Component / contract | Implementing ticket | Integration owner | Acceptance criterion | Evidence |
|---|---|---|---|---|---|---|
| CAP-7 | WF-8 | Retrieval entry `eval/run_retrieval.py` → `eval_run` and `eval_case_result` (top-3 with version labels) | AEA-24 | AEA-24 | AEA-24 AC-17 | `tests/capture/test_cap7_eval_records.py::test_wf8_retrieval_run_records`: report with `run_id`, `agent_version`, harness commit and digest; one result per query; no secret in the log |
| CAP-7 | WF-10 | Load suite: `eval_run` (suite `load`), client-side timings file, every request tagged `load` | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_cap7_eval_records.py::test_wf10_load_run_records`: one timing line per CON-2 call; headers on 100% of requests; no held-out key or secret in the log |
| EV-1 | WF-8 | Retrieval hard gate: an excluded file in a stale-trap query's top 3 | AEA-24 | AEA-24 | AEA-24 AC-18 | `test_retrieval_suite.py::test_excluded_file_fails_hard_gate`: gate failed with the query named |
| EV-1 | WF-9 | Seven hard gates checked by code on every e2e case | AEA-24 | AEA-24 | AEA-24 AC-19 | `test_scoring.py::test_hard_gates_on_every_case`: seven failing cases, one per gate; 0 on the clean case |
| EV-1 | WF-12 | Experiment run applies the e2e hard gates | AEA-24 | AEA-24 | AEA-24 AC-24 | `test_cap8_experiment.py::test_experiment_hard_gates`: gate failed on the seeded breach |
| EV-2 | WF-9 | E-5 slice: danger recall and false alarms, n of N | AEA-24 | AEA-24 | AEA-24 AC-20 | `test_report.py::test_e3_e4_e5_measures`: values equal hand counts |
| EV-3 | WF-9 | E-4 slice: in-scope correct resolution per handled topic, held-out only, not-ready label | AEA-24 | AEA-24 | AEA-24 AC-20 | `test_report.py::test_e3_e4_e5_measures`: seeded low topic labelled not ready |
| EV-4 | WF-9 | E-3/E-4 rates: wrong answers, escalation recall, false escalation | AEA-24 | AEA-24 | AEA-24 AC-20 | `test_report.py::test_e3_e4_e5_measures`: values equal hand counts, gate states shown |
| EV-7 | WF-10 | DB-copy check after every load run | AEA-24 | AEA-24 | AEA-24 AC-23 | `test_load.py::test_db_copy_check_after_load`: run failed naming the seeded double booking (one-slot concurrency test stays AEA-28 AC-6; deploy block is AEA-56's, part-5) |
| EV-9 | WF-12 | Experiment scores the committed dev keys and edits no expected output | AEA-24 | AEA-24 | AEA-24 AC-24 | `test_cap8_experiment.py::test_experiment_edits_no_case_file`: file hashes equal before and after |
| EV-12 | WF-9 | Held-out run: item pass/fail only, stamped `agent_version` | AEA-24 | AEA-24 | AEA-24 AC-21 | `test_report.py::test_failure_examples_redacted_and_heldout_items_only`: held-out results carry only `item`, `index`, `passed` (the "scored once" rule: Decision D-3) |
| EV-14 | WF-12 | Experiment run: code checks for `must_say`/`must_not_say`, judge advisory | AEA-24 | AEA-24 | AEA-24 AC-24 | `test_cap8_experiment.py::test_experiment_scoring_rules`: judge double 0 calls for code items; judge items `passed = None` |
| EV-15 | WF-8 | Harness digest recorded (AC-17) and tamper refusal | AEA-24 | AEA-24 | AEA-24 AC-18 | `test_retrieval_suite.py::test_tamper_refuses_retrieval`: `status == "failed"`, empty `results` |
| EV-15 | WF-10 | Harness digest recorded (AC-22) and tamper refusal | AEA-24 | AEA-24 | AEA-24 AC-23 | `test_load.py::test_tamper_refuses_load`: `status == "failed"`, empty `results` |
| EV-15 | WF-12 | Tamper refusal and `--dry-run` with no network call | AEA-24 | AEA-24 | AEA-24 AC-24 | `test_cap8_experiment.py::test_experiment_tamper_and_dry_run`: refusal; zero network calls |
| EV-16 | WF-10 | Load report: p50/p95/max with min–max across 3 repeats | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: each latency measure carries its min–max |
| EV-16 | WF-12 | Experiment report: each measure with min–max across 3 repeats | AEA-24 | AEA-24 | AEA-24 AC-15 | `test_cap8_experiment.py::test_experiment_record`: min–max present per measure |
| EV-17 | WF-8 | Retrieval report: hit @3 as n of N with run ID, agent version, date; target only in "Target" | AEA-24 | AEA-24 | AEA-24 AC-17 | `test_wf8_retrieval_run_records`: summary validates as OpenAPI `EvalRun` (repeat spread: Decision D-2) |
| EV-19 | WF-9 | First-failure filing; `degraded` and `environment_error` counted apart | AEA-24 | AEA-24 | AEA-24 AC-20 | `test_report.py::test_first_failure_and_categories`: three separate rows, hand counts |
| EV-19 | WF-10 | First-failure filing; notice and `client_timeout`/`environment_error` turns counted apart | AEA-24 | AEA-24 | AEA-24 AC-23 | `test_load.py::test_first_failure_and_degrades_filed_apart`: per-row counts equal hand counts |
| M-7 | WF-9 | Excluded-file citation fails the case and counts in the M-7 measure | AEA-24 | AEA-24 | AEA-24 AC-19 | `test_hard_gates_on_every_case`: M-7 shows 1 of N |
| M-9 | WF-10 | DB-copy check on the load run's working copy | AEA-24 | AEA-24 | AEA-24 AC-23 | `test_db_copy_check_after_load`: finding named; run failed |
| OBS-2 | WF-9 | Each dev case and repeat opens its own thread | AEA-24 | AEA-24 | AEA-24 AC-14 | `test_wf9_dev_case_records`: 3 distinct `thread_id`s |
| OBS-2 | WF-10 | Each scripted load conversation opens its own thread | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: 2 distinct `thread_id`s per repeat |
| OBS-5 | WF-8 | `run_id` on the retrieval report and every query result | AEA-24 | AEA-24 | AEA-24 AC-17 | `test_wf8_retrieval_run_records`: every result carries the run's `run_id` |
| OBS-5 | WF-9 | `run_id` on every case result and in `X-Meridian-Run-Id` with run tag `eval` | AEA-24 | AEA-24 | AEA-24 AC-14 | `test_wf9_dev_case_records`: headers on 100% of requests |
| OBS-5 | WF-10 | `run_id` on every timing line and in `X-Meridian-Run-Id` with run tag `load` | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: headers on 100% of requests |
| OBS-6 | WF-12 | `experiment_id` on the run, its `run_id` and `agent_version` (configuration hash, DAT-22) | AEA-24 | AEA-24 | AEA-24 AC-15 | `test_cap8_experiment.py::test_experiment_record`: `experiment_id == "XP-1"` (the one changed variable: Stage 9 write-up, Decision D-4) |
| OBS-11 | WF-8 | `agent_version` on the retrieval `eval_run` | AEA-24 | AEA-24 | AEA-24 AC-17 | `test_wf8_retrieval_run_records`: equals the `MERIDIAN_AGENT_VERSION` the test sets |
| OBS-11 | WF-9 | `agent_version` from `getLatestEval` on the e2e `eval_run` | AEA-24 | AEA-24 | AEA-24 AC-14 | `test_wf9_dev_case_records`: present |
| OBS-11 | WF-10 | `agent_version` on the load `eval_run` | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: present |
| OBS-12 | WF-8 | `eval_run` and `eval_case_result` records | AEA-24 | AEA-24 | AEA-24 AC-17 | `test_wf8_retrieval_run_records`: records present |
| OBS-12 | WF-9 | `eval_run` and `eval_case_result` records | AEA-24 | AEA-24 | AEA-24 AC-14 | `test_wf9_dev_case_records`: records present |
| OBS-12 | WF-10 | `eval_run` (load) and client-side turn timings | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: report and timings file present |
| OBS-12 | WF-12 | `experiment` as `eval_runs.experiment_id` on its run | AEA-24 | AEA-24 | AEA-24 AC-15 | `test_cap8_experiment.py::test_experiment_record`: report with `experiment_id` and `run_id` |
| OBS-13 | WF-8 | `eval_run.status` within `started/completed/failed/incomplete` | AEA-24 | AEA-24 | AEA-24 AC-17 | `test_wf8_retrieval_run_records`: `completed` (failed and incomplete: AC-18) |
| OBS-13 | WF-9 | `eval_run.status` within the listed values | AEA-24 | AEA-24 | AEA-24 AC-14 | `test_wf9_dev_case_records`: `completed` (failed: AC-5; incomplete: AC-7) |
| OBS-13 | WF-10 | `eval_run.status` within the listed values | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: `completed` (failed and incomplete: AC-23) |
| OBS-13 | WF-12 | `eval_run.status` within the listed values | AEA-24 | AEA-24 | AEA-24 AC-15 | `test_experiment_record`: `completed` (failed and incomplete: AC-24) |
| OBS-21 | WF-8 | Harness run log: allow-listed JSON lines only | AEA-24 | AEA-24 | AEA-24 AC-17 | `test_wf8_retrieval_run_records`: every line on the allow-list; sentinel phrase absent |
| OBS-21 | WF-9 | Harness run log: allow-listed JSON lines only | AEA-24 | AEA-24 | AEA-24 AC-14 | `test_wf9_dev_case_records`: every line on the allow-list; sentinel phrase absent |
| OBS-21 | WF-10 | Harness run log: allow-listed JSON lines only | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: every line on the allow-list; sentinel phrase absent |
| OBS-21 | WF-12 | Harness run log: allow-listed JSON lines only | AEA-24 | AEA-24 | AEA-24 AC-15 | `test_cap8_experiment.py::test_experiment_record`: every line on the allow-list; sentinel phrase absent |
| OBS-24 | WF-8 | Eval key and demo password kept out of the retrieval run's log | AEA-24 | AEA-24 | AEA-24 AC-17 | `test_wf8_retrieval_run_records`: absence asserted per value |
| OBS-24 | WF-9 | Eval key, demo password and inbox code kept out of the e2e run's log | AEA-24 | AEA-24 | AEA-24 AC-14 | `test_wf9_dev_case_records`: absence asserted per value (reports and timings: AC-11) |
| OBS-24 | WF-10 | Eval key, demo password, inbox code kept out of the load log, timings and report | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: absence asserted per value |
| OBS-24 | WF-12 | Eval key, demo password, inbox code kept out of the experiment's log and report | AEA-24 | AEA-24 | AEA-24 AC-15 | `test_cap8_experiment.py::test_experiment_record`: absence asserted per value |
| OBS-25 | WF-9 | Report `dev_failures` redacted; held-out item pass/fail only; logs ids only | AEA-24 | AEA-24 | AEA-24 AC-21 | `test_failure_examples_redacted_and_heldout_items_only`: seeded names, phones, emails, addresses absent |
| OBS-26 | WF-9 | Message text only as redacted dev-failure summaries; never in held-out results or logs | AEA-24 | AEA-24 | AEA-24 AC-21 | `test_failure_examples_redacted_and_heldout_items_only`: verbatim message text absent |
| OBS-29 | WF-8 | Retrieval run opens no network connection | AEA-24 | AEA-24 | AEA-24 AC-17 | `test_wf8_retrieval_run_records` with the network-blocking fixture on |
| OBS-29 | WF-9 | Runner talks only to `--base-url` | AEA-24 | AEA-24 | AEA-24 AC-14 | `test_wf9_dev_case_records`: every recorded request to the base-url host; network blocked otherwise |
| OBS-29 | WF-10 | Load runner talks only to `--base-url` | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: every recorded request to the base-url host |
| OBS-29 | WF-12 | Experiment run talks only to `--base-url` | AEA-24 | AEA-24 | AEA-24 AC-15 | `test_cap8_experiment.py::test_experiment_record`: every recorded request to the base-url host |
| OBS-38 | WF-8 | Retrieval run with a missing query is `incomplete`, unreported | AEA-24 | AEA-24 | AEA-24 AC-18 | `test_retrieval_suite.py::test_incomplete_retrieval_run_not_reported`: no hit @3 in the summary |
| OBS-38 | WF-10 | Load run with an unfinished conversation is `incomplete`, unreported | AEA-24 | AEA-24 | AEA-24 AC-23 | `test_load.py::test_incomplete_load_run_not_reported`: no latency measure |
| OBS-38 | WF-12 | Experiment run with a missing case is `incomplete`, unreported | AEA-24 | AEA-24 | AEA-24 AC-24 | `test_cap8_experiment.py::test_incomplete_experiment_not_reported`: no XP-1 measure |
| R-36 | WF-10 | Load run's log, timings and report carry no code, password or eval key | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: absence asserted per value |
| R-36 | WF-12 | Experiment run's log and report carry no code, password or eval key | AEA-24 | AEA-24 | AEA-24 AC-15 | `test_cap8_experiment.py::test_experiment_record`: absence asserted per value |
| R-48 | WF-10 | Load runner signs in once and reuses the session cookie | AEA-24 | AEA-24 | AEA-24 AC-22 | `test_wf10_load_run_records`: one `login` first; cookie on 100% of later requests |
| DC-23 | WF-8 | Retrieval report per run, `summary` valid as OpenAPI `EvalRun` (read by CON-20) | AEA-24 | AEA-24 | AEA-24 AC-17 | `test_wf8_retrieval_run_records`: `eval/reports/<run_id>.json` with top-3 and version labels; summary validates. **Replaces audit line 509** (it cited AC-14, now WF-9 only) |
| EV-10 | WF-9 | Synthetic generator pins model, temperature and seed; re-run changes no file | AEA-06 | AEA-06 | AEA-06 AC-6 | `test_generator_pinned_and_idempotent`: pinned values printed; 0 changed files (in addition to the existing AC-1 row) |
| EV-18 | WF-9 | Flag-promoted case needs flag and trace IDs, `labelled_by = "Innocent"`, `labelled_on` | AEA-06 | AEA-06 | AEA-06 AC-15 | `test_flag_promoted_case_requires_review`: each fixture refused naming the missing field |
| EV-18 | WF-12 | Finding-promoted case needs `FT-n` and trace ID, Innocent's label, dev split only | AEA-06 | AEA-06 | AEA-06 AC-16 | `test_finding_promoted_case_requires_review_and_dev`: each fixture refused |
| R-42 | WF-9 | Eval set and issued dataset tracked in the public repo; no held-out key tracked | AEA-06 | AEA-06 | AEA-06 AC-14 | `test_splits.py::test_eval_set_tracked_in_repo`: 0 untracked case files; counts printed |

## Reworded

AEA-24 (existing rows now resolve because the criterion names the workflow it drives):

| AC | Change | Rows it fixes |
|---|---|---|
| AC-1 | opens **WF-9:**; "a case" → "an e2e case" | R-48 WF-9 |
| AC-2 | **WF-9:**; the fixture case is played through the runner (`run --suite e2e --split dev` on the stub) | M-8, M-10 WF-9 |
| AC-3 | **WF-9:**; scored through the runner | EV-14 WF-9 |
| AC-4 | **WF-9:**; names the e2e report and CON-20's read of `summary` | R-39, EV-16, EV-17, M-1, DC-23 WF-9 |
| AC-5 | **WF-9:** | EV-15 WF-9 |
| AC-6 | **WF-9:**; names `run --suite e2e --split held-out` | R-38 WF-9 |
| AC-7 | **WF-9:** (OBS-38); "an e2e run" | OBS-38, M-5 WF-9 |
| AC-8 | **WF-9:**; the runner runs the DB-copy check after every e2e run; adds `test_runner.py::test_runner_runs_db_check_after_e2e` | EV-7, M-9 WF-9 |
| AC-9 | **WF-10:** | R-38, EV-1, EV-8, EV-9 WF-10 |
| AC-10 | **WF-8:** | R-12, R-38, R-39, EV-5, M-6, M-7 WF-8 |
| AC-11 | **WF-9:** | R-36 WF-9 |
| AC-14 | rewritten: CAP-7 **WF-9** only (one dev case, 3 repeats), adds thread, header, host, status, log allow-list and sentinel assertions; its WF-8 and WF-10 halves moved to AC-17 and AC-22 | CAP-7, M-2, M-4 WF-9 |
| AC-15 | rewritten: CAP-8 **WF-12**, adds repeats spread, status, log allow-list, secrets and host assertions; test names `::test_experiment_record`, `::test_experiment_refused_on_heldout` | CAP-8, R-38, EV-12, M-2 WF-12 |
| AC-17…AC-24 | new (see matrix rows) | — |
| AC-25 | was AC-17 [regression/context]; text unchanged | — |
| *Observability* | capture-evidence line now lists one capture AC per workflow | — |

AEA-06:

| AC | Change | Rows it fixes |
|---|---|---|
| AC-1 | **WF-9** (the case files the end-to-end eval loads) | EV-10 WF-9 |
| AC-4 | **WF-9:** | EV-11 WF-9 |
| AC-6 | **WF-9:**; adds the pinned-generator claim and `::test_generator_pinned_and_idempotent` (part-6 EV-10) | new EV-10 WF-9 row |
| AC-7 | **WF-8** (the queries the retrieval eval loads) | EV-9 WF-8 |
| AC-8 | **WF-8, WF-9:** | EV-9 WF-9 |
| AC-14…AC-16 | new (see matrix rows) | — |
| AC-17 | was AC-14 [regression/context]; text unchanged | — |

**Audit rows citing a regression criterion of these tickets:** none. No row cites AEA-24 AC-17 (old regression) or
AEA-06 AC-14 (old regression). The one existing row whose citation breaks is **DC-23 WF-8 (line 509)**, which cited
AEA-24 AC-14 for WF-8; its replacement row is above.

## Blocked-by edits

None. Every new row has the same implementing ticket and integration owner, so no new edge is needed.

Note for the audit owner: the four R-38 rows (lines 290–293) list AEA-06 as implementing and AEA-24 as integration owner.
The checker passes them only because AEA-24's *Blocked by* prose mentions "AEA-06" ("No ticket edge to AEA-06"). Slice
plan §2 removed that edge on purpose (the harness is built on fixture cases), so I did not add it; adding it would not
raise AEA-24's wave (06 is wave 0, 24 wave 1) but would contradict the slice plan. Either keep the rows as they are, or
set their implementing ticket to AEA-24 (the split, held-out and experiment handling those rows cite is harness code).

## Decisions

Each needs Innocent (or the audit owner where it is a scope cell). None was applied.

- **D-1. EV-6 and M-11 on WF-9 (handoff-brief recall).** DO-5 E-6 and DO-7 M-11 score "each required brief item
  present" from `eval_case_result` brief items, but data.md §5 `CaseKey` has no brief-item list and §6
  `ItemResult.item` has no `brief` kind. The runner could read the brief over HTTP (`switchRole` then `getCase`, both
  in the OpenAPI). Options: **A** amend data.md §5/§6 (a `brief_items` list on `CaseKey`, a `brief` item kind) and give
  AEA-24 an AC that reads the brief and scores it; **B** no contract change: AEA-06's `FORMAT.md` puts brief items in
  `must_do` with a source prefix, and AEA-24 scores those against the `getCase` brief; **C** leave E-6 to the Stage 9 run
  by hand. *Recommended: A* (DO-5 and DO-7 already name brief items as their own records). **Decision needed:** how
  are brief items stored and scored: A, B or C?
- **D-2. EV-16 (and the "repeat spread" in EV-17) on WF-8.** Retrieval over a fixed index is deterministic, so three
  repeats always give min = max, and `python -m eval.run_retrieval` has no `--repeats` flag in data.md §6. Options:
  **A** scope fix: EV-16 excludes WF-8 ("deterministic suite; spread is zero by construction"); **B** add `--repeats`
  to the retrieval command (contract change). *Recommended: A.* **Decision needed:** exclude WF-8 from EV-16, or add
  repeats to the retrieval command?
- **D-3. EV-12 "held-out scored once" on WF-9.** AC-21 covers "scored only" (item pass/fail, no text to fix from) and
  the stamped `agent_version`; nothing links a report to the sealed split it used, so the harness cannot refuse a second
  held-out run. Options: **A** add `heldout_key_sha256` to `EvalRunRecord` (data.md §6) and an AEA-24 AC refusing a
  second `completed` held-out run on the same hash; **B** keep "once" as a Stage 9 process rule. *Recommended: A* (one
  field; makes the rule enforceable). **Decision needed:** enforce "once" in the harness (A) or by process (B)?
- **D-4. EV-13 on WF-12 (and OBS-6's "one changed variable").** Part-6 proposes the harness refuse `--experiment XP-n`
  unless `docs/testing/experiments/XP-n.md` names one `FT-n`, one changed variable and a baseline `run_id`, and print
  before-and-after. That file's format is not defined anywhere, and the ticket body puts the write-up in Stage 9.
  Options: **A** a Stage 9 `lane::human` ticket for EV-13 (and the OBS-6 variable); **B** add the gate to AEA-24 with
  a format defined first. *Recommended: A.* **Decision needed:** EV-13 by a Stage 9 ticket or by a harness gate?
- **D-5. EV-10 on WF-8 (retrieval query provenance).** EV-10 says every case file records `case_id`, `provenance`,
  `labelled_by`, `labelled_on` and more; data.md §5 `RetrievalQuery` has only `query_id`, `query`, `expected_file`,
  `expect_below_floor`, `trap`, `source`, `synthetic`. Options: **A** amend `RetrievalQuery` with `provenance`,
  `labelled_by`, `labelled_on` (and `synthetic_assumption`, `varied_dimension` for synthetic queries), then an AEA-06
  AC; **B** scope fix: EV-10's field list applies to case scripts, and WF-8's queries are held to their own model.
  *Recommended: A* (additive; AEA-06 writes these values anyway). **Decision needed:** amend `RetrievalQuery` (A) or
  narrow EV-10 for WF-8 (B)?
- **D-6. Part-6's `cases_digest` per run (EV-9, all four eval workflows).** It would add a field to `EvalRunRecord`
  (data.md §6, signed). Not applied; WF-12's EV-9 row instead uses AC-24's before-and-after file-hash test, and the WF-8,
  WF-9, WF-10 EV-9 rows already exist. **Decision needed:** add `cases_digest` to the run record, yes or no?
- **D-7. Stage 9 ticket (already on the list).** R-43 WF-9 (the committed held-out report and the README number) and
  NFR-4 WF-10 (the deployed 20-conversation load run) are Stage 9 runs, which the slice plan keeps out of the ticket
  set. AEA-24 AC-9/AC-22 prove the load harness on a stub only.

## Not fixed

| Pair | Reason |
|---|---|
| EV-6 WF-9, M-11 WF-9 | Decision D-1 (contract has no slot for brief items) |
| EV-16 WF-8 | Decision D-2 |
| EV-13 WF-12 | Decision D-4 |
| EV-10 WF-8 | Decision D-5 |
| R-43 WF-9, NFR-4 WF-10 | Decision D-7 (Stage 9) |
| M-12, M-14…M-21, M-25, M-26 on WF-9; M-21, M-23…M-26 on WF-10; M-26 on WF-12 | Part-7 proposes AEA-51 (app-side records tagged `eval`/`load`); not my tickets. Part-7 also proposes adding AEA-24 to AEA-51's *Blocked by*; whoever owns AEA-51 should confirm it does not raise AEA-51's wave |
| R-12 WF-8 on the built index | Part-1 proposes an AEA-50 deploy AC; not my ticket. AEA-24 AC-17 uses a `SearchesPassages` double |

**Caveats, so nobody over-reads the coverage.**

- AEA-06's reworded criteria (AC-1, AC-4, AC-6, AC-7, AC-8, AC-14…AC-16) check the case files WF-8, WF-9 and WF-12
  load. They do not run the harness: AEA-06 has no entry point, and slice plan §2 removed the AEA-06 → AEA-24 edge. The
  files first meet the real runner in the Stage 9 E-runs.
- AEA-24 AC-17 takes WF-8's `agent_version` from `MERIDIAN_AGENT_VERSION`. data.md §6 says `agent_version` comes from
  `getLatestEval`, which only the HTTP suites call. `eval/run_retrieval.py` may import app code, and `Settings.agent_version` is
  the value every other stamp reads (stage7/graph-core.md `Settings.agent_version`; data.md §9 item 1b). This is an engineering reading, not a product
  choice; the planner should confirm it.
- EV-12 WF-9 (AC-21) is partial until D-3 is decided; OBS-6 WF-12 (AC-15) is partial until D-4 is decided.
