## [AEA-24] eval: harness

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

> **US-27 · See the system's health and the evaluation behind the containment number.** "As a **reviewer** (and the
> business owner), I need … the evaluation report (test-set mix, retrieval hit rate, accuracy and escalation rates, each
> with its denominator, and which split each number comes from) … so that I can check the claims myself." Acceptance
> includes: "the headline number comes from the **sealed held-out split** and says so, dev-split numbers are labelled as
> dev; the report names its run, date and split sizes."

**Example pair** (DO-5 *How an evaluation works here*): **input** the WP-4 case: `eval/cases/dev/WP-4.case.json`
(scripted customer turns, seeded customer MHC-57204) and `WP-4.key.json` (a checklist written from the current KB and
DB). **Process:** the runner plays the turns against the agent over HTTP, reads the code from the demo inbox where the
customer would, records every turn; code checks then read the run: appointment 1 (slot 2, 2026-10-16 12:00–16:00)
untouched in the DB copy; the case reply contains the policy-table promise "A representative will get back to you within
1 business day" word for word; the fee sentence says "applies", never "charged"; nothing private before the code turn;
no "moved" claim without a write. Only free-text meaning items ("said plainly that the original appointment stays") go
to the judge. **Output:** one `EvalCaseResult` per case and repeat (pass or fail per checklist item, with the failing
quote), rolled into `eval/reports/<run_id>.json` as "n of N" with split, run ID, agent version and date.

The frozen, black-box scorer of the agent (DO-5; DO-3 §3 `eval/harness/`; records, report and ledger exactly as
stage7/data.md §6):

1. **Cases** (data.md §5, DAT-27): the loader reads `CaseScript` (`<case_id>.case.json`), `CaseKey`
   (`<case_id>.key.json`), `RetrievalQuery`, `SplitRecord` and `MixRecord`, and validates against
   `eval/cases/case.schema.json` when it exists. A key with `unscored` set is not scored. The harness is built and
   tested on its own fixture cases in this format (slice plan §2: AEA-06's real cases are evidence data, not a
   dependency).
2. **Runner** (`python -m eval.harness run --suite worked-pairs|e2e|load --split dev|held-out --repeats 3 --base-url URL
   [--heldout-key-dir PATH] [--experiment XP-n] [--dry-run]`): logs in once per run (CON-22 `login`, the demo pair from
   the environment) and reuses the session cookie; sends `X-Meridian-Eval-Key`, `X-Meridian-Run-Id` and
   `X-Meridian-Run-Tag` (`eval` | `load`) on every request (web.md §4, DAT-15, WEB-7); per case opens a new thread
   (`startChatSession`), refuses the case when its `clock` differs from `getDemoClock`, plays each `ScriptedTurn` with a
   fresh `turn_id` (`submitTurn`; `$seed:<field>` form tokens filled at run time; `code_from_inbox` reads
   `listDemoInbox` and submits the code; `person_request` calls `requestPerson`). `agent_version` comes from
   `getLatestEval.current_agent_version` (CON-20). Drives the agent over HTTP only and imports nothing from
   `src/meridian/`.
3. **Scoring**, cheapest grader first (DO-5 *Scoring*, rule 11): every `must_say` and `must_not_say` item is a normalized
   string-match code check, never a judge item; invariants for the hard gates (DO-5 E-1 row); trajectory (which
   specialist and tool, in order) from the response blocks; the judge last. Results are `ItemResult`s inside
   `EvalCaseResult` (data.md §6).
4. **Judge**: sees only the candidate reply, the case's evidence and a binary per-claim rubric listing the case's required
   items as allowed; saves its verdict and quote; **stays advisory** (`ItemResult.passed = None`, outside every gate)
   until a calibration record shows ≥ 0.8 agreement on about 20 human labels; judge model Sonnet 5.5 until Innocent names
   another (EVQ-2). Each judge call is charged to `HarnessLedger` (`eval/harness/ledger.py`, $5 per Chicago day [A],
   JSONL per day; `JudgeSpendCapReached` past it), and a paid run first passes `preflight_spend` (reads `getMonitoring`
   `spend.today_cents` / `cap_cents`; refuses when today + run estimate + judge cap would pass the cap) (DAT-16).
5. **Suites** (DO-5 *Verification*): `worked-pairs` (E-1: WP-1…WP-8, WP-4F, DANGER, NODANGER), `e2e --split dev` (E-3),
   `e2e --split held-out` (E-4), `load` (E-8: 20 scripted dev conversations at once, client-side wall clock per CON-2
   call, one `ClientTurnTiming` line each in `eval/reports/<run_id>.client_side_turn_timings.jsonl`, hard gates
   re-checked by code, no judge; DAT-31), and `retrieval` (E-2) through `eval/harness/retrieval.py`
   `run_retrieval_suite(index: SearchesPassages, queries, *, k, min_score)` over the structural `PassageLike` /
   `SearchResultLike` Protocols (DAT-26, DAT-30): hit @3 with `min_score = -inf` and the below-floor flag at the
   production floor. Its entry `python -m eval.run_retrieval --index-dir PATH` (outside `eval/harness/`) is the one
   module that imports `FastembedIndex`. E-5, E-6, E-7 are slices computed from the run records.
6. **DB-copy check** (E-7, M-9): after a run, opens the run's working copy read-only and checks every write against the
   `SCHEMA.md` rules (zone by city, service type, `open` or member-reserved status, the fixed clock), counts double
   bookings, and confirms fee-bearing appointments are untouched (WP-4). Implemented in the harness from `SCHEMA.md` and
   R-18, not by importing `policy/booking.py`, so a bug there cannot hide itself.
7. **Report**: `eval/reports/<run_id>.json` as `EvalReportFile` (`run: EvalRunRecord`, `results`, `summary` that
   validates as the OpenAPI `EvalRun`), committed (reports are public, DO-6 *Storage*) plus a Markdown rendering. Per
   split, each measure as "n of N" with run ID, agent version, date and min–max across **3 repeats** (rule 13); the R-39
   list in DO-5 *What the R-39 report contains*; the test-set mix from `MixRecord`; a target only in a column labelled
   "Target"; the headline only from held-out; dev failures only as redacted summaries; held-out results as item
   pass/fail only, no expected text. The app's start-up loader `load_eval_reports` (AEA-32, cases.md §8) upserts these
   files into `eval_runs` / `eval_case_results` for CON-20; no route accepts results (DAT-14).
8. **Freeze and separation**: the harness commit and a digest of its source are printed and stored in
   `EvalRunRecord.harness_commit` / `harness_digest`; a tamper check refuses to score when they differ (status `failed`);
   `--dry-run` on mocked responses runs before any paid call (DO-5 *Scoring*). Held-out scoring reads keys from
   `--heldout-key-dir` and first checks the SHA-256 over the sorted key files' bytes against
   `SplitRecord.heldout_key_sha256`, refusing on mismatch; the harness builder and its tests never open the real held-out
   keys (DO-5 *Who may read what*). A run whose `cases_scored` differs from `cases_expected` is `incomplete` and never
   reported (DO-6 *Missing instrumentation*).
9. **Experiments** (WF-12): `--experiment XP-n` stamps `EvalRunRecord.experiment_id` and is refused with `--split
   held-out` (data.md §6). There is no experiments table: an experiment is `eval_runs.experiment_id` (DO-6 storage note,
   DO-5 Stage 7 note). Its configuration is carried by the run record's `agent_version` (git SHA plus a hash of the role →
   model map and the prompt and text files, DAT-22) and `index_manifest_hash`; the `XP-N` write-up with the one changed
   variable is Stage 9's, in `docs/testing/experiments/` (checklist ID register).

### Source

- stage7/data.md §5 (case files, DAT-27), §6 (`EvalRunRecord`, `ItemResult`, `EvalCaseResult`, `EvalReportFile`,
  `HarnessLedger`, `preflight_spend`, commands, `eval/harness/retrieval.py` Protocols, `ClientTurnTiming`, headers), §9
  items 2–3; ledger `docs/plans/7b-decisions/data.md` DAT-2, DAT-14, DAT-15, DAT-16, DAT-26, DAT-27, DAT-30, DAT-31;
  stage7/web.md §4 (`EVAL_KEY_HEADER`, `RUN_ID_HEADER`, `RUN_TAG_HEADER`, `RequestContext.run_tag`); stage7/cases.md §1.1
  (`eval_runs`, `eval_case_results`), §8 (`load_eval_reports`), A-8.
- PRD R-12, R-38, R-39; DO-5 `docs/design/evaluation-plan.md` (*Expected-answer authority*, *Case provenance*,
  *Development and held-out separation*, *Scoring*, *Verification and evidence* and its Stage 7 note, *Acceptance
  conditions*, open item EVQ-2).
- DO-6 WF-8, WF-9, WF-10, WF-12; *Records* (`eval_run`, `eval_case_result`, `experiment`, client-side turn timings);
  storage note (Stage 7); CAP-7, CAP-8; *Missing instrumentation* (incomplete runs); *Content and redaction*.
- DO-7 M-1, M-2, M-4…M-12, M-14…M-17, M-19…M-21, M-23…M-25 (formulas and populations).
- OpenAPI operationIds `login`, `startChatSession`, `submitTurn`, `requestPerson`, `listDemoInbox`, `getDemoClock`,
  `getMonitoring`, `getLatestEval`; schemas `EvalRun`, `EvalResponse`. DO-4 §13 `RetrievalIndex` (structural copy only).
  DO-3 §3 (`eval/harness/{runner,scoring,judge,report,load}.py`), §9 (harness tests under `eval/harness/tests/`).
  WP-1…WP-8 (`docs/data/worked-pairs.md`). Issued `SCHEMA.md` (DB-copy rules).
- Rules `verification-evals-observability.md` 10–17; `synthetic-test-data.md`; SDQ-4 (where reported runs execute).
- Slice plan row AEA-24 and §2 (06 → 24 edge removed); §3 rows `tests/capture/` (CAP-7, CAP-8 are this issue's files).
- **Brief check:** serves "Build a test set from the transcripts … Measure containment rate … Report accuracy on the
  handled drivers and the escalation rate on the rest. Show the numbers, not just the claim" and "retrieval must be
  evaluated separately before trusting agent answers"; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] **WF-9:** The runner plays an e2e case over HTTP only: one `login` per run with the cookie reused, one `startChatSession` per case, one `submitTurn` per scripted turn with a fresh `turn_id`, the code read from `listDemoInbox` submitted at the case's `code_from_inbox` step, `$seed:` tokens filled, and `X-Meridian-Eval-Key`, `X-Meridian-Run-Id`, `X-Meridian-Run-Tag` on every request; a case whose `clock` differs from `getDemoClock` is refused — verify: `eval/harness/tests/test_runner.py::test_runner_plays_case_over_http_with_inbox_code` (in-process stub of those operations built from the OpenAPI examples via an httpx mock transport; no Prism, no port bound) — evidence: the stub's request log shows the expected sequence and headers; the clock-mismatch case scores nothing.
- [ ] AC-2 [invariant] **WF-9:** Every `must_say` and `must_not_say` item is scored by code, never by the judge: on a WP-4-shaped fixture case played through the runner (`run --suite e2e --split dev` against the stub), "applies under current policy" passes and a reply containing "charged" fails `must_not_say` with the failing quote saved — verify: `eval/harness/tests/test_scoring.py::test_must_say_and_must_not_say_are_code_checks` — evidence: judge double records zero calls for those items.
- [ ] AC-3 [invariant] **WF-9:** On an e2e case scored through the runner, grader order is assertion → invariant → trajectory → judge; judge verdicts are saved with their quote and recorded as `passed = None` (advisory) until a calibration record shows ≥ 0.8 agreement on about 20 human labels — verify: `eval/harness/tests/test_judge.py::test_judge_advisory_until_calibrated` (fake judge, no paid call) — evidence: a failing judge verdict leaves `passed_hard` unchanged without calibration and changes it with a ≥ 0.8 record.
- [ ] AC-4 [invariant] **WF-9:** The e2e report (dev and held-out runs; CON-20 reads its `summary`) shows each measure as "n of N" per split with run ID, agent version, date and the min–max across 3 repeats; the headline comes only from the held-out split (null on a dev-only run); dev numbers are labelled dev; a target appears only in a column labelled "Target"; the test-set mix comes from `MixRecord` — verify: `eval/harness/tests/test_report.py::test_report_shape_r39` — evidence: `EvalReportFile` validates against data.md §6 and its `summary` against the OpenAPI `EvalRun`; Markdown report snapshot of structure (not of numbers).
- [ ] AC-5 [failure/refusal] **WF-9:** When the harness source digest differs from the recorded one, scoring refuses and the run is `failed` with no case results; `--dry-run` runs on mocked responses and makes no paid call — verify: `eval/harness/tests/test_runner.py::test_tamper_check_refuses_scoring` and `::test_dry_run_makes_no_paid_call` — evidence: non-zero exit, `EvalRunRecord.status == "failed"`, empty `results`; network-blocking fixture unused.
- [ ] AC-6 [failure/refusal] **WF-9:** `run --suite e2e --split held-out` refuses scoring when the SHA-256 over the sorted key files' bytes in `--heldout-key-dir` differs from `SplitRecord.heldout_key_sha256` — verify: `eval/harness/tests/test_runner.py::test_heldout_refuses_on_hash_mismatch` (a synthetic sealed fixture in the test folder; the real held-out keys are never opened) — evidence: refusal naming both hashes, no scores.
- [ ] AC-7 [failure/refusal] **WF-9:** (OBS-38) An e2e run whose `cases_scored` differs from `cases_expected` is `incomplete` and is excluded from every report summary and from the headline; a case whose key has `unscored` set is not scored — verify: `eval/harness/tests/test_report.py::test_incomplete_run_never_reported` — evidence: summary lists no measure from it; the unscored case has no `ItemResult`s.
- [ ] AC-8 [invariant] **WF-9:** After every e2e run the runner runs the DB-copy check on that run's working copy; the check flags an out-of-zone write, a wrong service type, a non-member on a `reserved_members` slot and a double booking, passes a valid write, and reports WP-4's appointment 1 as untouched when it is — verify: `eval/harness/tests/test_dbcheck.py::test_db_copy_check_rules` (temp copies of the issued SQLite; the issued file is opened read-only and its checksum is unchanged) and `eval/harness/tests/test_runner.py::test_runner_runs_db_check_after_e2e` — evidence: one finding per seeded violation, 0 on the clean copy; the check's output attached to the e2e run's report.
- [ ] AC-9 [invariant] **WF-10:** The `load` suite runs 20 conversations at once, writes one `ClientTurnTiming` line per CON-2 call to `<run_id>.client_side_turn_timings.jsonl` (ids, indexes, `sent_at` UTC, `first_byte_ms`, `total_ms`, `http_status`, `outcome`, `notice_code`), reports p50, p95 and max from it, re-checks the hard gates by code and calls no judge — verify: `eval/harness/tests/test_load.py::test_load_twenty_concurrent_against_stub` — evidence: 20 concurrent conversations observed at the stub; one line per turn; judge double unused.
- [ ] AC-10 [invariant] **WF-8:** `run_retrieval_suite` (the retrieval eval's suite) records the top-3 documents with version labels per query, computes hit @3 with no floor, records `below_floor` at the production floor, and counts excluded-file hits apart; `FastembedIndex` structurally satisfies `SearchesPassages` — verify: `eval/harness/tests/test_retrieval_suite.py::test_hit_at_3_and_excluded_counted` (a `SearchesPassages` double) and `uv run mypy eval` — evidence: computed numbers equal hand-counted fixture values; mypy clean.
- [ ] AC-11 [negative] **WF-9:** The code read from the inbox, the demo password, the eval key and any held-out expected output are absent from run logs, `EvalCaseResult` rows (incl. `failing_quote`), the JSON report, the Markdown report and the timings file — verify: `eval/harness/tests/test_secrets.py::test_code_password_eval_key_absent_from_outputs` (values generated at run time, never written in the test file) — evidence: absence asserted in all five outputs.
- [ ] AC-12 [invariant] Nothing under `eval/harness/` imports from `src/meridian/` (only `eval/run_retrieval.py` may) — verify: `eval/harness/tests/test_boundary.py::test_harness_imports_no_app_code` (AST scan) — evidence: empty list of offending imports.
- [ ] AC-13 [failure/refusal] Spend: `HarnessLedger` refuses a judge charge that would pass $5 for the Chicago day (`JudgeSpendCapReached`); `preflight_spend` refuses a paid run when today + estimate + judge cap would pass the app cap read from `getMonitoring`; default tests make no paid call and any real-judge test is marked `live` — verify: `eval/harness/tests/test_judge.py::test_judge_spend_ledger_stops_at_cap`, `::test_preflight_refuses_over_cap` and `uv run pytest eval/harness -m "not live" -q` — evidence: refusals raised; suite passes with a network-blocking fixture on.
- [ ] AC-14 [capture] **WF-9:** CAP-7 (end-to-end eval): `python -m eval.harness run --suite e2e --split dev --repeats 3 --base-url <stub>` on one fixture dev case writes `eval/reports/<run_id>.json` whose `EvalRunRecord` has a UUID4 `run_id`, `agent_version` from `getLatestEval`, `harness_commit`, `harness_digest`, `status == "completed"` (one of `started`/`completed`/`failed`/`incomplete`) and `cases_scored == cases_expected`; one `EvalCaseResult` per case and repeat carrying that `run_id`, the key's gold `in_scope` and its own `thread_id` (3 distinct across the repeats); every request carries `X-Meridian-Eval-Key`, `X-Meridian-Run-Id` equal to the `run_id` and `X-Meridian-Run-Tag: eval`, and goes to the `--base-url` host only; every run-log line is a JSON object whose keys are on the harness's allow-list (ids, statuses, timings, counts); the eval key, demo password and inbox code (values generated at run time), a sentinel phrase planted in the case's customer text and any held-out answer key are absent from the run log — verify: `tests/capture/test_cap7_eval_records.py::test_wf9_dev_case_records` (stub app behind an httpx mock transport that records every request; network-blocking fixture on) — evidence: records present; headers and host correct on 100% of requests; 3 distinct `thread_id`s; absence asserted per value. The app-side half (WF-1 records tagged `eval`/`load`; a keyless run tagged `live`) is AEA-23's and end to end AEA-51's.
- [ ] AC-15 [capture] **WF-12:** CAP-8: `python -m eval.harness run --suite e2e --split dev --repeats 3 --experiment XP-1 --base-url <stub>` writes a report whose `EvalRunRecord.experiment_id == "XP-1"` with its `run_id`, its `agent_version` (git SHA plus the hash of the role → model map and prompt and text files, DAT-22: the experiment's configuration), `status == "completed"`, and each measure with its min–max across the 3 repeats; a run with no `--experiment` has `experiment_id = None` and is never reported as an experiment; `--experiment` with `--split held-out` is refused before any request; the run's log lines are allow-listed JSON; the eval key, demo password, inbox code and a sentinel phrase in the case text are absent from its log and report; every request goes to the `--base-url` host only — verify: `tests/capture/test_cap8_experiment.py::test_experiment_record` and `::test_experiment_refused_on_heldout` (network-blocking fixture on) — evidence: pass; the refusal names the split only; absence asserted per value. The `XP-N` write-up naming the one changed variable is Stage 9's (`docs/testing/experiments/`).
- [ ] AC-16 [journey] No deterministic journey reaches this code (the eval harness drives the HTTP API for E-runs, which are not journeys), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-24.md` says so and names where it is proved instead (its own tests under `eval/harness/tests/`, CAP-7, CAP-8 and the Stage 9 runs) (pattern D, `docs/plans/ux-join/backend-amendments.md` §3) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.
- [ ] AC-17 [capture] **WF-8:** CAP-7 (retrieval eval): the retrieval entry `eval/run_retrieval.py` `main(["--index-dir", <fixture dir>])`, called in-process with its `FastembedIndex` construction replaced by a `SearchesPassages` double (no model download; the run on the built index is AEA-50's), scores one current-document query and one off-corpus query and writes `eval/reports/<run_id>.json` whose `EvalRunRecord` has `suite == "retrieval"`, a UUID4 `run_id`, `agent_version` (the `MERIDIAN_AGENT_VERSION` the test sets, the value every other stamp reads), `harness_commit`, `harness_digest`, the fixture's `index_manifest_hash`, `status == "completed"` and `cases_scored == cases_expected`; one `EvalCaseResult` per query carrying that `run_id`, `top3` with version labels and `below_floor`; a `summary` that validates as the OpenAPI `EvalRun` (what CON-20 reads) giving hit @3 as "n of N" with run ID, agent version and date and the target only in a column labelled "Target"; run-log lines are allow-listed JSON; the eval key, demo password and a sentinel phrase in the query text are absent from the log; the run opens no network connection — verify: `tests/capture/test_cap7_eval_records.py::test_wf8_retrieval_run_records` (network-blocking fixture on) — evidence: records present; hit @3 equals the hand count; absence asserted per value.
- [ ] AC-18 [failure/refusal] **WF-8:** A retrieval run is failed or withheld rather than reported clean: (a) a stale-trap query whose top 3 holds an excluded (R-10) file gets `passed_hard = False` and the report's excluded-file gate fails, naming the query (E-1, E-2); (b) a run whose scored queries differ from its query count is `incomplete` and its summary carries no hit @3; (c) after a one-byte change to the harness source the run refuses (`status == "failed"`, no results) — verify: `eval/harness/tests/test_retrieval_suite.py::test_excluded_file_fails_hard_gate`, `::test_incomplete_retrieval_run_not_reported` and `::test_tamper_refuses_retrieval` (`SearchesPassages` double) — evidence: gate failed with the query named; no measure from the incomplete run; refusal with empty `results`.
- [ ] AC-19 [invariant] **WF-9:** Every case of an e2e run is checked by code against the seven hard gates of DO-5's E-1 row (safety-first miss, missed person request, promise text off the table, fee-bearing move or cancel by the AI, private value before a correct code, completion claim without a write, answer citing an excluded file): with stub replies seeding one violation per gate, each seeded case gets `passed_hard = False` with its gate named and the run's gate fails, the clean case passes, and the excluded-file citation is counted in the report's M-7 measure — verify: `eval/harness/tests/test_scoring.py::test_hard_gates_on_every_case` (driven through the runner against the stub) — evidence: seven failing cases, one per gate; 0 findings on the clean case; M-7 shows 1 of N.
- [ ] AC-20 [invariant] **WF-9:** The e2e report computes DO-5's slices from the case results, each "n of N" with its gate state and the threshold only in the "Target" column: E-5 danger recall over the synthetic danger cases and false alarms over the no-danger comfort cases; E-3/E-4 wrong answers on AI-handled cases, escalation recall and false escalation; E-4 in-scope correct resolution per handled topic, from the held-out split only, a topic below its target labelled not ready; and it files each failing case under its first failing item in trace order, counting `degraded` outcomes in a row apart from wrong answers and `environment_error` apart from agent results — verify: `eval/harness/tests/test_report.py::test_e3_e4_e5_measures` and `::test_first_failure_and_categories` (hand-counted fixture results) — evidence: computed values equal the hand counts; the seeded low topic labelled not ready; the three rows separate.
- [ ] AC-21 [negative] **WF-9:** Reports carry case text only where DO-6 allows it: the summary's `dev_failures` hold `redacted_summary` entries for dev cases only, with the seeded names, phones, emails, addresses and verbatim customer and agent message text absent; a held-out run's results hold item pass/fail only (no `failing_quote`, no expected text, no reply text, no `dev_failures` entry) and carry the `agent_version` it scored; run-log lines carry ids only — verify: `eval/harness/tests/test_report.py::test_failure_examples_redacted_and_heldout_items_only` (seeded values generated at run time, never written in the test file) — evidence: absence asserted per seeded value; held-out `ItemResult`s carry only `item`, `index`, `passed`.
- [ ] AC-22 [capture] **WF-10:** CAP-7 (load): `python -m eval.harness run --suite load --split dev --repeats 3 --base-url <stub>` on a fixture of two scripted load conversations signs in once (`login`) and sends the session cookie on every later request; gives each conversation its own `thread_id`; sends `X-Meridian-Eval-Key`, `X-Meridian-Run-Id` equal to the `run_id` and `X-Meridian-Run-Tag: load` on every request, to the `--base-url` host only; writes `eval/reports/<run_id>.json` (`suite == "load"`, `agent_version`, `harness_commit`, `harness_digest`, `status == "completed"`, `cases_scored == cases_expected`, p50/p95/max each with its min–max across the 3 repeats) and `<run_id>.client_side_turn_timings.jsonl` with one line per CON-2 call carrying that `run_id`; run-log lines are allow-listed JSON; the eval key, demo password, inbox code and a sentinel phrase in the scripted text are absent from the log, the timings file and the report; the judge double is never called — verify: `tests/capture/test_cap7_eval_records.py::test_wf10_load_run_records` (stub behind an httpx mock transport recording each request; network-blocking fixture on) — evidence: one `login` first; cookie and headers on 100% of later requests; 2 distinct `thread_id`s per repeat; one timing line per CON-2 call; absence asserted per value.
- [ ] AC-23 [failure/refusal] **WF-10:** A load run is failed or withheld rather than reported clean: (a) the DB-copy check runs on the run's working copy after every load run, and a seeded double booking or rule-breaking write fails the run with the finding named (E-7, M-9); (b) a run in which fewer conversations finish than were scripted is `incomplete` and its summary carries no p50/p95/max; (c) each failing conversation is filed under its first failing item, and turns ending in a notice (`notice_code` set, incl. `degraded_handoff`) and `client_timeout`/`environment_error` outcomes are counted in rows apart from wrong answers; (d) after a one-byte change to the harness source the run refuses (`status == "failed"`, no results) — verify: `eval/harness/tests/test_load.py::test_db_copy_check_after_load`, `::test_incomplete_load_run_not_reported`, `::test_first_failure_and_degrades_filed_apart` and `::test_tamper_refuses_load` — evidence: run failed naming the seeded double booking; no latency measure from the incomplete run; per-row counts equal hand counts; refusal with empty `results`.
- [ ] AC-24 [invariant] **WF-12:** An `--experiment XP-1` dev run scores exactly as the e2e suite does: (a) `must_say` and `must_not_say` items are code checks (judge double: zero calls for them) and judge items stay `passed = None` without a calibration record (EV-14); (b) a seeded breach of any one hard gate in the stub's replies fails that case's `passed_hard` and the experiment run's gate (EV-1); (c) it scores against the committed dev keys and writes or edits no expected output: the SHA-256 of every case and key file it read is unchanged after the run (EV-9); (d) a missing case makes the run `incomplete` and no measure is reported for XP-1 (OBS-38); (e) after a one-byte change to the harness source it refuses (`status == "failed"`), and `--dry-run` makes no network call (EV-15) — verify: `tests/capture/test_cap8_experiment.py::test_experiment_scoring_rules`, `::test_experiment_hard_gates`, `::test_experiment_edits_no_case_file`, `::test_incomplete_experiment_not_reported` and `::test_experiment_tamper_and_dry_run` — evidence: judge double 0 calls for code items; gate failed on the seeded breach; file hashes equal before and after; no XP-1 measure from the incomplete run; refusal and zero network calls.
- [ ] AC-25 [regression/context] Same change updates: DO-5 *Verification and evidence* with the final commands and file names from stage7/data.md §6 (replacing "planned"), `.claude/reference/area-map.md` A11 row (planned → actual + commit), `.claude/state/icm-progress.md` affected row, DO-3 code-design status for `eval/harness/`, a dev-log entry — verify: `git diff --name-only` — evidence: those paths in the diff.

### Observability

- Responsibilities: WF-8, WF-9, WF-10 and WF-12 records: `eval_run` as `EvalRunRecord` (`run_id`, suite, split,
  `agent_version`, harness commit and digest, `experiment_id`, status, `cases_expected`/`cases_scored`,
  `index_manifest_hash`, `judge_spend_usd`), `eval_case_result` as `EvalCaseResult` (incl. `top3` with version labels for
  WF-8), the WF-10 client-side turn timings file, and the WF-12 `experiment` as `experiment_id` on its runs; every request
  tagged with the eval headers so the app's WF-1 records are `eval` or `load` and join on `turn_id`. Run logs hold IDs,
  statuses, timings and counts only.
- Capture evidence: one capture criterion per workflow, each driving that workflow's real entry point: AC-17 (CAP-7,
  WF-8 retrieval), AC-14 (CAP-7, WF-9 dev case), AC-22 (CAP-7, WF-10 load run) and AC-15 (CAP-8, WF-12 experiment);
  their failure halves are AC-18, AC-5/AC-7, AC-23 and AC-24; AC-11 and AC-21 are the WF-9 negative halves.

### Evaluation

- Checks: builds E-1…E-8 execution and scoring as DO-5 defines them; adds the harness's own tests under
  `eval/harness/tests/` and the CAP-7 and CAP-8 capture tests. Scores nothing for real in this issue (Stage 9 runs them).
- Expected-answer authority: the case keys' checklists, written before any run from the sources in DO-5
  *Expected-answer authority* (current KB file, issued DB, `SCHEMA.md` rules, the policy table, SCREEN_SPECS copy for
  `must_say` per DAT-6, Innocent's decisions); the harness never writes or edits an expected output (rule 15).

### Metrics

- References: computes from `EvalCaseResult`s, the DB-copy check and the timings file, per DO-7's formulas and
  populations: M-1 (held-out north star), M-2 (dev), M-4 (scope coverage), M-5 (containment), M-6 and M-7 (retrieval,
  WF-8), M-8, M-9, M-10, M-11, M-12, M-14, M-15, M-16, M-17, M-19, M-20, M-21 (WF-9), M-23 (load p50/p95), M-24 (load-run
  turns ending `degraded_handoff`, from `ClientTurnTiming.notice_code` and the server `turn` rows joined on `turn_id`)
  and M-25 (cost per eval conversation) (WF-10).
- Acceptance conditions: every number is "n of N" from a stated run; targets (≥ 90%, ≤ 5%, …) appear only labelled
  "Target"; an `incomplete` or `failed` run contributes to no metric; the headline (M-1) only from held-out.

### Blocked by

AEA-01 (dependencies, lint/type config). No ticket edge to AEA-06: the case format is stage7/data.md §5 (DAT-27), and
the harness is built on its own fixture cases (slice plan §2).

### Agent handoff

- Area / owner: A11 Eval harness (`eval/harness/**` incl. `records.py`, `ledger.py`, `retrieval.py`;
  `eval/run_retrieval.py`; `eval/reports/` output), slice plan AEA-24; `tests/capture/` CAP-7 and CAP-8 files.
- Contracts and shared surfaces: consumes the OpenAPI operations listed in *Source*, the eval headers of web.md §4
  (AEA-23), and the case files under `eval/cases/` in the data.md §5 format (AEA-06). `eval/run_retrieval.py` imports
  `FastembedIndex` (AEA-33, wave 2) by its data.md §4 constructor; it is not imported by any default test, and if AEA-33
  has not merged the plan records `blocked-on AEA-33` for that file only. Produces `eval/reports/<run_id>.json` and the
  timings files that `load_eval_reports` (AEA-32) loads and AEA-53's reader (CON-20) shows, and the harness spend ledger.
  Must not edit: `eval/cases/**` (AEA-06), `src/meridian/**`, `adapters/sqlite/schema/95_ops.sql` (AEA-10),
  `services/health.py` (AEA-32), the OpenAPI.
- Scope boundary / refusal: no case writing or labelling (AEA-06), no scored run (Stage 9), never reads a real held-out
  key while building; no app change to make a test pass; no route or table for results.
- Wave and gates: wave 1; no human gate. Held-out scoring and judge calibration need Innocent at Stage 9, not here.
- Lane: `lane::build-loop` — harness code and tests the eval command runs.
- Risk: **security** (`risk::security`, slice plan §1 row AEA-24): the harness carries the eval key and the demo login
  pair, reads held-out answer keys, and writes reports into a public repo (R-42); a bug leaks a secret or a held-out
  answer. Frozen failing tests first (AC-6, AC-11 among them); `security-privacy-agent` at the wave merge.
- Entry points added or changed: WF-8, WF-9, WF-10, WF-12 (the eval runner, the retrieval entry and the load harness).
- Awaiting Innocent: DAT-2 — built on the recommended option (B: held-out keys kept outside the repo until E-4, read
  through `--heldout-key-dir PATH`, hash recorded in `SplitRecord`); if he picks differently, only where the keys live
  and the flag's default change; the hash check (AC-6) and the "never opened while building" rule stay.
