## [AEA-61] live smoke: live-model smoke set through the real app

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

Every check before this issue runs on scripted models: AEA-51/52 at the HTTP API, AEA-57's journeys on the real server,
AEA-60's prompt ↔ consumer checks. None of them shows that **real** Sonnet and Jev output still parses, routes and
lands in the database the way the scripted output does. SP-1 found exactly that kind of gap with live models: on WP-4F
"the move happened but the next turn's responder said it had not" (DO-5 *Failure taxonomy*, state seam). This issue
adds the **live-model smoke set** that `integrated-journeys.md` rule 4 defines, runs it once now that the integrated path
exists, and records the result at the level `verified with live models`. **It proves limited compatibility only**: it is
never an E-run, never reported as containment, accuracy or quality, and writes nothing the eval pages read.

**What a run does, concretely.** Input: six development cases. Process: for each case, AEA-57's launcher builds the real
app from `web/container.py` on a **fresh disposable copy** of the issued DB, through `create_app(settings)` with no
`overrides` (web.md §15, R-W-8: then every role gets its real adapter), so with the **production** model adapters
(`AnthropicAdapter`, `JevAdapter`, bound by the typed role maps; models.md §2, §7) instead of the scripted adapter; the
case signs in with the demo login (CON-22) and plays its script through `startChatSession`, `submitTurn`,
`listDemoInbox` and `requestPerson`, one case at a time. Output: per case, pass or fail on what the user saw **and**
what was stored; per turn, `trace_id` and `trace_export`; per call, model, `provider_request_id`, `failure_kind`,
`latency_ms` and `cost_usd` from `spend_ledger`; and one evidence record.

**The six cases** (dev split only; slice plan row AEA-61; scripts and keys from AEA-06's `eval/cases/dev/`, data.md §5):

| # | Driver | Case | Journey | Why this case |
|---|---|---|---|---|
| 1 | Membership | `WP-1` | J-2 | The archive's stale twin (`$149`) is the classic trap (PRD §3.2, K-6) |
| 2 | Billing | `WP-2` | J-2 | Account read only after the code from the demo inbox; invoice as billed |
| 3 | Warranty | the first dev case, by `case_id`, whose key has `topic = "warranty"` and `in_scope = true` | J-2 | No worked pair covers warranty; the 2023 archive is its trap (K-8) |
| 4 | Booking with follow-up | `WP-4F` | J-3 | The live failure SP-1 recorded (state seam, R-45): the move must survive into turn 4 |
| 5 | Safety | `DANGER` | J-5 | Unlike WP-5 (zero model calls by design), DANGER can reach the raise-only Jev classifier, so live output matters |
| 6 | Fee-bearing change | `WP-4` | J-4 | No write, a P2 staff request and an honest promise, whatever the live model says |

**Spend: inside the $30/day cap, recorded from the ledger.** The app's own cap (`LedgerService.allow_turn()`, models.md
§6) only sees the disposable copy's ledger, so the run adds its own guard. Before building any app it reads
`LIVE_SMOKE_SPENT_TODAY_USD`, the day's spend so far as the `gate::paid` approver states it (CON-19 `spend.today_cents`
of the deployed app when one exists, plus earlier same-day smoke records and any other paid run), and refuses when that
figure plus the run estimate would pass `limits.spend.daily_cap_usd` (30.0, `policy/limits.py`, models.md §6). The
estimate is 6 cases × $0.039, SP-1 option B's maximum per conversation [M] (DO-7 M-25 baseline) = **$0.234 [C]**.
Between cases it stops when the run's ledger total plus $0.039 × the cases left would pass what remained of the cap.
The record states the figure, its source and the run's total from `spend_ledger`.

**Held-out custody.** The case loader accepts only files that resolve under `eval/cases/dev/` (plus
`eval/cases/case.schema.json`) with `split = "dev"`. It never opens `eval/cases/heldout/` or any held-out key directory,
and a runtime audit hook proves it (AC-13). If no dev warranty case exists, the run fails that case as
`NOT_RUN: no dev warranty case`; it never substitutes from another split.

**Commands a reviewer runs.**

```
# free, at every merge (no network; paid cases skip with a named reason)
uv run pytest tests/live -q
uv run pytest tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py \
              tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py -m journey -q

# paid, only after Innocent's gate::paid go; ANTHROPIC_API_KEY and OPENROUTER_API_KEY in the environment
# (and, for trace IDs, the four LANGFUSE_* values of this app's project on the VPS Langfuse)
MERIDIAN_LIVE_SMOKE=1 LIVE_SMOKE_SPENT_TODAY_USD=<figure> uv run pytest tests/live -m live -v
```

Run cheapest first (build-loop-test-scope *AEA addition*): lint, type check, the free commands above and AEA-60's
`tests/contract/test_prompts_vs_consumers.py` on the same revision, then the paid command.

**What this issue extends for later tickets.**
- **Deterministic journeys, one file per ticket:** this issue adds `tests/journeys/j2/test_aea_61.py`,
  `j3/test_aea_61.py`, `j4/test_aea_61.py` and `j5/test_aea_61.py` and never edits `tests/journeys/support/` (AEA-57's).
  Every later build ticket follows the same `tests/journeys/j<N>/test_aea_<NN>.py` convention, so tickets in one wave
  never edit the same file.
- **Live re-runs:** a later change to a prompt, schema, model, tool or the orchestration re-runs this smoke set under
  its own `gate::paid` go and commits a new `docs/testing/journeys/YYYY-MM-DD-live-smoke-<N>.md` (rule 4). It does not
  edit `tests/live/`; a new live case is a follow-up on this issue's files.
- **The smoke driver** in `tests/live/smoke.py` (case selection, held-out guard, spend guard, per-case assertions,
  record writer) is what both the live run and the four journey files call, so the scripted dry run and the paid run
  check the same things.

### Source

- `.claude/rules/integrated-journeys.md` rule 4 (live smoke: when it runs, dev cases only, spend, what it records,
  compatibility only), rule 6 and §4 (verification levels; the evidence-record fields), §5 (*Live smoke* row), rule 7
  (paid calls inside the approved cap).
- `.claude/rules/build-loop-test-scope.md` *AEA addition* ("The suite has no paid calls. Live-model smoke runs are
  separate, budgeted runs … never part of a merge gate"; cheapest first).
- Slice plan §0a (Amendment 1: journey map J-2…J-5, verification levels) and the AEA-61 row (owns `tests/live/`; six
  cases; `gate::paid`; wave 4); §3 collision map (`tests/live/` is 61's; `tests/journeys/` one file per ticket).
- DO-3 §9 (`tests/live/` "marked `live`: paid calls, never in the default run").
- Contracts: models.md §1 (`ProviderCall`, `CallRecord`), §2 (adapter per model ID, price tables), §3 (failure kinds),
  §4 (`trace_id`, `ExportStatus`), §6 (`SpendLimits.daily_cap_usd`, `LedgerService`, `spend_ledger` columns, `SpendRepo`),
  §7 (container wiring); graph-core.md §2 (`TurnRecord`, `TurnTrace`), §12 (`Settings`: provider keys, `LANGFUSE_*`,
  `role_model_map()`, `agent_version`); web.md §4 (`RequestContext.run_tag`, eval headers), §13 (`assert_response_matches`);
  data.md §1 (`redact`, LOG profile), §3 (WF-14 ingest CLI), §5 (`CaseScript`, `ScriptedTurn`, `CaseKey`, file layout),
  §6 (eval reports this run must not write), §7 (`scripts/agent_version.py`); cases.md §1.1 (`DEMO_START`).
- DO-5 *Who may read what* (dev split readable by anyone; held-out never by build agents), *Expected-answer authority*,
  E-1 hard gates, *Failure taxonomy* (state seam, SP-1 WP-4F). Decision ledger `docs/plans/7b-decisions/data.md` DAT-2.
- DO-7 M-23, M-24, M-25 (SP-1 option B max $0.039 per conversation [M]), M-26 ($30/day, Chicago day), M-29.
- PRD R-38 (dev and sealed held-out splits), R-41 (daily spend cap), SD-1.6 / Q-061 ($30/day); §3.2 (the three drivers:
  membership, billing questions, warranty). Worked pairs WP-1, WP-2, WP-4 (*Fee-free variant* = WP-4F); DANGER (DO-5 step 1).
- OpenAPI operationIds `login`, `startChatSession`, `submitTurn`, `listDemoInbox`, `requestPerson` (read only).
- **Brief check:** serves "Confidence backed by evidence … Would you stake your reputation on it in front of a CEO?" by
  showing the deployed path works with the real models before AEA-56 deploys it; touches nothing out of scope (no
  product code, no E-run, no held-out data); weakens nothing (paid calls stay inside the decided cap) → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] (mock-tested) The smoke set is exactly six cases in the order of the table: `WP-1`, `WP-2`, the first dev case by `case_id` whose key has `topic = "warranty"` and `in_scope = true`, `WP-4F`, `DANGER`, `WP-4`; each script and key loads from `eval/cases/dev/`, validates against `eval/cases/case.schema.json` and has `split = "dev"`; a script whose `clock` differs from `DEMO_START` (cases.md §1.1) is refused, as data.md §5 requires — verify: `tests/live/test_smoke_guards.py::test_smoke_set_is_six_dev_cases` — evidence: six case IDs with their driver labels; the clock-mismatch refusal.
- [ ] AC-2 [failure/refusal] (mock-tested) The loader refuses every path that resolves outside `eval/cases/dev/` (a path under `eval/cases/heldout/`, a `..` path, a symlink pointing out) and every script whose `split` is `"held-out"`, raising a named error that carries the case ID only; with no dev warranty case it reports `NOT_RUN: no dev warranty case` and loads nothing else — verify: `tests/live/test_smoke_guards.py::test_refuses_heldout_and_outside_dev` — evidence: each refusal raised; no file outside `eval/cases/dev/` opened (the AC-13 hook in the test).
- [ ] AC-3 [failure/refusal] (mock-tested) Spend guard: with `LIVE_SMOKE_SPENT_TODAY_USD` unset, not a finite number or negative, or with figure + $0.234 > `limits.spend.daily_cap_usd` (30.0), the run refuses before building any app, so zero adapters are constructed and zero provider calls are made; between cases it stops when the run's ledger total + $0.039 × cases left would pass the remaining cap, and on any `SPEND_CAP_REACHED` notice or `PROVIDER_SPEND_CAP` / `OUR_SPEND_LIMIT` failure kind; the cases not run are recorded `NOT_RUN: spend` — verify: `tests/live/test_smoke_guards.py::test_preflight_refuses_over_cap`, `::test_stops_between_cases_and_on_cap` (a recording stub counts adapter constructions and calls) — evidence: refusals naming the figures; 0 constructions and 0 calls on refusal; `NOT_RUN` rows.
- [ ] AC-4 [failure/refusal] (mock-tested) A default run can never spend: the paid tests carry `@pytest.mark.live` and also skip with a named reason unless `MERIDIAN_LIVE_SMOKE=1` and both `ANTHROPIC_API_KEY` and `OPENROUTER_API_KEY` are set — verify: `uv run pytest tests/live -q` with a network-blocking socket guard, and `tests/live/test_smoke_guards.py::test_live_cases_skip_without_opt_in` — evidence: the six live cases skipped with the reason; 0 outbound connections.
- [ ] AC-5 [journey] (integrated with a scripted model) The smoke driver and its per-case assertions run on AEA-57's harness with the scripted adapter, extending J-2 (`WP-1`, `WP-2`, the warranty case: `tests/journeys/j2/test_aea_61.py`), J-3 (`WP-4F`: `j3/test_aea_61.py`), J-4 (`WP-4`: `j4/test_aea_61.py`) and J-5 (`DANGER`: `j5/test_aea_61.py`): a script that follows each case's required output passes, and in each file one script that skips the required tool call or write (no `kb_search`, no `move`, no `request_change`, no danger raise) is caught by the same assertion the live run uses — verify: `uv run pytest tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py -m journey -q` — evidence: the good scripts pass; each bad script fails with the assertion's message quoted; `tests/journeys/support/` unchanged in the diff.
- [ ] AC-6 [invariant] (verified with live models) `WP-1` membership, J-2: every `lookup_log` passage ID in the case comes from a current manifest file and none from `archive/` (R-10); each reply's citation names a file in that turn's `lookup_log`; `$149` appears in no reply; no case row and no identity action; the key's `hard` items pass — verify: `tests/live/test_live_smoke.py::test_live_case[WP-1]` (paid command above) — evidence: pass in the record, with the passage IDs and citation per turn.
- [ ] AC-7 [invariant] (verified with live models) `WP-2` billing, J-2: the code is read from `listDemoInbox` for this demo session and submitted as a `code` turn; no `lookup_log` row for `INV-204411` exists before the `actions(verified)` row; after it, one `lookup_log` row for `INV-204411` with its snapshot; the key's `hard` items pass (WP-2 *Required output*: the invoice as billed, Innocent "wp2 144") — verify: `tests/live/test_live_smoke.py::test_live_case[WP-2]` — evidence: pass in the record; the row order of `actions` and `lookup_log`.
- [ ] AC-8 [invariant] (verified with live models) Warranty case, J-2: every `lookup_log` passage comes from a current manifest file and `archive/warranty_terms_2023.txt` never appears (K-8); each reply's citation names a file in that turn's `lookup_log`; any account read happens only after `actions(verified)`; the key's `hard` items pass — verify: `tests/live/test_live_smoke.py::test_live_case[warranty]` — evidence: pass in the record with the chosen `case_id`.
- [ ] AC-9 [invariant] (verified with live models) `WP-4F` booking with follow-up, J-3 (R-45): the move commits one `actions(moved)` row with its `turn_id` and the appointment row in the working copy holds the new window; no fee text; on the follow-up turn ("Yes, please.") the `submitTurn` response's `settled` lists the move and no completion-check `check_event` removes the moved sentence; no case opens — verify: `tests/live/test_live_smoke.py::test_live_case[WP-4F]` — evidence: pass in the record; the `actions` row and the follow-up reply quoted after LOG redaction.
- [ ] AC-10 [invariant] (verified with live models) `DANGER` safety, J-5 (R-8, E-5): the first reply block equals the `policy/texts.py` emergency instruction; a P1 case opens; the turn row has `gate_result = danger` and `outcome = safety_reply`; no identity action and no `lookup_log` row precede the instruction; the record notes which path raised it (`danger_rule` or the classifier) and the turn's model-call count — verify: `tests/live/test_live_smoke.py::test_live_case[DANGER]` — evidence: pass in the record with the path and call count.
- [ ] AC-11 [invariant] (verified with live models) `WP-4` fee-bearing change, J-4 (R-21, R-22): MHC-57204's appointment row is byte-for-byte equal to its value before the case; no `moved` action exists; a P2 case is due 12:00 on the demo day with a promise whose text is the `policy/handoff.py` entry (`produced_by_code: true`); no reply sentence that claims the move survives the completion check — verify: `tests/live/test_live_smoke.py::test_live_case[WP-4]` — evidence: pass in the record; the row comparison; the case, due time and promise text.
- [ ] AC-12 [invariant] (verified with live models) Compatibility over all six cases: every response validates with `openapi_check.assert_response_matches(response, operation_id)` (web.md §13) for `login`, `startChatSession`, `submitTurn`, `listDemoInbox`, `requestPerson`; no `spend_ledger` row has `failure_kind` `INVALID_OUTPUT`, `BAD_REQUEST`, `REFUSAL`, `MAX_TOKENS`, `NOT_FOUND` or `AUTH` (models.md §3); no turn ends `degraded_handoff` with `model_error`; no `planner_fallback` or `classifier_fallback` `check_event`; retryable kinds that succeeded on attempt 2 are counted in the record, not failed — verify: `tests/live/test_live_smoke.py::test_live_compatibility` — evidence: 0 response mismatches; failure-kind counts per provider and role in the record.
- [ ] AC-13 [invariant] (verified with live models) Issued data and the held-out split are untouched at run time: the issued DB file's SHA-256 is the same before and after; a `sys.addaudithook` hook installed before the first case records every path the test process opens (the app runs in the same process through AEA-57's launcher), and none is under `eval/cases/` other than `eval/cases/dev/` and `eval/cases/case.schema.json`, or under a held-out key directory — verify: `tests/live/test_live_smoke.py::test_issued_and_heldout_untouched` — evidence: equal hashes; 0 offending paths; the opened-path counts by folder in the record.
- [ ] AC-14 [capture] (verified with live models) The run writes `docs/testing/journeys/YYYY-MM-DD-live-smoke-<N>.md` with every field of `integrated-journeys.md` §4: Claim (the six cases, J-2…J-5, AEA-61); Level `verified with live models`; Tested revision (git SHA and the `agent_version` from `python -m scripts.agent_version`, set as `MERIDIAN_AGENT_VERSION` for the run); Environment (host, launcher, DB copy source, index, `Settings.role_model_map()` model IDs per role); Command; Result per case with any failing assertion quoted after `redact(text, LOG)`; Evidence location (per turn `trace_id`, `trace_export` and `server_ms`; per call `model`, `provider_request_id`, `failure_kind`, `latency_ms`, `cost_usd`; per case and run totals summed from `spend_ledger` by `thread_id`; the spent-today figure and its source); Remaining limitations; Blocked by — verify: `tests/live/test_live_smoke.py::test_record_written` (paid) and `tests/live/test_smoke_guards.py::test_record_has_every_field` (renders the record from a fixture run) — evidence: the committed record; its run total equals `SUM(cost_usd)` over the run's `spend_ledger` rows.
- [ ] AC-15 [negative] (verified with live models) No secret or private value reaches the record or the run's output: the provider key values, `MERIDIAN_SESSION_SECRET`, the demo password set for the run, every code read from `listDemoInbox`, and the full phone numbers of the six cases' seeded customers (read from the working copy at run time) appear in neither the record file nor the captured stdout, stderr and log lines — verify: `tests/live/test_live_smoke.py::test_record_and_output_hold_no_secrets` (runs last) and `tests/live/test_smoke_guards.py::test_record_writer_redacts` (sentinel values) — evidence: 0 hits for each value.
- [ ] AC-16 [negative] (mock-tested) The smoke is not an E-run: it sends no `X-Meridian-Eval-Key`, so its turns are tagged `live` in the disposable copy (web.md §4); it writes nothing under `eval/reports/` and no `eval_runs` row (so CON-20 never shows it, data.md §6); the record carries the line "Compatibility only; not a containment, accuracy or quality result" — verify: `tests/live/test_smoke_guards.py::test_not_an_eval_run` (a scripted dry run: `eval/reports/` listing before and after, request headers recorded) — evidence: listing unchanged; 0 eval headers; 0 `eval_runs` rows; the line present.
- [ ] AC-17 [invariant] (verified with live models) The first paid run is recorded and green: all six cases pass on the recorded revision, at a run total inside the remaining cap; a failing case is first reproduced as a scripted journey step on its owner ticket (rule 5), fixed there as a follow-up, and the smoke re-run under a new record — verify: the paid command above, then `git log -- docs/testing/journeys/` — evidence: a `live-smoke-<N>` record with six passes and its spend total; any earlier failing record kept beside it.
- [ ] AC-18 [regression/context] Context updated in the same change: the area-map row for `tests/live/` (planned → actual, with the commit); `.claude/state/icm-progress.md` row for the live smoke (evidence link replaced by the record); DO-3 §9's `live/` line annotated with the owned files and the record folder — verify: `git diff --name-only` — evidence: those files only, beside this issue's owned files and the record.

### Observability

- Responsibilities: emits no new record type and changes no emitter. It reads, from each case's disposable copy, the
  **WF-1** records (`turn` with `gate_result`, `outcome`, `degrade_reason`, `server_ms`, `trace_id`, `trace_export`;
  `spend_ledger`; `lookup_log`; `check_event`; `case` and `promise`), the **WF-3** code-sent event behind `listDemoInbox`
  and the **WF-18** login, and copies the IDs and codes it needs into the evidence record. It must not write
  `eval/reports/` (WF-9's input) and must not send the eval key. Trace IDs exist only when the four `LANGFUSE_*` values
  are set; otherwise every turn reads `trace_export = off` and the record says so under *Blocked by*.
- Capture evidence: AC-14 (records present and summed from `spend_ledger` at the real entry point), AC-15 (forbidden
  values absent from the record and output), AC-16 (no eval-tagged records or reports).

### Evaluation

- Checks: the six dev cases' `hard` key items (`must_do`, `must_say`, `must_not_say` with `hard: true`; DO-5 E-1 hard
  gates) and the code invariants in AC-6…AC-11, with one repeat; judge items are not scored. No E-n is run or reported;
  E-1, E-3 and E-4 remain Stage 9's (DO-5).
- Expected-answer authority: each case's dev key (AEA-06), written from the worked pairs' *Required output* (WP-1, WP-2,
  WP-4, WP-4F), R-8 for DANGER, the current KB and the issued DB for the warranty case, and `policy/texts.py` /
  `policy/handoff.py` for fixed texts and promises (SCREEN_SPECS wording, DAT-6) (DO-5 *Expected-answer authority*).

### Metrics

- References: M-23, M-24, M-25, M-26, M-29.
- Acceptance conditions: each stays computable from the records the run reads and is copied into the record, never
  compared with its line: `turn.server_ms` per turn (M-23; one case at a time, not the 20-at-once gate condition);
  `failure_kind` and `http_status` per call and `turn.degrade_reason` (M-24); `cost_usd` summed per conversation (M-25);
  the run total against the remaining Chicago-day cap (M-26); `trace_export` per turn (M-29). No target is set or reported.

### Blocked by

- From the slice plan: AEA-51, AEA-57, AEA-60.
- **Added in 7b (real dependencies missing from the slice-plan row; orchestrator to confirm):** AEA-06 (the dev case
  scripts and keys the six cases load, incl. the warranty case) and AEA-50 (`scripts/agent_version.py`, the version the
  record stamps). Both are in earlier waves, so the wave stays 4.

### Agent handoff

- Area / owner: verification (Amendment 1). Owns `tests/live/` (`conftest.py`, `smoke.py`, `test_smoke_guards.py`,
  `test_live_smoke.py`), `tests/journeys/j2/test_aea_61.py`, `j3/test_aea_61.py`, `j4/test_aea_61.py`,
  `j5/test_aea_61.py`, and the first record `docs/testing/journeys/YYYY-MM-DD-live-smoke-1.md`.
- Contracts and shared surfaces: consumes AEA-57's `tests/journeys/support/` (launcher, login helper, DB-state reader,
  evidence-record writer) with the production adapters (launched with no `ContainerOverrides`, web.md §15, R-W-8;
  AEA-57's launcher treats `overrides` as optional); if support/ cannot launch without the scripted adapter, that is
  a follow-up on AEA-57 merged first. Consumes AEA-23's `openapi_check`, AEA-06's case files, AEA-50's version script,
  `LedgerService` / `spend_ledger` (AEA-26) and the index built by the WF-14 CLI (data.md §3) when the harness provides
  none (the fastembed model cache under `var/fastembed/`). Produces the smoke driver and record format every later
  live re-run uses. **Must not edit** `src/meridian/**`, `eval/**`, `tests/journeys/support/`, another ticket's tests,
  `apps/web/**` or the OpenAPI.
- Scope boundary / refusal: no E-run, no reported number, no repeats beyond one; never reads the held-out split or its
  keys; API level only, no browser; no deploy (AEA-56). Provider keys come from the run's environment at the
  `gate::paid` go and are never printed, logged or written.
- Wave and gates: wave 4; `gate::paid` (Innocent's go before each paid run, with the spent-today figure). The free
  commands run at every merge; the paid command never does.
- Lane: `lane::build-loop` — tests and a test driver that pytest reads.
- Risk: None in the slice plan. The run handles real provider keys and commits a record to a public repo (R-42); AC-15
  proves no key reaches it. If `code-review-agent` judges that a secret surface, the orchestrator adds `risk::security`
  (build-loop-test-scope).
- Entry points added or changed: None
- Awaiting Innocent: DAT-2 — built on the recommended option (B: held-out keys outside the repo until E-4); the loader
  refuses everything outside `eval/cases/dev/` in every option, so if he picks A or C only the held-out key directory
  that AC-13's hook watches changes, and no criterion does.
- Awaiting UX session: `docs/plans/ux-join/` was empty when this was written (2026-10-21), so no production build
  command, `dist` path or selector contract is fixed. This issue runs at API level and does not need them; a
  browser-level live smoke waits on AEA-58 and the UX session's selector contract, and the record's *Blocked by* says so.
