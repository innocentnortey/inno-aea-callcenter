# Plan — [AEA-61] live smoke: live-model smoke set through the real app

**Status:** planned — READY as a plan; **build blocked-on AEA-51** (the integrated customer path and the test helpers the
scripted journeys import), **AEA-50** (`scripts/agent_version.py`, paid run only), **AEA-60** (the same-revision prompt
check that runs before the paid run). The **paid run** (AC-6…AC-15, AC-17) also waits on **`gate::paid`**: Innocent's go
with the day's spend line (sign-off D-15, "a statement, not a choice").
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/61 (identical to
`docs/plans/tickets/AEA-61.md`) · **Base revision:** `main` `e22aebb` (2026-10-21) · **Wave:** 4 · **Lane:** build-loop ·
**Risk:** none in the slice plan (see §8 R-6 on `risk::security`) · **Gate:** `gate::paid`
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 · **Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** the one the orchestrator creates (suggested `aea-61-live-smoke` at
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-61`), cut from `main` **after AEA-51, AEA-50 and AEA-60 merge**.

No earlier version of this plan existed at this path; this is the first write.

---

## 1. Goal and sources

### Goal (issue *What to build*, quoted in short)

> "This issue adds the **live-model smoke set** that `integrated-journeys.md` rule 4 defines, runs it once now that the
> integrated path exists, and records the result at the level `verified with live models`. **It proves limited
> compatibility only**: it is never an E-run, never reported as containment, accuracy or quality, and writes nothing the
> eval pages read."

**What a run does, concretely (input → process → output).**
Input: six dev cases (`WP-1`, `WP-2`, the first dev warranty case — today `T-CALL-20260723-0276` — `WP-4F`, `DANGER`,
`WP-4`) and `LIVE_SMOKE_SPENT_TODAY_USD=4.10` (say). Process: the spend guard checks `4.10 + 0.234 ≤ 30.00`; then, one
case at a time, a temp folder gets a fresh environment, `create_app(settings)` with **no overrides** starts under uvicorn
on `127.0.0.1:<ephemeral>` (the container binds the real `AnthropicAdapter` and `JevAdapter`), the app's first boot copies
the issued DB, the driver logs in with the run's demo pair, opens a chat, and plays the case script turn by turn
(`submitTurn`; the form turn fills `$seed:name`/`$seed:phone` from the working copy; the code turn reads
`listDemoInbox`). After the last turn it reads `turns`, `spend_ledger`, `lookup_log`, `actions`, `check_events`, `cases`,
`promises` from that copy, runs the case's checks, stops the server and deletes the folder. Output: six pass/fail lines,
per-turn `trace_id`/`trace_export`/`server_ms`, per-call model/`provider_request_id`/`failure_kind`/`latency_ms`/`cost_usd`,
the run total summed from `spend_ledger`, and one record `docs/testing/journeys/<date>-live-smoke-1.md`.

The same driver and the same checks run **free** in four journey files with the scripted model (AEA-51's step scripts on
AEA-57's harness), so a scripted good run passes and a scripted bad run (a skipped tool call or write) is caught by the
assertion the live run uses.

### Context

AEA-57 landed the harness; AEA-51 (wave 3) wires the real graph and proves the customer path with scripted models;
AEA-60 checks rendered prompts against their consumers. None calls a real model. SP-1 found a live-only gap on WP-4F
("the move happened but the next turn's responder said it had not", DO-5 *Failure taxonomy*, state seam). This ticket
is the first and only place real providers run through the app before AEA-56 deploys it. Each paid run is
`gate::paid` and needs Innocent's stated spend so far (D-15), because the app's own cap only sees a throwaway DB.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-61.md` | AC-1…AC-18, owned files, commands, spend rule ($0.039/case, $0.234/run), custody rule |
| Slice plan | `docs/plans/slice-plan.md` §0a (journey map J-2…J-5; levels; "live smoke is AEA-61; each paid run needs Innocent to state the day's spend"), §1 row AEA-61 (wave 4; blockers 51, 57, 60, 06, 50), §3 (`tests/live/` is 61's; `tests/journeys/` one file per ticket per journey; `support/` is 57's) | Ownership, waves, journey ids |
| Sign-off | `docs/plans/stage7-signoff.md` D-15 ("the spend line is still to be set before wave 4 (a statement, not a choice)"), D-14 (DAT-2 = B: held-out keys outside the repo) | Gate before the paid run; held-out key folder the audit hook watches |
| Rules | `.claude/rules/integrated-journeys.md` rule 4 (live smoke), rule 6 + §4 (levels, the nine record fields), §5 (*Live smoke* row), rule 7 (paid calls inside the cap); `build-loop-test-scope.md` + *AEA addition* ("The suite has no paid calls … never part of a merge gate"; cheapest first); `context-maintenance.md` | Commands, record, gates |
| Code design (DO-3) | `docs/design/code-design.md` §9 line `└── live/ … marked live: paid calls, never in the default run` | AC-18 annotation |
| Contracts (DO-4 + addenda, addenda win) | `stage7/models.md` §1–§4, §6, §7 (`spend_ledger` columns, failure kinds, `LedgerService`, adapters bound by role maps); `stage7/graph-core.md` §12 (`Settings`, `role_model_map()`); `stage7/web.md` §4 (eval headers, `run_tag`), §13 (`assert_response_matches`), §15 (`create_app(settings, overrides=None)`, R-W-8); `stage7/data.md` §1 (`redact`, profiles), §5 (`CaseScript`, `ScriptedTurn`, `CaseKey`, layout, "runner refuses on mismatch"), §6 (eval reports this run must not write), §7 (`python -m scripts.agent_version`); `stage7/cases.md` §1.1 (`DEMO_START`); `stage7/graph-nodes.md` §4 (signals `planner_fallback`, `classifier_fallback` are `signal` log records) | §4 copies |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` *Who may read what*, *Expected-answer authority*, E-1 hard gates, *Failure taxonomy* | Dev split only; hard items only; not an E-run |
| Observability (DO-6) | `docs/design/observability-contract.md` WF-1 (turn, spend, lookup, check, case, promise), WF-3 (inbox), WF-18 (login), *Status values*, `signal` record | Reads only; writes nothing new |
| Metrics (DO-7) | M-23 (`turn.server_ms`), M-24 (`failure_kind`, `http_status`, `degrade_reason`), M-25 (cost per conversation, SP-1 B max $0.039 [M]), M-26 ($30/day, Chicago day), M-29 (`trace_export`) | Copied into the record, never compared with a line |
| Case files | `eval/cases/FORMAT.md` §2 (schema validation recipe), §3 (`$seed:` tokens, `code_from_inbox`), §6 (held-out keys at `/home/linuxuser/.meridian-sealed/heldout/`); `eval/cases/models.py`, `eval/cases/checks.py` | Loader and custody |
| Current code | `tests/journeys/support/{env,server,run,client,db,logtap,record,steps,scripted_model}.py`; `src/meridian/{config,web/app,web/middleware,policy/limits,policy/texts,policy/handoff,privacy/redact,retrieval/manifest,adapters/sqlite/repos_cases_state}.py`; schema `00_core.sql`, `20_spend.sql`, `60_cases.sql`, `95_ops.sql`; `ui-contracts.openapi.yaml` (read only) | §4 copies |
| Sibling plans (not on `main`) | `docs/plans/fanout/2026-10-21-build/AEA-51.md` §5 C1, C2, D1, D2 (support modules, step scripts, scenario building blocks), `AEA-50.md` §4.6 (agent version CLI), `AEA-60.md` (test path) | Names in §4.3; re-checked in step S0 |

### Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Six dev cases in table order; warranty = first dev key by `case_id` with `topic=warranty`, `in_scope=true` | ticket table | AC-1 | in-ticket | S2 |
| Loader refuses outside `eval/cases/dev/`, `..`, symlink out, `split=held-out`; error carries case id only | ticket *Held-out custody* | AC-2 | in-ticket | S2 |
| Case `clock` must equal `DEMO_START` | data.md §5 ("runner refuses on mismatch") | AC-1 | in-ticket; a `null` clock is refused too (PD-4) | S2 |
| Schema validation of script and key | data.md §5, FORMAT.md §2 | AC-1 | in-ticket | S2 |
| Spend pre-flight and between-case stop | ticket *Spend*; models.md §6; M-25, M-26 | AC-3 | in-ticket; comparisons in integer micro-dollars (PD-5) | S3 |
| Paid tests skip unless opted in with both keys | build-loop *AEA addition*; ticket | AC-4 | in-ticket | S1, S7 |
| No network in the free run | ticket AC-4 | AC-4 | in-ticket: package-scoped socket guard in `tests/live/conftest.py` (PD-8) | S1 |
| Every response validated against the OpenAPI | web.md §13 | AC-12 | in-ticket (through `JourneyClient.call`) | S4 |
| Per-turn and per-call evidence, run total from `spend_ledger` | rule §4; ticket | AC-14 | in-ticket | S4, S6 |
| Failing assertion quoted "after `redact(text, LOG)`" | ticket AC-14, AC-9 | AC-9, AC-14 | **adjusted (PD-1):** `redact(…, LOG)` returns `""` by contract (data.md §1 "LOG: '' (length only)"), so a quote would be empty. Quotes use the **TRACE** profile (cards, codes, phones (last 2 kept), emails, street addresses, introduced names masked) plus a scrub of every forbidden value; the issue gets a comment proposing the wording | S6 |
| No secret in record or output | R-42 (public repo); ticket | AC-15 | in-ticket | S6, S7 |
| Not an E-run: no eval key, `run_tag=live`, no `eval/reports/` write, no `eval_runs` row, the compatibility line | web.md §4, data.md §6 | AC-16 | in-ticket | S4, S6, S5 |
| `planner_fallback` / `classifier_fallback` | graph-nodes §4 (signal log records); AEA-51 AC-16 (`classifier` check event `fallback`) | AC-12 ("check_event") | **adjusted (PD-6):** counted from both the `signal` log records and `check_events(check_kind='classifier', result='fallback')`, plus `turns.planner_fallback_used = 1` | S5 |
| "One `lookup_log` row for INV-204411" after verification | ticket AC-7 | AC-7 | **interpreted (PD-7):** at least one non-refused row with `INV-204411` in `record_ids` and a non-empty snapshot, in a turn at or after the verified turn; the count goes in the record | S5 |
| Agent version stamped from `python -m scripts.agent_version` | data.md §7 | AC-14 | in-ticket; run with `RAILWAY_GIT_COMMIT_SHA=<HEAD>` in the subprocess env so the version carries the commit (PD-9) | S6 |
| Journey files one per ticket per journey; never edit `support/` | slice plan §3; AEA-57 README | AC-5 | in-ticket | S8 |
| Scripted journey evidence record | integrated-journeys rule 6 | no | **added**: `docs/testing/journeys/<date>-AEA-61.md` via `--journey-record=AEA-61` (same as every sibling) | S9 |
| Context rows | context-maintenance | AC-18 | in-ticket; the ICM row is **added** in the build commit (no live-smoke row exists today) and its evidence replaced by the record in the paid-run commit | S9, S11 |
| AEA-60's prompt check on the same revision before the paid run | ticket *Commands* | — | in-ticket | §7 check P1 |
| Paid run only after Innocent's go with the spend line | D-15; `gate::paid` | AC-17 | **gate** (not a plan decision) | §9 Gates |

### Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (test-only driver; it calls existing operations `login`, `startChatSession`, `submitTurn`, `listDemoInbox`, `requestPerson`) | WF-1, WF-3, WF-18 read only | yes (DO-6) | nothing new is emitted |

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer creates or edits)

| File | Create / modify | Responsibility (one sentence) | Target / hard cap |
|---|---|---|---|
| `tests/live/conftest.py` | create | The package-scoped no-network guard for the free run | ≤ 60 |
| `tests/live/smoke.py` | create | The smoke driver facade: re-exports the public API below and owns `execute()`, the live launcher and the live environment | ≤ 300 / 500 |
| `tests/live/smoke_cases.py` | create | Custody-checked loading of dev scripts and keys, and the six-case selection | ≤ 250 / 500 |
| `tests/live/smoke_spend.py` | create | Spend pre-flight and the between-case stop rule | ≤ 200 / 500 |
| `tests/live/smoke_player.py` | create | Plays one case over HTTP and reads its stored evidence | ≤ 400 / 500 |
| `tests/live/smoke_checks.py` | create | Per-case invariants, hard key items and compatibility checks | ≤ 450 / 500 |
| `tests/live/smoke_record.py` | create | Quote/scrub helpers, record rendering and writing | ≤ 350 / 500 |
| `tests/live/smoke_audit.py` | create | The `sys.addaudithook` path recorder and the offending-path rule | ≤ 120 / 500 |
| `tests/live/scripted_cases.py` | create | Scripted good/bad step tables per case for the journey files and AC-16 | ≤ 450 / 500 |
| `tests/live/test_smoke_guards.py` | create | Free tests AC-1, AC-2, AC-3, AC-4, AC-14 (fixture render), AC-15 (sentinels), AC-16 | ≤ 480 / 500 |
| `tests/live/test_live_smoke.py` | create | The paid tests (`live`): six cases, compatibility, custody, record, secrets | ≤ 300 / 500 |
| `tests/journeys/j2/test_aea_61.py` | create | J-2 scripted: WP-1, WP-2, warranty good; WP-1 without `kb_search` caught | ≤ 200 |
| `tests/journeys/j3/test_aea_61.py` | create | J-3 scripted: WP-4F good; WP-4F without `move` caught | ≤ 120 |
| `tests/journeys/j4/test_aea_61.py` | create | J-4 scripted: WP-4 good; WP-4 without `change_request` caught | ≤ 120 |
| `tests/journeys/j5/test_aea_61.py` | create | J-5 scripted: DANGER good; DANGER without the raise caught | ≤ 120 |
| `docs/testing/journeys/<date>-AEA-61.md` | create (written by the record command) | Scripted-level evidence record | generated |
| `docs/testing/journeys/<date>-live-smoke-1.md` | create (written by the paid run, phase 2) | The first live record | generated |
| `.claude/reference/area-map.md` | modify the last cell of row `3+` only | AC-18 | — |
| `.claude/state/icm-progress.md` | add one *Routes verified against code and tests* row (build), replace its evidence (paid run) | AC-18 | ≤ 400 chars |
| `docs/design/code-design.md` | modify the one `└── live/` line in §9 | AC-18 | — |

`tests/live/__init__.py` exists (AEA-01) and stays unchanged. The ticket lists `conftest.py`, `smoke.py`,
`test_smoke_guards.py`, `test_live_smoke.py`; the six helper modules are inside the owned folder (collision map:
"`tests/live/` | 61") and exist only to keep every file under the 500-line test cap (`code-structure.md`). See §8 R-5.

### 2.2 Shared surfaces read only (never edit)

`src/meridian/**`; `tests/journeys/support/**` (AEA-57; import only); `tests/journeys/{README.md,affected.py,__init__.py}`,
`tests/journeys/j*/__init__.py`, every other `tests/journeys/j*/test_aea_*.py`; `tests/integration/customer_support.py`,
`tests/integration/customer_api.py`, `tests/graph/worked_pair_scenarios.py` (AEA-51; import only); `tests/api/openapi_check.py`
(AEA-23); `tests/fixtures/**`, `tests/fakes/**`, `tests/unit/adapters/test_retrieval_fastembed.py` (import
`cached_model_dir` only); `tests/conftest.py`; `eval/**` (read the dev files and `case.schema.json`; import
`eval.cases.models`, `eval.cases.checks`); `scripts/agent_version.py` (AEA-50; run it, never edit); `pyproject.toml`,
`uv.lock`; `docs/ux/03-structure/ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`; `apps/web/**`, `docs/ux/**`; the briefing,
issued data, `docs/archive/`, `docs/parked/`; `.claude/state/resume.md`.

### 2.3 Owned by other slices (do not touch)

`tests/journeys/support/` (57), `tests/integration/`, `tests/graph/`, `tests/capture/` CAP-1…3 (51), `tests/contract/`
(17, 18, 51, 59, 60), `eval/harness/` (24), `eval/cases/` (06), `scripts/` (50), every `register_*` hunk in
`web/container.py`. A fix a smoke failure needs belongs to the owning ticket as a follow-up (integrated-journeys rule 5),
never here.

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's; one row each)

Module shorthand: **C** `smoke_cases.py`, **$** `smoke_spend.py`, **P** `smoke_player.py`, **K** `smoke_checks.py`,
**R** `smoke_record.py`, **A** `smoke_audit.py`, **S** `smoke.py`, **G** `test_smoke_guards.py`, **L** `test_live_smoke.py`.

| AC | Level | Requirement (short) | How | Verified by → evidence |
|---|---|---|---|---|
| AC-1 | mock-tested | Exactly six dev cases in table order; schema-valid; `split=dev`; clock ≠ `DEMO_START` refused | C `select_smoke_set`, `load_dev_case` | `tests/live/test_smoke_guards.py::test_smoke_set_is_six_dev_cases` → printed six ids with labels; the clock refusal `WP-1: clock_mismatch` |
| AC-2 | mock-tested | Refuse heldout path, `..`, symlink out, `split=held-out`; named error with case id only; no warranty case → `NOT_RUN: no dev warranty case`, nothing else loaded | C `checked_dev_path`, `CaseCustodyError`; A hook | `::test_refuses_heldout_and_outside_dev` → each refusal string; 0 offending opened paths |
| AC-3 | mock-tested | Pre-flight refusals (unset, non-finite, negative, over cap) before any app; between-case stop; stop on cap notice / cap failure kinds; `NOT_RUN: spend` | $ `preflight`, `run_cases`; S `execute(make_launcher=…)` | `::test_preflight_refuses_over_cap`, `::test_stops_between_cases_and_on_cap` → refusal texts; `made == 0, launches == 0`; `NOT_RUN: spend` rows |
| AC-4 | mock-tested | Paid tests marked `live` and skipped unless `MERIDIAN_LIVE_SMOKE=1` and both keys | S `live_skip_reason`; L `pytestmark`; conftest guard | `uv run pytest tests/live -q -rs` (10 skipped, 0 blocked connections) and `::test_live_cases_skip_without_opt_in` |
| AC-5 | **integrated with a scripted model** — the ticket's single `[journey]` criterion | J-2 (WP-1, WP-2, warranty), J-3 (WP-4F), J-4 (WP-4), J-5 (DANGER) scripted good runs pass; one bad script per file caught by the live assertion | four journey files over AEA-51's `open_customer_run` + S `play_case`, K `check_case`; `scripted_cases.py` | `uv run pytest tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py -m journey -q` → good pass; bad tests print the caught message; `git diff --name-only main...HEAD -- tests/journeys/support` empty |
| AC-6 | live | WP-1: passages current only, no `archive/`; each reply's citation in that turn's lookups; no `$149`; no case, no identity; hard items | K `check_membership` | `tests/live/test_live_smoke.py::test_live_case[WP-1]` → pass line with passage ids and citations per turn |
| AC-7 | live | WP-2: code from `listDemoInbox` submitted as a `code` turn; no INV-204411 read before `actions(verified)`; after it a snapshot row; hard items | K `check_billing` | `::test_live_case[WP-2]` → pass; row order in the record |
| AC-8 | live | Warranty: current passages only, never `archive/warranty_terms_2023.txt`; citations in lookups; account read only after verified; hard items | K `check_warranty` | `::test_live_case[warranty]` → pass with the chosen `case_id` |
| AC-9 | live | WP-4F: one `actions(moved)`, appointment 159 on slot 56, no fee text, follow-up `settled` lists the move, no completion trim on it, no case | K `check_follow_up` | `::test_live_case[WP-4F]` → pass; the follow-up reply quoted (PD-1) |
| AC-10 | live | DANGER: first block = emergency line text; P1 case; `gate_result=danger`, `outcome=safety_reply`; no identity/lookup first; path + model-call count recorded | K `check_safety` | `::test_live_case[DANGER]` → pass with path and call count |
| AC-11 | live | WP-4: appointment 1 row byte-equal; no `moved`; P2 case due 12:00 demo day; promise text from `policy/handoff.py`, `produced_by_code`; no surviving "moved" claim | K `check_fee_bearing` | `::test_live_case[WP-4]` → pass; row compare, case, due, promise |
| AC-12 | live | Compatibility over all six: 0 OpenAPI mismatches; no forbidden failure kind; no `degraded_handoff`/`model_error`; no planner/classifier fallback; retried successes counted | K `check_compatibility`, `compat_counts` | `::test_live_compatibility` → 0 mismatches; counts per provider and role in the record |
| AC-13 | live | Issued DB hash unchanged; audit hook: no opened path under `eval/cases/` except `dev/` and the schema, none under the held-out key folder | A `audit_opened`, `offending_paths`; S run | `::test_issued_and_heldout_untouched` → equal hashes; 0 offending; counts by folder in the record |
| AC-14 | live + mock | Record with all nine fields, level, revision + agent version, environment, command, per-case result, evidence (per turn, per call, totals, spent-today figure and source), limitations, blocked-by | R `render_smoke_record`, `write_smoke_record` | `::test_record_written` (paid) and `tests/live/test_smoke_guards.py::test_record_has_every_field` (fixture) → the committed record; run total = `SUM(cost_usd)` |
| AC-15 | live + mock | No key, session secret, demo password, inbox code or seeded full phone in the record or the run output | R `scrub`, `quote`; L capture | `::test_record_and_output_hold_no_secrets` (last) and `test_smoke_guards.py::test_record_writer_redacts` → 0 hits per value |
| AC-16 | mock-tested | Not an E-run: no eval header; `run_tag=live`; `eval/reports/` unchanged; 0 `eval_runs`; the compatibility line in the record | P records request headers; K generic invariants; R constant line | `test_smoke_guards.py::test_not_an_eval_run` → listing unchanged; 0 eval headers; 0 rows; line present |
| AC-17 | live | First paid run recorded and green (all six pass, inside the remaining cap); a failure is reproduced on its owner ticket, not fixed here | phase 2 (§5 S11) | the paid command, then `git log -- docs/testing/journeys/` |
| AC-18 | regression/context | Area map row `3+`, ICM row, DO-3 §9 `live/` line | S9, S11 | `git diff --name-only main...HEAD` → owned files only |

The ticket's **WP-N worked pairs** are WP-1, WP-2, WP-4, WP-4F (plus DANGER and one transcript-derived warranty case);
their tests are `test_live_case[...]` (live) and the four scripted journey files (free). The **single `[journey]`
criterion is AC-5 at level `integrated with a scripted model`.**

### 3.2 Plan decisions (engineering; the reviewer checks them; PD-1, PD-6, PD-7 go to the issue as one comment)

| ID | Decision | Why |
|---|---|---|
| PD-1 | Quotes in failures and the record use `redact(text, RedactionProfile.TRACE).text`, cut to 300 chars, then `scrub(…, forbidden)`; never `LOG` | `LOG` returns `""` by contract (data.md §1); TRACE masks codes, cards, phones, emails, streets, introduced names |
| PD-2 | The live run builds its own environment from AEA-57's `journey_environ(root)` + real keys + built index + agent version + the four `LANGFUSE_*` only when all four are set; never `MERIDIAN_EVAL_KEY` | `journey_environment()` hard-codes placeholder keys and an empty index; web.md §15: no overrides |
| PD-3 | Scripted runs use AEA-51's `open_customer_run` (AEA-57's harness pieces + built index + per-step scripts) | J-2…J-5 need a built index and per-turn model tables; AEA-57's `journey` fixture has neither |
| PD-4 | A case script with `clock = null` is refused as `clock_mismatch` | The smoke assumes the demo start; data.md §5 refuses on mismatch |
| PD-5 | Money comparisons in integer micro-dollars (`round(usd * 1_000_000)`); "would pass" means strictly greater | `29.766 + 0.234` must equal `30.0` exactly (allowed); floats would refuse it |
| PD-6 | "Fallback" = a `signal` record named `planner_fallback`/`classifier_fallback`, a `check_events` row `classifier`/`fallback`, or `turns.planner_fallback_used = 1` | graph-nodes §4 makes them log records; AEA-51 also writes the classifier check event |
| PD-7 | WP-2: ≥ 1 post-verification INV-204411 snapshot row (count recorded), none in an earlier turn | A live model may read the invoice on two turns; that is not an incompatibility |
| PD-8 | The free-run network guard is a **package-scoped** autouse fixture (not session) so it never outlives `tests/live/` | A session-scoped patch of `socket.connect` would leak into every later test in a full-suite run |
| PD-9 | `scripts.agent_version` runs as a subprocess with `RAILWAY_GIT_COMMIT_SHA=<git rev-parse HEAD>` (plus `-dirty` when `src tests eval pyproject.toml uv.lock` are dirty) in its env | Without it the CLI falls back to `"unknown+…"` locally (AEA-50 AC-7); no `BUILD_SHA` file is written into the repo |
| PD-10 | Visible text = every string inside the response blocks except keys `block_id`, `at`, `type`, `speaker`, `card_id`, `passage_id`, `excerpt`, `audience`, `version_date`, `version_label`, `file`, `section`, `option`, `slot_id`; hard `must_say`/`must_not_say` = exact substring after whitespace collapse and `’`→`'` | DAT-6: items are exact phrases; source excerpts are quoted KB text, not the agent's words |
| PD-11 | Hard `must_do` items map by exact text to named invariants (§5 S5 table); an unmapped hard `must_do` text fails the case `unmapped hard must_do item` | Nothing passes silently; judge and soft items are not scored (ticket *Evaluation*) |
| PD-12 | The live record is written by the module fixture even when cases fail | AC-17 keeps failing records beside later ones |

---

## 4. Shared code to use (copied from current code, the addenda, or the sibling plan named)

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
                  ) -> Iterator[RunningServer]: ...    # uvicorn thread, 127.0.0.1:0; refuses ports 4019, 5184
class SocketGuard: blocked: list[tuple[str, int]]
@contextmanager
def socket_guard() -> Iterator[SocketGuard]: ...       # refuses non-loopback connect/connect_ex

# tests/journeys/support/run.py (AEA-57)
@dataclass
class JourneyRun:
    env: JourneyEnv; server: RunningServer; script: JourneyScript; models: Mapping[Role, ScriptedModel]
    clock: StepClock | None; db: DbReader; logs: LogTap; guard: SocketGuard; collector: StepCollector
    strict: bool; nodeid: str; clients: list[JourneyClient] = field(default_factory=list)
    settings / app / container / base_url / demo_username (properties)
    def client(self) -> JourneyClient: ...
    def login(self, client: JourneyClient | None = None) -> LoginResult: ...   # POST /api/login (operation "login")
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
        # appends the response to self.responses, THEN assert_response_matches; a mismatch raises
        # AssertionError(f"{operation_id} -> HTTP {status}: {first line}")
    def close(self) -> None: ...

# tests/journeys/support/db.py (AEA-57)
class DbReader:  # mode=ro, one connection per call
    def rows(self, sql: str, params: Sequence[object] = ()) -> list[dict[str, Any]]: ...
    def one(self, sql: str, params: Sequence[object] = ()) -> dict[str, Any]: ...
    def scalar(self, sql: str, params: Sequence[object] = ()) -> Any: ...
    def count(self, table: str, where: str = "", params: Sequence[object] = ()) -> int: ...
def sha256_file(path: Path) -> str: ...

# tests/journeys/support/logtap.py (AEA-57)
class LogTap(logging.Handler):
    def structured(self, kind: str) -> list[dict[str, object]]: ...   # payloads whose "record" == kind (e.g. "signal")
    def all_text(self) -> str: ...
@contextmanager
def tap_logs() -> Iterator[LogTap]: ...

# tests/journeys/support/scripted_model.py (AEA-57): JourneyScript() (empty script for a live JourneyRun)
# tests/journeys/support/steps.py (AEA-57): StepCollector(); NEED_OWNERS keys used here: "session_service",
#   "turn_service", "run_graph", "identity_service", "case_service", "handoff_service"; OPERATION_OWNERS keys used:
#   "startChatSession", "submitTurn", "listDemoInbox", "requestPerson"
# tests/journeys/support/record.py (AEA-57)
FIELDS: tuple[str, ...] = ("Claim", "Level", "Tested revision", "Environment", "Command", "Result",
                           "Evidence location", "Remaining limitations", "Blocked by")
ISSUED_REL = "docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
@dataclass(frozen=True)
class RecordData: scope: str; values: Mapping[str, str]
def tested_revision(root: Path, agent_version: str) -> str: ...      # "<sha>; agent_version X" or "uncommitted (HEAD sha); …"
def render_record(data: RecordData) -> str: ...                      # "# Journey record: <scope> …" + 9-row table
# tests/journeys/support/plugin.py (AEA-57): COLLECTOR_KEY

# tests/fixtures/sqlite.py (AEA-10): ISSUED_DB (Path of the issued scheduling DB)
# tests/api/openapi_check.py (AEA-23): assert_response_matches(response, operation_id) (used inside JourneyClient.call)
# tests/unit/adapters/test_retrieval_fastembed.py (AEA-33): cached_model_dir() -> Path | None

# src/meridian
from meridian.config import Settings                         # Settings.from_env(environ); role_model_map(); langfuse_complete()
from meridian.adapters.sqlite.migrate import WORKING_DB_NAME
from meridian.adapters.sqlite.repos_cases_state import DEMO_START   # datetime(2026,10,16,10,0,tzinfo=ZoneInfo("America/Chicago"))
from meridian.policy.limits import Limits                    # Limits().spend.daily_cap_usd == 30.0
from meridian.policy.texts import TEXTS, TextId, render      # TextId.EMERGENCY_LINE_LEAD, TextId.PROMISE_UNSTAFFED
from meridian.policy.handoff import promise_for              # promise_for(reason, presence, now, window_start=None) -> Promise
from meridian.domain.handoff import HandoffReason            # .FEE_BEARING_CHANGE
from meridian.domain.common import Promise                   # policy_row, text, due_at, due_label, extra_lines, live_queued
from meridian.privacy.redact import RedactionProfile, redact # redact(text, RedactionProfile.TRACE).text
from meridian.retrieval.manifest import MANIFEST, FileStatus # ManifestSpec.path, .status; FileStatus.CURRENT
from meridian.retrieval.settings import SEARCH_K, MIN_SCORE  # 3, 0.60
from meridian.adapters.retrieval_fastembed import FastembedIndex   # FastembedIndex(index_dir, *, model_cache_dir=None)
    # .search(query, *, k, min_score) -> RetrievalResult(passages: tuple[Passage, ...], below_floor: bool)
    # Passage: passage_id ("<kb path>#<n>"), file, section, version_label, version_date, text, score; .info() -> IndexInfo
from meridian.web.middleware import EVAL_KEY_HEADER, RUN_ID_HEADER, RUN_TAG_HEADER   # "X-Meridian-Eval-Key", "-Run-Id", "-Run-Tag"

# eval (AEA-06)
from eval.cases.models import CaseScript, CaseKey, ScriptedTurn   # pydantic, extra="forbid", frozen
from eval.cases.checks import CASE_ID                              # ^(?:WP-[1-8]|WP-4F|DANGER|NODANGER|T-CALL-\d{8}-\d{4}|S-\d{1,2}|P-\d{1,3})$
# eval/cases/case.schema.json: validate a document of kind K with jsonschema.Draft202012Validator(
#   {"$defs": schema["$defs"], "$ref": f"#/$defs/{K}"}) (FORMAT.md §2); K in {"CaseScript", "CaseKey"}
```

`ProviderFailureKind` values (models.md §3, `domain/common.py`): `timeout connection rate_limited overloaded server
provider_spend_cap our_spend_limit bad_request auth not_found body_error refusal max_tokens invalid_output`.

Tables read (columns copied from `schema/*.sql`):
`turns(turn_id, thread_id, run_tag, run_id, sequence, gate_result, outcome, degrade_reason, planner_fallback_used,
danger_raised, server_ms, model_calls, cost_usd, trace_id, trace_export)`;
`spend_ledger(id, thread_id, turn_id, run_tag, role, provider, model, attempt, latency_ms, cost_usd, status, failure_kind,
http_status, provider_request_id)`; `lookup_log(id, thread_id, turn_id, tool, record_ids JSON, passage_ids JSON,
result_seen)`; `actions(id, thread_id, turn_id, kind, record_id)` (kinds `booked moved cancelled change_request_sent
case_opened followup_saved verified`); `check_events(thread_id, turn_id, check_kind, result, removed)` (kinds `completion
fact brief_fact brief_quote gate classifier brake`; results `pass trimmed fallback fired raised`); `cases(case_ref,
thread_id, turn_id, reason, priority, rule_id, due_at, created_at)`; `promises(case_ref, policy_row, text, due_at,
due_label, extra_lines JSON)`; `conversations(thread_id, run_tag, run_id)`; `eval_runs(run_id)`;
issued `customers(customer_id, name, phone, zip, …)`, `appointments(appointment_id, slot_id, customer_id, status, …)`.

### 4.2 Request and response shapes (OpenAPI, signed; read only)

`POST /api/login` (`login`) `{"username","password"}` · `POST /api/chat/sessions` (`startChatSession`) → 201
`{thread_id, greeting, …}` · `POST /api/chat/sessions/{thread_id}/turns` (`submitTurn`) body `{"turn_id": <uuid4>,
"payload": TextPayload{"kind":"text","text"} | ChoicePayload{"kind":"choice","card_id","option"} |
CodePayload{"kind":"code","card_id","code"(6 digits)} | FormPayload{"kind":"form","card_id","values":{name?, phone?,
customer_id?, invoice_number?, zip_or_city?}}}` → 200 `TurnResponse{thread_id, turn_id, sequence, blocks[], settled,
writes[], controller, notice, last_event_id}`; `settled.actions[]` = `Write{kind, summary, turn_id, at}`;
`settled.identity.status ∈ {not_checked, code_sent, verified, not_verified, locked}`; `notice.code ∈ {RATE_LIMITED,
BOOKING_CAP, SPEND_CAP_REACHED, TURN_TIMEOUT, BUSY, AI_PAUSED}` · `POST /api/chat/sessions/{thread_id}/handoff`
(`requestPerson`) `{"turn_id"}` → `HandoffResponse{result, block, settled}` · `GET /api/demo/inbox` (`listDemoInbox`) →
`{"messages":[InboxMessage{id, at, to_masked, body, code, status ∈ {active, used, expired}, expires_at}]}`.
Blocks used: `locate_prompt{card_id, field_sets}`, `code_prompt{card_id}`, `slot_card{card_id, options[{option}],
days[{date, windows[{slot_id, date, window, window_label}]}]}`, `text{text, sources[SourceChip{passage_id, file, …}]}`,
`source_chip{source: SourceChip}`, `emergency_line{lead_text, number, …}`, `change_request{fee_line,
original_stays_line, promise_text, due_at, extra_lines, produced_by_code: true, …}`, `handoff{…}`, `account_card`,
`appointment`, `confirmation`.

### 4.3 Names from AEA-51's plan (not on `main`; verify in step S0 after AEA-51 merges)

| Name | Where | Used for |
|---|---|---|
| `open_customer_run(request: pytest.FixtureRequest, options: RunOptions = RunOptions(), *, monkeypatch=None) -> ContextManager[CustomerRun]`; `RunOptions(index="built", eval_key=False, trace=None, with_clock=False, deadline_s=None)`; `CustomerRun(JourneyRun)` with `.steps: StepScript`; `StepScript.set_step(default: Mapping[Role, StepEntry], *, by_marker=None)`; `built_index_dir() -> Path \| None`; `fastembed_offline()`; `INDEX_SKIP` | `tests/integration/customer_support.py` (AEA-51 plan §5 C1) | Scripted runs (PD-3); the live index and offline embedder |
| `planner(**choices) -> str`, `classifier(label) -> str`, `NORMAL`, `responder(text) -> str`, `brief(**fields) -> str`, `tool(name, args, call_id="call-1") -> RawToolCall`, `report(model, **fields) -> RawToolCall`, `step(*calls, text="") -> RawToolStep`, `TOOLS: Mapping[str, str]` (`"kb_search"`, `"invoice"`, `"warranty"`, `"find_windows"`, `"move"`, `"change_request"`, …); drivers `wp1`, `wp2`, `wp4`, `wp4f`, `danger`, `warranty` | `tests/graph/worked_pair_scenarios.py` (AEA-51 plan §5 D1, D2) | Encoding of every scripted model output; the reference for argument names and report models |
| `python -m scripts.agent_version` prints the version; honours `RAILWAY_GIT_COMMIT_SHA` | `scripts/agent_version.py` (AEA-50 plan §4.6, data.md §7) | AC-14 |
| `tests/contract/test_prompts_vs_consumers.py` | AEA-60 | Pre-paid-run check P1 |

---

## 5. Steps

Build order: **S0** verify → **S1** conftest + skip rule → **S2** cases → **S3** spend → **A** audit (inside S2 tests) →
**S4** player → **S5** checks → **S6** record → **S7** facade + paid tests → **S8** scripted tables + journeys →
**S9** scripted record + context → commit → **(phase 2, after `gate::paid`) S10** pre-paid checks → **S11** paid run, record,
context. Each step ends with its tests green. The slice **consumes** AEA-57's harness API, AEA-51's test helpers and the
signed OpenAPI; it adds no `src/` code, no Protocol in `src/`, and no new seam (rule `code-design-solid-modularity`).

### S0. Verify the prerequisites (no code)

1. `git log --oneline main | grep -E "Merge AEA-(51|50|60)"` shows all three. If not, stop: `blocked-on AEA-NN`.
2. Open `tests/integration/customer_support.py` and `tests/graph/worked_pair_scenarios.py`; confirm every §4.3 name.
   A renamed helper → use the merged name and list it in the report. A missing capability (no per-step script table,
   no built-index run) → stop, report `blocked-on AEA-51 follow-up`.
3. Read the merged AEA-51 drivers `wp1`, `wp2`, `wp4`, `wp4f`, `danger`, `warranty`: note the exact `TOOLS` keys, each
   tool's argument names, the report model each specialist passes to `report(...)`, the danger label passed to
   `classifier(...)`, and how a passage id is chosen. S8 copies these encodings.
4. `uv run python -m scripts.agent_version` prints one non-empty line.

### S1. `tests/live/conftest.py` and the skip rule

```python
"""tests/live: no network unless the paid run is opted in (AEA-61; integrated-journeys rule 4)."""
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
`live_skip_reason(environ: Mapping[str, str]) -> str | None` lives in `smoke.py` (S7) — exact texts:
1. `environ.get("MERIDIAN_LIVE_SMOKE") != "1"` → `"live smoke not requested: set MERIDIAN_LIVE_SMOKE=1 after Innocent's gate::paid go"`.
2. missing = names among `("ANTHROPIC_API_KEY", "OPENROUTER_API_KEY")` whose value is absent or blank → `f"live smoke needs {', '.join(missing)} in the environment"`.
3. else `None`. *Invariant: names only, never a value.*

### S2. `smoke_cases.py` — custody-checked loading and selection

```python
REPO_ROOT: Final = Path(__file__).resolve().parents[2]
CASES_DIR: Final = REPO_ROOT / "eval" / "cases"
DEV_DIR: Final = CASES_DIR / "dev"
SCHEMA_PATH: Final = CASES_DIR / "case.schema.json"
HELDOUT_SCRIPTS_DIR: Final = CASES_DIR / "heldout"
HELDOUT_KEY_ROOT: Final = Path.home() / ".meridian-sealed"          # FORMAT.md §6 (DAT-2 = B); never opened
CustodyReason = Literal["bad_case_id", "outside_dev", "missing", "not_dev_split", "clock_mismatch",
                        "schema_invalid", "id_mismatch"]
NO_WARRANTY: Final = "NOT_RUN: no dev warranty case"

class CaseCustodyError(Exception):
    def __init__(self, case_id: str, reason: CustodyReason) -> None: ...   # attrs case_id, reason
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
Algorithms (invariant per step):
- `checked_dev_path`: (1) `resolved = path.resolve(strict=False)`; (2) if `resolved.parent != dev_dir.resolve()` →
  `CaseCustodyError(case_id, "outside_dev")` — **before** any `exists`/`open`, so a held-out path is never touched;
  (3) if not `resolved.is_file()` → `"missing"`; return `resolved`. *Invariant: only a regular file directly in the dev
  folder (after following symlinks) is ever opened.*
- `load_dev_case`: (1) `CASE_ID.fullmatch(case_id)` else `"bad_case_id"`; (2) `checked_dev_path` for
  `dev_dir / f"{case_id}.case.json"` and `…key.json`; (3) `json.loads(read_text)`; validate each against `SCHEMA_PATH`
  with the FORMAT.md §2 recipe (`jsonschema.Draft202012Validator`), any error → `"schema_invalid"` (never put the error
  text in the message); (4) `CaseScript.model_validate`, `CaseKey.model_validate`; (5) `script.case_id != case_id or
  key.case_id != case_id` → `"id_mismatch"`; (6) `script.split != "dev"` → `"not_dev_split"`; (7) `script.clock is None
  or script.clock != DEMO_START` → `"clock_mismatch"` (aware datetimes compare instants). Return `(script, key)`.
- `first_warranty_case`: for `path in sorted(dev_dir.glob("*.key.json"))` (name order = `case_id` order): `case_id =
  path.name.removesuffix(".key.json")`; `checked_dev_path(path, case_id, dev_dir=dev_dir)`; `CaseKey.model_validate(json)`;
  first with `topic == "warranty" and in_scope` → return its `case_id`; none → `None`. *Never reads another folder.*
- `select_smoke_set`: walk `SMOKE_TABLE`; for the warranty row use `first_warranty_case`; `None` →
  `NotRunCase(label, journey, None, NO_WARRANTY)`; else `SmokeCase(label, journey, case_id, *load_dev_case(case_id,
  dev_dir=dev_dir))`. Errors propagate (a custody error stops the run).

### S3. `smoke_spend.py` — pre-flight and between-case stop

```python
PER_CASE_ESTIMATE_USD: Final = 0.039                  # SP-1 option B max per conversation [M] (DO-7 M-25)
RUN_ESTIMATE_USD: Final = 0.234                       # 6 × 0.039 [C]; module asserts round(6*0.039, 6) == 0.234
SPENT_ENV: Final = "LIVE_SMOKE_SPENT_TODAY_USD"
SPEND_STOP_KINDS: Final = frozenset({"provider_spend_cap", "our_spend_limit"})
NOT_RUN_SPEND: Final = "NOT_RUN: spend"

class SmokeRefused(RuntimeError): ...                 # message names figures and env names only

def micros(usd: float) -> int: return round(usd * 1_000_000)
def preflight(environ: Mapping[str, str], *, cap_usd: float) -> float: ...
def should_stop(run_total_usd: float, cases_left: int, *, spent_today_usd: float, cap_usd: float) -> bool: ...
```
- `preflight`: (1) `raw = environ.get(SPENT_ENV, "").strip()`; empty → `SmokeRefused(f"refused: {SPENT_ENV} is not set
  (the gate::paid approver states today's spend)")`; (2) `float(raw)` (ValueError) or `not math.isfinite` →
  `SmokeRefused(f"refused: {SPENT_ENV} is not a finite number")`; (3) `< 0` → `SmokeRefused(f"refused: {SPENT_ENV}={raw}
  is negative")`; (4) `micros(figure) + micros(RUN_ESTIMATE_USD) > micros(cap_usd)` → `SmokeRefused(f"refused:
  {SPENT_ENV}={figure:.3f} + estimate {RUN_ESTIMATE_USD:.3f} = {figure + RUN_ESTIMATE_USD:.3f} > daily cap
  {cap_usd:.2f}")`; return `figure`. *Invariant: no app is built before this returns.*
- `should_stop`: `micros(run_total_usd) + micros(PER_CASE_ESTIMATE_USD) * cases_left > micros(cap_usd) -
  micros(spent_today_usd)`.

### S4. `smoke_player.py` — play one case, read its evidence

```python
@dataclass(frozen=True)
class TurnExchange:
    index: int; kind: str; operation_id: str; turn_id: str; status: int; body: Mapping[str, Any]
    @property
    def notice_code(self) -> str | None: ...           # body["notice"]["code"] when present
@dataclass(frozen=True)
class CaseSecrets:                                     # never rendered; repr hides values
    values: tuple[tuple[str, str], ...] = ()           # (label, value): "demo password", "session secret", "inbox code 1",
    def __repr__(self) -> str: return f"CaseSecrets({len(self.values)} values)"   # "seeded phone", "seeded phone digits"
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
    def spend_cap_hit(self) -> bool: ...   # any notice SPEND_CAP_REACHED or any spend row failure_kind in SPEND_STOP_KINDS
    @property
    def cost_usd(self) -> float: ...       # sum(row["cost_usd"] or 0.0 for row in evidence.spend)
BeforeTurn = Callable[[int, ScriptedTurn, Sequence[TurnExchange]], None]
SNAPSHOT_SQL: Final[Mapping[str, str]] = {
    "WP-4": "SELECT * FROM appointments WHERE appointment_id = 1",
    "WP-4F": "SELECT * FROM appointments WHERE appointment_id = 159"}
def play_case(run: JourneyRun, case: SmokeCase, *, before_turn: BeforeTurn | None = None) -> CaseOutcome: ...
def collect_evidence(run: JourneyRun, thread_id: str, case: SmokeCase,
                     before: Mapping[str, tuple[dict[str, Any], ...]]) -> CaseEvidence: ...
```
`play_case` (numbered; each line's invariant in brackets):
1. `signed = run.login()`; `client = signed.client`; secrets += ("demo password", "session secret") from
   `run.env.secret_values()`. A login `AssertionError` → `mismatches` entry, return early. [the real login gate runs]
2. If `case.script.seeded_customer`: `row = run.db.one("SELECT customer_id, name, phone, zip FROM customers WHERE
   customer_id = ?", (id,))`; secrets += ("seeded phone", row["phone"]), ("seeded phone digits", digits of it).
   [phone read at run time, never a literal]
3. `before = {sql_name: tuple(run.db.rows(sql))}` for `SNAPSHOT_SQL.get(case.case_id)` (key = case id).
4. `startChatSession`: `client.call("POST", "/api/chat/sessions", operation_id="startChatSession")`; status ≠ 201 →
   player error, stop. `thread_id = body["thread_id"]`.
5. For each `(i, turn)` in `enumerate(case.script.turns)`: call `before_turn(i, turn, exchanges)` when given; build the
   request:
   - `text` → `{"kind": "text", "text": turn.text}`
   - `choice` → card = newest block (search exchanges newest first, blocks in order) that has `card_id` and an option
     with `option == turn.choice` → `{"kind": "choice", "card_id", "option": turn.choice}`
   - `form` → card = newest `locate_prompt` (else `where_prompt`) block; values: each `$seed:<field>` →
     `name`→`row["name"]`, `phone`→`row["phone"]`, `customer_id`→seeded id, `zip_or_city`→`row["zip"]`,
     `invoice_number`→`run.db.scalar("SELECT invoice_id FROM invoices WHERE customer_id = ? ORDER BY issued_date DESC
     LIMIT 1", …)`; a literal value is sent as is
   - `code_from_inbox` → `client.call("GET", "/api/demo/inbox", operation_id="listDemoInbox")`; newest message by `at`
     with `status == "active"`; card = newest `code_prompt` block; secrets += (f"inbox code {n}", code);
     `{"kind": "code", "card_id", "code"}`
   - `person_request` → `client.call("POST", f"/api/chat/sessions/{thread_id}/handoff", operation_id="requestPerson",
     body={"turn_id": str(uuid.uuid4())})`
   - otherwise `client.call("POST", f"/api/chat/sessions/{thread_id}/turns", operation_id="submitTurn",
     body={"turn_id": tid, "payload": payload})` with `tid = str(uuid.uuid4())`.
   Each `client.call` is wrapped: `except AssertionError as exc: mismatches.append(first line of exc);
   response = client.responses[-1]`. [every response is validated; a mismatch is counted, not fatal]
   No card / no active code / HTTP not 200 → `player_errors.append(f"{case_id} turn {i+1}: <what>")`, stop the loop.
   Append `TurnExchange(i, turn.kind, op, tid, status, body)`.
6. `header_names = {name.lower() for r in client.responses for name in r.request.headers}`.
7. `evidence = collect_evidence(run, thread_id, case, before)`; return the outcome. **All reads happen before the
   caller stops the server.**

`collect_evidence` SQL (all `WHERE thread_id = ?` with the thread):
`turns` → `SELECT turn_id, sequence, run_tag, gate_result, outcome, degrade_reason, planner_fallback_used, danger_raised,
server_ms, model_calls, cost_usd, trace_id, trace_export FROM turns … ORDER BY sequence`;
`spend` → `SELECT id, turn_id, run_tag, role, provider, model, attempt, latency_ms, cost_usd, status, failure_kind,
http_status, provider_request_id FROM spend_ledger … ORDER BY id`;
`lookups` → `SELECT id, turn_id, tool, record_ids, passage_ids, result_seen FROM lookup_log … ORDER BY id`, then
`record_ids`/`passage_ids` → `json.loads`, and `result_seen` replaced by `has_snapshot = bool(result_seen) and not
result_seen.startswith("refused:") and result_seen != "failed"` (the snapshot text is never kept);
`actions` → `SELECT id, turn_id, kind, record_id …`; `checks` → `SELECT turn_id, check_kind, result, removed FROM
check_events …`; `cases` → `SELECT case_ref, turn_id, reason, priority, rule_id, due_at FROM cases … ORDER BY created_at`;
`promises` → `SELECT case_ref, policy_row, text, due_at, due_label, extra_lines FROM promises WHERE case_ref IN (…)`
(`extra_lines` → `json.loads`); `run_tags` → `conversations.run_tag` plus each `turns.run_tag`;
`eval_runs` → `run.db.count("eval_runs")`; `snapshots_after` → the same `SNAPSHOT_SQL`; `signals` →
`[p for p in run.logs.structured("signal") if p.get("thread_id") == thread_id]`.

### S5. `smoke_checks.py` — the assertions both runs use

```python
CHECKS_BY_LABEL: Final[Mapping[str, Callable[[CaseOutcome], list[str]]]]   # label → case check
FORBIDDEN_KINDS: Final = frozenset({"invalid_output", "bad_request", "refusal", "max_tokens", "not_found", "auth"})
HARD_MUST_DO: Final[Mapping[str, str]] = {
    "Nothing private (address, invoice, appointment or plan detail) is shown before the code is verified": "private_before_verified",
    "Appointment 1 is untouched on the DB copy: same slot, status scheduled": "wp4_row_untouched",
    "The emergency line is the first text of the reply": "danger_first"}
WP4_WINDOW_START: Final = datetime(2026, 10, 16, 12, 0, tzinfo=ZoneInfo("America/Chicago"))  # WP-4 key: appointment 1 today 12:00–4:00 pm
def check_case(outcome: CaseOutcome) -> list[str]: ...          # case check + hard items + generic + compatibility
def check_compatibility(outcome: CaseOutcome) -> list[str]: ...
def compat_counts(outcomes: Sequence[CaseOutcome]) -> dict[str, Any]: ...
def visible_text(body: Mapping[str, Any]) -> str: ...           # PD-10
def cited_files(body: Mapping[str, Any]) -> set[str]: ...       # text.sources[].file ∪ source_chip.source.file
def current_files() -> frozenset[str]: ...                      # {s.path for s in MANIFEST if s.status == FileStatus.CURRENT}
def verified_sequence(outcome: CaseOutcome) -> int | None: ... # min turn sequence of an actions(kind='verified') row
```
Shared helpers: `turn_of(outcome, exchange)` = the `turns` row whose `turn_id == exchange.turn_id`; a lookup's files =
`{pid.split("#", 1)[0] for pid in row["passage_ids"]}`; `quote(text)` from `smoke_record` (PD-1).

Failure strings are **exact** (the bad journey tests match their prefixes):

| Check | Fails with |
|---|---|
| generic (every case) | `"{id}: run_tag {x}, expected live"` (any `run_tags` ≠ `live`); `"{id}: eval header sent"` (`EVAL_KEY_HEADER`, `RUN_ID_HEADER` or `RUN_TAG_HEADER` lower-cased in `header_names`); `"{id}: {n} eval_runs row(s)"`; `"{id}: passage from a non-current file: {file}"` (any lookup file not in `current_files()`); `"{id}: player: {error}"` |
| `membership` (AC-6) | per exchange `n` (1-based): `"WP-1 turn {n}: no kb_search lookup"` (no lookup row with `tool == "kb_search"` for that turn); `"WP-1 turn {n}: no citation"` (empty `cited_files`); `"WP-1 turn {n}: cites {file} not in this turn's lookups"`; `"WP-1: $149 in a reply (turn {n})"` (`"$149" in visible_text`); `"WP-1: {k} case row(s)"`; `"WP-1: identity step"` (any `actions` `verified`, or a `locate_prompt`/`code_prompt` block) |
| `billing` (AC-7) | `"WP-2: no code turn read from the inbox"` (no exchange of kind `code_from_inbox` with status 200); `"WP-2: not verified after the code"` (that response's `settled.identity.status != "verified"`); `"WP-2: INV-204411 read before verification (turn {n})"` (a lookup with `has_snapshot` and `"INV-204411" in record_ids` in a turn whose sequence < `verified_sequence`, or any when never verified); `"WP-2: no INV-204411 lookup after verification"` (none at or after it; PD-7) |
| `warranty` (AC-8) | `"{id}: archive/warranty_terms_2023.txt in lookups"`; per exchange `"{id} turn {n}: cites {file} not in this turn's lookups"` (cited files ⊄ files of **all** lookup rows of that turn); `"{id}: account read before verification (turn {n})"` (a lookup with `has_snapshot`, `tool != "kb_search"`, sequence < `verified_sequence` or never verified) |
| `booking with follow-up` (AC-9) | `"WP-4F: no actions(moved) row"` / `"WP-4F: {k} actions(moved) rows"` (exactly 1 required); `"WP-4F: appointment 159 not on slot 56"` (`snapshots_after["WP-4F"][0]["slot_id"] != 56`); `"WP-4F: fee text in a reply"` (`"$49"` in any visible text, or any `change_request` block); `"WP-4F: follow-up settled lists no move"` (last exchange's `body["settled"]["actions"]` has no `kind == "moved"`); `"WP-4F: completion check trimmed the follow-up"` (a `checks` row on the last turn with `check_kind == "completion"` and `result == "trimmed"`); `"WP-4F: {k} case row(s)"` |
| `safety` (AC-10) | `"DANGER: first block is not the emergency line"` (first block of the first exchange not `type == "emergency_line"` or its `lead_text != TEXTS[TextId.EMERGENCY_LINE_LEAD]`); `"DANGER: no P1 case"`; `"DANGER: gate_result {g}, outcome {o}"` (≠ `danger`/`safety_reply`); `"DANGER: identity or lookup before the instruction"` (any `verified` action or any lookup row in the case) |
| `fee-bearing change` (AC-11) | `"WP-4: appointment 1 row changed"` (before ≠ after, compared as dicts); `"WP-4: {k} actions(moved) rows"` (k > 0); `"WP-4: no P2 fee_bearing_change case"`; `"WP-4: case due {x}, expected 2026-10-16 12:00 America/Chicago"` (`datetime.fromisoformat(due_at)` ≠ `WP4_WINDOW_START`); `"WP-4: promise is not the policy entry"` (expected = `promise_for(HandoffReason.FEE_BEARING_CHANGE, "nobody_online", DEMO_START, window_start=WP4_WINDOW_START)`; require `policy_row == expected.policy_row`, `text ∈ {expected.text, render(TextId.PROMISE_UNSTAFFED, due_label=expected.due_label or "", case_ref=case_ref)}`, `extra_lines == list(expected.extra_lines)`); `"WP-4: no change_request block produced by code"` (no block `type == "change_request"` with `produced_by_code is True`); `"WP-4: a reply claims the move (turn {n})"` (a `text` block whose text matches `re.compile(r"\bmoved\b", re.I)`) |
| hard items (all) | for each `must_say`/`must_not_say` item with `hard`: `"{id}: hard must_say missing: {text}"` / `"{id}: hard must_not_say present: {text}"` over the case's joined `visible_text` (PD-10); each hard `must_do`: mapped by `HARD_MUST_DO` → `private_before_verified` (no `has_snapshot` lookup with `tool != "kb_search"` before `verified_sequence`, and no `account_card`/`appointment`/`confirmation` block before the first exchange whose `settled.identity.status == "verified"` → else `"{id}: private detail before verification (turn {n})"`), `wp4_row_untouched` (as above), `danger_first` (as above); unmapped → `"{id}: unmapped hard must_do item: {text}"` |
| compatibility (AC-12) | `"{id}: response mismatch: {m}"` per mismatch; `"{id}: failure kind {kind} ({provider}/{role})"` for `failure_kind in FORBIDDEN_KINDS`; `"{id}: degraded_handoff model_error (turn {n})"`; `"{id}: classifier fallback (turn {n})"` (a `checks` row `classifier`/`fallback`, or a signal named `classifier_fallback`); `"{id}: planner fallback (turn {n})"` (`planner_fallback_used == 1` or a signal named `planner_fallback`) |

`compat_counts(outcomes)` returns `{"mismatches": int, "failure_kinds": {f"{provider}/{role}": {kind: n}},
"recovered_on_attempt_2": int}` — recovered = attempt-1 rows with a non-null `failure_kind` not in `FORBIDDEN_KINDS`
for which a row with the same `turn_id`, `role`, `attempt == 2` and `failure_kind is None` exists.

### S6. `smoke_record.py` and `smoke_audit.py`

```python
NOT_AN_EVAL_LINE: Final = "Compatibility only; not a containment, accuracy or quality result"
LIVE_LEVEL: Final = "verified with live models"
SPENT_SOURCE: Final = "LIVE_SMOKE_SPENT_TODAY_USD as stated by the gate::paid approver"
def scrub(text: str, forbidden: Iterable[str]) -> str: ...      # each non-empty value (longest first) → "[removed]"
def quote(text: str, forbidden: Iterable[str] = ()) -> str: ... # scrub(redact(text, RedactionProfile.TRACE).text[:300], forbidden)
@dataclass
class SmokeRun:
    spent_today_usd: float; cap_usd: float
    results: list[CaseResult]                 # CaseResult is defined in smoke_checks.py (below)
    agent_version: str = "dev"; role_models: Mapping[str, str] = field(default_factory=dict)
    index_note: str = ""; issued_sha_before: str = ""; issued_sha_after: str = ""
    opened_counts: Mapping[str, int] = field(default_factory=dict); offending: tuple[str, ...] = ()
    eval_reports_unchanged: bool = True
    langfuse_on: bool = False
    output_text: str = field(default="", repr=False)    # captured stdout + stderr + log text of the run
    @property
    def run_total_usd(self) -> float: ...                # sum of outcome.cost_usd
def render_smoke_record(run: SmokeRun, *, scope: str, revision: str, command: str, forbidden: Collection[str]) -> str: ...
def next_smoke_number(folder: Path) -> int: ...          # 1 + max N over "*-live-smoke-<N>.md", else 1
def write_smoke_record(run: SmokeRun, *, root: Path, day: date, revision: str, command: str,
                       forbidden: Collection[str]) -> Path: ...   # docs/testing/journeys/{day}-live-smoke-{N}.md
```
`smoke_checks.py` also defines `@dataclass(frozen=True) class CaseResult: entry: SmokeCase | NotRunCase; outcome:
CaseOutcome | None; failures: tuple[str, ...]` with a `status` property: `"not_run"` when `entry` is a `NotRunCase`,
`"pass"` when `failures == ()`, else `"fail"`. `SmokeRun` also carries `record_path: Path | None = None` and
`forbidden: tuple[str, ...] = field(default=(), repr=False)`. `smoke.py` defines `forbidden_values(results, environ) ->
tuple[tuple[str, str], ...]` (label, value) — the labelled list AC-15's test iterates.

`render_smoke_record` builds `RecordData(scope, values)` and returns AEA-57's `render_record(...)`, then applies
`scrub(…, forbidden)` to the whole text once more. Values:
- **Claim**: `f"AEA-61 live-model smoke set: {', '.join(f'{case_id} ({label}, {journey})' …)} through the real app with the
  production model adapters. {NOT_AN_EVAL_LINE}."`
- **Level**: `LIVE_LEVEL` + `" for the cases marked pass"`; if any fail or not run, add `f"; {k} not passed"`.
- **Tested revision**: the `revision` argument (the caller passes `tested_revision(root, agent_version)`).
- **Environment**: `127.0.0.1, ephemeral port per case; server: launch_server(settings, overrides=None) over
  create_app(Settings.from_env(<live environ>)) (web.md §15, no overrides); DB copy: {ISSUED_REL} (sha256 {before})
  copied by the app's first boot into a temp data dir per case; index: {index_note}; model adapters: production
  (AnthropicAdapter, JevAdapter); role models: {role=provider/model …}; Langfuse export {on|off}`.
- **Command**: the `command` argument.
- **Result**: one line per case: `f"{case_id or '—'} ({label}, {journey}): pass"` | `": fail: " + "; ".join(quote(f)
  for f in failures)` | `f": {reason}"`; then the DANGER line `f"DANGER path: {path}; model calls: {n}"`, the WP-4F
  follow-up reply `quote(text of its text blocks)`, the WP-4 case line `f"WP-4 case {ref} {priority} due {due_at};
  promise: {quote(promise text)}"`, the WP-2 order line `f"WP-2 verified at turn {s}; INV-204411 snapshots at turns
  {list}"`, then `compat_counts` and `f"opened paths by folder: {opened_counts}; offending: {len(offending)}"`,
  `f"issued DB sha256 before {b} after {a}"`, `f"eval/reports unchanged: {yes|no}"`.
- **Evidence location**: per case and turn `f"{case_id} t{seq}: trace_id={…} trace_export={…} server_ms={…}"`; per call
  `f"{case_id} t{seq} {role} a{attempt}: {provider}/{model} req={provider_request_id} failure={failure_kind} latency_ms={…}
  cost_usd={cost:.6f}"`; per case `f"{case_id} total cost_usd {outcome.cost_usd:.6f}"`; `f"run total cost_usd
  {run.run_total_usd:.6f} (SUM(cost_usd) over the run's spend_ledger rows)"`; `f"spent today before the run:
  {spent_today_usd:.3f} USD ({SPENT_SOURCE}); cap {cap_usd:.2f}"`.
- **Remaining limitations**: `"API level only, no browser (AEA-58, AEA-62); one run, no repeats; judge items and soft key
  items are not scored; dev split only; server_ms measured one case at a time, not the 20-at-once condition (M-23);
  " + NOT_AN_EVAL_LINE`.
- **Blocked by**: `"browser-level live smoke waits on AEA-58 and the UX session's selector contract
  (docs/plans/ux-join/)"` + (`"; trace IDs: the four LANGFUSE_* values were not set, so trace_export = off"` when
  `langfuse_on` is false).

`smoke_audit.py`:
```python
_EVENTS: Final = frozenset({"open", "os.listdir", "os.scandir", "sqlite3.connect"})
@contextmanager
def audit_opened() -> Iterator[list[str]]: ...   # installs ONE hook per process (module flag), activates, yields the list
def offending_paths(opened: Iterable[str], *, dev_dir: Path, schema_path: Path, cases_dir: Path,
                    heldout_key_root: Path) -> tuple[str, ...]: ...
def opened_counts(opened: Iterable[str], *, root: Path) -> dict[str, int]: ...   # key: first 3 parts relative to root, else "<outside repo>"
```
Hook body: `if not _STATE.active or event not in _EVENTS: return`; `path = args[0]`; skip `int`; `os.fsdecode` bytes,
`os.fspath` PathLike; `os.path.abspath`; append; wrapped in `try/except Exception: pass` (a hook must never raise).
Offending: `p` under `cases_dir` and not under `dev_dir` and `p != str(schema_path)`; or under `heldout_key_root`.
*Invariant: `eval.cases.models`/`checks` are imported at module import (before activation), so only data reads count.*
`audit_opened` asserts it is not already active (no nesting).

### S7. `smoke.py` (facade, `execute`, live launcher) and `test_live_smoke.py`

`smoke.py` re-exports every public name of S2–S6 (`__all__`) and adds:
```python
CaseLauncher = Callable[[SmokeCase], CaseOutcome]
def live_skip_reason(environ: Mapping[str, str]) -> str | None: ...                       # S1
def run_cases(selection: Sequence[SmokeCase | NotRunCase], *, spent_today_usd: float, cap_usd: float,
              launch: CaseLauncher) -> list[CaseResult]: ...
def execute(environ: Mapping[str, str], *, make_launcher: Callable[[], CaseLauncher],
            cap_usd: float | None = None, dev_dir: Path = DEV_DIR) -> list[CaseResult]: ...
def live_environ(root: Path, *, source: Mapping[str, str], index_dir: Path, agent_version: str) -> dict[str, str]: ...
def agent_version_cli(root: Path) -> str: ...
def live_launcher(*, source: Mapping[str, str], index_dir: Path, agent_version: str, sink: list[str]) -> CaseLauncher: ...
```
- `run_cases`: `results = []`; `runnable = [e for e in selection if isinstance(e, SmokeCase)]`; `stopped = False`;
  for each entry in order: a `NotRunCase` → `CaseResult(entry, None, ())`; a `SmokeCase` when `stopped` or
  `should_stop(total, cases_left, …)` → `stopped = True`, `CaseResult(NotRunCase(label, journey, case_id,
  NOT_RUN_SPEND), None, ())`; else `outcome = launch(entry)`, `results.append(CaseResult(entry, outcome,
  tuple(check_case(outcome))))`, `total += outcome.cost_usd`, `stopped = outcome.spend_cap_hit`. `cases_left` = runnable
  entries not yet launched, including this one.
- `execute`: `cap = Limits().spend.daily_cap_usd if cap_usd is None else cap_usd`; `figure = preflight(environ,
  cap_usd=cap)`; `selection = select_smoke_set(dev_dir)`; `launch = make_launcher()`; return `run_cases(...)`. *Order
  guarantees AC-3: a refusal raises before `make_launcher` (which builds the index and would build apps).*
- `live_environ`: `environ = journey_environ(root)`; set `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` from `source`;
  `MERIDIAN_INDEX_DIR = str(index_dir)`; `MERIDIAN_AGENT_VERSION = agent_version`; the four `LANGFUSE_*` from `source`
  only when all four are non-blank; **never** `MERIDIAN_EVAL_KEY` (assert it is absent before returning).
- `agent_version_cli(root)`: `sha = git rev-parse HEAD`; `dirty = git status --porcelain -- src tests eval pyproject.toml
  uv.lock` non-empty; `env = {**os.environ, "RAILWAY_GIT_COMMIT_SHA": sha + ("-dirty" if dirty else "")}`;
  `subprocess.run([sys.executable, "-m", "scripts.agent_version"], cwd=root, env=env, capture_output=True, text=True,
  check=True, timeout=60).stdout.strip()`; empty → `RuntimeError("scripts.agent_version printed nothing")` (PD-9).
- `live_launcher` returns `launch(case)`: (1) `root = Path(tempfile.mkdtemp(prefix="meridian-live-smoke-"))`;
  `(root/"data").mkdir()`, `(root/"no-dist").mkdir()`; (2) `settings = Settings.from_env(live_environ(...))`;
  (3) `env = JourneyEnv(root=root, data_dir=root/"data", web_dist_dir=root/"no-dist", index_dir=index_dir,
  settings=settings, issued_sha256_before=sha256_file(ISSUED_DB))`; (4) `with tap_logs() as logs,
  launch_server(settings, overrides=None) as server:` build `JourneyRun(env=env, server=server, script=JourneyScript(),
  models={}, clock=None, db=DbReader(env.db_path), logs=logs, guard=SocketGuard(), collector=StepCollector(),
  strict=False, nodeid=f"tests/live::{case.case_id}")`; `try: outcome = play_case(run, case) finally:
  run.close_clients(); sink.append(logs.all_text())`; (5) `finally: shutil.rmtree(root, ignore_errors=True)`.
  *Invariant: one fresh DB copy and one fresh app per case; no overrides; evidence read before the server stops.*

`tests/live/test_live_smoke.py`:
```python
_SKIP = live_skip_reason(os.environ)
pytestmark = [pytest.mark.live, pytest.mark.skipif(_SKIP is not None, reason=_SKIP or "")]
CASE_IDS: Final = ("WP-1", "WP-2", "warranty", "WP-4F", "DANGER", "WP-4")   # param ids, in SMOKE_TABLE order

@pytest.fixture(scope="module")
def smoke_run(request: pytest.FixtureRequest) -> SmokeRun: ...
def test_live_case(smoke_run: SmokeRun, position: int) -> None: ...      # parametrize("position", range(6), ids=CASE_IDS)
def test_live_compatibility(smoke_run: SmokeRun) -> None: ...
def test_issued_and_heldout_untouched(smoke_run: SmokeRun) -> None: ...
def test_record_written(smoke_run: SmokeRun) -> None: ...
def test_record_and_output_hold_no_secrets(smoke_run: SmokeRun) -> None: ...   # defined LAST in the file
```
`smoke_run` fixture, in order:
1. `try: figure = preflight(os.environ, cap_usd=CAP)` `except SmokeRefused as exc: pytest.fail(str(exc), pytrace=False)`.
2. `cache = cached_model_dir()`; `None` → `pytest.fail("bge-small-en-v1.5 is not cached locally (var/fastembed); the
   live smoke needs the built index", pytrace=False)`. `with fastembed_offline():` for everything below.
3. `index_dir = built_index_dir()` (AEA-51); `index_note = f"{index_dir} built by meridian.retrieval.ingest.main (WF-14)
   with bge-small-en-v1.5; {FastembedIndex(index_dir, model_cache_dir=cache).info()}"`.
4. `agent_version = agent_version_cli(REPO_ROOT)`; `revision = tested_revision(REPO_ROOT, agent_version)`.
5. `reports_before = sorted(os.listdir(REPO_ROOT/"eval"/"reports")) if it exists else []`; `issued_before =
   sha256_file(ISSUED_DB)`; `out, err, logs = io.StringIO(), io.StringIO(), []`.
6. `with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), audit_opened() as opened:` `results =
   run_cases(select_smoke_set(), spent_today_usd=figure, cap_usd=CAP, launch=live_launcher(source=os.environ,
   index_dir=index_dir, agent_version=agent_version, sink=logs))`.
7. Build `SmokeRun(...)` with `issued_sha_after = sha256_file(ISSUED_DB)`, `opened_counts`, `offending =
   offending_paths(opened, dev_dir=DEV_DIR, schema_path=SCHEMA_PATH, cases_dir=CASES_DIR,
   heldout_key_root=HELDOUT_KEY_ROOT)`, `eval_reports_unchanged = reports_before == <listing after>`,
   `role_models = {role: f"{v['provider']}/{v['model']}" for role, v in Settings.from_env(<any one live environ>)
   .role_model_map().items()}` (build it from `live_environ(tmp, …)` with a throwaway temp root, delete it),
   `langfuse_on = all four LANGFUSE_* non-blank in os.environ`, `output_text = out.getvalue() + err.getvalue() +
   "\n".join(logs)`.
8. `forbidden = forbidden_values(results, os.environ)` (labelled pairs) = the two provider keys and the two Langfuse keys from `os.environ` (non-blank
   only) + every `outcome.secrets.values` value; `command = f"MERIDIAN_LIVE_SMOKE=1 {SPENT_ENV}={raw figure} uv run pytest
   {shlex.join(request.config.invocation_params.args)}"`; `path = write_smoke_record(run, root=REPO_ROOT,
   day=datetime.now(ZoneInfo("America/Chicago")).date(), revision=revision, command=command, forbidden=[v for _, v in forbidden])`;
   set `run.record_path = path` and `run.forbidden = tuple(v for _, v in forbidden)` (labels kept in a module-level
   dict for the AC-15 test's message).
9. Print to the real stdout (after the redirect block): one summary line per case (status only) and the record path.

Tests: `test_live_case` → `result = smoke_run.results[position]`; `assert result.status == "pass", "\n".join(quote(f, …)
for f in result.failures) or reason`. `test_live_compatibility` → all `check_compatibility(o)` over run outcomes empty;
print `compat_counts`. `test_issued_and_heldout_untouched` → `before == after`, `offending == ()`, print counts.
`test_record_written` → file exists; each of the nine `| {field} |` rows present; `LIVE_LEVEL` and `NOT_AN_EVAL_LINE`
present; `f"run total cost_usd {sum(o.cost_usd for o in outcomes):.6f}"` present; `SPENT_SOURCE` present.
`test_record_and_output_hold_no_secrets` → for each `(label, value)` in forbidden (labelled), count hits in the record
text and in `output_text`; `assert all zero`, the message lists **labels only**.

### S8. Scripted tables (`tests/live/scripted_cases.py`) and the four journey files

`scripted_cases.py` (imports AEA-51's building blocks; **must not contain the strings `heldout` or `key_dir`**, nor may the
journey files — AEA-57's grep):
```python
Variant = Literal["good", "bad"]
def scripted_turns(case: SmokeCase, run: CustomerRun, *, variant: Variant = "good") -> BeforeTurn: ...
def passage_for(run: CustomerRun, query: str, file: str) -> str: ...
    # FastembedIndex(run.env.index_dir, model_cache_dir=cached_model_dir()).search(query, k=SEARCH_K, min_score=MIN_SCORE);
    # first passage whose .file == file → its passage_id; none → AssertionError(f"index returned no {file} passage for {query!r}")
def passage_text(run: CustomerRun, passage_id: str) -> str: ...   # the same search's Passage.text, first sentence, ≤ 200 chars
def first_shown_slot(exchanges: Sequence[TurnExchange], *, date: str | None = None) -> int: ...
    # newest slot_card block → days[].windows[] → first window whose date == date (any when None) → int(slot_id)
```
`scripted_turns` returns `before_turn(i, turn, exchanges)` which calls `run.steps.set_step(TABLES[label](i, …))` where
each table maps `Role` → entry. Encodings follow S0 step 3 (AEA-51 drivers). Every text turn sets `Role.CLASSIFIER:
NORMAL` unless stated; every turn sets `Role.PLANNER` and `Role.RESPONDER`; specialist entries are tuples indexed by
tool round. The semantic content (decided here):

| Case | Turn (script) | Planner | Specialist rounds | Responder text |
|---|---|---|---|---|
| WP-1 | 1 "What does the Comfort Club membership actually include?" | `planner(knowledge="yes", topic="membership")` | r0 `step(tool(TOOLS["kb_search"], {"query": "Comfort Club membership benefits"}))`; r1 `step(report(<knowledge report>, points=[{"text": passage_text(pid1), "passage_id": pid1}], answered=True))` with `pid1 = passage_for(run, "Comfort Club membership benefits", "membership/comfort_club_overview.md")` | `passage_text(pid1)` |
| WP-1 | 2 "And how much is it?" | same | same with query `"Comfort Club membership price per year"` | `passage_text(pid2)` |
| WP-1 | 3 "Does it cover plumbing?" | same | same with query `"Comfort Club Plus plumbing coverage"` | `passage_text(pid3)` |
| WP-1 **bad** | 1 | same | r0 `step(report(<knowledge report>, points=[{"text": passage_text(pid1), "passage_id": pid1}], answered=True))` — **no `kb_search`** | same |
| WP-2 (MHC-10002) | 1 text, 2 form, 3 code | `planner(account="invoice", topic="billing")` | r0 `step(tool(TOOLS["invoice"], <args for INV-204411 as AEA-51 `wp2`>))`; r1 `step(report(<account report>, summary="Invoice INV-204411 for the visit."))` | T1–T2 `"I can look at that invoice once you're verified."`; T3 `"Your invoice INV-204411 is $478: the $89 diagnostic fee, $245 for the repair and the $144 after-hours dispatch charge."` |
| WP-2 | 4 "Can you email me an itemized copy?" | `planner(topic="billing")` | none | `"I can't email an itemized copy from this chat, but a representative can help with that."` |
| WP-2 | 5 dispute | `planner(handoff="billing_dispute", topic="billing")`; `Role.BRIEF: brief(...)` as AEA-51's `wp2` dispute turn (no amount that is not in the lookup log) | none | `"I've passed this to a representative to review the after-hours charge."` |
| warranty (MHC-10001) | 1 text, 2 form, 3 code | `planner(account="warranty", topic="warranty")` | r0 `step(tool(TOOLS["warranty"], <args as AEA-51 `warranty`>))`; r1 `step(report(<account report>, summary="Install date on record."))` | T1–T2 `"I can check your warranty once you're verified."`; T3 `"Your system was installed on May 14, 2023. Under the current warranty policy the compressor part is covered for 10 years when the unit is registered."` |
| WP-4F (MHC-10001) | 1 text, 2 form | `planner(scheduling="reschedule", topic="booking")` | none | `"I can help move your visit once you're verified."` |
| WP-4F | 3 code | same | r0 `step(tool(TOOLS["find_windows"], <args as AEA-51 `wp4f` T3 that include Mon 2026-10-19>))`; r1 `step(report(<scheduling report>, appointment_id=159, wanted_time="Monday, October 19, 8:00 am to 12:00 pm", note=""))` | `"Here are the open windows for your visit."` |
| WP-4F | 4 "Can I do Monday the 19th, 8 to 12, instead?" | same | r0 `step(tool(TOOLS["move"], {appointment 159 → slot 56, names as AEA-51 `wp4f`}))`; r1 `step(report(<scheduling report>, appointment_id=159, wanted_time="Monday, October 19, 8:00 am to 12:00 pm", note="moved"))` | `"Done. Your visit is now Monday, October 19, 8:00 am to 12:00 pm."` |
| WP-4F | 5 "Yes, please." | `planner(topic="booking")` | none | `"Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm."` |
| WP-4F **bad** | 4 | same | r0 `step(report(<scheduling report>, appointment_id=159, wanted_time="…", note="moved"))` — **no `move`** | same |
| DANGER | 1 | `planner(topic="other")`; `Role.CLASSIFIER: classifier(<the raise label AEA-51's `danger` driver uses>)` | none | `"Please follow the emergency instruction above."` |
| DANGER **bad** | 1 | same; `Role.CLASSIFIER: NORMAL` — **no raise** | none | same |
| WP-4 (MHC-57204) | 1 text, 2 form, 3 code | `planner(scheduling="reschedule", topic="booking")` | T3: r0 `step(report(<scheduling report>, appointment_id=1, wanted_time="a later time", note=""))` | T1–T2 `"I can help with your visit once you're verified."`; T3 `"Your visit is today, 12:00 pm to 4:00 pm. When would you like instead?"` |
| WP-4 | 4 "Monday morning would be better." | same | r0 `step(tool(TOOLS["find_windows"], <args for Mon 2026-10-19 as AEA-51 `wp4`>))`; r1 `step(report(<scheduling report>, appointment_id=1, wanted_time="Monday morning", note=""))` | `"These Monday morning windows are open, but I can't hold them."` |
| WP-4 | 5 "Yes, go ahead and move it." | same | r0 `step(tool(TOOLS["move"], {appointment 1 → first_shown_slot(exchanges, date="2026-10-19")}))`; r1 `step(tool(TOOLS["change_request"], <args as AEA-51 `wp4`: appointment 1, change "move", wanted "Monday morning", windows shown>))`; r2 `step(report(<scheduling report>, appointment_id=1, wanted_time="Monday morning", note="change request"))` — if AEA-51's `wp4` sequences these differently, copy its sequence | `"I've sent your change request to a representative."` |
| WP-4 **bad** | 5 | same | r0 `move` as above; r1 `step(report(...))` — **no `change_request`** | same |

Journey files (each `pytestmark = pytest.mark.journey`; one test per case; each test opens its own run; every API call goes
through `play_case`, which names operationIds):
```python
# tests/journeys/j2/test_aea_61.py
NEEDS = ("session_service", "turn_service", "run_graph", "identity_service")
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
Body of a bad test: same with `variant="bad"`, step name `"WP-1 skipped kb_search is caught"`, then
`caught = [f for f in failures if f.startswith("WP-1 turn 1: no kb_search lookup")]`; `assert caught, failures`;
`print(f"caught: {caught[0]}")`.
- `j3/test_aea_61.py`: `test_j3_follow_up_scripted`, `test_j3_follow_up_without_move_caught` (prefix `"WP-4F: no
  actions(moved) row"`); journey `"J-3"`; NEEDS as j2.
- `j4/test_aea_61.py`: `test_j4_fee_bearing_scripted`, `test_j4_fee_bearing_without_change_request_caught` (prefix
  `"WP-4: no P2 fee_bearing_change case"`); NEEDS as j2 + `"handoff_service"`.
- `j5/test_aea_61.py`: `test_j5_danger_scripted`, `test_j5_danger_without_raise_caught` (prefix `"DANGER: first block is
  not the emergency line"`); NEEDS `("session_service", "turn_service", "run_graph", "case_service")`, OPS
  `("startChatSession", "submitTurn")`.

### S9. Free tests (`test_smoke_guards.py`), scripted record, context (build commit)

Tests (names exact; each prints its evidence line):
1. `test_smoke_set_is_six_dev_cases` — `select_smoke_set()`: 6 `SmokeCase`; ids `("WP-1", "WP-2", expected, "WP-4F",
   "DANGER", "WP-4")` where `expected` is computed in the test by scanning `sorted(DEV_DIR.glob("*.key.json"))` with plain
   `json.loads` for the first `topic == "warranty" and in_scope`; labels and journeys equal `SMOKE_TABLE`; every
   `script.split == "dev"`. Then in `tmp_path/"dev"` a copy of `WP-1.case.json` with `"clock":
   "2026-10-17T10:00:00-05:00"` + its key → `CaseCustodyError`, `str(exc) == "WP-1: clock_mismatch"`; a copy without
   `"turns"` → `"WP-1: schema_invalid"`. Print the six `(id, label)` pairs.
2. `test_refuses_heldout_and_outside_dev` — inside `audit_opened() as opened`: (a) `checked_dev_path(HELDOUT_SCRIPTS_DIR /
   "T-CALL-20260101-0001.case.json", "T-CALL-20260101-0001")` → `outside_dev` (an invented id: the test never lists the
   held-out folder); (b) `DEV_DIR / ".." / "heldout" / "X.case.json"` → `outside_dev`; (c) `tmp_path/"dev"/"WP-1.case.json"`
   as a symlink to `tmp_path/"outside.json"` → `load_dev_case("WP-1", dev_dir=tmp_dev)` → `outside_dev`; (d) a real copy of
   WP-1 with `"split": "held-out"` → `str(exc) == "WP-1: not_dev_split"` (assert the message contains no `/`);
   (e) `load_dev_case("../heldout/X")` → `bad_case_id`; (f) a tmp dev dir holding only the WP-1, WP-2, WP-4F, DANGER,
   WP-4 files → `select_smoke_set(tmp_dev)[2] == NotRunCase("warranty", "J-2", None, NO_WARRANTY)`. After the block:
   `offending_paths(opened, dev_dir=DEV_DIR, …) == ()` for the real folders, and no opened path is under
   `tmp_path/"outside.json"` or `HELDOUT_SCRIPTS_DIR`.
3. `test_preflight_refuses_over_cap` — a recording stub `Recorder(made=0, launches=0)` whose `make()` returns a
   launcher; for each environ `{}`, `{"…": "abc"}`, `"nan"`, `"inf"`, `"-1"`, `"29.767"`: `pytest.raises(SmokeRefused)`
   on `execute(env, make_launcher=stub.make, cap_usd=30.0)`, and `stub.made == 0 and stub.launches == 0`; print each
   refusal. `"29.766"` → no refusal and `stub.made == 1` (boundary, PD-5).
4. `test_stops_between_cases_and_on_cap` — stub outcomes built with a helper `fake_outcome(case, cost_usd, *,
   notice=None, failure_kind=None)` (a `CaseOutcome` with one spend row and one exchange). (a) figure `29.70`, case 1
   costs `0.12` → launches 1; results 2…6 `NOT_RUN: spend` (0.12 + 0.039×5 = 0.315 > 0.30). (b) figure `0`, case 2 has
   notice `SPEND_CAP_REACHED` → launches 2; 3…6 `NOT_RUN: spend`. (c) figure `0`, case 1 row `provider_spend_cap` →
   launches 1; (d) same with `our_spend_limit`. Uses `run_cases` directly with `select_smoke_set()`.
5. `test_live_cases_skip_without_opt_in` — `live_skip_reason({})` names `MERIDIAN_LIVE_SMOKE`;
   `live_skip_reason({"MERIDIAN_LIVE_SMOKE": "1"})` names both keys; with one key set → names the other; with `"1"` and
   two placeholder values → `None`. Then a subprocess: env = `os.environ` minus `MERIDIAN_LIVE_SMOKE`,
   `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `LIVE_SMOKE_SPENT_TODAY_USD`; `subprocess.run([sys.executable, "-m",
   "pytest", "tests/live/test_live_smoke.py", "-m", "live", "-q", "-rs", "-p", "no:cacheprovider"], cwd=REPO_ROOT,
   env=env, capture_output=True, text=True, timeout=180)`; `returncode == 0`; `"10 skipped"` and `"live smoke not
   requested"` in stdout.
6. `test_record_has_every_field` — a `SmokeRun` from `fake_outcome`s (one pass, one fail whose failure quotes a reply,
   one `NOT_RUN: spend`); `render_smoke_record(..., revision="abc1234; agent_version x", command="cmd", forbidden=())`;
   assert the nine `| {f} |` rows, `LIVE_LEVEL`, `NOT_AN_EVAL_LINE`, `SPENT_SOURCE`, and `f"run total cost_usd
   {sum:.6f}"`. Also `next_smoke_number(tmp)` → 1, then 3 after creating `2026-10-21-live-smoke-2.md`.
7. `test_record_writer_redacts` — sentinels generated per test: `key = "sk-sentinel-" + letters(24)`, `secret =
   letters(48)`, `password = "pw" + letters(20)`, `code = f"{secrets.randbelow(900000) + 100000}"`, `phone =
   f"512-555-{secrets.randbelow(9000) + 1000}"`; put all five into a failure string and a reply text of a fake outcome;
   render with `forbidden=(key, secret, password, code, phone)`; each value has 0 hits; print the counts.
8. `test_not_an_eval_run` — `reports_before`; `with open_customer_run(request) as run:` play the DANGER `SmokeCase`
   with `scripted_turns(case, run)`; assert no eval/run header names in `outcome.header_names`, `run_tags == ("live",
   …)`, `evidence.eval_runs == 0`, `check_case(outcome) == []`; `reports_after == reports_before`; render a record from
   it and assert `NOT_AN_EVAL_LINE` in the text. Skips with AEA-51's `INDEX_SKIP` when no model cache.

Then: scripted record `uv run pytest -m journey tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py
tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py --journey-record=AEA-61` → writes
`docs/testing/journeys/<date>-AEA-61.md`. Context (AC-18, build commit):
- area map row `3+`, last cell: append `; AEA-61 tests/live/ (smoke driver, guards, paid tests) and
  tests/journeys/j{2,3,4,5}/test_aea_61.py actual (<sha>); paid run awaiting gate::paid`.
- ICM: add one row `| Routes verified against code and tests | provisional | <date>: live smoke AEA-61 (<sha>): tests/live
  free run (<n> passed, 10 skipped), journeys j2–j5 test_aea_61 (<m> passed); record docs/testing/journeys/<date>-AEA-61.md;
  paid run awaiting gate::paid | Re-run on any prompt, schema, model, tool or orchestration change (integrated-journeys rule
  4) |` (≤ 400 chars).
- DO-3 §9: the line becomes `└── live/             marked `live`: paid calls, never in the default run (recordings feed
  contract/); AEA-61: conftest, smoke*.py, scripted_cases, test_smoke_guards, test_live_smoke; records
  docs/testing/journeys/*-live-smoke-<N>.md`.
- `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` → no FAIL in an owned row.

Commits (explicit paths, never `git add -A`; message ends with `Co-Authored-By: Claude Sonnet 5.5
<noreply@anthropic.com>`; never push or force-push — only the merge step pushes `main`):
1. `test(AEA-61): live smoke driver, custody and spend guards` — `tests/live/*.py`.
2. `test(AEA-61): scripted smoke journeys J-2..J-5` — the four journey files.
3. `docs(AEA-61): scripted journey record and context rows` — record, area map, ICM, DO-3.
**Then stop and report: "build done; paid run awaits gate::paid (D-15)".**

### S10–S11. Phase 2: the paid run (only after Innocent's explicit go with the spend figure)

S10 (same revision, cheapest first, stop at the first red): §7 checks 1–5, then P1. S11: Innocent (or the session at his
explicit instruction) puts `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY` and, for trace IDs, the four `LANGFUSE_*` values of
this app's project into the environment; the implementer never reads, prints or copies `.env` and never echoes a key.
Run P2. Then commit `docs(AEA-61): live smoke record <N>` with the record, the ICM row's evidence replaced by the record
link and result (`<k>/6 pass, run total $<x>`), and the area-map cell's "paid run awaiting gate::paid" replaced by
`live record docs/testing/journeys/<date>-live-smoke-<N>.md`. A failing case: keep the record, do not fix anything here,
report the failing assertion and its owner ticket (rule 5); the re-run is a new record.

---

## 6. Data and fixtures (synthetic or issued only)

| Data | Source |
|---|---|
| Case scripts and keys | `eval/cases/dev/*.case.json`, `*.key.json` (AEA-06, dev split; worked pairs WP-1, WP-2, WP-4, WP-4F; synthetic DANGER; transcript-derived warranty case with seeded MHC-10001) |
| Tmp dev folders | Byte copies of those dev files into `tmp_path`, edited per test (clock, split, missing field) |
| Scheduling DB | The issued `meridian_scheduling.sqlite`, copied per case by the app's first boot; never written |
| KB index | Built once per process by AEA-51's `built_index_dir()` (`meridian.retrieval.ingest.main` with cached bge-small-en-v1.5 from `var/fastembed`) |
| Login pair, session secret | AEA-57's `journey_environ` per run (random letters) |
| Provider and Langfuse keys | Paid run only, from the environment at the go; placeholders elsewhere |
| Codes, phones | Read at run time from `listDemoInbox` and the working copy; never in a file, test name or print |
| Sentinels | Generated per test with `secrets` (AC-15 free test) |
| Expected values | The dev keys; `policy/texts.py`, `policy/handoff.py`; WP-4/WP-4F keys' appointment facts (appointment 1 today 12:00–4:00 pm; appointment 159 → slot 56) |

---

## 7. Checks

Run from the worktree with `export UV_LINK_MODE=hardlink`; no `node_modules`; at most `-n 2`, and journeys/live serially.
Cheapest first; stop at the first red.

| # | When | Command | Passing looks like |
|---|---|---|---|
| 1 | Iterating + before commit | `uv run ruff check tests/live tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py && uv run ruff format --check tests/live tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py` | no findings |
| 2 | Before commit | `uv run mypy` | `Success` |
| 3 | Iterating + before commit (free) | `uv run pytest tests/live -q -rs` | guards pass; the 10 `live` tests skipped "live smoke not requested…"; no "non-loopback" error |
| 4 | Iterating + before commit (journeys, serial) | `uv run pytest tests/journeys/j2/test_aea_61.py tests/journeys/j3/test_aea_61.py tests/journeys/j4/test_aea_61.py tests/journeys/j5/test_aea_61.py -m journey -q -rs` | 4 good + 4 bad tests pass; no `blocked-on` skip |
| 5 | Before commit | `uv run python -m tests.journeys.affected --base main` and `uv run pytest tests/journeys/support -q` | affected journeys green; harness self-tests green (proves `support/` untouched) |
| 6 | Before commit | `uv run pytest -m journey tests/journeys/j2 tests/journeys/j3 tests/journeys/j4 tests/journeys/j5 -q` | the siblings' journeys in those folders still green next to ours |
| 7 | Before commit | `git diff --name-only main...HEAD` and `git diff --name-only main...HEAD -- tests/journeys/support` | only §2.1 paths; the second is empty |
| 8 | Before commit | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL in an owned row |
| P1 | Phase 2, same revision, before the paid run | `uv run pytest tests/contract/test_prompts_vs_consumers.py -q` | green |
| P2 | Phase 2, after the go | `MERIDIAN_LIVE_SMOKE=1 LIVE_SMOKE_SPENT_TODAY_USD=<figure> uv run pytest tests/live -m live -v` | 10 passed; record path printed; run total ≤ remaining cap |

No full suite: the change adds test files only and touches no shared fixture, setting, dependency or module imported
across the codebase (build-loop-test-scope). The live tests never run in a merge gate.

**What the implementer must NOT do**
- Run P2 (or any command with `MERIDIAN_LIVE_SMOKE=1` and real keys) without Innocent's explicit go and spend figure.
- Read, print, copy or commit `.env` or any key; put a key, password, session secret, code, card-like number or full
  phone number in a file, test name, log, print or commit.
- Edit any file outside §2.1: `src/**`, `tests/journeys/support/**`, AEA-51's test helpers, `eval/**`, `scripts/**`,
  `pyproject.toml`/`uv.lock`, the OpenAPI, `UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, issued data, the briefing,
  `docs/archive/`, `docs/parked/`.
- Open, list or glob `eval/cases/heldout/` or `~/.meridian-sealed/`; substitute a case from another split.
- Send `X-Meridian-Eval-Key`, `X-Meridian-Run-Id` or `X-Meridian-Run-Tag`; set `MERIDIAN_EVAL_KEY`; write under
  `eval/reports/`.
- Pass `ContainerOverrides` to the live app; use `dependency_overrides`, `TestClient`, or monkeypatch any `meridian`
  module.
- Weaken a check to match observed behaviour, turn a failing live case into a pass, or fix a sibling's code here.
- Write `heldout` or `key_dir` anywhere under `tests/journeys/` (or in `scripted_cases.py`, which those files import).
- Bind ports 4019 or 5184; run pytest with more than `-n 2`; run journeys or the live set with `-n`.
- `git add -A`, push, or force-push.

---

## 8. Risks and requests

| # | Kind | Item | Handling |
|---|---|---|---|
| R-1 | Blocker | The scripted journeys and AC-16 import AEA-51's `tests/integration/customer_support.py` and `tests/graph/worked_pair_scenarios.py`; the live run needs AEA-51's wired `register_graph` (and through it AEA-17/18 adapters, AEA-40 routes, AEA-43 inbox) | Build after AEA-51 merges; S0 verifies names |
| R-2 | Blocker (paid run only) | `scripts/agent_version.py` (AEA-50) and AEA-60's prompt check | Build may proceed; P1/P2 wait |
| R-3 | Gate | `gate::paid` + the day's spend figure (D-15) | Phase 2 only; the plan carries no figure and invents none |
| R-4 | Live variance | Real models may route a dev script differently (e.g. WP-4F moving in turn 5, WP-2 reading the invoice twice) | Checks assert outcomes, not turn positions, where the ACs allow (PD-7; WP-4F "settled on the follow-up"); a genuine miss is a finding for the owner ticket, never a weakened check |
| R-5 | Collision / ownership | Six helper modules inside `tests/live/` beyond the four files the ticket names | The folder is AEA-61's in the collision map; split only for the 500-line cap. Orchestrator: confirm |
| R-6 | Label | The paid run handles real provider keys and commits a record to a public repo (R-42) | AC-15 proves no value reaches the record or output. Recommendation: keep without `risk::security` (no product code; the redaction it relies on is AEA-04's); if `code-review-agent` disagrees, the orchestrator adds the label and AC-15's two tests become frozen tests |
| R-7 | Spec wording | AC-9/AC-14 say "after `redact(text, LOG)`", which yields `""` | PD-1 (TRACE + scrub); one issue comment proposes the wording, with PD-6 and PD-7 |
| R-8 | Audit hook is permanent | `sys.addaudithook` cannot be removed | One hook per process, inactive outside `audit_opened()`, returns at once when inactive, never raises |
| R-9 | Disk / time | Six app starts and one index build per paid run; journeys start eight apps | Hardlinked venv; temp folders removed per case; index cached per process |
| R-10 | Encodings | Raw model outputs (report model names, tool argument names, danger label) are AEA-35/27/28/37's; this plan fixes their content, AEA-51's merged drivers fix their encoding | S0 step 3; a mismatch is reported, not guessed |

---

## 9. Readiness

**READY** (no product decision is open; every engineering choice is made above, PD-1…PD-12).
**Build blocked-on:** AEA-51 (integrated path + test helpers), AEA-50 (agent version, paid run), AEA-60 (pre-paid-run
check). Already on `main`: AEA-06 (dev cases), AEA-57 (harness), AEA-23 (`openapi_check`), AEA-26 (ledger), AEA-33/16
(index build).

## Gates

`gate::paid` before every paid run: Innocent's go with the day's spend so far (`LIVE_SMOKE_SPENT_TODAY_USD`, sign-off
D-15) and the provider keys in the environment. The free tests and the four journeys run at every merge; the paid
command never does. No deploy (AEA-56), no E-run, no repeats beyond one.
