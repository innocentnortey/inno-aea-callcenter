# Plan — [AEA-60] contract: prompt ↔ consumer checks (rendered prompts vs parsers, ToolDefs and schemas)

**Status:** planned — **READY**, build **blocked-on AEA-35, AEA-37, AEA-39** (refresh 2 at `c9b17ea`: the same three as
refresh 1; they are real imports of this test, §9). Journey level additionally waits on AEA-30, AEA-40 and AEA-51 (steps
skip, never pass, until then).
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/60 (spec copy:
`docs/plans/tickets/AEA-60.md`) · **Base revision:** `main` at `c9b17ea` (refresh 2, 2026-10-21; refresh 1 at `bb9a471`; first written at `35aefdd`) · **Lane:** `lane::build-loop` ·
**Risk:** none (no `risk::security`: no test-writer, no wave-merge security review) · **Wave:** 3 · **Gates:** none
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 (first written at `35aefdd`; refreshed at `bb9a471` and `c9b17ea`) · **Implementer:**
`fanout-implementer` on Sonnet · **Slug / branch:** `prompt-consumer-checks` → `aea-60-prompt-consumer-checks`, worktree
`/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-60` (the orchestrator creates it from `main` once §9's blockers
have merged).

Read this whole file before writing code. Every decision is made here (§5.0 lists them as PD-n). **If the code on `main`
disagrees with a name in this plan, the code on `main` wins: follow it and say so in your report.** If a name this plan
needs is **missing** on `main`, stop and report `BLOCKED-ON <ticket>`; never invent it, never add product code.

### Refresh 2 (2026-10-21, `main` at `c9b17ea`): what changed since `bb9a471` (read this first)

1. **Merged since refresh 1:** AEA-29 (case service, handoff service, `BriefAssembler`; merge `ef561fc`), AEA-24 (eval
   harness), AEA-50 (deploy image), AEA-54 (deployment guide). `git diff --stat bb9a471..main` over `src/`,
   `tests/fakes/`, `tests/fixtures/`, `tests/journeys/support/`, `tests/unit/agent/_gateway_doubles.py`,
   `tests/conftest.py`, `tests/contract/` and `pyproject.toml` touches only `src/meridian/services/{cases,handoff,
   _case_actions,_case_rules,_case_views}.py` and `src/meridian/web/container.py`. Every other §4 name is unchanged
   (re-read on `c9b17ea`: `agent/nodes/reply.py` `brief` / `checks` / `_store_brief`, `agent/prompts/reply.py`,
   `nodes/compose.py`, `context.py`, `gateway.py`, the AEA-11 fakes, the AEA-57 harness and `NEED_OWNERS`).
2. **PD-9 changed: the brief consumer is now real.** `GraphDeps.brief` is `RecordingBriefAssembler`, a subclass of the
   real `meridian.services.handoff.BriefAssembler` (pure: no I/O, no clock) that records each `attach_extraction` call
   and delegates to `super()` (§5.2). AC-9's "headings 2, 4 and 7 `not_generated`" and `status == "failed"` are now
   asserted on the real assembler's output (§5.8 item 11). `GraphDeps.cases` stays `CasesDouble`: the real
   `CaseService` needs a case opened through `HandoffService`, which is AEA-51's integration, and storing the brief is
   not what AC-9 checks.
3. **Build blockers unchanged.** In `.claude/state/build-ledger.md`, AEA-35 and AEA-39 are still `blocked` on the same
   NEEDS-DECISION (where the specialist task types live; §9.1 of each plan), and AEA-37 is still `blocked` with its
   build on `aea-37-graph-plan-node` at `36dc321`, not merged. `stage7-signoff.md` D-4…D-15 do not touch this ticket.
4. **Journey blockers moved.** AEA-29 and AEA-44 are merged, so `case_service`, `handoff_service` and
   `login_sessions` are bound. The steps now skip on AEA-30 (`demo_clock`, `demo_service`; ledger `blocked`), AEA-40
   (`session_service`, `turn_service`, the CON-2 operations) and AEA-51 (`run_graph`, `reply_composer`). Copy whatever
   the harness prints.
5. **Context budget:** `.claude/state/icm-progress.md` is now 15,697 B (§7.2 G-11).

Nothing else changed: the AC text, owned files, PD-1…PD-8 and PD-10…PD-14, the case table and the checks stand.

### Refresh 1 (2026-10-21, `main` at `bb9a471`): what changed since `35aefdd`

1. **Merged since the first plan:** AEA-17 (Anthropic adapter), AEA-18 (Jev adapter), AEA-21 (spine: `GraphDeps`,
   signals, `ReplyComposer`, node stubs), AEA-27 (account tools), AEA-28 (scheduling tools), AEA-38 (reply nodes and
   reply prompt). Every name this plan takes from them was re-read on `main`; §4.3 now marks each row **main**,
   **branch** or **plan only**. No name the plan uses changed. Blockers drop from nine to three: AEA-35, AEA-37, AEA-39 (§9).
2. **AEA-38 detail that matters here:** the `brief` and `checks` nodes build the brief's `shown` mapping themselves with
   `brief_shown(...)` over the customer rows of `messages.recent(...)`, and `check_quotes` is imported into
   `meridian.agent.nodes.reply` by name, so the Step 4 spy works as written. The labels are public constants in
   `meridian.agent.prompts.reply`: import them (Step 2 `LABELS`).
3. **AEA-37 is built on its branch (`36dc321`), not merged.** Its planner and classifier behaviour matches what AC-7
   asserts (§4.3 row). F-1 is still true there (§8).
4. **AEA-35 and AEA-39 have no branch;** both plans are NEEDS-DECISION on one question (where the specialist task types
   live). That is not AEA-60's decision, but it gates this ticket (§8 R-10).
5. **Journeys:** use the harness's own `journey.login()` / `journey.client()` (on `main`), as J-1 does (§5.9).
6. **Context budget:** `.claude/state/icm-progress.md` is now 14,555 B (§7.2 G-11).

Nothing else changed: the AC text, owned files, PD-1…PD-14, the case table and the checks are as first planned.

---

## 1. Goal and sources

### 1.1 Goal (from the issue's *What to build*)

> On Riverside every unit test passed while real turns failed, partly because a prompt told the model it could answer
> with a value the parsing code did not accept. Each prompt ticket (AEA-35, 37, 38) tests its own wording, and each
> consumer ticket (AEA-17, 18, 20, 22, 27, 28, 33) tests its own parser, but nothing yet puts a **rendered** prompt next
> to the code that reads the answer. This ticket does, and it also feeds each consumer the broken answers a real model
> can send, and checks that the documented fallback happens.

Deliverables: one contract test module `tests/contract/test_prompts_vs_consumers.py` (AC-1…AC-12, AC-14, level
`mock-tested`), its helper modules (§2), two journey files `tests/journeys/j5/test_aea_60.py` and
`tests/journeys/j9/test_aea_60.py` (AC-13), the evidence record and two context edits (AC-15). **No product code.**

**WP pair (ticket's worked examples).**
- *Example pair 1 (drift caught):* the planner request's `handoff` options equal `PlannerChoices.handoff`'s `Literal`
  set (incl. `late_technician`); each maps through `join_plan` to a `HandoffReason`. A drifted copy offering
  `cancel_membership` fails with `routing.planner.handoff offers 'cancel_membership'; PlannerChoices.handoff does not
  accept it` → tests `::test_routing_fields_match_planner_choices_and_danger_label`, `::test_check_fails_on_drift[planner_extra_option]`.
- *Example pair 2 (malformed answer):* NODANGER + raw Jev classifier body choosing `emergency` → real `JevAdapter`
  `INVALID_OUTPUT`, one attempt → `DangerAssessment(label="normal", raised=False, failure=invalid_output)`, one
  `classifier` event `fallback` codes `("fallback", "invalid_output")`, one `classifier_fallback` signal, `plan_join`
  still builds the booking plan → `::test_malformed_routing_outputs[classifier_emergency]`; integrated:
  `tests/journeys/j5/test_aea_60.py::test_j5_classifier_outside_options_books_normally`.

### 1.2 Context (why now)

Wave 3, Amendment 1 (slice plan §0a). On `c9b17ea` the adapters (AEA-17/18), dispatcher (AEA-22), account and
scheduling tools (AEA-27/28) and the reply node and prompt (AEA-38) and the brief assembler (AEA-29) are on `main`; routing (AEA-37) is built on its
branch; the specialists (AEA-35) and the act node (AEA-39) are planned only; AEA-61's live smoke waits for this ticket. The
test is data-driven from the real inventory (`Role`, `SPECS`, the registry built from the three factories), so later
tools, options and report fields are checked without editing it.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-60.md` | AC-1…AC-15 verbatim (§3); owned files; reviewer commands |
| Slice plan | `docs/plans/slice-plan.md` §0a (journey map J-5, J-9; AEA-60 wave 3), §1 row AEA-60 (blockers 20, 22, 35, 37, 38, 39, 17, 18, 27, 28, 33, 57), §3 collision map (`tests/contract/` prompt files: "60 (`test_prompts_vs_consumers`) … one file each"; `tests/journeys/`: one file per ticket per journey, `support/` is AEA-57's) | Ownership; one-file-per-journey convention |
| Rules | `.claude/rules/integrated-journeys.md` §3 rule 4–6, §4 (levels, record fields); `build-loop-test-scope.md` + *AEA addition*; `context-maintenance.md` rule 6; workspace `context-management-multi-turn.md` rule 3 (turns 1, 2, 5) | Rendered prompts through real builders; malformed outputs; evidence record; ICM row |
| Requirements | `docs/prd/inno-aea-callcenter-prd.md` R-46 (line 235), R-47 (line 157); HP-1, HP-4 | Fallback when the model is malformed; rules stand on a classifier failure |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §0 (`LLMFacing`, errors never carry values), §3–§5, §7, §9, §11, §12; addenda win (§16): `stage7/models.md` §1, §3, §5; `stage7/graph-tools.md` §1, §2, §4, §6; `stage7/graph-nodes.md` §1, §2, §4, §5, §9.4–§9.6; `stage7/graph-core.md` §2, §4, §11, closing table A-6; `stage7/cases.md` §3.3, §3.4, §4, §5; `stage7/data.md` §4, §5, §8a | Every type, signature and failure mapping in §4 |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` (E-1 dev set WP-1…WP-8, WP-4F, DANGER, NODANGER, line 58–62) | Fixture texts; adds no E-n case, runs no eval |
| Observability contract | DO-6 `docs/design/observability-contract.md` WF-1 (line 76), `model_call` span = "the full rendered context and raw output **after masking**" (line 113) | AC-14 records; PD-7 (AC-10 reading) |
| Key-metrics registry | DO-7 M-3, M-12, M-16, M-17, M-24 | Records AC-13/AC-14 assert stay computable; no target set |
| Decisions | `docs/plans/stage7-signoff.md` D-14 (CAS-16 option A → `HandoffReason.BURNING_RULED_OUT` is on `main`; DAT-2 option B → keys outside the repo) | Code-only set includes `burning_ruled_out`; AC-12 guards `eval/cases/heldout/` and `~/.meridian-sealed/` |
| Sibling code and plans | On `main` `c9b17ea`: the AEA-17, 18, 21, 27, 28, 29 and 38 modules (read). AEA-37 branch `aea-37-graph-plan-node` at `36dc321` (read). Plans only: `docs/plans/fanout/2026-10-21-build/AEA-35.md` §4.4–§4.6, `AEA-39.md` §5 | Exact builder and node names in §4 |

### 1.4 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Render every role's request through the real builder, turns 1, 2, 5 | integrated-journeys rule 4; ctx-mgmt rule 3 | AC-1 | in-ticket | Step 4 (`prompts_render.py`) |
| Offered option sets equal consumer `Literal` sets both ways | integrated-journeys rule 4 | AC-2 | in-ticket | Step 2, 5 |
| Every offered planner value has a consumer path | DO-4 §4, cases §3.4 | AC-3 | in-ticket | Step 5 |
| Every consumer-accepted `HandoffReason` (minus code-only) is reachable from some offered option | ticket "What to build" 2, bullet 2 | partly (AC-3 lists one direction) | **added** to AC-3's test (PA-1) | Step 5 |
| Code-only values never offered; no tool/report field sets priority, case ref, promise, customer id | DO-4 §7, §5 | AC-4 | in-ticket; scope decided in PD-6 | Step 5 |
| Tools sent = dispatcher schemas + `report_facts`; scope fields never in a schema | graph-tools §1–§2 | AC-5 | in-ticket | Step 2, 5 |
| Responder/brief output models; labelled blocks; brief ids = `check_quotes` shown keys | DO-4 §7, §9; graph-nodes §2–§3 | AC-6 | in-ticket | Step 4, 5 |
| Malformed routing/specialist/reply outputs reach documented fallback through real adapters + gateway + nodes | models.md §3, §5; graph-nodes §4, §5; cases §3.4 | AC-7, AC-8, AC-9 | in-ticket | Steps 3, 6, 7 |
| Rejected values never travel | DO-4 §0 | AC-10 | in-ticket; reading of "trace span" per DO-6 line 113 decided in PD-7 | Step 7 |
| Drifted copies fail by role, field and value | ticket step 4 | AC-11 | in-ticket | Step 5 |
| Dev data only; no network | data.md §5 (DAT-2) | AC-12 | in-ticket | Step 5 (module guard) |
| J-5, J-9 extended through CON-2 | slice plan §0a | AC-13 | in-ticket | Step 8 |
| WF-1 records per malformed case, codes only | DO-6 WF-1 | AC-14 | in-ticket | Step 7 |
| Docs: DO-3 §9 line, ICM row, record; area map unchanged | context-maintenance | AC-15 | in-ticket | Step 9 |
| `account="appointments"` with `scheduling="none"` yields `READ_APPOINTMENTS` on the **account** specialist, whose tools (`read_invoices`, `read_membership`, `read_warranty`) cannot read appointments | graph-tools §4 vs AEA-37 join step 5 | no | **other-ticket**: finding F-1 (§8) for AEA-37 / AEA-27; not asserted here (no AC owns it; a red-by-design test would block the merge) | orchestrator posts F-1 |
| Live compatibility of the same prompts | integrated-journeys rule 4 | no (moved) | other-ticket: AEA-61 | — |
| OpenAPI/fixture validation; browser; redaction beyond AC-10 | — | no | other-ticket: AEA-59, AEA-58, AEA-04/35/37 + CAP-1 (AEA-51) | — |

### 1.5 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (test-only; AC-13 drives the existing CON-2 route owned by AEA-40 and changes nothing in it) | — | — | — |

---

## 2. Boundary

### 2.1 Owned files (the only files you may create or edit)

| File | Create / modify | Role (size target / hard cap) |
|---|---|---|
| `tests/contract/test_prompts_vs_consumers.py` | create | the 12 named tests + the module guard (≤ 500 lines, hard cap 500) |
| `tests/contract/prompts_compare.py` | create | `PromptDrift` and the pure comparison helpers (≤ 300) |
| `tests/contract/prompts_world.py` | create | ids, fixture conversation, DB seeding, doubles, state/context builders, `GraphDeps` builder (≤ 400) |
| `tests/contract/prompts_render.py` | create | `Rendered`, `render_turn` through the real nodes with AEA-11 recording fakes (≤ 300) |
| `tests/contract/prompts_wire.py` | create | raw provider bodies, `Wire` (stubbed HTTP transports), real adapters, real gateway (≤ 300) |
| `tests/contract/prompts_cases.py` | create | `RawWorld`, the malformed-case table and its runners, the record corpus (≤ 450) |
| `tests/journeys/j5/test_aea_60.py` | create | J-5 step (AC-13) |
| `tests/journeys/j9/test_aea_60.py` | create | J-9 (a) and (b) steps (AC-13) |
| `docs/testing/journeys/<run-date>-AEA-60.md` | create | evidence record (AC-15; `<run-date>` = the America/Chicago date you run the final checks, `YYYY-MM-DD`) |
| `docs/design/code-design.md` | modify | **only** the §9 `contract/` tree line and the `**Built on `main`:**` line under it (AC-15) |
| `.claude/state/icm-progress.md` | modify | **add one** `Routes verified against code and tests` row for AEA-60 after the last such row (AC-15) |

The five `prompts_*.py` helper modules follow AEA-59's precedent on `main` (`tests/contract/openapi_cases.py`,
`openapi_driver.py`, `openapi_variants.py` beside their tests). No other ticket touches them (orchestrator: please
accept them as AEA-60's in the collision map; §8 R-1).

### 2.2 Shared surfaces: read only, never edit

`src/meridian/**` (all of it), `tests/fakes/**` (AEA-11), `tests/fixtures/sqlite.py` (AEA-10),
`tests/unit/agent/_gateway_doubles.py` (AEA-20), `tests/journeys/support/**` (AEA-57), `tests/conftest.py` (AEA-01),
every other `tests/contract/*` file (AEA-17/18/59/…), `docs/ux/**`, `apps/web/**`, the OpenAPI and `UI_CONTRACTS.md`,
`docs/data/issued/**`, `docs/archive/**`, `eval/**`, `.claude/reference/area-map.md` (AC-15: unchanged).

**The prompt modules are never edited** (AC-11): drift is tested on *copies* passed to the comparison helpers. Spying
on `meridian.agent.nodes.reply.check_quotes` with `MonkeyPatch.setattr` inside a context is allowed (it edits no file).

### 2.3 What you must not do

- Do not write or change product code, a prompt, a `ToolDef`, an adapter or a consumer type. A mismatch the test finds
  is reported as a defect on the owning ticket and the test stays red (ticket *Scope boundary*).
- No paid or live call, no `live` marker, no socket (AC-12). No `.env` read. No port 4019 or 5184.
- No secret, verification code, card-like number or full phone number in code, fixtures, logs or test ids. Placeholder
  API keys are generated: `"sk-test-" + secrets.token_hex(8)` and `"or-test-" + secrets.token_hex(8)`.
- Do not read anything under `eval/cases/heldout/` or `~/.meridian-sealed/` (AC-12).
- Do not edit `tests/journeys/support/` (a missing harness capability is a follow-up on AEA-57, merged first — none is
  needed by this plan, PD-10).
- `git add` explicit paths only (§7.4), never `-A`. Never force-push. Only the merge step pushes `main`.
- Do not add a `conftest.py` anywhere (a shared fixture would make every test "affected").

---

## 3. Requirements table

Every AC is verbatim in the ticket; the "How" column is this plan's implementation; "Verify" names the test or command.
All unit tests are in `tests/contract/test_prompts_vs_consumers.py` (prefix `::` below) at level `mock-tested`.

| ID | Requirement (short; ticket text wins) | How (step) | Verify |
|---|---|---|---|
| AC-1 [invariant] | Every `Role` and every `SPECS` kind has a rendered request through its real builder on turns 1, 2, 5; offered sets identical on all three turns; a missing role/kind fails by name; a fake extra role fails with its name | `rendered` module fixture renders turns 1, 2, 5 via the real nodes (Step 4); `check_inventory`, `offered_sets` (Step 2) | `::test_every_role_and_spec_has_a_rendered_case` |
| AC-2 [invariant] | Planner field names = `PlannerChoices` fields; options = `Literal` sets both ways (incl. `late_technician`), ≤ 255; fallback carries the same fields; classifier offers exactly `normal, burning_unclear, danger`; quoted option keys in wording are options | `check_choice_fields`, `check_wording_keys` | `::test_routing_fields_match_planner_choices_and_danger_label` |
| AC-3 [invariant] | Every offered planner option has a consumer path through `join_plan`, `priority_for`, `decide_escalation`, `SPECS`, `Plan.topic`; (PA-1) every non-code-only `HandoffReason` is reachable | parametrised over every `(field, option)` | `::test_join_plan_accepts_every_offered_value[<field>=<option>]` (+ `[reverse_reachability]`) |
| AC-4 [invariant] | Code-only set ∩ every offered planner/fallback option = ∅; no tool/report/reply field named priority/case ref/promise/customer id | `check_code_only`, `check_no_forbidden_fields` (PD-6) | `::test_no_prompt_offers_a_code_only_value` |
| AC-5 [invariant] | Specialist tools = `dispatcher.schemas(spec.tool_kinds)` + `report_facts`; names resolve, match `[a-z_]{1,64}`, kind in spec; no registry `report_facts`; `check_covers`; schemas = trimmed args schema, strict, no scope fields; `report_facts` = report model's; wording mentions only sent tools | `check_specialist` (PD-5, PD-8) | `::test_specialist_tools_match_registry_and_report_models` |
| AC-6 [invariant] | Responder `output_model is ResponderDraft`, wire schema = `anthropic.transform_schema(ResponderDraft)` with only `text` (1–1200); both labels present; brief `output_model is BriefExtraction`; brief ids = `check_quotes` shown keys, customer messages only, byte-identical | `check_reply_schema`, `check_brief_ids`, wire capture through real `AnthropicAdapter` | `::test_reply_schemas_and_brief_message_ids_match_checks` |
| AC-7 [failure/refusal] | Malformed Jev planner (a outside, b missing, c unparseable) → `INVALID_OUTPUT`, one attempt, one fallback; recovered plan `fallback_used=True`, signal `invalid_output` / `recovered=True`; (d) both malformed → `planner_failed` plan, `recovered=False`; (e) classifier `emergency` / `{}` → rules stand, `classifier` event `fallback`, `classifier_fallback` signal, plan built | `run_routing` (Step 6) on real `JevAdapter`/`AnthropicAdapter` + real gateway + real `plan.py` nodes | `::test_malformed_routing_outputs[<case>]` |
| AC-8 [failure/refusal] | Unknown tool, not-allowed, `args=None`, extra `customer_id`, 301-char query, `INV-12`, invalid `report_facts` (6 points; 301-char summary), unparseable / `max_tokens` / `refusal` step → documented codes, records, lookup rows; failed result → `specialist_failed` + rule 6 `AI.specialist_failed` P3 degraded | `run_specialist_case` (Step 6) on real registry, dispatcher, runner, act node | `::test_malformed_specialist_outputs[<case>]` |
| AC-9 [failure/refusal] | Responder `""`, 1,201 chars, extra `promise`, `refusal` → `fallback_used`, code-built reply + person offer, `responder_fallback`; brief 0/3 needs, 6 claims, 201-char decision → `brief_extraction=None`, `brief_failed`, headings 2/4/7 `not_generated`; AI/staff/paraphrase quote → removed `quote_not_found`, `brief_quote` `trimmed` | `run_reply_case` (Step 6) on real `AnthropicAdapter`, gateway, `reply.py` nodes, `ReplyComposer` | `::test_malformed_reply_outputs[<case>]` |
| AC-10 [negative] | Markers `zq-rejected-option-7731`, `…zq-rejected-query-7731` (301 chars), `zq-rejected-draft-7731` absent from every record of AC-7…AC-9 | `case_corpus` (Step 7); PD-7 for the specialist `model_call` raw output | `::test_rejected_values_absent_from_records` |
| AC-11 [failure/refusal] | Six drifted copies fail by role, field and value; prompt modules unchanged | `pytest.raises(PromptDrift, match=…)` on the helpers | `::test_check_fails_on_drift[<case>]`; `git diff --name-only` shows no `src/` path |
| AC-12 [negative] | Dev data only; no held-out open; no socket connect | module audit hook + socket guard + per-test check (Step 5) | `::test_no_heldout_reads_and_no_network` |
| AC-13 [journey] | J-5 NODANGER with classifier outside options books normally (no case, one `classifier` `fallback` event); J-9 (a) both planners malformed → handoff reply, turn `degraded_handoff`/`model_error`, case `ai_failure` P3; J-9 (b) malformed draft → code-built reply, `degraded_handoff`/`model_error` | Step 8 on AEA-57's harness; level `integrated with a scripted model` once AEA-30, AEA-40 and AEA-51 bind; until then the steps report *blocked* | `uv run pytest -m journey tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py -rs` |
| AC-14 [capture] | Per malformed case: `CallRecord` `status="error"` + failure kind (ledger row + sink span per attempt); `signal` fields; check events; one `lookup_log` row per dispatched call | `assert_records` over `MALFORMED_CASES` (Step 7) | `::test_malformed_cases_leave_their_records[<case>]` |
| AC-15 [regression/context] | DO-3 §9 line, ICM row, record; area map unchanged | Step 9 | `git diff --name-only` |
| PA-1 (plan-added, in AC-3's test) | Every `HandoffReason` not in the code-only set is produced by some offered `handoff` option | §5 Step 5 | `::test_join_plan_accepts_every_offered_value[reverse_reachability]` |

---

## 4. Shared code to use (copied from `main`, the addenda and the sibling plans)

**Rule for this section:** names marked **(main)** were read on `main` at `c9b17ea` (refresh 2). Names marked **(branch)** were
read on a sibling's built branch; names marked **(plan)** come from a sibling's plan. When those land, the code on
`main` wins.

### 4.1 Domain and ports (main)

```python
# meridian.domain.common
class LLMFacing(MeridianModel)                       # extra="forbid", frozen
class Role(StrEnum): PLANNER="planner"; CLASSIFIER="classifier"; PLANNER_FALLBACK="planner_fallback"
                     SPECIALIST="specialist"; RESPONDER="responder"; BRIEF="brief"
class ProviderFailureKind(StrEnum): …; REFUSAL="refusal"; MAX_TOKENS="max_tokens"; INVALID_OUTPUT="invalid_output"
class ProviderFailure(MeridianModel): kind; provider: Literal["anthropic","openrouter_jev"]; http_status: int|None
                                      retry_after_s: float|None; retryable: bool; provider_request_id: str|None
class CallRecord(ProviderCall): role: Role; attempt: int (1..2)   # ProviderCall: provider, model, latency_ms, *_tokens,
                                      # cost_usd, cost_source, status: Literal["ok","error"], failure, provider_request_id, stop_reason
class HandoffReason(StrEnum): SAFETY, DANGER, BURNING_UNCLEAR, CUSTOMER_REQUESTED_PERSON, REFUND, BILLING_DISPUTE,
    COMPLAINT_OR_MANAGER, LEGAL_OR_CHARGEBACK, COMMERCIAL, LATE_TECHNICIAN, FEE_BEARING_CHANGE, MEMBERSHIP_CANCEL,
    UNSUPPORTED_ACTION, IDENTITY_UNVERIFIED, AI_FAILURE, BURNING_RULED_OUT          # 16 values (D-14)
class Priority(StrEnum): P0..P4
class ToolErrorCode(StrEnum): NOT_ALLOWED="not_allowed"; BAD_ARGUMENTS="bad_arguments"; UNKNOWN_TOOL="unknown_tool"; …
class ToolKind(StrEnum): KB_SEARCH="kb_search"; ACCOUNT_READ="account_read"; SLOT_SEARCH; BOOK; MOVE; CANCEL; CHANGE_REQUEST
class ToolCallRecord(MeridianModel): tool_call_id; name (≤64); kind: ToolKind|None; outcome: Literal["ok","refused","failed"]
                                     error: ToolErrorCode|None; record_ids; passage_ids; lookup_id: int|None; elapsed_ms
ThreadId, TurnId, RequestId (UUID4 str subclasses), CustomerId ("MHC-\d{5}"), CaseRef ("^MHC-C-[0-9]{4}$"),
PassageId ("^[^#\s]+#[0-9]+$")
# meridian.domain.turn
class TurnIds(MeridianModel): thread_id; turn_id; request_id; run_tag: Literal["live","eval","load"]; run_id: str|None; agent_version: str
@dataclass(frozen=True) class TurnBudget: started: float; deadline: float
@dataclass(frozen=True) class TurnContext: ids; budget; now; demo_session: str; span: SpanHandle; intake: Intake|None = None
class TurnInput(MeridianModel): turn_id; message_id: int; kind: Literal["text","choice","code","form"]; text_store: str
                                card_id=None; choice=None; card_number_seen=False; received_at: datetime
class RuleMatches(MeridianModel): safety; burning_unclear; danger_words; person; policy_trigger; rule_ids; correction
class GateKind(StrEnum): …FREE_TEXT="free_text"
class GateDecision(MeridianModel): kind; rules; burning_answer=None; resume_task_id=None
class TaskIntent(StrEnum): ANSWER_QUESTION, READ_INVOICE, READ_MEMBERSHIP, READ_APPOINTMENTS, READ_WARRANTY,
                           BOOK_NEW, RESCHEDULE, CANCEL, CONFIRM
class PlannerChoices(LLMFacing):
    knowledge: Literal["no","yes"]; account: Literal["none","invoice","membership","appointments","warranty"]
    scheduling: Literal["none","book_new","reschedule","cancel","confirm"]
    handoff: Literal["none","refund","billing_dispute","membership_cancel","unsupported_other",
                     "complaint_or_manager","late_technician"]
    topic: Topic   # Topic = Literal["booking","membership","billing","warranty","other"]
class PlannerOutcome(MeridianModel): choices; probabilities; model: str; fallback_used: bool; failure
class DangerAssessment(MeridianModel): label: Literal["normal","burning_unclear","danger"]; raised; confidence=None; failure
class PlannedTask(MeridianModel): order (1..3); specialist: SpecialistKind; intent; needs_identity; resumes_task_id=None
class Plan(MeridianModel): mode; tasks (≤3); handoff_request: HandoffReason|None; topic: Topic; source; planner_failed=False
class EscalationInputs(MeridianModel): gate; plan; results; counters; identity; halt; models_disabled; now
class EscalationDecision(MeridianModel): outcome: Literal["none","offer","escalate"]; reason; priority; rule_id; degraded=False
class CheckEvent(MeridianModel): check; turn_id; result; removed=0; claim_kinds=(); codes=()
class SignalRecord(MeridianModel): record="signal"; name: SignalName; turn_id; thread_id; request_id; run_tag; node: str
                                   cause=None; role=None; specialist=None; attempt=None; recovered=None
class TurnFacts(MeridianModel): turn_id; gate_kind; plan_mode; points; passages; no_source_tasks; windows_shown;
                                writes_this_turn; change_request; handoff; escalation; identity_step; quick_checks=()
class ResponderDraft(LLMFacing): text: str = Field(min_length=1, max_length=1200)
class CheckedReply(MeridianModel): text; removals; fallback_used: bool; events: tuple[CheckEvent, ...]
class ComposedReply(MeridianModel): blocks; settled_view; writes; notice; path; outcome; degrade_reason
# meridian.domain.state
class ChatLine(MeridianModel): speaker: Literal["customer","assistant","representative","event"]; text; turn_id; at
class ConversationState(MeridianModel): thread_id; settled=None; controller; identity; open_tasks; shown_slots; counters;
    burning_card_id=None; turn_input: TurnInput; chat_window; gate; planner; danger; plan; identity_step;
    specialist_results; escalation; handoff; facts; draft; brief_extraction; checked; reply; halt; check_events
class SpecialistSend(TypedDict): planned: PlannedTask; state: ConversationState
# meridian.domain.identity
class IdentityState(MeridianModel): status; customer_id; masked_hint; code_expires_at; tries_left (0..3); codes_sent (0..3); verified_at
# meridian.domain.actions
class ActionKind(StrEnum): …CASE_OPENED="case_opened"…
class ActionKey(MeridianModel): thread_id; turn_id; kind; record_id: str
class CompletedAction(MeridianModel): key; kind; records: dict[Literal["appointment","slot","old_slot","case","customer","promise"], str]; before=None; after=None; at
class Settled(MeridianModel): actions; open_case; read_at
# meridian.domain.handoff
class CaseSummary(MeridianModel): case_ref; reason; priority; state: CaseState; created_at; promise; followup; version: int; seed=False; due_at
class HandoffResult(MeridianModel): case; created: bool; action: CompletedAction; alert: Literal["supervisor_now"]|None
class Quote(LLMFacing): message_id: int; text: str = Field(max_length=300)
class BriefExtraction(LLMFacing): needs: list[Quote] (1..2); claims: list[Quote] (≤5); open_decision: str (≤200)
class Brief(MeridianModel): case_ref; thread_id; assembled_at; status: Literal["ready","being_written","failed"]; headings
class BriefHeading(MeridianModel): number; key; title; origin; checked; items; trimmed; trim_note; not_generated
BRIEF_TITLES, BRIEF_KEYS, BRIEF_ORIGINS   # tuples of 8; heading index 3 ("says") has checked=False
# meridian.domain.specialists
class KnowledgeReport(LLMFacing): points: list[ReportedPoint] (≤5); answered: bool   # ReportedPoint: text ≤500, passage_id
class AccountReport(LLMFacing): summary: str (≤300)
class SchedulingReport(LLMFacing): appointment_id: int; wanted_time: str; note: str (≤200)
class SchedulingSlice(MeridianModel): customer_zone; member; appointments; shown_slots; pending_change; bookings_left
class SchedulingSliceInputs(MeridianModel): zone: Zone|None; member: bool; appointments=()
class KnowledgeResult / AccountResult / SchedulingResult  # kind, status, …, tools: tuple[ToolCallRecord,...], calls, brake, failure
# meridian.domain.records
class Passage(MeridianModel): passage_id; file; section; version_label; version_date: date|None; text; score: float
# meridian.domain.tools
class ToolCallScope(MeridianModel): ids; customer_id; shown_slot_ids; now; message_id   # the five scope field names
# meridian.ports.models
class ChoiceField(MeridianModel): name; instructions; options: dict[str, str] (≤255)
class ChoiceRequest(MeridianModel): system: str; state: dict[str, JsonValue]; fields: tuple[ChoiceField, ...]
class ChoiceAnswer(MeridianModel): choices: dict[str, str]; probabilities: dict[str, dict[str, float]] | None
class StructuredRequest[T](MeridianModel): system_prefix; system_dynamic; user; output_model: type[T]; max_tokens; effort
class ToolSchema(MeridianModel): name; description; input_schema: dict[str, JsonValue]; strict: bool = True
class ToolStepRequest(MeridianModel): system_prefix; system_dynamic; messages: ProviderMessages; tools: tuple[ToolSchema,...]; max_tokens; effort
class ToolStep(MeridianModel): text; tool_calls: tuple[ToolCall,...]; raw: JsonValue; stop_reason: str|None
```

### 4.2 Policy, storage, gateway, dispatch (main)

```python
from meridian.policy.limits import Limits, Brakes        # Brakes(tasks_per_turn=3, tool_rounds=2, sonnet_calls=6)
from meridian.policy.handoff import priority_for, promise_for
#   priority_for(reason, *, promise_due: datetime|None = None, renewal_date: date|None = None) -> Priority (ValueError if no row)
#   promise_for(reason, presence: Literal["nobody_online","simulated_on_shift"], now, window_start=None) -> Promise
from meridian.policy.escalation import decide_escalation  # (inputs: EscalationInputs) -> EscalationDecision
from meridian.privacy.redact import RedactionProfile, redact   # redact(text, profile).text; profiles STORE, SONNET, JEV, TRACE, LOG
from meridian.adapters.sqlite.rows import ConversationRow
#   ConversationRow(thread_id, demo_session, run_tag, agent_version, started_at, …defaults)
# tx.core.conversations.insert(row); tx.core.messages.append(thread_id, role, text_redacted, at, *, turn_id=None, kind=None) -> int
# tx.core.lookup_log.for_thread(thread_id) -> tuple[LookupRow, ...]   (LookupRow: id, thread_id, turn_id, message_id, tool,
#   record_ids, passage_ids, result_seen); lookup_log.append needs a real messages row (FK).
from tests.fixtures.sqlite import TempStore, temp_sqlite      # with temp_sqlite() as store: store.uow, store.db_path
from meridian.agent.gateway import ModelGateway, ModelOutcome
#   ModelGateway(*, choice, structured, tools, ledger, trace, redact, limits)
#   choice: Mapping[ChoiceRole, (ChoiceModel, RoleSpec)]; structured / tools likewise (structured/tools adapters must be "anthropic";
#   a Jev role's RoleSpec.redaction must be RedactionProfile.JEV).
from meridian.agent.tools.dispatch import ToolDispatcher, ToolRegistry
#   ToolRegistry(defs).get(name) -> ToolDef|None; .for_kinds(kinds) sorted by name; .check_covers(kinds) raises ValueError
#   ToolDispatcher(registry, uow).schemas(kinds) -> tuple[ToolSchema, ...]  (input_schema = args schema with every
#   "title" key removed, recursion rule of dispatch._strip_titles lines 78-93; strict=True)
from meridian.agent.tools.knowledge import KB_SEARCH_NAME, KbSearchArgs, knowledge_tools   # "kb_search"; query 1..300
from tests.unit.agent._gateway_doubles import RecordingLedger, spec
#   RecordingLedger().records: list[(CallRecord, TurnIds)]; admit_call → ALLOW; models_disabled() → False
#   spec(*, cap_s, redaction, model="model-test", max_tokens=500, effort="low") -> RoleSpec
from tests.fakes import (WORKED_PAIRS_NOW, FakeAnthropicChoiceModel, FakeChoiceModel, FakeIndex, FakeStructuredModel,
                         FakeToolModel, InMemoryTraceSink, ScriptedFailure)
#   FakeChoiceModel(script, *, model=None).requests: list[ChoiceRequest]   (records BEFORE answering, failures included)
#   FakeStructuredModel(script).requests; FakeToolModel(script).requests: list[ToolStepRequest]
#   ScriptedFailure(kind=ProviderFailureKind.INVALID_OUTPUT)
#   InMemoryTraceSink(): `with sink.turn(ids) as span:`; sink.spans_for(span).model_calls: list[RecordedModelCall(record,
#   masked_input, masked_output)]; .nodes: list[RecordedNode(name, elapsed_ms, status)]. model_call/node raise ValueError for
#   a span the sink did not open → ALWAYS build TurnContext.span inside sink.turn(ids).
#   FakeIndex(passages).searches: list[(query, k, min_score)]
from langgraph.runtime import Runtime          # Runtime(context=ctx) is the node's `runtime` argument
```

### 4.3 Siblings — what this test imports (status on `main` at `c9b17ea`)

| Import | From | Status | Signature this plan uses |
|---|---|---|---|
| `meridian.adapters.models.openrouter_jev`: `JevAdapter`, `DECISIONS_URL` | AEA-18 | **main** (`900a1d8`) | `JevAdapter(http: httpx.Client, *, api_key: SecretStr, model: str)`; `model` needs a `JEV_PRICES` row (else `ValueError`): use `"typesafe/jev-1.13"`. Request: POST `DECISIONS_URL`, JSON `{"model", "state": {"instructions": req.system, **req.state}, "questions": {name: {"type": "choice", "instructions", "criteria": {options}}}, "provider": {"data_collection": "deny"}}`. A 2xx body with `"error"` → `BODY_ERROR`; no `answers` dict, a field missing, a choice that is not a str or not in the options, or a non-JSON body → `INVALID_OUTPUT`, `retryable=False`, `http_status=200` |
| `meridian.adapters.models.anthropic`: `AnthropicAdapter` | AEA-17 | **main** (`0a85270`) | `AnthropicAdapter(client: anthropic.Anthropic, *, model: str)`, `model="claude-sonnet-5-5"`. Test client: `anthropic.Anthropic(api_key=<placeholder>, max_retries=0, open_telemetry=False, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)))` (the shape of `tests/contract/_anthropic_fixtures.adapter_for`, which uses `max_retries=2`; use 0 here). `structured` sends `output_config.format = {"type": "json_schema", "schema": anthropic.transform_schema(req.output_model)}` and reads the text with `output_model.model_validate_json`; `stop_reason` `"refusal"` / `"max_tokens"` → `REFUSAL` / `MAX_TOKENS` before any parsing; any parse or validation error after the response arrived → `INVALID_OUTPUT` (catch-all; nothing bound or logged); `choose` needs a text block whose JSON keys equal the field names exactly; `tool_step` sends each `ToolSchema` with `"strict": True` and maps `tool_use` blocks to `ToolCall(id, name, args)` with `args=None` when `input` is not a dict; `start(user)` / `append(...)` make it the `ToolTranscript` |
| `meridian.agent.context`: `GraphDeps` | AEA-21 | **main** (`5531664`) | frozen dataclass, fields in order `gateway, retrieval, uow, identity, scheduling, handoff, brief, demo, limits, trace, specialists, cases, ledger` (the service fields are typed `Any` until AEA-51) |
| `meridian.agent.signals`: `SIGNAL_LOGGER` | AEA-21 | **main** | `SIGNAL_LOGGER = "meridian.signal"`; `emit_signal` logs `logging.getLogger(SIGNAL_LOGGER).info("signal", extra={"signal": record.model_dump(mode="json")})`, so the `LogRecord` carries attribute `signal` (a dict) |
| `meridian.agent.nodes.compose`: `ReplyComposer` | AEA-21 | **main** | `ReplyComposer().compose(state, ctx) -> ComposedReply`; with `state.checked.fallback_used` → path `"degraded"`, outcome `"degraded_handoff"`, `degrade_reason="model_error"`, and a `FailureOfferBlock` (`type="failure_offer"`, `person_key=True`) |
| `meridian.agent.nodes.reply`: `responder`, `brief`, `checks`; module attribute `check_quotes` | AEA-38 | **main** (`042ad35`) | `fn(state, runtime, *, deps) -> update`. `responder` raises `RuntimeError` unless `state.facts` and `state.settled` are set; on a failure it returns `{"draft": None}` and emits `responder_fallback` (node `"responder"`, role `"responder"`, cause = failure kind, `attempt=len(outcome.calls)`). `brief`: `deps.cases.open_case_for_thread(thread_id)` returning `None` → `{"brief_extraction": None}`; else, in one `deps.uow()`, `tx.core.lookup_log.for_thread(thread_id)` and `tx.core.messages.recent(thread_id, turns=deps.limits.context.window_turns)`; then `deps.cases.attach_brief(case.case_ref, deps.brief.assemble(case, state, lookups))`; `shown = brief_shown([(r.id, r.text) for r in rows if r.role == "customer"], deps.limits.context.window_line_chars)`; `Role.BRIEF` call; a failure → `brief_failed` (node `"brief"`, cause = failure kind) and `{"brief_extraction": None}`. `checks`: brief path only when `state.handoff is not None and state.handoff.created`; `state.draft is None` → `CheckedReply(text="", fallback_used=True)` with `completion` and `fact` events `result="fallback"`; extraction `None` → `deps.brief.attach_extraction(draft_brief, None, None)`; else it rebuilds the same `shown`, calls `check_quotes(ext, shown)` (imported into this module by name, so `MonkeyPatch.setattr(meridian.agent.nodes.reply, "check_quotes", spy)` intercepts it), then `attach_extraction(draft_brief, kept, facts_check)` and adds `brief_quote` and `brief_fact` events (`CheckEvent.from_check`: `"trimmed"` when there are removals, `removed=len`, `claim_kinds` = sorted removal kinds, `codes=()`). `attach_brief` is called once in `brief` and once in `checks` (so `CasesDouble.attached` has 2 entries on a brief turn) |
| `meridian.agent.prompts.reply`: `LABEL_THIS_TURN`, `LABEL_SETTLED`, `brief_shown` | AEA-38 | **main** | `LABEL_THIS_TURN = "WHAT HAPPENED THIS TURN"`, `LABEL_SETTLED = "ALREADY DONE IN THIS CONVERSATION"` (both rendered in the responder's `system_dynamic`); `brief_request(case, shown).user == "CUSTOMER MESSAGES:\n" + "\n".join(f"[message {mid}] {text}" for mid, text in shown.items())`, which `prompts_compare.BRIEF_LINE` parses; `output_model` is `ResponderDraft` / `BriefExtraction`. `brief_shown` applies `RedactionProfile.SONNET` and cuts each line to `window_line_chars` |
| `meridian.services.handoff`: `BriefAssembler` | AEA-29 | **main** (`ef561fc`) | `BriefAssembler(staff_guidance: Mapping[PassageId, StaffGuidance] \| None = None)`; `assemble(case: CaseSummary, state: ConversationState, lookups: Sequence[LookupRow]) -> Brief` (pure; `status="being_written"`; headings 2 and 4 start empty); `attach_extraction(brief: Brief, extraction: BriefExtraction \| None, check: CheckResult \| None, *, customer_messages: Mapping[int, str] \| None = None) -> Brief`: `extraction is None` → headings 2, 4, 7 `not_generated=True` and `status="failed"`; otherwise `status="ready"`. The reply node never passes `customer_messages`. `CaseService(uow, clock, *, handoff_block=None, settled_view=None)` (`meridian.services.cases`) is **not** used here (PD-9) |
| `meridian.agent.tools.account`: `account_tools` | AEA-27 | **main** (`13adc86`) | `account_tools(uow) -> tuple[ToolDef, ...]`: `read_invoices` (`ReadInvoicesArgs.invoice_number`), `read_membership`, `read_warranty`; kind `account_read`, `requires_verified=True` |
| `meridian.agent.tools.scheduling`: `scheduling_tools` | AEA-28 | **main** (`2c2e8c5`) | `scheduling_tools(scheduling: SchedulingService) -> tuple[ToolDef, ...]`; on `main` the names are `find_windows`, `book_visit`, `move_visit`, `cancel_visit`, `request_visit_change`. **Still read them from the registry, never hard-code them.** The factory only closes over the service, so `SchedulingDouble` (raises on any method other than `slice_inputs`) is enough |
| `meridian.agent.prompts.routing`: `DANGER_FIELD` | AEA-37 | **branch** `aea-37-graph-plan-node` at `36dc321` (built, not merged) | `DANGER_FIELD = "danger_level"`. `planner_request(PlannerInput)` and `classifier_request(latest: str)` build the requests (system text and fields are module constants, identical every turn); the classifier system text quotes `"normal"`, the planner's quotes `"none"` and `"no"` (all are options, so `check_wording_keys` passes) |
| `meridian.agent.nodes.plan`: `planner`, `danger_classifier`, `plan_join`, `join_plan` | AEA-37 | **branch** `36dc321`; `main` has the AEA-21 stubs that raise `NotImplementedError` | `join_plan(planner: PlannerOutcome \| None, danger: DangerAssessment \| None, gate: GateDecision, state: ConversationState, *, tasks_per_turn: int = 3) -> Plan`. Branch behaviour AC-7 asserts: a Jev failure → one `Role.PLANNER_FALLBACK` call with the same request; signal `planner_fallback` (node `"planner"`, role `"planner"`, cause = the Jev failure kind, `recovered` = the fallback parsed); outcome `fallback_used=True`, `failure` = the fallback's failure or `None`. A classifier failure or unknown label → `DangerAssessment(label="normal", raised=False, failure=<the failure, or INVALID_OUTPUT>)`, signal `classifier_fallback` (node `"danger_classifier"`, role `"classifier"`, `recovered=None`) and `check_events=(CheckEvent.from_danger(turn_id, danger),)`. `planner_failed = planner is not None and choices is None and not drafts and handoff_request is None` |
| `meridian.agent.specialists.specs`: `SPECS`, `REPORT_FACTS_TOOL` (`"report_facts"`) | AEA-35 | **plan only** (no branch; AEA-35's plan is NEEDS-DECISION, §8 R-10) | `SPECS: Mapping[SpecialistKind, SpecialistSpec]`; `SpecialistSpec.tool_kinds: frozenset[ToolKind]`, `.report_model`; `report_facts` is sent with `spec.report_model.model_json_schema()` untrimmed (AEA-35 PD-9; PD-8 here accepts either form) |
| `meridian.agent.specialists.runner`: `SpecialistRunner` | AEA-35 | **plan only** | `SpecialistRunner(*, gateway, transcript, dispatcher, specs, brakes, trace)`; `transcript` = the SAME object as the gateway's `Role.SPECIALIST` adapter |
| `meridian.agent.nodes.act`: `run_specialist`, `escalation` | AEA-39 | **plan only** (no branch; same NEEDS-DECISION as AEA-35); `main` has the stubs | `run_specialist(payload: SpecialistSend, runtime, *, deps)` reads `deps.scheduling.slice_inputs(customer_id)` for a verified scheduling task and emits `specialist_failed` (cause = failure kind, or `"tool_error"`); `escalation(state, runtime, *, deps) -> {"escalation": EscalationDecision}` wraps `meridian.policy.escalation.decide_escalation` (on `main`: `AI.planner_failed` / `AI.specialist_failed` → `ai_failure`, `degraded=True`, priority from `priority_for` = P3) |

On `main` and unchanged since the first plan (checked again): `ToolRegistry`, `ToolDispatcher` (incl. `_strip_titles`,
lines 78-93, which `prompts_compare.strip_titles` mirrors), `KB_SEARCH_NAME`, `KbSearchArgs`, `ModelGateway` (the span's
`masked_output` for a tool step holds the tool-call args; its `masked_input` holds only the system text and tool names,
never the transcript, so PD-7 stands), `RecordingLedger`, `spec`, `default_specs`, the AEA-11 fakes, `decide_escalation`,
`priority_for`, `promise_for`, and the `turns`, `cases` (`rule_id` column present) and `check_events` table columns the
journeys read.

---

## 5. Steps

### 5.0 Decisions made here (PD-n)

| ID | Decision | Basis |
|---|---|---|
| PD-1 | Helper modules `tests/contract/prompts_{compare,world,render,wire,cases}.py` beside the test, no sub-package, no conftest | AEA-59 precedent; test hard cap 500 lines (`code-structure.md`) |
| PD-2 | Rendering = run the **real nodes** with a **real `ModelGateway`** whose adapters are AEA-11 recording fakes; the request captured is the one the model port receives (after the gateway's redaction). One fresh `temp_sqlite()` per rendered turn (1, 2, 5); computed once per module (`scope="module"` fixture) | ticket step 1 ("captured from a recording gateway double that honours DO-4 §12") |
| PD-3 | The rendering world uses `Limits(brakes=Brakes(sonnet_calls=12))` because one rendered turn makes 6 Sonnet calls (fallback, 3 specialists, responder, brief) in one `TurnContext`; the brake is not under test here. The malformed-case worlds use `Limits()` unchanged | gateway rule 3 (models.md §5) |
| PD-4 | An "option key named in the wording" = a double-quoted lowercase token `"[a-z][a-z_]*"` in `ChoiceRequest.system` or a field's `instructions` (SP-1 wording quotes keys: `Choose "none" or "no"`, `Choose "normal"`) | AC-2 |
| PD-5 | A "tool name the specialist wording mentions" = any snake_case token (`\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b`) in that specialist's `system_prefix + "\n" + system_dynamic` that is **not** in the specialist vocabulary (property names and enum/const strings of `SchedulingSlice`, the three report models and every registry args model, all depths incl. `$defs`). Each such token must be a tool sent with that request. The user message (task text + slice JSON) is data, not wording, and is not scanned | AC-5; vocabulary is derived from code, so it grows with the types |
| PD-6 | AC-4's code-only check applies to every option of the **planner** and **planner_fallback** requests. The classifier's `danger_level` options are `DangerAssessment.label` values (AC-2 requires exactly `normal, burning_unclear, danger`), not `HandoffReason`s, so they are excluded. Forbidden field names for tools, `report_facts` and reply output models: `{"priority", "case_ref", "case_reference", "reference", "promise", "promise_text", "due_at", "customer_id"}` | AC-2 vs AC-4 literal overlap |
| PD-7 | AC-10: markers are placed **only** in values a consumer rejects. `zq-rejected-option-7731` and `zq-rejected-draft-7731` are rejected by the adapter (value `None`), so they must be absent from **every** record incl. trace spans. The 301-char query is rejected later by **dispatch**, after a schema-valid tool step; DO-6 line 113 requires the specialist `model_call` span to hold "the raw output after masking", so `…zq-rejected-query-7731` is asserted **present** in exactly that span's `masked_output` and absent from everything else (incl. `ToolError.message`, `ToolCallRecord`, lookup rows, logs, signals, node spans, the DB). The brief marker goes in the schema-invalid 6-claims extraction | DO-4 §0 ("errors never carry values") vs DO-6 (signed); ticket's expected-answer authority is the signed contracts |
| PD-8 | `report_facts` schema passes when it equals `spec.report_model.model_json_schema()` **or** its title-stripped form (AEA-35 PD-9 sends the untrimmed one; both are generated from the report model) | AC-5 |
| PD-9 | (refresh 2) `GraphDeps.brief` = `RecordingBriefAssembler`: the **real** AEA-29 `BriefAssembler` (on `main`, pure), subclassed only to record `attach_extraction` calls. AC-9's headings 2, 4, 7 `not_generated` and `status="failed"` are asserted on its real output. `GraphDeps.cases` = `CasesDouble` (the two methods the reply node calls, DO-4 §13; it must never raise, because `_store_brief` would turn that into a `brief_failed` `write_error` signal): the real `CaseService` needs a case opened through `HandoffService`, which is AEA-51's integration. `identity`, `handoff`, `demo` are `Unused` sentinels that fail loudly if touched | the ticket's `brief` row names `BriefAssembler.attach_extraction` as a consumer; AEA-29 merged at `ef561fc`; slice plan rule 1 for `CaseService` |
| PD-10 | Unit tests feed raw **HTTP** bodies through `httpx.MockTransport` (Jev) and `httpx2.MockTransport` (Anthropic). Journeys use AEA-57's scripted adapter, which takes the raw **output text** per role and parses it like the adapters (`tests/journeys/support/scripted_model.py`), so no AEA-57 follow-up is needed | ticket AC-13; AEA-57 docstring |
| PD-11 | One case table `MALFORMED_CASES` (in `prompts_cases.py`) feeds AC-7, AC-8, AC-9 (outcomes), AC-14 (records) and AC-10 (markers). Each test re-runs its cases in a fresh world (cheap: the issued DB is 115 KB) | one source of truth for cases |
| PD-12 | AC-12: one process-wide audit hook added once and gated by a module flag (audit hooks cannot be removed); a module-scoped autouse fixture turns it on and patches `socket.socket.connect`/`connect_ex`; a function-scoped autouse fixture fails any test that added a held-out open or a connect; the named test proves both guards are live | `sys.addaudithook` semantics; xdist splits a module across workers |
| PD-13 | J-5 scripts the planner as a booking (`scheduling="book_new"`) and asserts invariants that do not depend on the identity path's later wording (no safety block, no case, `gate_result="clear"`, the one `classifier` `fallback` event, plan intent `book_new` stored) | "books normally" while identity is AEA-36's |
| PD-14 | Fixture conversation (dev data only): turns 1–2 WP-3, 3–4 WP-1, 5 WP-7 (exact texts §6.1). Rendered turns are 1, 2 and 5 | ctx-mgmt rule 3; AC-6 "WP-7's refund turn" |

### 5.1 Step 0 — setup and blocker check (stop if red)

1. In the worktree: `export UV_LINK_MODE=hardlink && uv sync` (never copy a venv; no `node_modules`).
2. Run exactly:
   ```bash
   uv run python -c "import meridian.adapters.models.openrouter_jev, meridian.adapters.models.anthropic, \
   meridian.agent.context, meridian.agent.signals, meridian.agent.nodes.compose, meridian.agent.nodes.plan, \
   meridian.agent.nodes.act, meridian.agent.nodes.reply, meridian.agent.prompts.routing, meridian.agent.prompts.reply, \
   meridian.agent.prompts.specialists, meridian.agent.specialists.specs, meridian.agent.specialists.runner, \
   meridian.agent.tools.account, meridian.agent.tools.scheduling, meridian.services.handoff; \
   from meridian.agent.nodes.plan import planner, danger_classifier, plan_join, join_plan; \
   from meridian.agent.nodes.act import run_specialist, escalation; \
   from meridian.agent.nodes.reply import responder, brief, checks; \
   from meridian.agent.specialists.specs import SPECS; print(sorted(SPECS))"
   ```
   Expect `['account', 'knowledge', 'scheduling']`. Any `ImportError` or `NotImplementedError` stub → stop and report
   `BLOCKED-ON <owning ticket>` (map: adapters 17/18; context/signals/compose 21; plan 37; act 39; reply 38;
   specs/runner/prompts.specialists 35; tools.account 27; tools.scheduling 28). On `c9b17ea` exactly AEA-35's, 37's and
   39's names fail; every other module imports.
3. Open and read (do not edit) the §4.3 modules on `main`; note every name that differs from §4.3 for your report.

### 5.2 Step 1 — `tests/contract/prompts_world.py` (ids, conversation, seeding, doubles, builders)

Module docstring: "AEA-60 shared world: fixture conversation (WP-3, WP-1, WP-7, NODANGER), DB seeding, doubles for
AEA-29/28 services and context builders. Development data only."

Constants (exact):
```python
NOW = WORKED_PAIRS_NOW                                   # Fri 2026-10-16 10:00 America/Chicago
THREAD = ThreadId("6f1c2d3e-4b5a-4c6d-8e7f-0a1b2c3d4e50")
REQUEST = RequestId("3c4d5e6f-7a8b-4c9d-8e0f-2a3b4c5d6e50")
TURN_IDS: Mapping[int, TurnId] = MappingProxyType({n: TurnId(f"7d2e3f40-5b6c-4d7e-9f80-1a2b3c4d5e{n:02d}") for n in range(1, 6)})
#   letters in every group: no 13–19 digit run, so the SONNET card rule never fires on an id (AEA-35 lesson)
AGENT_VERSION = "test-aea60"; DEMO_SESSION = "demo-aea60"
VERIFIED_CUSTOMER = CustomerId("MHC-10001")              # issued DB: Standard member (WP-3, WP-8)
TURNS: tuple[str, ...] = (                                # PD-14; index 0 = turn 1
    "I need to schedule a service call. My AC isn't cooling.",                                     # WP-3
    "This Saturday if possible, 4 to 7, after work.",                                              # WP-3
    "What does the Comfort Club membership actually include?",                                     # WP-1
    "And how much is it?",                                                                         # WP-1
    "I want a full refund on the repair. It didn't fix anything and I had to call another company.",  # WP-7
)
REPLIES: tuple[str, ...] = (                              # assistant lines after turns 1..4 (generated in the test)
    "I can help book a visit. Which days and times work for you?",
    "Let me check the open windows for you.",
    "The Comfort Club includes two tune-ups a year.",
    "Let me look that up.",
)
NODANGER = "my AC isn't cooling"                         # DO-5 line 61
STAFF_LINE = "Riley here, I am looking at your repair notes now."
WP1_PASSAGES: tuple[Passage, ...] = (
    Passage(passage_id=PassageId("membership/comfort_club_overview.md#0"), file="membership/comfort_club_overview.md",
            section="What's included", version_label="Effective 2026-01-01", version_date=date(2026, 1, 1),
            text="Comfort Club members get two seasonal tune-ups a year and priority scheduling.", score=0.82),
    Passage(passage_id=PassageId("membership/comfort_club_overview.md#1"), file="membership/comfort_club_overview.md",
            section="Price", version_label="Effective 2026-01-01", version_date=date(2026, 1, 1),
            text="The Comfort Club costs a monthly fee with a 12-month minimum.", score=0.78),
)
UNVERIFIED = IdentityState(status="not_checked", customer_id=None, masked_hint=None, code_expires_at=None,
                           tries_left=3, codes_sent=0, verified_at=None)
VERIFIED = IdentityState(status="verified", customer_id=VERIFIED_CUSTOMER, masked_hint="the phone ending in 01",
                         code_expires_at=None, tries_left=3, codes_sent=1, verified_at=NOW)
```

Functions and classes (exact signatures; bodies as described):

```python
@dataclass(frozen=True)
class Seeded:
    customer_ids: Mapping[int, int]      # turn number → messages.id of the customer line
    assistant_ids: Mapping[int, int]     # turn number → messages.id of the assistant line after it
    staff_id: int | None                 # the representative line, when seeded

def seed_conversation(store: TempStore, texts: Sequence[str], *, upto: int, staff_after: int | None = None) -> Seeded:
    # One write tx: conversations.insert(ConversationRow(thread_id=THREAD, demo_session=DEMO_SESSION, run_tag="live",
    #   agent_version=AGENT_VERSION, started_at=NOW)); for n in 1..upto: customer line
    #   messages.append(THREAD, "customer", redact(texts[n-1], RedactionProfile.STORE).text, at_of(n), turn_id=TURN_IDS[n], kind="text");
    #   for n < upto: assistant line messages.append(THREAD, "assistant", REPLIES[n-1], at_of(n) + 30 s, turn_id=TURN_IDS[n]);
    #   when staff_after == n: messages.append(THREAD, "representative", STAFF_LINE, at_of(n) + 40 s)  (turn_id None).
    #   tx.commit(). Invariant: the DB holds exactly the conversation up to turn `upto` (no future lines), so
    #   messages.recent() and the brief's shown mapping see what turn `upto` would see.

def at_of(n: int) -> datetime: return NOW + timedelta(minutes=n)

def chat_window(texts: Sequence[str], upto: int) -> list[ChatLine]:
    # customer + assistant ChatLines for turns 1..upto-1, in order (texts STORE-redacted as stored); never turn `upto`.

def free_text_gate() -> GateDecision:
    return GateDecision(kind=GateKind.FREE_TEXT, rules=RuleMatches(safety=None, burning_unclear=False, danger_words=False,
                        person=False, policy_trigger=None, rule_ids=(), correction=False))

def make_state(texts: Sequence[str], seeded: Seeded, n: int, *, identity: IdentityState = UNVERIFIED,
               **update: Any) -> ConversationState:
    # ConversationState(thread_id=THREAD, settled=Settled(actions=(), open_case=None, read_at=at_of(n)), identity=identity,
    #   turn_input=TurnInput(turn_id=TURN_IDS[n], message_id=seeded.customer_ids[n], kind="text",
    #   text_store=redact(texts[n-1], RedactionProfile.STORE).text, received_at=at_of(n)),
    #   chat_window=chat_window(texts, n), gate=free_text_gate()).model_copy(update=update)

@contextmanager
def open_turn(sink: InMemoryTraceSink, n: int) -> Iterator[TurnContext]:
    # ids = TurnIds(thread_id=THREAD, turn_id=TURN_IDS[n], request_id=REQUEST, run_tag="live", run_id=None, agent_version=AGENT_VERSION)
    # with sink.turn(ids) as span: t0 = time.monotonic(); yield TurnContext(ids=ids, budget=TurnBudget(started=t0,
    #   deadline=t0 + 60.0), now=at_of(n), demo_session=DEMO_SESSION, span=span, intake=None)

def runtime(ctx: TurnContext) -> Runtime[TurnContext]: return Runtime(context=ctx)

def facts_for(n: int, *, handoff: HandoffResult | None) -> TurnFacts:
    # TurnFacts(turn_id=TURN_IDS[n], gate_kind=GateKind.FREE_TEXT, plan_mode="talk", points=(), passages=(),
    #   no_source_tasks=(), windows_shown=(), writes_this_turn=(), change_request=None, handoff=handoff, escalation=None,
    #   identity_step=None)   # if main's TurnFacts gained required fields, pass their empty values and report it

def refund_case(n: int) -> CaseSummary:
    # CaseSummary(case_ref=CaseRef("MHC-C-0001"), reason=HandoffReason.REFUND, priority=Priority.P3, state="unassigned",
    #   created_at=at_of(n), promise=promise_for(HandoffReason.REFUND, "nobody_online", at_of(n)), followup=None,
    #   version=1, due_at=None)

def refund_handoff(n: int) -> HandoffResult:
    # HandoffResult(case=refund_case(n), created=True, action=CompletedAction(key=ActionKey(thread_id=THREAD,
    #   turn_id=TURN_IDS[n], kind=ActionKind.CASE_OPENED, record_id="MHC-C-0001"), kind=ActionKind.CASE_OPENED,
    #   records={"case": "MHC-C-0001"}, at=at_of(n)), alert=None)

class CasesDouble:            # GraphDeps.cases (AEA-29 CaseService): the two methods the reply node calls (DO-4 §13)
    def __init__(self, case: CaseSummary | None) -> None: self.case = case; self.attached: list[Brief] = []
    def open_case_for_thread(self, thread_id: ThreadId) -> CaseSummary | None: return self.case
    def attach_brief(self, case_ref: CaseRef, brief: Brief) -> None: self.attached.append(brief)

class RecordingBriefAssembler(BriefAssembler):   # GraphDeps.brief: the REAL AEA-29 assembler (refresh 2, PD-9)
    """The real BriefAssembler; records each attach_extraction call and adds no behaviour."""
    def __init__(self) -> None:
        super().__init__(None)
        self.attach_calls: list[tuple[Brief, BriefExtraction | None, CheckResult | None]] = []
    def attach_extraction(self, brief: Brief, extraction: BriefExtraction | None, check: CheckResult | None, *,
                          customer_messages: Mapping[int, str] | None = None) -> Brief:
        self.attach_calls.append((brief, extraction, check))
        return super().attach_extraction(brief, extraction, check, customer_messages=customer_messages)
    # assemble(...) is inherited unchanged. Imports: BriefAssembler from meridian.services.handoff; CheckResult from
    # meridian.domain.turn; Brief, BriefExtraction from meridian.domain.handoff. The override signature is copied from
    # main; keep it identical so mypy accepts the override.

class SchedulingDouble:       # GraphDeps.scheduling + scheduling_tools(...) argument (AEA-28, cases.md §4)
    def slice_inputs(self, customer_id: CustomerId) -> SchedulingSliceInputs:
        return SchedulingSliceInputs(zone="north", member=True, appointments=())
    def __getattr__(self, name: str) -> Any: raise AssertionError(f"SchedulingService.{name} is not called by AEA-60")

class Unused:                 # GraphDeps.identity / handoff / demo
    def __init__(self, label: str) -> None: self._label = label
    def __getattr__(self, name: str) -> Any: raise AssertionError(f"GraphDeps.{self._label}.{name} is not used by AEA-60")

def build_registry(index: FakeIndex, store: TempStore) -> ToolRegistry:
    return ToolRegistry((*knowledge_tools(index), *account_tools(store.uow), *scheduling_tools(SchedulingDouble())))

def build_deps(*, gateway: ModelGateway, index: FakeIndex, store: TempStore, sink: InMemoryTraceSink,
               runner: SpecialistRunner, cases: CasesDouble, brief: RecordingBriefAssembler, ledger: RecordingLedger,
               limits: Limits) -> GraphDeps:
    # GraphDeps(gateway=gateway, retrieval=index, uow=store.uow, identity=Unused("identity"), scheduling=SchedulingDouble(),
    #   handoff=Unused("handoff"), brief=brief, demo=Unused("demo"), limits=limits, trace=sink, specialists=runner,
    #   cases=cases, ledger=ledger)

def signals(records: Sequence[logging.LogRecord]) -> list[dict[str, Any]]:
    return [cast(dict[str, Any], getattr(r, "signal")) for r in records if r.name == SIGNAL_LOGGER and hasattr(r, "signal")]

@contextmanager
def capture_logs() -> Iterator[list[logging.LogRecord]]:
    # a logging.Handler subclass appending every record to a list, added to the ROOT logger with level DEBUG; the root
    # logger's level set to INFO for the block and restored in `finally` (handler removed in `finally` too).
```

Check: `uv run ruff check tests/contract/prompts_world.py && uv run mypy tests/contract/prompts_world.py`.

### 5.3 Step 2 — `tests/contract/prompts_compare.py` (pure; no I/O)

```python
class PromptDrift(AssertionError):
    """A rendered prompt and its consumer disagree. Messages name role, field and value; never customer text."""

CODE_ONLY: Final[frozenset[str]] = frozenset({"safety", "danger", "burning_unclear", "customer_requested_person",
    "legal_or_chargeback", "commercial", "fee_bearing_change", "identity_unverified", "ai_failure", "burning_ruled_out"})
FORBIDDEN_FIELDS: Final[frozenset[str]] = frozenset({"priority", "case_ref", "case_reference", "reference", "promise",
    "promise_text", "due_at", "customer_id"})
SCOPE_FIELDS: Final[frozenset[str]] = frozenset(ToolCallScope.model_fields)     # ids, customer_id, shown_slot_ids, now, message_id
TOOL_NAME: Final = re.compile(r"[a-z_]{1,64}")
QUOTED_KEY: Final = re.compile(r'"([a-z][a-z_]*)"')
SNAKE: Final = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
BRIEF_LINE: Final = re.compile(r"^\[message (\d+)\] (.*)$", re.M)
LABELS: Final = (LABEL_THIS_TURN, LABEL_SETTLED)   # imported from meridian.agent.prompts.reply (AEA-38, on main)

def literal_values(model: type[BaseModel], field: str) -> tuple[str, ...]:
    return tuple(str(v) for v in typing.get_args(model.model_fields[field].annotation))

def strip_titles(node: Any) -> Any:
    # EXACT mirror of meridian.agent.tools.dispatch._strip_titles (main lines 78-93): drop key "title" when its value is
    # a str; recurse into the values of "properties" and "$defs" by name; copy "default", "examples", "const", "enum"
    # unchanged; recurse into every other dict value and list item.

def schema_names(schema: Any) -> set[str]:        # every key under any "properties" mapping, all depths (incl. $defs)
def schema_vocabulary(*schemas: Mapping[str, Any]) -> set[str]:
    # schema_names(each) ∪ every str in any "enum" list ∪ every str "const" value, all depths

def check_choice_fields(role: str, request: ChoiceRequest, consumer: type[BaseModel],
                        field_map: Mapping[str, str] | None = None) -> None:
    # 1. mapping = field_map or {name: name for name in consumer.model_fields}
    # 2. sent = [f.name for f in request.fields]; if set(sent) != set(mapping):
    #      raise PromptDrift(f"routing.{role} fields {sorted(sent)} differ from {consumer.__name__} fields {sorted(mapping)}")
    # 3. for f in request.fields: cfield = mapping[f.name]; accepted = literal_values(consumer, cfield)
    #      if len(f.options) > 255: raise PromptDrift(f"routing.{role}.{f.name} offers {len(f.options)} options; Jev allows 255")
    #      for key in f.options (insertion order): if key not in accepted:
    #          raise PromptDrift(f"routing.{role}.{f.name} offers '{key}'; {consumer.__name__}.{cfield} does not accept it")
    #      for value in accepted: if value not in f.options:
    #          raise PromptDrift(f"{consumer.__name__}.{cfield} accepts '{value}'; routing.{role}.{f.name} does not offer it")
    #    Invariant: forward direction is checked before the reverse one (the ticket's example message).

def check_wording_keys(role: str, request: ChoiceRequest) -> None:
    # keys = set().union(*(f.options for f in request.fields)); for text in (request.system, *(f.instructions for f in request.fields)):
    #   for k in QUOTED_KEY.findall(text): if k not in keys:
    #     raise PromptDrift(f"routing.{role} wording names option '{k}'; no field of the request offers it")

def check_code_only(role: str, request: ChoiceRequest) -> None:
    # for f in request.fields: for key in f.options: if key in CODE_ONLY:
    #   raise PromptDrift(f"routing.{role}.{f.name} offers code-only value '{key}'")

def check_no_forbidden_fields(where: str, schema: Mapping[str, Any]) -> None:
    # bad = sorted(schema_names(schema) & FORBIDDEN_FIELDS); if bad: raise PromptDrift(f"{where} lets the model set '{bad[0]}'")

def check_specialist(kind: str, request: ToolStepRequest, *, registry: ToolRegistry, expected_tools: Sequence[ToolSchema],
                     tool_kinds: frozenset[ToolKind], report_model: type[BaseModel], vocabulary: set[str]) -> None:
    # 1. names = [t.name for t in request.tools]; want = [t.name for t in expected_tools] + ["report_facts"]
    #    names != want → PromptDrift(f"specialist.{kind} sends tools {names}; expected {want}")
    # 2. registry.get("report_facts") is not None → PromptDrift("registry holds a tool named 'report_facts'")
    # 3. registry.check_covers(tool_kinds)  (ValueError propagates as a test failure)
    # 4. for t in request.tools[:-1]: d = registry.get(t.name)
    #    d is None → PromptDrift(f"specialist.{kind} sends '{t.name}'; ToolRegistry.get does not resolve it")
    #    not TOOL_NAME.fullmatch(t.name) → PromptDrift(f"specialist.{kind} tool '{t.name}' is not [a-z_]{{1,64}}")
    #    d.kind not in tool_kinds → PromptDrift(f"specialist.{kind} sends '{t.name}' of kind {d.kind.value}, not in its tool kinds")
    #    t.strict is not True → PromptDrift(f"specialist.{kind} tool '{t.name}' is not strict")
    #    t.input_schema != strip_titles(d.args_model.model_json_schema()) →
    #        PromptDrift(f"specialist.{kind} tool '{t.name}' schema differs from {d.args_model.__name__}")
    #    schema_names(t.input_schema) & SCOPE_FIELDS → PromptDrift(f"specialist.{kind} tool '{t.name}' exposes scope field '{x}'")
    #    check_no_forbidden_fields(f"specialist.{kind} tool '{t.name}'", t.input_schema)
    # 5. rf = request.tools[-1]; full = report_model.model_json_schema()
    #    rf.input_schema not in (full, strip_titles(full)) → PromptDrift(f"specialist.{kind} report_facts schema differs from {report_model.__name__}")   (PD-8)
    #    check_no_forbidden_fields(f"specialist.{kind} report_facts", rf.input_schema)
    # 6. wording = request.system_prefix + "\n" + request.system_dynamic; sent = set(names)
    #    for token in sorted(set(SNAKE.findall(wording)) - vocabulary): if token not in sent:
    #        raise PromptDrift(f"specialist.{kind} wording names '{token}'; it is not a tool sent with it")

def check_reply_schema(role: str, request: StructuredRequest[Any], expected: type[BaseModel]) -> None:
    # got = request.output_model
    # extra = sorted(set(got.model_fields) - set(expected.model_fields)) → first: PromptDrift(f"{role}.output_model has field '{extra[0]}'; {expected.__name__} does not")
    # got is not expected → PromptDrift(f"{role}.output_model is {got.__name__}; expected {expected.__name__}")
    # check_no_forbidden_fields(f"{role}.output_model", got.model_json_schema())

def parse_brief_user(user: str) -> dict[int, str]: return {int(m.group(1)): m.group(2) for m in BRIEF_LINE.finditer(user)}

def check_brief_ids(rendered: Mapping[int, str], shown: Mapping[int, str], customer_ids: AbstractSet[int]) -> None:
    # for mid in rendered: mid not in customer_ids → PromptDrift(f"brief shows message {mid} that is not a customer message of this thread")
    # set(rendered) != set(shown) → PromptDrift(f"brief shows messages {sorted(rendered)}; check_quotes compares {sorted(shown)}")
    # for mid in rendered: rendered[mid] != shown[mid] → PromptDrift(f"brief message {mid} text differs from what check_quotes compares")

def check_inventory(roles: Iterable[str], kinds: Iterable[str], have_roles: AbstractSet[str], have_kinds: AbstractSet[str]) -> None:
    # role not in have_roles → PromptDrift(f"role '{role}' has no rendered case"); kind → f"specialist kind '{kind}' has no rendered case"
```

Check: `uv run ruff check tests/contract/prompts_compare.py && uv run mypy tests/contract/prompts_compare.py`.

### 5.4 Step 3 — `tests/contract/prompts_wire.py` (raw bodies, stubbed transports, real adapters, real gateway)

```python
JEV_MODEL: Final = "typesafe/jev-1.13"; SONNET_MODEL: Final = "claude-sonnet-5-5"
Body = dict[str, Any] | bytes          # dict → HTTP 200 JSON; bytes → HTTP 200 with that raw content (non-JSON allowed)

@dataclass
class Wire:
    bodies: list[Body]
    requests: list[dict[str, Any]] = field(default_factory=list)   # json.loads(request.content) of each request
    exhausted: int = 0
    def _next(self, content: bytes) -> tuple[int, bytes, dict[str, str]]:
        # append json.loads(content); if no body left: exhausted += 1 and return (500, b'{"error":"aea60 script exhausted"}', h)
        # dict → (200, json.dumps(body).encode(), h); bytes → (200, body, h); h = {"content-type": "application/json",
        #   "request-id": "req_aea60test01"}
    def httpx_handler(self, request: httpx.Request) -> httpx.Response: status, content, h = self._next(request.content); return httpx.Response(status, content=content, headers=h)
    def httpx2_handler(self, request: httpx2.Request) -> httpx2.Response: same with httpx2.Response

def jev_adapter(wire: Wire) -> JevAdapter:
    return JevAdapter(httpx.Client(transport=httpx.MockTransport(wire.httpx_handler)),
                      api_key=SecretStr("or-test-" + secrets.token_hex(8)), model=JEV_MODEL)
def anthropic_adapter(wire: Wire) -> AnthropicAdapter:
    client = anthropic.Anthropic(api_key="sk-test-" + secrets.token_hex(8), max_retries=0, open_telemetry=False,
                                 http_client=httpx2.Client(transport=httpx2.MockTransport(wire.httpx2_handler)))
    return AnthropicAdapter(client, model=SONNET_MODEL)

def jev_body(choices: Mapping[str, str]) -> dict[str, Any]:
    return {"id": "gen-aea60", "answers": {k: {"type": "choice", "choice": v} for k, v in choices.items()},
            "usage": {"input_tokens": 300, "output_tokens": 0, "cost": 1.26e-05}}
def message(content: list[dict[str, Any]], *, stop_reason: str = "end_turn") -> dict[str, Any]:
    return {"id": "msg_aea60", "type": "message", "role": "assistant", "model": SONNET_MODEL, "content": content,
            "stop_reason": stop_reason, "stop_sequence": None, "usage": {"input_tokens": 100, "output_tokens": 20}}
def text_message(text: str, *, stop_reason: str = "end_turn") -> dict[str, Any]: return message([{"type": "text", "text": text}], stop_reason=stop_reason)
def tool_use(call_id: str, name: str, args: object) -> dict[str, Any]: return {"type": "tool_use", "id": call_id, "name": name, "input": args}
def tool_message(*blocks: dict[str, Any]) -> dict[str, Any]: return message(list(blocks), stop_reason="tool_use")

VALID_PLAN: Final[Mapping[str, str]] = MappingProxyType({"knowledge": "no", "account": "none", "scheduling": "book_new",
                                                          "handoff": "none", "topic": "booking"})   # NODANGER booking
def raw_specs() -> dict[Role, RoleSpec]:
    # PLANNER, CLASSIFIER: spec(cap_s=3.0, redaction=RedactionProfile.JEV, model=JEV_MODEL, effort=None)
    # PLANNER_FALLBACK: spec(cap_s=8.0, redaction=RedactionProfile.SONNET, model=SONNET_MODEL)
    # RESPONDER, BRIEF: spec(cap_s=12.0, redaction=RedactionProfile.SONNET, model=SONNET_MODEL)
    # SPECIALIST: spec(cap_s=8.0, redaction=RedactionProfile.SONNET, model=SONNET_MODEL, max_tokens=3000)

ROLE_WIRES: Final = ("planner", "classifier", "planner_fallback", "responder", "brief", "specialist")

@dataclass
class Adapters:
    wires: dict[str, Wire]
    jev: dict[str, JevAdapter]                 # "planner", "classifier"
    sonnet: dict[str, AnthropicAdapter]        # "planner_fallback", "responder", "brief", "specialist"

def build_adapters(bodies: Mapping[str, Sequence[Body]]) -> Adapters:
    # one Wire per name in ROLE_WIRES (empty list when not given); one adapter object per role (separate queues so a
    # planner body is never consumed by the classifier)

def real_gateway(a: Adapters, *, ledger: RecordingLedger, sink: InMemoryTraceSink, limits: Limits) -> ModelGateway:
    # s = raw_specs(); ModelGateway(choice={Role.PLANNER: (a.jev["planner"], s[Role.PLANNER]), Role.CLASSIFIER:
    #   (a.jev["classifier"], s[Role.CLASSIFIER]), Role.PLANNER_FALLBACK: (a.sonnet["planner_fallback"], s[...])},
    #   structured={Role.RESPONDER: (a.sonnet["responder"], …), Role.BRIEF: (a.sonnet["brief"], …)},
    #   tools={Role.SPECIALIST: (a.sonnet["specialist"], …)}, ledger=ledger, trace=sink, redact=redact, limits=limits)

def tool_result_texts(wire: Wire) -> list[str]:
    # every "content" of every block with "type" == "tool_result" in every recorded request's "messages" items
    # (this is what the model received as ToolError / tool output)
```

Check: a 6-line scratch check in the REPL is enough: `jev_adapter(Wire([jev_body({"danger_level": "emergency"})]))
.choose(<a 1-field request>, timeout_s=3).failure.kind` prints `invalid_output`. Then ruff + mypy on the file.

### 5.5 Step 4 — `tests/contract/prompts_render.py` (AC-1, AC-2, AC-4, AC-5, AC-6 inputs)

```python
@dataclass(frozen=True)
class Rendered:
    turn: int
    planner: ChoiceRequest; planner_fallback: ChoiceRequest; classifier: ChoiceRequest
    specialists: Mapping[str, ToolStepRequest]             # kind → the first ToolStepRequest of that kind's run
    expected_tools: Mapping[str, tuple[ToolSchema, ...]]   # kind → dispatcher.schemas(SPECS[kind].tool_kinds)
    responder: StructuredRequest[Any]; brief: StructuredRequest[Any]
    brief_shown: Mapping[int, str]                         # the `shown` the checks node passed to check_quotes
    customer_ids: frozenset[int]; assistant_ids: frozenset[int]
    registry: ToolRegistry
    def roles(self) -> frozenset[str]: return frozenset({"planner", "planner_fallback", "classifier", "specialist", "responder", "brief"} if self.specialists else …)

def offered_sets(r: Rendered) -> dict[str, object]:
    # {"planner": tuple((f.name, tuple(f.options)) for f in r.planner.fields), "planner_fallback": same for fallback,
    #  "classifier": same, **{f"specialist.{k}": tuple((t.name, json.dumps(t.input_schema, sort_keys=True)) for t in req.tools)
    #  for k, req in sorted(r.specialists.items())}, "responder": (r.responder.output_model.__name__,
    #  json.dumps(r.responder.output_model.model_json_schema(), sort_keys=True)), "brief": same for r.brief}

def render_turn(n: int) -> Rendered:
```

`render_turn(n)` algorithm (each step's invariant in italics):
1. `with temp_sqlite() as store, pytest.MonkeyPatch.context() as mp:` → `seeded = seed_conversation(store, TURNS, upto=n)`.
   *The DB holds the conversation up to turn n only.*
2. Fakes: `planner_fake = FakeChoiceModel([ScriptedFailure(kind=ProviderFailureKind.INVALID_OUTPUT)])` (so the node
   also renders the fallback); `fallback_fake = FakeAnthropicChoiceModel([ChoiceAnswer(choices=dict(VALID_PLAN),
   probabilities=None)])`; `classifier_fake = FakeChoiceModel([ChoiceAnswer(choices={DANGER_FIELD: "normal"},
   probabilities=None)])`; `tool_fake = FakeToolModel([ToolStep(text="Nothing to look up.", tool_calls=(), raw={"role":
   "assistant", "content": []}, stop_reason="end_turn")] * 3)`; `responder_fake = FakeStructuredModel([ResponderDraft(
   text="Thanks for your message. A person will look at the repair.")])`; `brief_fake = FakeStructuredModel(
   [BriefExtraction(needs=[Quote(message_id=seeded.customer_ids[n], text=<first 20 chars of the STORE-redacted turn-n
   text>)], claims=[], open_decision="Decide whether the repair needs a follow-up visit.")])`.
   *Every fake records the request it receives, after the gateway's redaction.*
3. Gateway: `ModelGateway(choice={PLANNER: (planner_fake, default_specs()[PLANNER]), CLASSIFIER: (classifier_fake, …),
   PLANNER_FALLBACK: (fallback_fake, …)}, structured={RESPONDER: (responder_fake, …), BRIEF: (brief_fake, …)},
   tools={SPECIALIST: (tool_fake, …)}, ledger=RecordingLedger(), trace=sink, redact=redact, limits=RENDER_LIMITS)` where
   `RENDER_LIMITS = Limits(brakes=Brakes(sonnet_calls=12))` (PD-3) and `default_specs` from `_gateway_doubles`.
4. `index = FakeIndex(WP1_PASSAGES)`; `registry = build_registry(index, store)`; `dispatcher = ToolDispatcher(registry,
   store.uow)`; `runner = SpecialistRunner(gateway=gw, transcript=tool_fake, dispatcher=dispatcher, specs=SPECS,
   brakes=RENDER_LIMITS.brakes, trace=sink)`; `cases = CasesDouble(refund_case(n))`; `brief_double = RecordingBriefAssembler()`;
   `deps = build_deps(...)` with `limits=RENDER_LIMITS`.
5. Spy: `shown_seen: list[dict[int, str]] = []`; `real = reply_nodes.check_quotes`;
   `mp.setattr(reply_nodes, "check_quotes", lambda ext, shown: (shown_seen.append(dict(shown)), real(ext, shown))[1])`
   (write it as a small named function for mypy). *We observe exactly the mapping the consumer compares.*
6. `with open_turn(sink, n) as ctx:` `rt = runtime(ctx)`; `base = make_state(TURNS, seeded, n, identity=VERIFIED)`.
   - `planner(base, rt, deps=deps)`; then `planner_req = planner_fake.requests[-1]`, `fallback_req = fallback_fake.requests[-1]`.
   - `danger_classifier(base, rt, deps=deps)`; `classifier_req = classifier_fake.requests[-1]`.
   - For `kind, intent in (("knowledge", TaskIntent.ANSWER_QUESTION), ("account", TaskIntent.READ_MEMBERSHIP),
     ("scheduling", TaskIntent.BOOK_NEW))` in that order: `planned = PlannedTask(order=1, specialist=kind, intent=intent,
     needs_identity=kind != "knowledge")`; `state = base.model_copy(update={"plan": Plan(mode="act", tasks=(planned,),
     handoff_request=None, topic="other", source="planner")})`; `run_specialist({"planned": planned, "state": state}, rt,
     deps=deps)`; the request is `tool_fake.requests[i]` (i = 0, 1, 2). *One model step per kind: the final-answer
     branch; the scheduling quick check is a dispatch, not a model step.*
   - `facts_state = base.model_copy(update={"facts": facts_for(n, handoff=refund_handoff(n)), "handoff":
     refund_handoff(n), "plan": Plan(mode="talk", tasks=(), handoff_request=None, topic="other", source="planner")})`;
     `r_up = responder(facts_state, rt, deps=deps)`; `b_up = brief(facts_state, rt, deps=deps)`;
     `checks(facts_state.model_copy(update={"draft": r_up["draft"], "brief_extraction": b_up["brief_extraction"]}),
     rt, deps=deps)`. Requests: `responder_fake.requests[-1]`, `brief_fake.requests[-1]`; `brief_shown = shown_seen[-1]`.
7. Return `Rendered(turn=n, …, expected_tools={k: dispatcher.schemas(SPECS[k].tool_kinds) for k in SPECS},
   customer_ids=frozenset(seeded.customer_ids.values()), assistant_ids=frozenset(seeded.assistant_ids.values()),
   registry=registry)`. Assert inside nothing; the tests assert.

Check: `uv run python -c "from tests.contract.prompts_render import render_turn; r = render_turn(1); print(sorted(r.specialists))"`
prints `['account', 'knowledge', 'scheduling']`.

### 5.6 Step 5 — `tests/contract/test_prompts_vs_consumers.py`, the render-side tests + guard (AC-1…AC-6, AC-11, AC-12)

Module docstring: one paragraph naming AEA-60, level `mock-tested`, "no network, no paid call, development data only".
No `pytestmark` (default suite).

**Module guard (AC-12; PD-12)** — at module top:
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
_HELD_OUT = (str(REPO_ROOT / "eval" / "cases" / "heldout"), str(Path.home() / ".meridian-sealed"))
@dataclass
class _Guard:
    active: bool = False; opens: int = 0
    heldout: list[str] = field(default_factory=list); connects: list[str] = field(default_factory=list)
_GUARD = _Guard(); _HOOKED: list[bool] = []
def _audit(event: str, args: tuple[Any, ...]) -> None:          # must never raise
    if not _GUARD.active or event != "open" or not args or not isinstance(args[0], (str, bytes, os.PathLike)): return
    path = os.path.abspath(os.fsdecode(args[0])); _GUARD.opens += 1
    if any(path == root or path.startswith(root + os.sep) for root in _HELD_OUT): _GUARD.heldout.append(path)
@pytest.fixture(scope="module", autouse=True)
def _module_guard() -> Iterator[None]:
    if not _HOOKED: sys.addaudithook(_audit); _HOOKED.append(True)
    def refuse(self: socket.socket, address: Any) -> None: _GUARD.connects.append(repr(address)); raise OSError("AEA-60: network refused")
    def refuse_ex(self: socket.socket, address: Any) -> int: _GUARD.connects.append(repr(address)); return 111
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(socket.socket, "connect", refuse); mp.setattr(socket.socket, "connect_ex", refuse_ex)
        _GUARD.active = True
        try: yield
        finally: _GUARD.active = False
@pytest.fixture(autouse=True)
def _no_heldout_or_network() -> Iterator[None]:
    before = (len(_GUARD.heldout), len(_GUARD.connects)); yield
    assert (len(_GUARD.heldout), len(_GUARD.connects)) == before, "held-out read or network connect during this test"
```

**Rendered fixture:** `@pytest.fixture(scope="module") def rendered() -> dict[int, Rendered]: return {n: render_turn(n) for n in (1, 2, 5)}`.

**Tests** (names exact; parametrise ids exact):

1. `test_every_role_and_spec_has_a_rendered_case(rendered)` (AC-1) —
   for each `r` in `rendered.values()`: `check_inventory([x.value for x in Role], SPECS, have_roles=r.roles(),
   have_kinds=set(r.specialists))`; `offered_sets(rendered[1]) == offered_sets(rendered[2]) == offered_sets(rendered[5])`;
   then `with pytest.raises(PromptDrift, match="role 'triage' has no rendered case"): check_inventory([*(x.value for x
   in Role), "triage"], SPECS, have_roles=rendered[1].roles(), have_kinds=set(rendered[1].specialists))` and the same for
   kind `"warranty"` → `"specialist kind 'warranty' has no rendered case"`. `Rendered.roles()` returns exactly
   `{"planner", "planner_fallback", "classifier", "specialist", "responder", "brief"}` minus any whose request is absent.
2. `test_routing_fields_match_planner_choices_and_danger_label(rendered)` (AC-2) — per turn:
   `check_choice_fields("planner", r.planner, PlannerChoices)`; `check_choice_fields("planner_fallback",
   r.planner_fallback, PlannerChoices)`; `r.planner_fallback.fields == r.planner.fields`;
   `check_choice_fields("classifier", r.classifier, DangerAssessment, field_map={DANGER_FIELD: "label"})`;
   `tuple(r.classifier.fields[0].options) == ("normal", "burning_unclear", "danger")` (set equality is enough if `main`
   orders them otherwise — use `set(...)`); `"late_technician" in r.planner.fields[...handoff].options`;
   `check_wording_keys("planner", r.planner)`; `check_wording_keys("classifier", r.classifier)`.
3. `test_join_plan_accepts_every_offered_value(rendered, field, option)` (AC-3), parametrised:
   `pytest.mark.parametrize(("field", "option"), [(f, o) for f in PlannerChoices.model_fields for o in literal_values(PlannerChoices, f)], ids=lambda …: f"{field}={option}")`
   (build the list at module level as `_PLANNER_OPTIONS` and `ids=[f"{f}={o}" for f, o in _PLANNER_OPTIONS]`). Body:
   - `assert option in {f.name: f.options for f in rendered[1].planner.fields}[field]` *(offered — AC-2 proved equality)*.
   - `choices = PlannerChoices(**{**BASE_CHOICES, field: option})` with `BASE_CHOICES = {"knowledge": "no", "account":
     "none", "scheduling": "none", "handoff": "none", "topic": "other"}`; `outcome = PlannerOutcome(choices=choices,
     probabilities=None, model=JEV_MODEL, fallback_used=False, failure=None)`.
   - `with temp_sqlite() as store: seeded = seed_conversation(store, TURNS, upto=1); state = make_state(TURNS, seeded, 1)`;
     `plan = join_plan(outcome, None, free_text_gate(), state)` (must not raise).
   - `all(t.specialist in SPECS for t in plan.tasks)`; `isinstance(t.intent, TaskIntent)`.
   - `field == "topic"` → `plan.topic == option`; `option in literal_values(Plan, "topic")`.
   - `field == "handoff"`: `option == "none"` → `plan.handoff_request is None`; else `reason = plan.handoff_request`,
     `reason is not None`, `reason.value not in CODE_ONLY`, expected = `{"unsupported_other": "unsupported_action"}.get(option, option)`,
     `reason.value == expected`; `priority_for(reason, promise_due=NOW, renewal_date=None)` is a `Priority`;
     `d = decide_escalation(EscalationInputs(gate=free_text_gate(), plan=plan, results=(), counters=FailureCounters(),
     identity=UNVERIFIED, halt=None, models_disabled=False, now=NOW))` → `d.outcome == "escalate"`, `d.reason is reason`,
     `d.priority is not None`.
   - Plus one extra parametrised id `reverse_reachability` (use a separate test function
     `test_join_plan_accepts_every_offered_value_reverse(rendered)` if mixing ids complicates the parametrisation — the
     verify command covers both via `-k test_join_plan_accepts_every_offered_value`): `reached = {join_plan(PlannerOutcome(
     choices=PlannerChoices(**{**BASE_CHOICES, "handoff": o}), …), None, free_text_gate(), state).handoff_request for o in
     <offered handoff options>} - {None}`; `{r.value for r in reached} == {h.value for h in HandoffReason} - CODE_ONLY` (PA-1).
4. `test_no_prompt_offers_a_code_only_value(rendered)` (AC-4) — `CODE_ONLY <= {h.value for h in HandoffReason}`; per
   turn: `check_code_only("planner", r.planner)`, `check_code_only("planner_fallback", r.planner_fallback)`; for each
   kind and each tool in `r.specialists[kind].tools`: `check_no_forbidden_fields(f"specialist.{kind} tool '{t.name}'",
   t.input_schema)`; `check_no_forbidden_fields("responder.output_model", ResponderDraft.model_json_schema())`; same for
   `BriefExtraction`.
5. `test_specialist_tools_match_registry_and_report_models(rendered)` (AC-5) — `vocabulary = schema_vocabulary(
   SchedulingSlice.model_json_schema(), *(SPECS[k].report_model.model_json_schema() for k in SPECS),
   *(d.args_model.model_json_schema() for d in <every ToolDef in r.registry>))` — get every def with
   `r.registry.for_kinds(frozenset(ToolKind))`; per turn and kind: `check_specialist(kind, r.specialists[kind],
   registry=r.registry, expected_tools=r.expected_tools[kind], tool_kinds=SPECS[kind].tool_kinds,
   report_model=SPECS[kind].report_model, vocabulary=vocabulary)`.
6. `test_reply_schemas_and_brief_message_ids_match_checks(rendered)` (AC-6) — per turn: `check_reply_schema("responder",
   r.responder, ResponderDraft)`; `r.responder.output_model is ResponderDraft`; `props =
   ResponderDraft.model_json_schema()["properties"]`; `set(props) == {"text"}`; `props["text"]["minLength"] == 1` and
   `props["text"]["maxLength"] == 1200`; `text = r.responder.system_prefix + r.responder.system_dynamic + r.responder.user`;
   `all(label in text for label in LABELS)`; `check_reply_schema("brief", r.brief, BriefExtraction)`; `rendered_ids =
   parse_brief_user(r.brief.user)`; `check_brief_ids(rendered_ids, r.brief_shown, r.customer_ids)`; `set(rendered_ids) ==
   set(r.customer_ids)` (all customer lines are within the 10-turn window). **Wire check (once):** `wire =
   Wire([text_message('{"text": "Thanks."}')])`; `anthropic_adapter(wire).structured(rendered[5].responder,
   timeout_s=5.0)`; `sent = wire.requests[0]["output_config"]["format"]["schema"]`; `sent ==
   anthropic.transform_schema(ResponderDraft)`; `set(sent["properties"]) == {"text"}`.
7. `test_check_fails_on_drift(rendered, case)` (AC-11), `@pytest.mark.parametrize("case", ["planner_extra_option",
   "planner_missing_late_technician", "classifier_extra_option", "specialist_names_unknown_tool",
   "responder_extra_promise_field", "brief_shows_staff_message"])`. `r = rendered[1]` (`rendered[5]` for the brief case).
   Build the drifted copy and the expected message:
   - `planner_extra_option`: replace the `handoff` field with `f.model_copy(update={"options": {**f.options,
     "cancel_membership": "Cancel"}})` in a `r.planner.model_copy(update={"fields": …})` →
     `check_choice_fields("planner", drifted, PlannerChoices)`; match
     `re.escape("routing.planner.handoff offers 'cancel_membership'; PlannerChoices.handoff does not accept it")`.
   - `planner_missing_late_technician`: options without `late_technician` → `"PlannerChoices.handoff accepts
     'late_technician'; routing.planner.handoff does not offer it"`.
   - `classifier_extra_option`: add `"emergency"` → `check_choice_fields("classifier", drifted, DangerAssessment,
     field_map={DANGER_FIELD: "label"})` → `"routing.classifier.danger_level offers 'emergency'; DangerAssessment.label
     does not accept it"`.
   - `specialist_names_unknown_tool`: `req = r.specialists["account"]`; drifted = `req.model_copy(update={"system_prefix":
     req.system_prefix + " If asked, call refund_invoice."})` → `check_specialist("account", drifted, …)` →
     `"specialist.account wording names 'refund_invoice'; it is not a tool sent with it"`.
   - `responder_extra_promise_field`: module-level `class _DraftWithPromise(LLMFacing): text: str = Field(min_length=1,
     max_length=1200); promise: str` (defined in the test file, not in product code); drifted =
     `r.responder.model_copy(update={"output_model": _DraftWithPromise})` → `"responder.output_model has field
     'promise'; ResponderDraft does not"`.
   - `brief_shows_staff_message`: `aid = min(rendered[5].assistant_ids)`; drifted ids = `{**parse_brief_user(
     rendered[5].brief.user), aid: "Let me look that up."}` → `check_brief_ids(drifted, rendered[5].brief_shown,
     rendered[5].customer_ids)` → `f"brief shows message {aid} that is not a customer message of this thread"`.
   Every case: `with pytest.raises(PromptDrift, match=<re.escape(message)>):` and assert no customer text in
   `str(excinfo.value)` (check `TURNS[4] not in str(excinfo.value)`).
8. `test_no_heldout_reads_and_no_network(rendered)` (AC-12) — `assert _HOOKED and _GUARD.active`; `before =
   _GUARD.opens`; `(tmp_path / "probe.txt").write_text("x")` then `open(...)`/read it → `_GUARD.opens > before` *(hook
   live)*; `socket.socket.connect.__name__ == "refuse"` *(guard installed)*; `_GUARD.heldout == []`; `_GUARD.connects ==
   []`; also every fixture text is one of `TURNS`, `REPLIES`, `NODANGER`, `STAFF_LINE` or generated (assert
   `all(t in TURNS for t in <the turn texts rendered>)` is enough). Use `tmp_path` (function fixture) for the probe.

Check while iterating: `uv run pytest tests/contract/test_prompts_vs_consumers.py -q -k "rendered_case or routing_fields or join_plan or code_only or specialist_tools or reply_schemas or drift or heldout"`.

### 5.7 Step 6 — `tests/contract/prompts_cases.py` (malformed cases: AC-7, AC-8, AC-9)

```python
OPTION_MARKER: Final = "zq-rejected-option-7731"
QUERY_MARKER_301: Final = "q" * (301 - len("zq-rejected-query-7731")) + "zq-rejected-query-7731"   # exactly 301 chars
DRAFT_MARKER: Final = "zq-rejected-draft-7731"

@dataclass(frozen=True)
class Case:
    id: str
    group: Literal["routing", "specialist", "reply"]
    bodies: Callable[[Seeded], Mapping[str, Sequence[Body]]]   # role-wire name → bodies (built after seeding: quotes need ids)
    kind: Literal["knowledge", "account", "scheduling"] | None = None    # specialist group
    intent: TaskIntent | None = None
    text: str = NODANGER                                        # the turn text seeded as turn 1 (routing / specialist)
    brief_turn: bool = False                                    # reply group: run the brief path (handoff created)

@dataclass
class RawRun:
    case: Case; seeded: Seeded; adapters: Adapters; ledger: RecordingLedger; sink: InMemoryTraceSink
    index: FakeIndex; cases: CasesDouble; brief: RecordingBriefAssembler; ctx: TurnContext
    updates: dict[str, Mapping[str, Any]]          # node name → its returned update
    logs: list[logging.LogRecord]; lookups: tuple[LookupRow, ...]; db_dump: str
    quote_calls: list[tuple[dict[int, str], QuoteCheck]]
    reply: ComposedReply | None = None

def run_case(case: Case) -> RawRun:
```

`run_case` algorithm:
1. `with temp_sqlite() as store, pytest.MonkeyPatch.context() as mp, capture_logs() as logs:`
2. Seed: routing/specialist → `seeded = seed_conversation(store, (case.text,), upto=1)`; reply → `seeded =
   seed_conversation(store, TURNS, upto=5, staff_after=4)`. Turn number `n = 1` or `5` accordingly.
3. `adapters = build_adapters(case.bodies(seeded))`; `ledger = RecordingLedger()`; `sink = InMemoryTraceSink()`;
   `limits = Limits()`; `gw = real_gateway(adapters, ledger=ledger, sink=sink, limits=limits)`; `index =
   FakeIndex(WP1_PASSAGES)`; `registry = build_registry(index, store)`; `dispatcher = ToolDispatcher(registry, store.uow)`;
   `runner = SpecialistRunner(gateway=gw, transcript=adapters.sonnet["specialist"], dispatcher=dispatcher, specs=SPECS,
   brakes=limits.brakes, trace=sink)`; `cases = CasesDouble(refund_case(n) if case.brief_turn else None)`; `bd =
   RecordingBriefAssembler()`; `deps = build_deps(...)`.
4. Spy `check_quotes` as in Step 4 step 5 but recording `(dict(shown), result)` into `quote_calls`.
5. `with open_turn(sink, n) as ctx:` `rt = runtime(ctx)`; `updates = {}`;
   - **routing:** `state = make_state((case.text,), seeded, 1)`; `updates["planner"] = planner(state, rt, deps=deps)`;
     `updates["danger"] = danger_classifier(state, rt, deps=deps)`; `joined = state.model_copy(update={"planner":
     updates["planner"].get("planner"), "danger": updates["danger"].get("danger")})`; `updates["plan_join"] =
     plan_join(joined, rt, deps=deps)`; `updates["escalation"] = escalation(joined.model_copy(update={"plan":
     updates["plan_join"]["plan"]}), rt, deps=deps)`.
   - **specialist:** `planned = PlannedTask(order=1, specialist=case.kind, intent=case.intent, needs_identity=case.kind !=
     "knowledge")`; `plan = Plan(mode="act", tasks=(planned,), handoff_request=None, topic="other", source="planner")`;
     `state = make_state((case.text,), seeded, 1, identity=VERIFIED, plan=plan)`; `updates["specialist"] =
     run_specialist({"planned": planned, "state": state}, rt, deps=deps)`; `updates["escalation"] = escalation(
     state.model_copy(update={"specialist_results": list(updates["specialist"]["specialist_results"])}), rt, deps=deps)`.
   - **reply:** `handoff = refund_handoff(5) if case.brief_turn else None`; `state = make_state(TURNS, seeded, 5,
     facts=facts_for(5, handoff=handoff), handoff=handoff, plan=Plan(mode="talk", tasks=(), handoff_request=None,
     topic="other", source="planner"))`; `updates["responder"] = responder(state, rt, deps=deps)`; if `case.brief_turn`:
     `updates["brief"] = brief(state, rt, deps=deps)`; `after = state.model_copy(update={"draft":
     updates["responder"].get("draft"), "brief_extraction": updates.get("brief", {}).get("brief_extraction")})`;
     `updates["checks"] = checks(after, rt, deps=deps)`; `reply = ReplyComposer().compose(after.model_copy(update=
     {"checked": updates["checks"]["checked"]}), ctx)`.
6. After the turn: `with store.uow() as tx: lookups = tx.core.lookup_log.for_thread(THREAD)`; `conn =
   sqlite3.connect(store.db_path)`; `db_dump = "\n".join(conn.iterdump())`; `conn.close()`. Return `RawRun(...)`.
   *Everything a later assertion needs is copied out before the temp directory is removed.*

**The case table** `MALFORMED_CASES: tuple[Case, ...]` (ids exact; `jb = jev_body`, `tm = text_message`,
`tl = tool_message`, `tu = tool_use`, `VP = dict(VALID_PLAN)`, `FB_OK = tm(json.dumps(VP))`):

| id | group | bodies (role-wire → list) | kind / intent / text |
|---|---|---|---|
| `planner_choice_outside` | routing | planner `[jb({**VP, "handoff": OPTION_MARKER})]`; planner_fallback `[FB_OK]`; classifier `[jb({DANGER_FIELD: "normal"})]` | text NODANGER |
| `planner_missing_field` | routing | planner `[jb({k: v for k, v in VP.items() if k != "topic"})]`; fallback `[FB_OK]`; classifier normal | |
| `planner_unparseable` | routing | planner `[b'{"answers": {']`; fallback `[FB_OK]`; classifier normal | |
| `both_planners_fallback_extra_field` | routing | planner `[jb({k: v for k, v in VP.items() if k != "topic"})]`; fallback `[tm(json.dumps({**VP, "extra": "x"}))]`; classifier normal | |
| `both_planners_fallback_outside` | routing | planner `[b'{"answers": {']`; fallback `[tm(json.dumps({**VP, "handoff": "cancel_membership"}))]`; classifier normal | |
| `classifier_emergency` | routing | planner `[jb(VP)]`; classifier `[jb({DANGER_FIELD: "emergency"})]` | |
| `classifier_empty` | routing | planner `[jb(VP)]`; classifier `[{"id": "gen-aea60", "answers": {}, "usage": {"input_tokens": 300, "output_tokens": 0}}]` | |
| `tool_unknown` | specialist | specialist `[tl(tu("toolu_1", "issue_refund", {})), tl(tu("toolu_2", "report_facts", {"points": [], "answered": False}))]` | knowledge / ANSWER_QUESTION / TURNS[2] |
| `tool_not_allowed` | specialist | `[tl(tu("toolu_1", "read_invoices", {})), tl(tu("toolu_2", "report_facts", {"points": [], "answered": False}))]` | knowledge / ANSWER_QUESTION / TURNS[2] |
| `tool_args_none` | specialist | `[tl(tu("toolu_1", "kb_search", "not-json{")), <report as above>]` | knowledge |
| `tool_extra_customer_id` | specialist | `[tl(tu("toolu_1", "kb_search", {"query": "comfort club", "customer_id": "MHC-10001"})), <report>]` | knowledge |
| `tool_query_301` | specialist | `[tl(tu("toolu_1", "kb_search", {"query": QUERY_MARKER_301})), <report>]` | knowledge |
| `tool_invoice_bad` | specialist | `[tl(tu("toolu_1", "read_invoices", {"invoice_number": "INV-12"})), tl(tu("toolu_2", "report_facts", {"summary": "No invoice read."}))]` | account / READ_INVOICE / "I got an invoice and I'm not sure what it's for." (WP-2) |
| `report_six_points` | specialist | `[tl(tu("toolu_1", "kb_search", {"query": "comfort club"})), tl(tu("toolu_2", "report_facts", {"points": [{"text": "Two tune-ups a year.", "passage_id": "membership/comfort_club_overview.md#0"}] * 6, "answered": True}))]` | knowledge |
| `report_long_summary` | specialist | `[tl(tu("toolu_1", "read_membership", {})), tl(tu("toolu_2", "report_facts", {"summary": "s" * 301}))]` | account / READ_MEMBERSHIP / "I want to cancel my Comfort Club membership." (WP-8) |
| `step_unparseable` | specialist | `[b"{not json"]` | knowledge |
| `step_max_tokens` | specialist | `[tm("partial", stop_reason="max_tokens")]` | knowledge |
| `step_refusal` | specialist | `[message([], stop_reason="refusal")]` | knowledge |
| `draft_empty` | reply | responder `[tm(json.dumps({"text": ""}))]` | |
| `draft_1201` | reply | responder `[tm(json.dumps({"text": DRAFT_MARKER + "d" * (1201 - len(DRAFT_MARKER))}))]` | |
| `draft_extra_promise` | reply | responder `[tm(json.dumps({"text": "Done.", "promise": "Someone will call you today."}))]` | |
| `draft_refusal` | reply | responder `[message([], stop_reason="refusal")]` | |
| `brief_zero_needs` | reply, brief_turn | responder `[tm('{"text": "A person will look at this."}')]`; brief `[tm(json.dumps({"needs": [], "claims": [], "open_decision": "Decide on the refund."}))]` | |
| `brief_three_needs` | reply, brief_turn | brief: `needs` = 3 × `{"message_id": s.customer_ids[5], "text": "I want a full refund"}` | |
| `brief_six_claims` | reply, brief_turn | brief: `needs` 1 valid, `claims` = 6 × `{"message_id": s.customer_ids[5], "text": DRAFT_MARKER}` | |
| `brief_long_decision` | reply, brief_turn | brief: 1 valid need, `open_decision` = `"o" * 201` | |
| `quote_ai_message` | reply, brief_turn | brief valid: need `{"message_id": s.customer_ids[5], "text": "I want a full refund"}`, claims `[{"message_id": s.assistant_ids[4], "text": "Let me look that up."}]`, decision "Decide on the refund." | |
| `quote_staff_message` | reply, brief_turn | claims `[{"message_id": s.staff_id, "text": "Riley here"}]` | |
| `quote_paraphrase` | reply, brief_turn | claims `[{"message_id": s.customer_ids[5], "text": "The repair did not work at all"}]` | |

`ROUTING = [c for c in MALFORMED_CASES if c.group == "routing"]`, same for `SPECIALIST`, `REPLY`; `MARKER_CASES =
("planner_choice_outside", "tool_query_301", "draft_1201", "brief_six_claims")`.

Check: `uv run python -c "from tests.contract.prompts_cases import MALFORMED_CASES, run_case; r = run_case(MALFORMED_CASES[0]); print(sorted(r.updates))"`.

### 5.8 Step 7 — the malformed-output tests in the test file (AC-7, AC-8, AC-9, AC-10, AC-14)

Helpers in the test file: `calls(run) = [c for c, _ in run.ledger.records]`; `sig(run) = signals(run.logs)`;
`spans(run) = run.sink.spans_for(run.ctx.span)`.

9. `test_malformed_routing_outputs(case)` — `@pytest.mark.parametrize("case", ROUTING, ids=[c.id for c in ROUTING])`;
   `run = run_case(case)`. Assertions by id:
   - (a)(b)(c) `planner_choice_outside`, `planner_missing_field`, `planner_unparseable`: `[(c.role, c.attempt,
     c.status) for c in calls(run) if c.role in (Role.PLANNER, Role.PLANNER_FALLBACK)] == [(Role.PLANNER, 1, "error"),
     (Role.PLANNER_FALLBACK, 1, "ok")]`; the planner record's `failure.kind is INVALID_OUTPUT` and `failure.retryable is
     False`; `po = run.updates["planner"]["planner"]`: `po.fallback_used is True`, `po.failure is None`, `po.choices is
     not None`; `run.updates["plan_join"]["plan"].source == "fallback_planner"`; signals named `planner_fallback`: exactly
     one, `cause == "invalid_output"`, `recovered is True`, `role == "planner"`, `node == "planner"`.
   - (d) `both_planners_fallback_extra_field`, `both_planners_fallback_outside`: both records `status == "error"`, kinds
     `INVALID_OUTPUT`; `run.updates["plan_join"]["plan"] == Plan(mode="act", tasks=(), handoff_request=None,
     topic="other", source="rules_only", planner_failed=True)`; one `planner_fallback` signal `recovered is False`, cause
     `"invalid_output"`; `run.updates["escalation"]["escalation"]` → `outcome == "escalate"`, `reason is
     HandoffReason.AI_FAILURE`, `priority is Priority.P3`, `rule_id == "AI.planner_failed"`, `degraded is True`.
   - (e) `classifier_emergency`, `classifier_empty`: `d = run.updates["danger"]["danger"]`: `d.label == "normal"`,
     `d.raised is False`, `d.failure.kind is INVALID_OUTPUT`; classifier records: exactly one, `attempt == 1`;
     `run.updates["danger"]["check_events"] == (CheckEvent(check="classifier", turn_id=TURN_IDS[1], result="fallback",
     codes=("fallback", "invalid_output")),)`; exactly one `classifier_fallback` signal (cause `invalid_output`);
     `plan = run.updates["plan_join"]["plan"]`: `plan.mode == "act"`, `[t.intent for t in plan.tasks] ==
     [TaskIntent.BOOK_NEW]` *(the turn goes on to plan_join; the rules stand)*.
10. `test_malformed_specialist_outputs(case)` — parametrised over `SPECIALIST`. `res =
    run.updates["specialist"]["specialist_results"][0]`; `tools = res.tools`. Expectations table (in the test as a dict):

    | id | assertion |
    |---|---|
    | `tool_unknown` | `tools[0].kind is None`, `outcome == "refused"`, `error is ToolErrorCode.UNKNOWN_TOOL`; one lookup row `tool == "issue_refund"`, `result_seen == "refused:unknown_tool"`; `run.index.searches == []`; `len(run.adapters.wires["specialist"].requests) == 2` (the run went on); `res.status != "failed"` |
    | `tool_not_allowed` | `tools[0].error is ToolErrorCode.NOT_ALLOWED`; lookup `refused:not_allowed` |
    | `tool_args_none` | `error is BAD_ARGUMENTS`; `run.index.searches == []` |
    | `tool_extra_customer_id` | `error is BAD_ARGUMENTS`; `run.index.searches == []` *(executor never called)* |
    | `tool_query_301` | `error is BAD_ARGUMENTS`; `run.index.searches == []` |
    | `tool_invoice_bad` | `error is BAD_ARGUMENTS`; lookup `refused:bad_arguments` |
    | `report_six_points` | `res.status == "no_current_source"`, `res.points == ()`, `len(res.passages) >= 1` (captures kept); `tools[0].outcome == "ok"` |
    | `report_long_summary` | `res.status == "read"`, `res.membership is not None` *(built from captures only)* |
    | `step_unparseable` / `step_max_tokens` / `step_refusal` | `res.status == "failed"`, `res.failure.kind` is `INVALID_OUTPUT` / `MAX_TOKENS` / `REFUSAL`; exactly one `specialist_failed` signal, `cause == res.failure.kind.value`, `specialist == "knowledge"`; `esc = run.updates["escalation"]["escalation"]`: `("escalate", HandoffReason.AI_FAILURE, Priority.P3, "AI.specialist_failed", True) == (esc.outcome, esc.reason, esc.priority, esc.rule_id, esc.degraded)` |

    For every non-step case also: `len(run.lookups) == len([t for t in tools])` (one row per dispatched call; `report_facts`
    is never dispatched) and no `specialist_failed` signal.
11. `test_malformed_reply_outputs(case)` — parametrised over `REPLY`.
    - `draft_empty`, `draft_1201`, `draft_extra_promise`: `run.updates["responder"]["draft"] is None`; responder record
      `status == "error"`, kind `INVALID_OUTPUT`; one `responder_fallback` signal cause `"invalid_output"`;
      `checked = run.updates["checks"]["checked"]`: `checked.fallback_used is True`, `checked.text == ""`, events
      completion/fact with `result == "fallback"`; `run.reply` has a block with `type == "failure_offer"` and
      `person_key is True`, no block with `type == "text"` whose text came from the model; `run.reply.outcome ==
      "degraded_handoff"`, `run.reply.degrade_reason == "model_error"`.
    - `draft_refusal`: same, kind/cause `"refusal"`.
    - `brief_zero_needs`, `brief_three_needs`, `brief_six_claims`, `brief_long_decision`:
      `run.updates["brief"]["brief_extraction"] is None`; `"halt" not in run.updates["brief"]`; one `brief_failed`
      signal cause `"invalid_output"`; `run.brief.attach_calls[-1][1] is None`; `stored = run.cases.attached[-1]`:
      `[h.not_generated for h in stored.headings] == [False, True, False, True, False, False, True, False]` and
      `stored.status == "failed"` *(real `BriefAssembler`, PD-9)*;
      `len(run.cases.attached) == 2` (draft brief, then final); `run.updates["checks"]["checked"]` exists *(turn not
      failed)*; no `brief_quote` event.
    - `quote_ai_message`, `quote_staff_message`, `quote_paraphrase`: `shown, q = run.quote_calls[-1]`; `q.removals[0].reason
      == "quote_not_found"`; `len(q.removals) == 1`; `ev = [e for e in run.updates["checks"]["checked"].events if
      e.check == "brief_quote"]`: `ev == [CheckEvent(check="brief_quote", turn_id=TURN_IDS[5], result="trimmed",
      removed=1, claim_kinds=("quote",))]`; `kept = run.brief.attach_calls[-1][1]`: `kept.claims == []`, `len(kept.needs)
      == 1`; for `quote_staff_message` also `run.seeded.staff_id not in shown`; for `quote_ai_message`
      `run.seeded.assistant_ids[4] not in shown`.
12. `test_rejected_values_absent_from_records()` (AC-10) — for each id in `MARKER_CASES`: `run = run_case(<case>)`;
    `marker = {"planner_choice_outside": OPTION_MARKER, "tool_query_301": "zq-rejected-query-7731", "draft_1201":
    DRAFT_MARKER, "brief_six_claims": DRAFT_MARKER}[id]`; `corpus = case_corpus(run, exclude_specialist_output=(id ==
    "tool_query_301"))`; `assert marker not in corpus`. For `tool_query_301` additionally assert the PD-7 exception
    explicitly: `outs = [m.masked_output for m in spans(run).model_calls if m.record.role is Role.SPECIALIST]`;
    `any("zq-rejected-query-7731" in o for o in outs)` *(DO-6 line 113: the model_call span holds the masked raw
    output)*. Put `case_corpus` in `prompts_cases.py`:
    ```python
    def case_corpus(run: RawRun, *, exclude_specialist_output: bool = False) -> str:
        parts: list[str] = []
        parts += [c.model_dump_json() for c, _ in run.ledger.records]                 # CallRecord, ProviderFailure
        for t in run.sink.turns:
            parts += [m.record.model_dump_json() + m.masked_input for m in t.model_calls]
            parts += [m.masked_output for m in t.model_calls
                      if not (exclude_specialist_output and m.record.role is Role.SPECIALIST)]
            parts += [f"{n.name} {n.status}" for n in t.nodes]                        # node / tool spans
        parts += [json.dumps(s, sort_keys=True) for s in signals(run.logs)]           # SignalRecord
        parts += [r.getMessage() + repr(r.args) + json.dumps(getattr(r, "signal", None), default=str) for r in run.logs]
        for upd in run.updates.values():                                              # CheckEvent, ToolCallRecord, ProviderFailure
            parts.append(repr(upd))
        parts += [r.model_dump_json() for r in run.lookups]                           # lookup_log rows
        parts.append(run.db_dump)                                                     # the whole DB copy
        for wire in run.adapters.wires.values(): parts += tool_result_texts(wire)     # ToolError.message as the model saw it
        return "\n".join(parts)
    ```
    Note: `repr(upd)` of the planner update holds `PlannerOutcome` (no rejected value: the adapter returned `None`);
    the specialist update holds `SpecialistResult` with `ToolCallRecord`s (no args). If a marker is found, the failure
    message must name the record type, not print the corpus: assert per part with `next((i for i, p in enumerate(parts)
    if marker in p), None) is None` and report the index's source label (keep a parallel list of labels).
13. `test_malformed_cases_leave_their_records(case)` (AC-14) — parametrised over `MALFORMED_CASES`. For each run:
    - `recs = calls(run)`; every failed call has `status == "error"` and `failure is not None` with the kind the group
      table expects; `spans(run).model_calls` has the same length as `recs` and `[m.record for m in
      spans(run).model_calls] == recs` *(one ledger row and one model_call span per attempt)*;
    - every signal dict has keys `{"record", "name", "turn_id", "thread_id", "request_id", "run_tag", "node", "cause",
      "role", "specialist", "attempt", "recovered"}` with `turn_id == str(run.ctx.ids.turn_id)`, `thread_id == str(THREAD)`,
      `request_id == str(REQUEST)`, `run_tag == "live"`, and `cause` a code (matches `^[a-z_]+$`);
    - routing classifier cases: the `classifier` check event present; quote cases: the `brief_quote` event present;
    - specialist cases: `len(run.lookups)` equals the number of `ToolCallRecord`s in the result, and each lookup row's
      `turn_id == TURN_IDS[1]` and `message_id == run.seeded.customer_ids[1]`.

Check while iterating: `uv run pytest tests/contract/test_prompts_vs_consumers.py -q -k "malformed or rejected or records"`.

### 5.9 Step 8 — journeys (AC-13)

Both files start with the J-1 pattern (`tests/journeys/j1/test_aea_57.py`): `pytestmark = pytest.mark.journey`, the
`journey` fixture, `journey.step(J, name, needs=…, operations=…)`, `client.call(..., operation_id=...)` (validates every
response against the OpenAPI). Constants:
```python
LOGIN_NEEDS = ("login_sessions", "demo_clock")
CHAT_NEEDS = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
TURN_NEEDS = (*CHAT_NEEDS, "turn_service", "run_graph")
CASE_NEEDS = (*TURN_NEEDS, "handoff_service", "case_service")
VALID_PLANNER = json.dumps({"knowledge": "no", "account": "none", "scheduling": "none", "handoff": "none", "topic": "other"})
CLASSIFIER_NORMAL = json.dumps({DANGER_FIELD: "normal"})          # from meridian.agent.prompts.routing
```
Helpers (the J-1 shapes on `main`, `tests/journeys/j1/test_aea_57.py`; copy them into each file, never import from
another ticket's journey file): inside each step, `signed = journey.login()` (`LoginResult`; `signed.client` is the
signed-in `JourneyClient`); `start = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")`,
assert `start.status_code == 201`, `thread_id = start.json()["thread_id"]`; `turn_id = str(uuid.uuid4())`;
`submit(client, thread_id, turn_id, text)` → `client.call("POST", f"/api/chat/sessions/{thread_id}/turns",
operation_id="submitTurn", body={"turn_id": turn_id, "payload": {"kind": "text", "text": text}})`. Because login and
start happen inside the step, every step's `operations` is `("login", "startChatSession", "submitTurn")`.

**`tests/journeys/j5/test_aea_60.py`** — docstring: "J-5 (AEA-60): a classifier answer outside its options leaves the
rules standing; NODANGER books normally. API level through CON-2 with AEA-57's scripted model (raw output text)."
`test_j5_classifier_outside_options_books_normally(journey)`: step `"J-5 NODANGER, classifier outside its options"`,
`needs=TURN_NEEDS`, `operations=("login", "startChatSession", "submitTurn")`:
1. `journey.script.add(Role.PLANNER, json.dumps({"knowledge": "no", "account": "none", "scheduling": "book_new",
   "handoff": "none", "topic": "booking"}))`; `journey.script.add(Role.CLASSIFIER, json.dumps({DANGER_FIELD:
   "emergency"}))`; `journey.script.add(Role.RESPONDER, json.dumps({"text": "I can help book a visit for your AC."}))`.
2. `resp = submit(client, thread_id, turn_id, NODANGER_TEXT)` with `NODANGER_TEXT = "my AC isn't cooling"`; `resp.status_code == 200`.
3. User sees: no block with `type in {"safety", "conditional_safety", "emergency_line"}`.
4. Stored: `turn = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))` → `gate_result == "clear"`,
   `outcome != "safety_reply"`, `danger_raised in (0, None)`, `"book_new" in json.loads(turn["plan_intents"] or "[]")`;
   `journey.db.count("cases", "thread_id = ?", (thread_id,)) == 0`; `rows = journey.db.rows("SELECT * FROM check_events
   WHERE turn_id = ? AND check_kind = 'classifier'", (turn_id,))` → exactly one, `result == "fallback"`,
   `json.loads(rows[0]["codes"]) == ["fallback", "invalid_output"]`.
5. Adapter calls: `[(c.role, c.result) for c in journey.script.problems()] == [(Role.CLASSIFIER, "invalid_output")]`.

**`tests/journeys/j9/test_aea_60.py`** — docstring names J-9 (a) and (b).
- `test_j9a_both_planners_malformed_hand_off(journey)`: step `"J-9a planner and fallback malformed"`, `needs=CASE_NEEDS`,
  ops `("login", "startChatSession", "submitTurn")`. Script: PLANNER `'{"knowledge": "maybe"}'`; PLANNER_FALLBACK `json.dumps({**json.loads(VALID_PLANNER),
  "extra": "x"})`; CLASSIFIER `CLASSIFIER_NORMAL`; RESPONDER `json.dumps({"text": "I'm passing this to a person."})`.
  Submit `"Can you help me with my account?"` (generated). Assert: 200; a block with `type in {"handoff", "live_queued"}`
  whose `reference` matches `^MHC-C-\d{4}$` and `promise_text` is non-empty; turn row `outcome == "degraded_handoff"`,
  `degrade_reason == "model_error"`, `planner_failed == 1`; `case = journey.db.one("SELECT * FROM cases WHERE thread_id
  = ?", (thread_id,))` → `reason == "ai_failure"`, `priority == "P3"`, `rule_id == "AI.planner_failed"`;
  `[(c.role, c.result) for c in journey.script.problems()] == [(Role.PLANNER, "invalid_output"),
  (Role.PLANNER_FALLBACK, "invalid_output")]`.
- `test_j9b_malformed_draft_code_built_reply(journey)`: step `"J-9b malformed responder draft"`, `needs=TURN_NEEDS`,
  ops `("login", "startChatSession", "submitTurn")`. Script: PLANNER `VALID_PLANNER`; CLASSIFIER `CLASSIFIER_NORMAL`; RESPONDER `json.dumps({"text": ""})`. Submit `"Hi, what
  can you help me with?"`. Assert: 200; a block `type == "failure_offer"` with `person_key is True`; no `type == "text"`
  block; turn `outcome == "degraded_handoff"`, `degrade_reason == "model_error"`; no case row; problems ==
  `[(Role.RESPONDER, "invalid_output")]`; the recorded responder request (`[c for c in journey.script.calls if c.role
  is Role.RESPONDER][0].request`) has `output_model is ResponderDraft` and both labels in `system_prefix +
  system_dynamic + user` *(prompt ↔ consumer at the integrated level)*.

Until AEA-30, AEA-40 and AEA-51 bind `demo_clock`/`demo_service`, `session_service`/`turn_service` and
`run_graph`/`reply_composer`, each step reports `blocked-on AEA-30, AEA-40, AEA-51: …` (the harness's own wording) and skips (the
harness does this; never mark it passed). Run `uv run pytest -m journey tests/journeys/j5/test_aea_60.py
tests/journeys/j9/test_aea_60.py -rs` and copy the skip reasons into the record.

### 5.10 Step 9 — evidence record and context (AC-15)

1. `docs/testing/journeys/<run-date>-AEA-60.md`, the `integrated-journeys.md` §4 table (format of
   `docs/testing/journeys/2026-10-21-AEA-48.md`): **Claim** "AEA-60 prompt ↔ consumer checks: AC-1…AC-12 and AC-14 in
   `tests/contract/test_prompts_vs_consumers.py`; AC-13 J-5 and J-9 steps"; **Level** `mock-tested` for the contract
   module; for the journeys `integrated with a scripted model` only if every step passed, else `mock-tested` with the
   blocked steps listed; **Tested revision** the commit adding the record (code commit SHA); **Environment** VPS,
   Python 3.12, real adapters on `httpx`/`httpx2` `MockTransport`, real `ModelGateway`, real nodes, temp SQLite copy of
   the issued DB, `FakeIndex`, `InMemoryTraceSink`, the real AEA-29 `BriefAssembler`, doubles for AEA-29 `CaseService` and AEA-28
   `SchedulingService`; journeys on AEA-57's harness; **Command** every command of §7; **Result** pass counts per
   command (from the run, not targets); **Evidence location** GitLab issue #60 comment; this file; **Remaining
   limitations** real `CaseService` storage not exercised (AEA-51); live compatibility is AEA-61; F-1 (§8);
   **Blocked by** AEA-30, AEA-40, AEA-51 (as the harness prints them) for the integrated journey level (or "none" if they have landed); **Journeys** J-5, J-9.
2. `docs/design/code-design.md` §9: on the `├── contract/` line (and its continuation line) append
   `; test_prompts_vs_consumers.py + prompts_{compare,world,render,wire,cases}.py (AEA-60, built <code sha>)` — keep the
   tree's alignment; on the `**Built on `main`:**` line add `` `tests/contract/test_prompts_vs_consumers.py` and its
   `prompts_*.py` helpers (AEA-60, `<code sha>`) `` before "the rest of this tree is planned". Change nothing else.
3. `.claude/state/icm-progress.md`: add **one** row directly after the last `Routes verified against code and tests`
   row: `| Routes verified against code and tests | provisional | <run-date>: AEA-60 prompt ↔ consumer checks
   tests/contract/test_prompts_vs_consumers.py (<code sha>; <N> passed); record docs/testing/journeys/<run-date>-AEA-60.md
   | Integrated level when AEA-30, AEA-40 and AEA-51 land |` (≤ 400 characters).
4. `.claude/reference/area-map.md`: unchanged (say so in the report: no area row owns `tests/contract/`).

### 5.11 Step 10 — commit

Two commits on `aea-60-prompt-consumer-checks` (explicit paths, §7.4): `test(AEA-60): prompt ↔ consumer contract checks
and J-5/J-9 journeys` (the eight test files), then `docs(AEA-60): journey record and context rows` (record, DO-3,
ICM). Last line of each message: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push.

---

## 6. Data and fixtures

Synthetic or issued-dev only; nothing from `eval/cases/heldout/`.

| Fixture | Source | Where |
|---|---|---|
| Turn texts 1–5 | WP-3 (turns 1–2), WP-1 (3–4), WP-7 (5): `docs/data/worked-pairs.md` lines 19–30, 102–115, 251–262 | `prompts_world.TURNS` |
| NODANGER `"my AC isn't cooling"` | DO-5 `evaluation-plan.md` line 61 | `prompts_world.NODANGER` |
| WP-2 / WP-8 account texts | `worked-pairs.md` WP-2 ("I got an invoice … and I'm not sure what it's for."), WP-8 ("I want to cancel my Comfort Club membership.") | case table |
| Customer `MHC-10001` (Standard, renewal on record) | issued DB (`customers`), read through `temp_sqlite()`'s working copy | `VERIFIED` |
| Assistant replies, staff line, passages, markers, placeholder keys | generated in the test | `REPLIES`, `STAFF_LINE`, `WP1_PASSAGES`, markers, `secrets.token_hex` |
| Raw provider bodies | generated; shapes copied from AEA-18's `tests/contract/test_jev_adapter.py` (`DANGER_BODY`) and AEA-17's `_anthropic_fixtures.message_body` | `prompts_wire.py` |

No phone number, code, card-like number or email appears anywhere (the masked hint is "the phone ending in 01").

---

## 7. Checks

### 7.1 While iterating (affected tests only)

```bash
uv run pytest tests/contract/test_prompts_vs_consumers.py -q
uv run pytest -m journey tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py -rs
```
If you want parallelism: `uv run --with pytest-xdist pytest -n 2 tests/contract/test_prompts_vs_consumers.py -q` (never
more than `-n 2`; the module-scoped `rendered` fixture is per worker, so serial is usually as fast).

### 7.2 Once before the final commit (cheapest first; stop at the first red)

| # | Gate | Command | Passing looks like |
|---|---|---|---|
| G-1 | Format | `uv run ruff format --check tests/contract/test_prompts_vs_consumers.py tests/contract/prompts_compare.py tests/contract/prompts_world.py tests/contract/prompts_render.py tests/contract/prompts_wire.py tests/contract/prompts_cases.py tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py` | `8 files already formatted` (run without `--check` first if needed) |
| G-2 | Lint | `uv run ruff check <same 8 paths>` | `All checks passed!` |
| G-3 | Types | `uv run mypy <same 8 paths>` | `Success: no issues found` |
| G-4 | Contract module | `uv run pytest tests/contract/test_prompts_vs_consumers.py -q` | all pass, 0 skipped, 0 xfail; record the count |
| G-5 | Collection of the folder (nothing else broke) | `uv run pytest tests/contract -q --co` | collects with no error |
| G-6 | Journey convention + harness | `uv run pytest tests/journeys/support/test_support.py -q -k "convention"` | pass |
| G-7 | This ticket's journeys | `uv run pytest -m journey tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py -rs` | pass, or skipped with `blocked-on AEA-30` / `AEA-40` / `AEA-51` reasons (never failed) |
| G-8 | Affected journeys (AEA addition; `tests/journeys/` is an always-input, so this runs all journeys) | `uv run python -m tests.journeys.affected --base main` | no failure (skips allowed with blocked reasons) |
| G-9 | No product code touched | `git diff --name-only main...HEAD` | only the 11 owned paths of §2.1 |
| G-10 | No sensitive literal | `grep -nE "[0-9]{3}-[0-9]{3}-[0-9]{4}\|[0-9]{4}[ -][0-9]{4}[ -][0-9]{4}\|sk-ant\|\b[0-9]{6}\b" tests/contract/prompts_*.py tests/contract/test_prompts_vs_consumers.py tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py` | no output (if a 6-digit literal is a harmless number such as a token count, write it as an expression, e.g. `300`) |
| G-11 | Context check | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no **new** FAIL. On 2026-10-21 `.claude/state/icm-progress.md` already FAILs its size budget (15,697 B > 8,192 B on `c9b17ea`); that is pre-existing, not this ticket's to fix. Keep the AEA-60 row as short as possible (≤ 250 characters) and report the before/after byte count; do not trim other tickets' rows |

**Full suite:** not required (test-only change; no `conftest.py`, settings, dependency or shared module changes —
`build-loop-test-scope.md`). **Existing tests that must stay green:** everything under `tests/contract/` (G-5 collection)
and `tests/journeys/support/test_support.py` (G-6); nothing else imports these files.

### 7.3 Report (in your final message)

Each AC with its test id and result; the G-1…G-11 outputs (counts from the run); every §4.3 name that differed on
`main`; any PromptDrift the test raised against product code (that is a **defect on the owning ticket** — leave the test
red, name the owner, do not "fix" the test to pass); F-1 status.

### 7.4 `git add` (exact)

```bash
git add tests/contract/test_prompts_vs_consumers.py tests/contract/prompts_compare.py tests/contract/prompts_world.py \
  tests/contract/prompts_render.py tests/contract/prompts_wire.py tests/contract/prompts_cases.py \
  tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py
git add docs/testing/journeys/<run-date>-AEA-60.md docs/design/code-design.md .claude/state/icm-progress.md
```

---

## 8. Risks and requests

| # | Kind | Item | What to do |
|---|---|---|---|
| R-1 | Collision map | Five helper modules `tests/contract/prompts_*.py` are new paths; §3 says "one file each" for prompt files | Orchestrator: accept them as AEA-60's (no other ticket owns or edits them; AEA-59 set the precedent) |
| R-2 | Sibling names | AEA-37 is on a branch and AEA-35/39 are planned only (§4.3). A rename when they merge changes this plan's call sites, not its checks | Implementer follows `main` and reports each difference |
| R-3 | Drift found = red | The test is meant to fail when a prompt and consumer disagree. If it fails against merged product code, the defect belongs to the owner (35/37/38 prompts, 17/18 adapters, 22/27/28/33 tools) | Report with the exact PromptDrift message; never weaken a check |
| R-4 | AC-10 reading (PD-7) | AC-10 lists "InMemoryTraceSink span"; DO-6 line 113 requires the model_call span to keep the masked raw output, which for the 301-char tool call contains the query | Plan asserts that one presence explicitly. Orchestrator: post the PD-7 note on issue #60 so the AC text and DO-6 read the same |
| R-5 | AC-4 overlap (PD-6) | "No routing option equals … danger, burning_unclear" literally hits the classifier's labels, which AC-2 requires | Plan scopes AC-4 to planner/fallback; post on #60 |
| R-6 | Case double (PD-9, refresh 2) | `BriefAssembler` is now real; `CaseService` stays a double (it only stores the brief) | Real case storage is AEA-51's integration; J-9a asserts the stored case row |
| F-1 | **Finding (other tickets)** | `account="appointments"` with `scheduling="none"` makes `join_plan` (AEA-37 step 5–6) emit `READ_APPOINTMENTS` on the **account** specialist, but the account tool set (graph-tools §4: `read_invoices`, `read_membership`, `read_warranty`) has no appointment read, so the model cannot do the task. AC-3 still passes (the specialist is a `SPECS` key) | Orchestrator: raise on #37 and #27 before AEA-51. Options: (a) join maps `appointments` with no scheduling to a scheduling `CONFIRM` task (the scheduling slice already holds appointments) — recommended, no new tool; (b) AEA-27 adds a `read_appointments` account tool (changes graph-tools §4). Not asserted here. Re-checked on AEA-37's branch `36dc321`: still present (`join_plan` clears `appointments` only when `scheduling != "none"`) |
| R-7 | Runtime | Each malformed case builds a temp DB; ~30 cases × (AC-7/8/9 + AC-14) + 4 (AC-10) ≈ 64 runs | Expected well under a minute; if slower, keep correctness, report the time |
| R-9 | Context budget | `icm-progress.md` is already over its 8 KB budget; the one-row AEA-60 addition makes it slightly worse | Orchestrator: schedule a `lane::direct` compaction of `icm-progress.md` (replace per-ticket rows with one rolling row); not in AEA-60's ownership |
| R-8 | Audit hook | Process-wide and permanent once added | Gated by `_GUARD.active`; cheap; never raises |
| R-10 | Blocker chain | AEA-35 and AEA-39 both wait on one NEEDS-DECISION in their own plans (§9.1 of each: where `SpecialistTask`, `KnowledgeSlice`, `AccountSlice` live). AEA-60 has no decision of its own, but it cannot start until that is answered and AEA-35, 37 and 39 merge | Orchestrator: route that single question to Innocent (it unblocks 35, 39 and then 60); merge AEA-37 when its gates are green. Do not dispatch AEA-60's implementer before all three are on `main` |

No shared primitive is requested from the integrator. No signed contract changes. Nothing here needs Innocent.

---

## 9. Readiness

**READY** — every decision is made (PD-1…PD-14); no product decision and no signed-contract change is needed for this
ticket.

**Blocked-on (true imports not yet on `main` at `c9b17ea`; the implementer starts only when all three are merged):**

| Ticket | What this test imports from it | State on 2026-10-21 |
|---|---|---|
| AEA-37 | `planner`, `danger_classifier`, `plan_join`, `join_plan`, `DANGER_FIELD` and the routing wording | built on `aea-37-graph-plan-node` (`36dc321`), not merged |
| AEA-35 | `SPECS`, `REPORT_FACTS_TOOL`, `SpecialistRunner`, the specialist wording | no branch; its plan is NEEDS-DECISION (specialist task types, its §9.1) |
| AEA-39 | `run_specialist`, `escalation` | no branch; the same NEEDS-DECISION, and it needs AEA-35 |

**Why these three are not replaced by doubles.** The slice plan's injection rule covers siblings in the same or a later
wave; these three are wave 2, earlier than AEA-60's wave 3. And the ticket's point is to render prompts "through the real
builders" and feed answers to the real nodes: a double of the builder or node would check the double against itself.

**Now on `main` (no longer blockers):** AEA-17 (`0a85270`), AEA-18 (`900a1d8`), AEA-21 (`5531664`), AEA-27 (`13adc86`),
AEA-28 (`2c2e8c5`), AEA-38 (`042ad35`), AEA-29 (`ef561fc`; the real `BriefAssembler`, PD-9); and, as before, AEA-20, 22, 33, 57.
**Journey level** (`integrated with a scripted model`) waits on AEA-30 (`demo_clock`, `demo_service`; ledger
`blocked`), AEA-40 (CON-2 route, `session_service`, `turn_service`;
branch `aea-40-aea-40-sessions-turns`, not merged) and AEA-51 (`run_graph`, `reply_composer`); until then the steps skip
with their blocked reasons and the record says `mock-tested`.

**Gates:** none (no human, paid or live gate).
