## [AEA-17] models: Anthropic adapter

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

> **US-16.** As a **homeowner**, I need the assistant never to say "done", "cancelled" or "refunded" unless it really did
> it, and to hand me to a person when it hits a limit, so that I can believe what it says. *(Acceptance: a rate or spend
> limit → a handoff, not an error page.)*

**What it does in practice.** Every Sonnet 5.5 call in the system (specialists, responder, brief, and the planner
fallback; DO-2 §A.1, SDQ-6) goes through one class, `AnthropicAdapter`, which makes **exactly one HTTP request** and
hands back a typed `Attempt`: the value, a `ProviderCall` that is always present, and a `ProviderFailure` when it failed.
It **never raises** to its caller. Retrying, deadlines, the ledger, spans, redaction and the role/attempt stamp are the
gateway's job (AEA-20); this class only speaks Anthropic and translates Anthropic's ways of failing into our
`ProviderFailureKind`s, so a 429 that means "monthly spend cap reached" is never retried as if it were a rate limit
(DO-4 §11; stage7/models.md §3).

**How it works: `adapters/models/anthropic.py`** (DO-3 §4.2, §4.3; DO-4 §12 as amended by stage7/models.md §1–§3):

- **Constructor (MOD-1):** `AnthropicAdapter(client: anthropic.Anthropic, *, model: str)`, with
  `provider: ClassVar[ProviderName] = "anthropic"` and a read-only `model`. Construction raises `ValueError` when `model`
  has no `ANTHROPIC_PRICES` row, so start-up fails instead of recording $0. `ANTHROPIC_PRICES` lives in this module
  (the `TokenPrice` dataclass is imported from `meridian.ports.models`, models.md §1, R-G-5), keyed by model ID: `"claude-sonnet-5-5"` → `TokenPrice(input=2.00, output=10.00, cache_write_5m=2.50,
  cache_read=0.10)` US dollars per million tokens (research §2a, S-187). The SDK client is built once by the container
  with `max_retries=0` (the SDK otherwise honours any `retry-after` with no ceiling, research §4).
- **What it returns (MOD-1):** `Attempt.record` is a **`ProviderCall`**, not a `CallRecord`: `provider`, `model` (always
  the constructor value, never what the response reports), `latency_ms`, `input_tokens`, `output_tokens`,
  `cache_read_tokens`, `cache_write_tokens`, `thinking_tokens`, `cost_usd`, `cost_source` (always `"price_table"`,
  MOD-5), `status` (`ok`/`error`), `failure` (set exactly when `status == "error"`), `provider_request_id` (the response's
  `request-id`), `stop_reason`. The gateway adds `role` and `attempt` with `CallRecord.from_provider` (stage7/models §1).
- **Cost (stage7/models §2, MOD-16):** `(input × 2.00 + output × 10.00 + cache_write × 2.50 + cache_read × 0.10) / 1e6`.
  `output_tokens` already contains thinking (research §1), so `thinking_tokens` is recorded for information only and is
  **never** priced. A failed attempt with no usage block: `cost_usd` 0.0 and every token count 0 [A] (the known
  undercount and its replacement measurement are stage7/models §2).
- **The three ports** (DO-4 §12; method signatures unchanged):
  - `ChoiceModel.choose` (the Sonnet planner fallback, SDQ-6): one enum-JSON structured request built from the
    `ChoiceField`s; each answer validated against its field's options; `probabilities` is `None` (Sonnet reports no
    calibrated confidence, DO-4 §0).
  - `StructuredModel.structured`: the request's `output_model` schema sent as `output_config.format`; the reply validated
    into `T`.
  - `ToolCallingModel.start` / `tool_step` / `append`: tools sent with `strict: true` and `tool_choice` **`auto` only**
    (forced `any` / `tool` returns 400 on Sonnet 5.5, research §1). `start` and `append` build and extend
    `ProviderMessages(provider, model, items)` (MOD-17): `items` are Anthropic's own message objects, in order, untouched,
    so thinking blocks keep their signatures; every tool result goes back with its `tool_use_id`. `append` with a
    `ProviderMessages` whose `provider` or `model` differs from this adapter's raises `ValueError` (a wiring bug, not an
    `Attempt.failure`).
- **Request rules:** the call gets `timeout=timeout_s`; effort per request (`low`/`medium`/`high`); the stable
  `system_prefix` carries `cache_control` and `system_dynamic` does not; `thinking: {"type": "disabled"}` is never sent
  (400 on Sonnet 5.5, research §1).
- **`stop_reason` before content:** `refusal` → `REFUSAL`, `max_tokens` → `MAX_TOKENS`, with no value even when text
  blocks are present.
- **Failure mapping, done here and nowhere else** (DO-4 §12: no shared classifier; DO-3 S-24): the whole of
  stage7/models.md §3's *Anthropic* table. In short: `APITimeoutError` → `TIMEOUT`; `APIConnectionError` → `CONNECTION`;
  400 matching the spend-limit pattern → `OUR_SPEND_LIMIT`; other 400 → `BAD_REQUEST`; 401 → `AUTH`; **402
  `billing_error` → `PROVIDER_SPEND_CAP`**; **403 → `AUTH`**; 404 → `NOT_FOUND`; **408 → `TIMEOUT`** (`http_status`
  408); **409 → `SERVER`** (`http_status` 409); **413 → `BAD_REQUEST`**; 429 with `retry-after` or `retry-after-ms` →
  `RATE_LIMITED` with `retry_after_s`; **429 with neither → `PROVIDER_SPEND_CAP`** (research §2b); 529 → `OVERLOADED`;
  500, 504 and any other 5xx → `SERVER`; any other 4xx → `BAD_REQUEST`; output failing parsing or `output_model`, or a
  choice outside its options → `INVALID_OUTPUT`; any other exception before a response → `CONNECTION`, after a response
  → `INVALID_OUTPUT` (MOD-2). `retryable` is true only for `TIMEOUT`, `CONNECTION`, `RATE_LIMITED`, `OVERLOADED`,
  `SERVER` (DO-4 §11).
- **Spend-limit pattern (MOD-3, [A]):** a 400 is `OUR_SPEND_LIMIT` when `error.type == "invalid_request_error"` and the
  lower-cased `error.message` contains `"spend limit"`, `"usage limit"` or `"credit balance"`. The message is read to
  classify and then dropped: it never reaches `ProviderFailure`, `ProviderCall`, a log line or a span. A 400 that matches
  no rule logs the fixed string `anthropic_400_unclassified` with the request ID only. Replaced by the `error.message`
  of the first real spend-limit 400.

**Example pair: none customer-visible; the unit is provider response → typed attempt.** A recorded HTTP 429 with no
`retry-after` header becomes `Attempt(value=None, failure.kind=PROVIDER_SPEND_CAP, failure.retryable=False)` with
`record.model == "claude-sonnet-5-5"`, `record.status == "error"`, `record.cost_usd == 0.0`. That is what lets the
gateway trip the circuit (stage7/models §5 rule 7) and the turn end in the `SPEND_CAP_REACHED` handoff US-16 asks for.
The stage7/models §1 example is the same shape: a 529 returns `ProviderCall(provider="anthropic",
model="claude-sonnet-5-5", status="error", failure.kind=OVERLOADED, …)`; the gateway, not this class, writes
`CallRecord(role=RESPONDER, attempt=1, …)`.

### Source
- stage7/models.md §1 (`ProviderCall`, `Attempt.record`, `ProviderMessages`), §2 (constructor, `ANTHROPIC_PRICES`, cost
  rule), §3 (Anthropic table, spend-limit pattern), §7 (one SDK client, `max_retries=0`); decision ledger
  `docs/plans/7b-decisions/models.md` MOD-1, MOD-2, MOD-3, MOD-5, MOD-14, MOD-16, MOD-17.
- DO-4 §11 (`ProviderFailureKind`, `ProviderFailure`), §12 (port Protocols, request/answer types, "Contract every
  implementation honours"; the Stage 7 superseded note), §16 (addenda win).
- DO-3 §4.2 (ports), §4.3 (`adapters/models/anthropic.py` notes), §6 S-1, S-2, S-24, §2.1 (no core module imports
  `anthropic`).
- DO-1 §8.1 (SDK retries off; retryable statuses incl. 408, 409), §11 decision 5; PRD R-41, §6.2 *Models* (mix B: Sonnet
  for words).
- Research `docs/research/2026-10-20-vendor-and-framework-facts.md` §1 (tool use, structured outputs, thinking, errors,
  `request-id`), §2a (model ID, prices), §2b (spend-cap 429 has no `retry-after`), §4 (error table, SDK retry behaviour).
- SP-1 build plan `docs/plans/fanout/2026-10-20-sp1/build.md` step 5 (`AnthropicClient` request and usage shapes,
  measured; "`model` is always `spec.model`").
- HP-1 (two-layer turn); US-16.
- **Brief check:** serves "Production-thinking expected: system should be able to run unmanned for a month, failures
  should be observable, and failure handling must be clean (agent admits uncertainty and hands off rather than
  guessing)."; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] One HTTP attempt per call and **never raises** for every port method and every fixture, including SDK exceptions raised before and after a response, malformed bodies and unmapped statuses; `record` is a `ProviderCall` on success and on failure, with `status` and `failure` consistent — verify: `tests/contract/test_anthropic_adapter.py::test_never_raises_and_always_records` (parametrised over every fixture) — evidence: each case returns an `Attempt` whose `record` is a `ProviderCall` (no `role`, no `attempt` field); the mocked transport saw exactly one request; `failure is not None` exactly when `record.status == "error"`.
- [ ] AC-2 [invariant] The adapter is bound to its model: `record.model` equals the constructor value on every fixture (even when the response names another model), `provider` is `"anthropic"`, and constructing with a model that has no `ANTHROPIC_PRICES` row raises `ValueError` — verify: `::test_model_bound_at_construction` — evidence: equality asserted across fixtures; `ValueError` on `AnthropicAdapter(client, model="claude-unknown")`.
- [ ] AC-3 [failure/refusal] The failure mapping is stage7/models.md §3's Anthropic table, with `retryable`, `http_status` and `retry_after_s` as it states — verify: `tests/contract/test_anthropic_adapter.py::test_failure_kind_mapping` (hand-built fixtures: timeout, connection error, 400, 400 spend-limit, 401, 402, 403, 404, 408, 409, 413, 418, 429 with `retry-after`, 429 with `retry-after-ms`, 429 with neither, 529, 500, 504, and two raised exceptions, one before and one after a response) — evidence: a fixture → kind table in the test output; 429-with-neither and 402 are `PROVIDER_SPEND_CAP`, not retryable; 408 is `TIMEOUT` and 409 is `SERVER`, both retryable; 403 is `AUTH`; 413 and 418 are `BAD_REQUEST`; the two exceptions are `CONNECTION` and `INVALID_OUTPUT`.
- [ ] AC-4 [failure/refusal] A 400 is `OUR_SPEND_LIMIT` only when `error.type` is `invalid_request_error` and the message contains "spend limit", "usage limit" or "credit balance" in any case (MOD-3); an unmatched 400 is `BAD_REQUEST` and logs exactly `anthropic_400_unclassified` with the request ID — verify: `::test_spend_limit_400_pattern` (three matching messages in mixed case, one non-matching message, one matching phrase under another `error.type`) — evidence: kinds asserted; one captured log record whose message is the fixed string and whose fields hold only the request ID.
- [ ] AC-5 [failure/refusal] `stop_reason` is read before content: a `refusal` or `max_tokens` response returns that kind and no value, even when text blocks are present — verify: `::test_stop_reason_checked_first` — evidence: `value is None`, kinds `REFUSAL` / `MAX_TOKENS`, `record.stop_reason` set.
- [ ] AC-6 [invariant] Request shape: `tool_choice` is `{"type": "auto"}` on every tool step and never `any`/`tool`; tools carry `strict: true`; structured and choice calls send `output_config.format`; `cache_control` sits on the system-prefix block only; no `thinking: disabled`; the call carries `timeout_s`; the container-built client has `max_retries=0` — verify: `::test_request_shape` (captures request bodies from a mocked transport) and `::test_client_built_without_retries` (this ticket's `register_<area>()` hunk) — evidence: the asserted bodies; `client.max_retries == 0`.
- [ ] AC-7 [invariant] Output validation: a structured reply that fails `output_model` validation, or a choice not in its field's options, returns `INVALID_OUTPUT`; a valid choice returns `ChoiceAnswer` with `probabilities=None` — verify: `::test_invalid_output_and_choice_validation` — evidence: kinds and values asserted.
- [ ] AC-8 [invariant] Tool steps round-trip through `ProviderMessages` (MOD-17): a response holding a thinking block and two `tool_use` blocks yields two `ToolCall`s (an unparseable input gives `args=None`); `append` returns `ProviderMessages(provider="anthropic", model=<constructor value>, items=…)` whose items carry the assistant content unchanged (thinking signature byte-identical) followed by `tool_result` blocks whose ids match; `append` with a `ProviderMessages` of another provider or model raises `ValueError` — verify: `::test_tool_step_round_trip` and `::test_append_rejects_foreign_messages` — evidence: the appended item list asserted; `ValueError` raised for both mismatches.
- [ ] AC-9 [negative] No key value or provider message text leaks: a distinctive sentinel placed in a fixture error's `message` (including inside a message that matches the spend-limit pattern) and the configured API key value are absent from the returned `ProviderFailure`, `ProviderCall`, the `repr` of both and all captured log output; `provider_request_id` holds only the request id — verify: `::test_no_key_or_message_in_failure` (fake key string, never a real one) — evidence: sentinel and key absent everywhere searched; request id present.
- [ ] AC-10 [capture] Every attempt's `ProviderCall` holds the fields DO-6's `model_call` span and the stage7/models §6 `spend_ledger` columns need (provider, model, latency, input/output/cache-read/cache-write/thinking tokens, `cost_usd`, `cost_source` = `price_table`, status, failure kind and HTTP status, provider request id, `stop_reason`), with cost per the §2 rule — verify: `::test_call_record_fields_and_cost` (a fixture usage block with non-zero thinking tokens → expected cost computed in the test from `ANTHROPIC_PRICES`, output tokens priced once; a failed fixture with no usage block) — evidence: fields asserted; cost equal to the hand computation and unchanged when `thinking_tokens` changes; the failed fixture has `cost_usd` 0.0 and all token counts 0.
- [ ] AC-11 [journey] No deterministic journey reaches this code (journeys replace the provider call with the scripted adapter), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-17.md` says so and names where it is proved instead (`tests/contract/test_anthropic_adapter.py` and AEA-61's live smoke) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.
- [ ] AC-12 [regression/context] In the same change: `.claude/reference/area-map.md` A2 row (`adapters/models/anthropic.py` planned → actual + commit); `.claude/state/icm-progress.md` A2 evidence replaced; `docs/design/code-design.md` A2 status for this file (planned → built); a dev-log entry per `.claude/reference/dev-log.md` — verify: `git diff --stat` on those paths — evidence: the diff.

### Observability
- Responsibilities: one complete `ProviderCall` per HTTP attempt (AC-10), the raw material of WF-1's `model_call` spans
  and `spend_ledger` rows (and of WF-9 / WF-10 records tagged `eval` / `load`). The adapter writes no span, row or
  ledger entry itself; the gateway (AEA-20) wraps the call as `CallRecord` and records both (stage7/models §5 rule 6).
  Its only log line is the fixed `anthropic_400_unclassified` string with a request ID (AC-4).
- Capture evidence: AC-10 here on fixtures; AEA-51's CAP-1 drives CON-2 and finds the spans and spend rows, and its
  wiring test asserts every ledger row's `model` equals its role's `RoleSpec.model` (stage7/models §7).

### Evaluation
- Checks: adds none to E-1…E-8. Its own contract file, and AEA-51's `tests/contract/test_model_ports_contract.py`
  (same `ProviderFailureKind` as the Jev adapter for the same situation: timeout, 408, rate limit, spend cap, invalid
  choice; DO-3 §4.3, DO-4 §12).
- Expected-answer authority: Anthropic's documented behaviour as recorded in research §1, §2b, §4, and stage7/models.md
  §3's Anthropic table (which completes DO-4 §11).

### Metrics
- References: M-23 (latency per step: needs `latency_ms`), M-24 (failure rate per provider and role: needs the kind and
  HTTP status), M-25 and M-26 (cost per conversation and per day: need `cost_usd`).
- Acceptance conditions: each stays computable from the `ProviderCall`s this adapter returns once the gateway adds role
  and attempt (AC-3, AC-10); cost is never double-counted for thinking (MOD-16). No target here.

### Blocked by
- AEA-02 (ports and domain types: the three model ports with their `provider` attribute, `ProviderCall`, `Attempt`,
  `ProviderMessages`, `TokenPrice` (R-G-5), `ProviderName`, `ProviderFailureKind`, `ProviderFailure`; stage7/models
  cross-topic 2).

### Agent handoff
- Area / owner: A2 Models; file `src/meridian/adapters/models/anthropic.py`, test `tests/contract/test_anthropic_adapter.py`,
  and only its own `register_<area>()` stub in `web/container.py` (builds the one `anthropic.Anthropic` client with
  `max_retries=0` from `Settings.anthropic_api_key`, stage7/models §7, graph-core.md §12).
- Contracts and shared surfaces: **consumes** `ports/models.py` (`ChoiceModel`, `StructuredModel`, `ToolCallingModel`,
  request/answer types, `ProviderCall`, `Attempt`, `ProviderMessages(provider, model, items)` (models.md §1, R-G-4),
  `TokenPrice` (R-G-5), `ToolSchema`, `ToolCall`) and `domain/common.py`
  (`ProviderFailureKind`, `ProviderFailure`) from AEA-02. **Produces** `AnthropicAdapter` and `ANTHROPIC_PRICES` for
  AEA-20 (gateway, every Sonnet role),
  AEA-51 (`adapter_for` memoises one adapter per (provider, model); runs the cross-adapter contract test) and, through
  the gateway, AEA-35/37/38. **Must not edit:** `ports/*`, `domain/*`, `adapters/models/openrouter_jev.py` (AEA-18),
  `agent/gateway.py` (AEA-20), `tests/contract/test_model_ports_contract.py` (AEA-51), another ticket's container hunk.
- Scope boundary / refusal: one attempt per call; **no retry loop, no deadline arithmetic, no ledger write, no span, no
  redaction, no role or attempt stamp** (all AEA-20); no shared failure-classifier module (S-24); no streaming (SDQ-2);
  no paid call in any default test (fixtures are hand-built from research §1/§4 and the SP-1 build's measured shapes).
- Wave and gates: wave 1; gates None.
- Lane: `lane::build-loop` — source and tests.
- Risk: **security** (`risk::security`, slice plan §0 and row AEA-17; MOD-14): the adapter holds the Anthropic key and
  reads provider error messages; a bug here could put a key or a payload into a failure, log or span. Frozen failing
  tests first (AC-9 is the guard); `security-privacy-agent` at the wave merge.
- Entry points added or changed: None
- Resolved R-G-5: `TokenPrice` is imported from `meridian.ports.models`; this module declares only its price table
  (models.md §1–§2; AEA-02 writes `TokenPrice` in wave 0). Neither adapter imports the other's module.
