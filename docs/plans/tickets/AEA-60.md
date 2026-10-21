## [AEA-60] contract: prompt ↔ consumer checks (rendered prompts vs parsers, ToolDefs and schemas)

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

**Why this ticket exists (slice plan §0a, Amendment 1).** On Riverside every unit test passed while real turns failed,
partly because a prompt told the model it could answer with a value the parsing code did not accept. Each prompt ticket
here (AEA-35, 37, 38) tests its own wording, and each consumer ticket (AEA-17, 18, 20, 22, 27, 28, 33) tests its own
parser, but nothing yet puts a **rendered** prompt next to the code that reads the answer. This ticket does, and it also
feeds each consumer the broken answers a real model can send, and checks that the documented fallback happens.

**Example pair 1 (drift caught).** Input: the planner request rendered by `agent/prompts/routing.py` offers the `handoff`
field the options `none, refund, billing_dispute, membership_cancel, unsupported_other, complaint_or_manager,
late_technician`. `PlannerChoices.handoff` (DO-4 §4, plus `late_technician` from graph-core closing table *cases A-6*)
accepts that same set, and `join_plan` maps each value to a `HandoffReason` (`unsupported_other` → `unsupported_action`,
cases.md §3.4). Output: pass. If a later prompt edit adds `cancel_membership`, the test fails with
`routing.planner.handoff offers 'cancel_membership'; PlannerChoices.handoff does not accept it`. Without this check, Jev
would pick the new value, the adapter would map it to `INVALID_OUTPUT` (models.md §3), and every membership-cancel turn
would quietly fall back to the Sonnet planner.

**Example pair 2 (malformed answer).** Input: NODANGER ("my AC isn't cooling") with the Jev classifier's raw reply
`{"danger_level": "emergency"}`. Process: the real `JevAdapter` validates the choice against the field's options and
returns `INVALID_OUTPUT` (models.md §3, not retryable), and the gateway makes no second attempt. Output: the classifier
node writes `DangerAssessment(label="normal", raised=False, failure=invalid_output)`, one `classifier` check event with
result `fallback` and codes `("fallback", "invalid_output")`, and one `classifier_fallback` signal. The turn goes on to
`plan_join` and the booking continues (R-47: the rules stand).

**The behaviour.** One test module, `tests/contract/test_prompts_vs_consumers.py` (slice plan row AEA-60; collision map
"`tests/contract/` (prompt and OpenAPI files)": this file is AEA-60's alone). It also adds two journey files,
`tests/journeys/j5/test_aea_60.py` and `tests/journeys/j9/test_aea_60.py`. It writes no product code. It runs in the
default suite (no `live` marker, no network, no paid call).

1. **Render every prompt the graph sends, through the real builders.** The inputs are typed state built from development
   fixtures (WP-1…WP-8, WP-4F, DANGER, NODANGER) with `FixedClock` (AEA-11, data.md §8a). The request each role would send
   is captured from a recording gateway double that honours DO-4 §12:

   | Role (`Role`, DO-4 §12) | Builder (owner) | What is offered to the model | Consumers checked against |
   |---|---|---|---|
   | `planner` (Jev, `ChoiceModel`) | `agent/prompts/routing.py` planner system text and fields; `plan.py` `planner` node (AEA-37) | `ChoiceRequest.fields`: `knowledge`, `account`, `scheduling`, `handoff`, `topic` with their options | `JevAdapter` option validation (AEA-18, models.md §3); `PlannerChoices` (`LLMFacing`, `extra="forbid"`, DO-4 §0, §4); `join_plan` mapping to `TaskIntent`, `HandoffReason`, `Plan.topic` (DO-4 §4, graph-nodes §5, cases.md §3.4); `ChoiceField.options` ≤ 255 (Jev limit, DO-4 §12) |
   | `planner_fallback` (Sonnet, `ChoiceModel`) | same fields, `Role.PLANNER_FALLBACK` [Decided SDQ-6] | the same `ChoiceRequest` | `AnthropicAdapter` mapping "a choice outside its options" → `INVALID_OUTPUT` (AEA-17, models.md §3); `PlannerChoices` |
   | `classifier` (Jev) | routing classifier system text and its one field (AEA-37) | `danger_level`: `normal`, `burning_unclear`, `danger` | `JevAdapter`; `DangerAssessment.label` (DO-4 §4); `CheckEvent.from_danger` (graph-nodes §1) |
   | `specialist` × knowledge, account, scheduling (Sonnet, `ToolCallingModel`) | `SPECS[kind].render` with `agent/prompts/specialists.py`; tools = `ToolDispatcher.schemas(spec.tool_kinds)` + the `report_facts` schema from `spec.report_model` (AEA-35, graph-tools §2) | tool names, each `ToolSchema.input_schema`, `report_facts` | `ToolRegistry.get` and the dispatch guard order (AEA-22, graph-tools §1); each `ToolDef.args_model`: `KbSearchArgs` (data.md §4), `ReadInvoicesArgs`, `ReadMembershipArgs`, `ReadWarrantyArgs` (graph-tools §4), the scheduling args models of `scheduling_tools` (AEA-28; names read from the registry, never hard-coded); `KnowledgeReport`, `AccountReport`, `SchedulingReport` (DO-4 §5); `KnowledgePoint.passage_id` "a passage returned in this run" (DO-4 §5, GRT-7) |
   | `responder` (Sonnet, `StructuredModel`) | `agent/prompts/reply.py`; `reply.py` `responder` node (AEA-38) | `StructuredRequest.output_model = ResponderDraft`; the labelled blocks "WHAT HAPPENED THIS TURN" and "ALREADY DONE IN THIS CONVERSATION" | `AnthropicAdapter` output validation (AEA-17); `ResponderDraft` (`text` 1–1200 chars, no promise or reference field, DO-4 §9); `check_completion`, `check_facts` (AEA-15) |
   | `brief` (Sonnet) | `agent/prompts/reply.py`; `reply.py` `brief` node (AEA-38) | `output_model = BriefExtraction`; the customer messages shown with their `message_id`s | `BriefExtraction` (`needs` 1–2, `claims` ≤ 5, `Quote.text` ≤ 300, `open_decision` ≤ 200, DO-4 §7); `check_quotes(extraction, shown)` (AEA-38, removal `quote_not_found`); `BriefAssembler.attach_extraction` (AEA-29, DO-4 §7) |

   The tool registry is built exactly as AEA-51's wiring builds it (graph-tools §1): `ToolRegistry((*knowledge_tools(
   retrieval), *account_tools(uow), *scheduling_tools(scheduling)))` from the real factories, with `FakeIndex`, a
   `temp_sqlite()` unit of work (`tests/fixtures/sqlite.py`, AEA-10) and a scheduling-service double that honours DO-4 §14.
   Each request is rendered on turns 1, 2 and 5 of one fixture conversation, so a value offered only on a later turn is
   caught too (workspace rule `context-management-multi-turn` 3).

2. **Compare what is offered with what is accepted, in both directions.**
   - Every value a prompt offers is accepted by its consumer.
   - Every value a consumer accepts from a model is offered by some prompt, except the values only code may set. These
     are the `HandoffReason`s `safety`, `danger`, `burning_unclear`, `customer_requested_person`, `legal_or_chargeback`,
     `commercial`, `fee_bearing_change`, `identity_unverified` and `ai_failure` (DO-4 §7; set by gates, policy words,
     scheduling refusals, identity and escalation rule 6), plus CAS-16's value once Innocent answers it. No prompt may
     offer any of them.
   - Option keys and tool names that the wording itself mentions (system text, field instructions, specialist rules)
     exist in the request they are sent with.

3. **Feed malformed and unsupported outputs through each consumer.** Raw provider bodies go into the real adapters,
   behind a stubbed HTTP transport, as in AEA-17/18's fixture tests. They then pass through the real `ModelGateway`
   (AEA-20; ledger double honouring models.md §6, `InMemoryTraceSink`) and into the real node, runner or dispatcher. Each
   case asserts the documented fallback (AC-7…AC-9).

4. **Prove the check bites.** Monkeypatched copies of the prompt constants or schemas, with one drifted value each, make
   the matching check fail and name the role, field and value. The prompt modules themselves are never edited (AC-11).

**How a reviewer checks it (one command each):**
- `uv run pytest tests/contract/test_prompts_vs_consumers.py -q` covers AC-1…AC-12 and AC-14, at level `mock-tested`. The
  builders and consumers are real; model replies are scripted; there is no server.
- `uv run pytest -m journey tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py` covers AC-13 through the
  real server, at level `integrated with a scripted model`.
- No criterion here claims `verified with live models`. The live smoke set is AEA-61 (`gate::paid`), which waits for this
  ticket.

**What it extends for later tickets.**
- The contract file is data-driven from the real inventory: `Role`, `SPECS`, the registry built from the three factories,
  and each request's `output_model`. A new tool, args model, choice option or report field is therefore checked without
  editing the file.
- A new `Role` or `SPECS` kind with no rendered case fails AC-1. Adding its case is a small follow-up on AEA-60, merged
  first, the same rule as `tests/journeys/support/` for AEA-57.
- Journeys follow the Amendment 1 convention: one file per ticket per journey, `tests/journeys/j<N>/test_aea_<NN>.py`.
  Later tickets add their own file, and never edit `test_aea_60.py` or `support/`.
- Any ticket that changes a prompt, a consumer type, a `ToolDef` or an adapter's output parsing counts this file and
  AEA-60's journey files as **affected** (`build-loop-test-scope.md`, *AEA addition*: "every journey whose path imports or
  calls a changed … prompt, schema").

### Source

- Slice plan `docs/plans/slice-plan.md` §0a (Amendment 1: "AEA-60 prompt ↔ consumer checks (wave 3)"; journey map J-5,
  J-9), §1 row AEA-60 (owns, blockers, wave, lane), §3 collision map (`tests/contract/` prompt and OpenAPI files;
  `tests/journeys/`).
- `.claude/rules/integrated-journeys.md` §3 rule 4 ("Render the **actual** prompts through the real prompt builder with
  real state … Feed malformed and unsupported outputs (unknown tool, missing field, out-of-range enum) and check the
  documented fallback"), rule 5, rule 6, §4 (levels and the evidence record), §5 (who runs what), §6 table row AEA-60.
- `.claude/rules/build-loop-test-scope.md` *AEA addition* (journeys in the merge gate; "affected" includes prompts and
  schemas; contract boundary checks at every wave merge; no paid calls in the suite).
- DO-4 `internal-components.md` §0 (`LLMFacing`, errors never carry values), §3–§5 (`StateFlags`, `PlannerInput`,
  `PlannerChoices`, `DangerAssessment`, `TaskIntent`, `Plan`, `join_plan`; `ToolDef`, `ToolCallScope`, `ToolError`,
  `ToolResult`, the report models, runner rules), §7 (`HandoffReason`, `Quote`, `BriefExtraction`), §9 (`ResponderInput`,
  `ResponderDraft`, `CheckedReply`), §11, §12 (`Role`, `ChoiceField`, `ChoiceRequest`, `StructuredRequest`, `ToolStep`,
  `ModelGateway`), §16 (addenda win).
- `docs/design/contracts/stage7/models.md` §1, §3 (failure mapping: `INVALID_OUTPUT`, `REFUSAL`, `MAX_TOKENS`; which are
  retryable), §5 (gateway rules), cross-topic 4 (fallback only for a failure, never a halt).
- `docs/design/contracts/stage7/graph-tools.md` §1 (`ToolKind`, `ToolErrorCode`, `ToolSchema`, `ToolCall.args None`,
  `ToolCallRecord`, `ToolRegistry`, `ToolDispatcher` guard order and lookup rule; factories), §2 (`RunOutcome.report`,
  `SpecialistSpec`, `SPECS`, `SpecialistRunner`), §4 (account args models), §6 (quick-check `kb_search` call).
- `docs/design/contracts/stage7/graph-nodes.md` §1 (`CheckEvent`, `from_danger`), §4 (`SignalName`, `SignalRecord`, signal
  table with turn outcomes), §5 (`Plan.planner_failed`, GRN-7), §9.4, §9.6 (node signatures).
- `docs/design/contracts/stage7/graph-core.md` §2 (`TurnContext`, `GraphOutcome`), §4 (`GraphDeps`), §11 (router edge 1),
  closing table *cases A-6* (`late_technician`).
- `docs/design/contracts/stage7/cases.md` §3.3–§3.4 (`priority_for`; rule 6 `AI.planner_failed`, `AI.specialist_failed`;
  CAS-16 pending). `docs/design/contracts/stage7/data.md` §1 (redaction profiles), §4 (`KbSearchArgs`, `knowledge_tools`),
  §5 (dev vs held-out case files; DAT-2), §8a (`FixedClock`). `docs/design/contracts/stage7/web.md` §9, §10 (CON-2 turn
  service; the `signal` log record), used by the journey criterion only.
- Decision ledgers: `docs/plans/7b-decisions/graph-tools.md` GRT-1, GRT-6, GRT-7; `graph-nodes.md` GRN-4, GRN-5, GRN-7;
  `models.md` MOD-2; `cases.md` CAS-12, CAS-16; `data.md` DAT-2.
- DO-3 §3 (`agent/prompts/{routing,specialists,reply}.py`), §9 (`tests/contract/`). SP-1 build step 7
  (`docs/plans/fanout/2026-10-20-sp1/build.md`: the measured planner and classifier fields the routing prompt starts from).
- PRD R-46, R-47; HP-1 (how much the model decides vs code), HP-4 (honest handoff, no invented facts).
- **Brief check:** serves "Do not let the agent guess. A confident wrong answer is worse than a handoff." and "failure
  handling must be clean (agent admits uncertainty and hands off rather than guessing)"; touches nothing out of scope;
  weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] The inventory is complete: every `Role` (`planner`, `classifier`, `planner_fallback`, `specialist`, `responder`, `brief`) and every `SPECS` kind (knowledge, account, scheduling) has at least one rendered request built through its real builder, rendered on turns 1, 2 and 5 of one fixture conversation, and the offered sets (options, tool names, output schemas) are identical on all three turns; a role or kind with no case fails the test by name — verify: `tests/contract/test_prompts_vs_consumers.py::test_every_role_and_spec_has_a_rendered_case` — evidence: one parametrised pass per role and kind; a temporary extra `Role` member in a monkeypatched copy fails with its name; level `mock-tested`.
- [ ] AC-2 [invariant] Routing fields match their consumers: the planner request's field names equal `PlannerChoices`' fields; each field's option keys equal its `Literal` set in both directions (`handoff` including `late_technician`), with at most 255 options each; the `planner_fallback` request carries the same fields; the classifier's one field `danger_level` offers exactly `normal`, `burning_unclear`, `danger` (= `DangerAssessment.label`); every option key named in the system text or a field's instructions is an option of that request — verify: `::test_routing_fields_match_planner_choices_and_danger_label` — evidence: set equality asserted per field; level `mock-tested`.
- [ ] AC-3 [invariant] Every offered planner value has a consumer path: for each option of every field, `join_plan` (with fixture gate and state) returns a `Plan` without raising; each non-`none` `handoff` option maps to a `HandoffReason` (`unsupported_other` → `unsupported_action`, `late_technician` → `LATE_TECHNICIAN`) that `priority_for` and the cases.md §3.4 rule table accept; each `account`, `scheduling` and `knowledge` option yields `TaskIntent`s whose `specialist` is a key of `SPECS`; each `topic` option is a `Plan.topic` value — verify: `::test_join_plan_accepts_every_offered_value` (parametrised over every option) — evidence: one pass per option; level `mock-tested`.
- [ ] AC-4 [invariant] No prompt offers a value only code may set: no routing option equals `safety`, `danger`, `burning_unclear`, `customer_requested_person`, `legal_or_chargeback`, `commercial`, `fee_bearing_change`, `identity_unverified` or `ai_failure`, and no specialist tool or report field lets the model set a priority, case reference, promise or customer id — verify: `::test_no_prompt_offers_a_code_only_value` — evidence: the code-only set intersected with every offered set is empty; level `mock-tested`.
- [ ] AC-5 [invariant] Specialist tools match the registry: for each `SPECS` kind the tools sent are `dispatcher.schemas(spec.tool_kinds)` plus `report_facts`; every sent name except `report_facts` resolves through `ToolRegistry.get`, matches `[a-z_]{1,64}`, and has a `kind` in `spec.tool_kinds`; no registry name equals `report_facts`; `check_covers(spec.tool_kinds)` passes; each `input_schema` equals its `ToolDef.args_model` trimmed JSON schema with `strict=True` and contains none of `ToolCallScope`'s fields (`ids`, `customer_id`, `shown_slot_ids`, `now`, `message_id`); the `report_facts` schema equals `spec.report_model`'s; every tool name the specialist wording mentions is among the tools sent with it — verify: `::test_specialist_tools_match_registry_and_report_models` (registry from the real `knowledge_tools`, `account_tools`, `scheduling_tools`) — evidence: per-kind pass; schema equality asserted; level `mock-tested`.
- [ ] AC-6 [invariant] Reply schemas match their consumers: the responder's `output_model` is `ResponderDraft` and the schema sent equals its trimmed schema (one field `text`, 1–1200 chars; no promise or reference field); both labelled blocks "WHAT HAPPENED THIS TURN" and "ALREADY DONE IN THIS CONVERSATION" are present; the brief's `output_model` is `BriefExtraction`; the `message_id`s rendered into the brief request are exactly the keys of the `shown` mapping `check_quotes` receives (customer messages of this thread only), with byte-identical text — verify: `::test_reply_schemas_and_brief_message_ids_match_checks` — evidence: schema and id-set equality asserted on WP-7's refund turn; level `mock-tested`.
- [ ] AC-7 [failure/refusal] Malformed routing outputs reach the documented fallback. Raw Jev bodies with (a) a choice outside its options, (b) a missing field and (c) unparseable JSON each give `INVALID_OUTPUT` with one attempt (not retryable, models.md §3) and exactly one `planner_fallback` call; a valid fallback answer gives the plan with `fallback_used=True` and a `planner_fallback` signal with cause `invalid_output` and `recovered=True`. (d) A malformed Jev reply plus a fallback reply that has an extra field or an option outside its set gives `Plan(mode="act", tasks=(), handoff_request=None, topic="other", source="rules_only", planner_failed=True)` and `recovered=False`. (e) Classifier replies `{"danger_level": "emergency"}` and `{}` give `DangerAssessment(label="normal", raised=False)` with failure `invalid_output`, one `classifier` check event `fallback` with codes `("fallback", "invalid_output")`, and one `classifier_fallback` signal; NODANGER continues to `plan_join` — verify: `::test_malformed_routing_outputs` (parametrised a–e; real `JevAdapter` and `AnthropicAdapter` on a stubbed transport, real gateway, real `plan.py` nodes) — evidence: outcome, plan, check event and signal fields asserted per case; level `mock-tested`.
- [ ] AC-8 [failure/refusal] Malformed specialist outputs reach the documented fallback through the real dispatcher and runner. An unknown tool `issue_refund` gives `unknown_tool`, is not executed, has a `ToolCallRecord` with `kind=None`, writes one `lookup_log` row `refused:unknown_tool`, and the run goes on. The knowledge specialist calling `read_invoices` gives `not_allowed`. `args=None` gives `bad_arguments`. Arguments with an extra `customer_id` gives `bad_arguments` (`extra="forbid"`), with the executor never called. `KbSearchArgs.query` of 301 chars and `invoice_number="INV-12"` give `bad_arguments`. A `report_facts` call failing its report model (6 knowledge points; a 301-char account summary) leaves `RunOutcome.report = None` and the result built from captures only (knowledge: `no_current_source`). A tool step whose body does not parse, or that stops on `max_tokens` or `refusal`, gives `status="failed"` with failure `invalid_output` / `max_tokens` / `refusal`; at the act node that is one `specialist_failed` signal and escalation rule 6 `AI.specialist_failed`, `ai_failure` P3, `degraded=True` — verify: `::test_malformed_specialist_outputs` (parametrised; real registry, dispatcher, runner and act node) — evidence: codes, records, lookup rows, result status and escalation fields asserted per case; level `mock-tested`.
- [ ] AC-9 [failure/refusal] Malformed reply outputs reach the documented fallback. Responder drafts with `text=""`, 1,201 chars, an extra `promise` field, or `stop_reason="refusal"` each give a responder failure: `CheckedReply.fallback_used=True`, the code-built reply from the facts plus a person offer (DO-4 §10), and a `responder_fallback` signal with cause `invalid_output` / `refusal`. Brief extractions with 0 or 3 `needs`, 6 `claims`, or a 201-char `open_decision` leave `brief_extraction=None`, give a `brief_failed` signal with cause `invalid_output`, and leave headings 2, 4 and 7 `not_generated`; the turn is not failed. A schema-valid quote whose `message_id` is an AI or staff message, or whose text is a paraphrase, is removed by `check_quotes` (`quote_not_found`) and gives a `brief_quote` check event with result `trimmed` — verify: `::test_malformed_reply_outputs` (parametrised; real `AnthropicAdapter`, gateway and `reply.py` nodes) — evidence: fields, signals and events asserted per case; level `mock-tested`.
- [ ] AC-10 [negative] Rejected values never travel. The test builds distinctive markers (`zq-rejected-option-7731` as a choice, a 301-char query ending `zq-rejected-query-7731`, a responder draft and a brief quote each containing `zq-rejected-draft-7731`). None of them appears in any `ProviderFailure`, `CallRecord`, `SignalRecord`, `CheckEvent`, `ToolError.message`, `ToolCallRecord`, `lookup_log` row, captured log record or `InMemoryTraceSink` span from AC-7…AC-9 (DO-4 §0 "Errors never carry values") — verify: `::test_rejected_values_absent_from_records` (caplog plus the sink and the DB copy) — evidence: substring search over every serialised record returns nothing; level `mock-tested`.
- [ ] AC-11 [failure/refusal] The check bites. Monkeypatched copies, each with one drifted value, make the matching check fail with a message naming the role, field and value (never customer text): a planner `handoff` option `cancel_membership` added; `late_technician` removed; a classifier option `emergency` added; specialist wording naming `refund_invoice`; a responder `output_model` with an extra `promise` field; a brief request whose shown ids include a staff message — verify: `::test_check_fails_on_drift` (parametrised; `pytest.raises` on the shared comparison helper) — evidence: six expected failures with their messages; the prompt modules are unchanged in `git diff`; level `mock-tested`.
- [ ] AC-12 [negative] Development data only, and no network. Every fixture comes from WP-1…WP-8, WP-4F, DANGER, NODANGER or values generated in the test; the module never opens a path under `eval/cases/heldout/` or the held-out key directory (data.md §5, DAT-2) and opens no socket — verify: `::test_no_heldout_reads_and_no_network` (a `sys.addaudithook` `open` audit and a socket guard around the whole module) — evidence: zero audited held-out opens; zero socket connects; level `mock-tested`.
- [ ] AC-13 [journey] Extends J-5 and J-9 (slice plan §0a journey map) through CON-2 with the scripted model adapter returning raw provider bodies. J-5: NODANGER with a classifier body outside its options books normally; no case row is written, and the stored `check_events` hold one `classifier` event `fallback`. J-9 (a): a malformed Jev planner reply plus a malformed fallback reply → the customer sees the handoff reply with its reference and promise; the stored turn has `outcome = degraded_handoff` and `degrade_reason = model_error`, and one case has reason `ai_failure`, priority P3. J-9 (b): a malformed responder draft → the code-built fallback reply; turn `degraded_handoff` / `model_error`. Files: `tests/journeys/j5/test_aea_60.py`, `tests/journeys/j9/test_aea_60.py` — verify: `uv run pytest -m journey tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py` — evidence: the steps pass at level `integrated with a scripted model`, each asserting what the user sees and what is stored; until AEA-57's harness accepts raw provider bodies and AEA-51's J-5 and J-9 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-60.md` states level `mock-tested` and *Blocked by* AEA-57, AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-14 [capture] Every malformed case leaves the WF-1 records the observability contract needs, with codes only: the gateway's `CallRecord` with `status="error"` and its failure kind (a ledger-double row and an `InMemoryTraceSink` model-call span per attempt); the `signal` record (`name`, `cause`, `role`, `node`, `turn_id`, `thread_id`, `request_id`, `run_tag`); the `classifier` / `brief_quote` check events; one `lookup_log` row per dispatched call — verify: `::test_malformed_cases_leave_their_records` — evidence: record counts and fields asserted per case of AC-7…AC-9; level `mock-tested` (the real-entry-point capture stays CAP-1 and CAP-2 in AEA-51).
- [ ] AC-15 [regression/context] Docs updated in the same change — verify: `git diff --name-only` — evidence: `docs/design/code-design.md` §9 `contract/` line lists `test_prompts_vs_consumers.py` (planned → built, with the commit); `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced, only this ticket's link added); the evidence record `docs/testing/journeys/YYYY-MM-DD-AEA-60.md` with every field of `integrated-journeys.md` §4; `.claude/reference/area-map.md` unchanged (no area row owns `tests/contract/`), said so in the MR.

### Observability

- Responsibilities: emits no record of its own and adds no entry point. For WF-1 (customer chat turn) it proves that the
  records a malformed model reply must leave are still emitted, holding codes only: the gateway's `model_call` span and
  `spend_ledger` row with `status="error"` and the failure kind (models.md §1, §3); the `signal` log records
  `planner_fallback`, `classifier_fallback`, `specialist_failed`, `responder_fallback`, `brief_failed` (graph-nodes §4;
  web.md §10); the `classifier` and `brief_quote` check events (graph-nodes §1); one `lookup_log` row per refused tool call
  with `result_seen = "refused:<code>"` (graph-tools §1); and, at J-9, the `turn` row's `degraded_handoff` / `model_error`.
- Capture evidence: AC-14 (records per malformed case), AC-10 (rejected values absent from every record, log and span),
  AC-13 (stored turn, case and check-event rows through CON-2). CAP-1 and CAP-2 at the real entry point stay with AEA-51.

### Evaluation

- Checks: adds no E-n case and runs no eval. The module runs in the default suite at every ticket merge that touches a
  prompt or consumer and at every wave merge (contract boundary checks). It keeps the E-1, E-3, E-4 and E-5 runs
  meaningful: a value the model can be offered is always one the graph can act on, so a failed case is a real agent
  failure, not prompt drift. Live compatibility of the same prompts is AEA-61's smoke set, which is not an E-run.
- Expected-answer authority: the consuming type or function as signed in DO-4 and the Stage 7 addenda (the `Literal` sets
  and `Field` limits, the `ToolRegistry` built from the three factories, models.md §3's failure mapping, graph-nodes §4's
  signal table, cases.md §3.4 rule 6). Never the prompt text, and never a model.

### Metrics

- References: M-3 (planner `topic` options equal `Plan.topic`, so the topic segment stays assignable), M-12 (`brief_quote`
  and brief fact check events stay recorded on a malformed brief), M-16 and M-17 (a malformed classifier reply still
  writes its `classifier` `fallback` event, so the per-turn denominator holds), M-24 (malformed replies end
  `degraded_handoff` with `degrade_reason = model_error` and a `model_call` error record, so they are counted).
- Acceptance conditions: each of these stays computable from the records AC-13 and AC-14 assert. No target is set or
  changed here.

### Blocked by

AEA-20, AEA-22, AEA-35, AEA-37, AEA-38, AEA-39 (slice plan row AEA-60). It also reads code from earlier waves that is on
`main` by wave 3: AEA-02, 04, 10, 11, 15, 17, 18, 21, 27, 28, 33, 57. The journey criterion's integrated level waits on
AEA-51 (same wave), which first lands J-5 and J-9.

### Agent handoff

- Area / owner: tests only, `tests/contract/test_prompts_vs_consumers.py` (DO-3 §9 `contract/`), plus
  `tests/journeys/j5/test_aea_60.py` and `tests/journeys/j9/test_aea_60.py`.
- Contracts and shared surfaces: reads (never edits) `agent/prompts/{routing,specialists,reply}.py` (AEA-37, 35, 38),
  `agent/nodes/{plan,act,reply}.py` (AEA-37, 39, 38), `agent/specialists/{specs,runner}.py` (AEA-35),
  `agent/tools/{dispatch,knowledge,account,scheduling}.py` (AEA-22, 33, 27, 28), `agent/gateway.py` (AEA-20), the two
  adapters (AEA-17, 18), `checks.py` (AEA-15), `domain/*` and `ports/models.py` (AEA-02), `tests/fakes/` (AEA-11) and
  `tests/journeys/support/` (AEA-57). It produces the check that AEA-61's live smoke set waits for. Every later prompt,
  schema, tool or adapter change counts it as affected. A missing scripted-adapter capability (raw provider bodies,
  `stop_reason`) is a follow-up on AEA-57, merged first. A missing builder entry point is a follow-up on the owning prompt
  ticket. This ticket never adds either to its own files.
- Scope boundary / refusal: no prompt wording, consumer type, `ToolDef` or adapter changes. A mismatch it finds is reported
  as a defect on the owning ticket, and the test stays red until that is fixed. No paid or live call; that is AEA-61. No
  OpenAPI or fixture validation; that is AEA-59. No browser; that is AEA-58. No redaction assertions beyond AC-10; those
  are AEA-04, 35 and 37, and CAP-1 in AEA-51.
- Reviewer command: `uv run ruff check && uv run ruff format --check`, the type check AEA-01 fixes, then
  `uv run pytest tests/contract/test_prompts_vs_consumers.py -q` and
  `uv run pytest -m journey tests/journeys/j5/test_aea_60.py tests/journeys/j9/test_aea_60.py` (cheapest first). The
  reviewer runs them; reading the diff does not count as a check (`integrated-journeys.md` rule 5).
- Awaiting Innocent: CAS-16 — built on the recommended option (A: a new code-set reason `burning_ruled_out`, P2). AC-4's
  code-only set then gains `burning_ruled_out`, and AC-2/AC-3 assert the planner never offers it. If he picks B (P1, no new
  reason), the set is unchanged. Either way, no prompt option changes.
- Awaiting Innocent: DAT-2 — built on the recommended option (B: held-out answer keys outside the repo, for example
  `/home/linuxuser/.meridian-sealed/heldout/`). AC-12's audit guards `eval/cases/heldout/` and the configured key
  directory. If he picks A, only the guarded path changes, to `eval/cases/heldout/` alone.
- Awaiting UX session: nothing. This ticket reads nothing under `apps/web/` and asserts no selector or build output. J-5
  and J-9 here run at the API level (CON-2). Their browser versions belong to AEA-58 and the `docs/plans/ux-join/`
  contract.
- Plan note for the orchestrator: `integrated-journeys.md` §5 and §6 name AEA-60 for the live smoke set too. Slice plan
  §0a, which is authoritative, moved that to AEA-61. This ticket follows the plan, and the rule's two rows should be
  reconciled when the rule is next edited.
- Wave and gates: wave 3; no gate.
- Lane: build-loop — it adds tests that run in the merge gate (`ticket-lanes.md`: tests are code-read).
- Risk: None per the slice plan. It reads no secret and writes no product code. AC-10 and AC-12 cover the values it
  handles.
- Entry points added or changed: None
  (test-only; AC-13 drives the existing CON-2 route, owned by AEA-40, and changes nothing in it).
