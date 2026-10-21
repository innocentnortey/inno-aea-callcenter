## [AEA-18] models: Jev adapter

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

> **US-5.** As a **homeowner** with no cooling on a hot day, I need to book a visit like any repair, with a couple of
> skippable urgency questions, and to be given the emergency number first if I say someone is in danger, so that I'm
> neither frightened needlessly nor left waiting when it matters.

**What it does in practice.** Model mix B (Innocent, 2026-10-21, after SP-1) gives two decisions to Jev, TypeSafe's
typed-classification model reached through OpenRouter as `typesafe/jev-1.13`: the **planner** (talk or act, which
specialists) and the raise-only **danger classifier** (R-47). Jev returns choices with calibrated probabilities and never
writes text. `JevAdapter` is the one class that talks to it: one HTTP request per call, a typed `Attempt` back, never an
exception. Because Jev's retention period is unstated (research §2e; accepted as a known limit), **every request carries
`provider.data_collection: "deny"`**, and because OpenRouter can report an error inside an HTTP 200 body, the adapter reads
the body for `error` before trusting it (readiness SD-6.3).

**How it works: `adapters/models/openrouter_jev.py`** (DO-3 §4.3; DO-4 §12 as amended by stage7/models.md §1–§3):

- **Implements `ChoiceModel` only.** It has no structured-output or tool methods, so it cannot be configured into a
  responder, brief or specialist role (DO-3 S-1: three role-shaped ports exist so Jev never has to raise for text).
- **Constructor (MOD-1):** `JevAdapter(http: httpx.Client, *, api_key: SecretStr, model: str)`, with
  `provider: ClassVar[ProviderName] = "openrouter_jev"` and a read-only `model`. Construction raises `ValueError` when
  `model` has no `JEV_PRICES` row. `JEV_PRICES` lives in this module (the `TokenPrice` dataclass is imported from
  `meridian.ports.models`, models.md §1, R-G-5): `"typesafe/jev-1.13"` → input $0.042 per million
  tokens, output, cache write and cache read 0.0 (research §2e, S-223, S-219: output tokens are free).
- **Request:** the OpenRouter decisions endpoint as measured in the SP-1 build (`POST
  https://openrouter.ai/api/alpha/decisions`; body `model` = the constructor value, `state` with the instructions and the
  already-redacted state, one `choice` question per `ChoiceField` with its options as criteria, and
  `provider: {"data_collection": "deny"}`), with `timeout=timeout_s`. The key travels only in the `Authorization` header.
- **Answer:** each field's `choice` must be one of that field's options, else `INVALID_OUTPUT`; a missing field or
  unparseable JSON is `INVALID_OUTPUT`; `probabilities` are carried into `ChoiceAnswer` as the provenance of the choice
  (DO-4 §0, §4).
- **What it returns (MOD-1):** `Attempt.record` is a **`ProviderCall`**: `provider` `"openrouter_jev"`, `model` (always
  the constructor value), `latency_ms`, `input_tokens` and `output_tokens` from the response usage (cache and thinking
  counts 0), `cost_usd`, `cost_source`, `status`, `failure`, `provider_request_id` (the response `id` when present),
  `stop_reason` (`None` unless the response carries one; the measured SP-1 shape has none). The gateway adds `role` and `attempt` (stage7/models §1).
- **Cost (MOD-5, stage7/models §2):** the response's `usage.cost` when it is a finite number ≥ 0
  (`cost_source = "reported"`), otherwise `input_tokens × 0.042 / 1e6` (`"price_table"`); a failed attempt with no usage
  block costs 0.0 with all token counts 0 [A]. Why the reported figure wins: it is what OpenRouter bills, the money the
  $30 cap guards; in SP-1, 258 of 258 Jev calls had `usage.cost` equal to input tokens × $0.042/M [M].
- **Failure mapping, done here from raw status and body** (DO-4 §12: no shared classifier): the whole of stage7/models.md
  §3's *OpenRouter / Jev* table. In short: `httpx.TimeoutException` → `TIMEOUT`; `httpx.TransportError` → `CONNECTION`;
  400 → `BAD_REQUEST`; 401 → `AUTH`; **402 → `PROVIDER_SPEND_CAP`** (not retryable); **403 → `AUTH`**; 404 →
  `NOT_FOUND`; **408 → `TIMEOUT`** (`http_status` 408, retryable); 413, 422 and other 4xx → `BAD_REQUEST`; 429 with
  `Retry-After` → `RATE_LIMITED` with `retry_after_s`; **429 without `Retry-After` → `RATE_LIMITED` with
  `retry_after_s = None`, retryable** (MOD-4: OpenRouter puts credit exhaustion on 402, so a bare 429 is a rate limit);
  502, 503 and other 5xx → `SERVER`; **`error` object inside an HTTP 200 → `BODY_ERROR`**, `http_status` = the inner
  `error.code` when it is an int, retryable only when that code is in `{408, 429, 500, 502, 503, 504, 529}` (MOD-2); any
  other exception before a response → `CONNECTION`, after one → `INVALID_OUTPUT`.

**Example pair (DANGER, the labelled synthetic case from SP-1 and the evaluation plan's first dev set).** Input to the
classifier role: the redacted message "my mother is 88 and it's 95 degrees in here" with one choice field whose options are
`normal`, `burning_unclear`, `danger` (the field itself is AEA-37's, `prompts/routing.py`). Expected adapter output, from
the response shape SP-1 measured (`{"answers": {"danger": {"type": "choice", "choice": "danger", "probabilities": {…}}},
"usage": {…}}`): `Attempt(value=ChoiceAnswer(choices={"danger": "danger"}, probabilities={"danger": {…}}),
failure=None)` with a `ProviderCall` whose `model` is `typesafe/jev-1.13` and `cost_source` is `reported` when the usage
block holds `cost`. The same response with `"choice": "emergency"` (not an option) returns `INVALID_OUTPUT` and no value,
so the plan node's rules stand (R-47; DO-4 §4 `DangerAssessment.failure`).

### Source
- stage7/models.md §1 (`ProviderCall`, `Attempt.record`), §2 (constructor, `JEV_PRICES`, cost rule), §3 (OpenRouter /
  Jev table; the `RATE_LIMITED` comment change), §7 (container wiring); decision ledger
  `docs/plans/7b-decisions/models.md` MOD-1, MOD-2, MOD-4, MOD-5, MOD-14.
- DO-4 §4 (`PlannerChoices`, `DangerAssessment.failure`: on failure the rules stand), §11, §12 (port contract: one
  attempt, never raises, same kind for the same situation, `data_collection: "deny"` on every request; the Stage 7
  superseded note), §16 (addenda win).
- DO-3 §4.2 (`ChoiceModel`), §4.3 (`openrouter_jev.py` notes), §6 S-1, S-2, S-22, S-24; §2.1 (no core module imports
  `httpx`).
- DO-1 §8.2 rows *Danger classifier* and *Planner*, §11 decisions 6 and 7; SDQ-6; PRD §6.2 *Models* (mix B), R-47.
- Research `docs/research/2026-10-20-vendor-and-framework-facts.md` §2e (Jev: choices only, ≤ 255 options, price, data
  terms, weaknesses), §4; source register S-229, S-230 (OpenRouter errors and 402).
- SP-1 §3–§4 (mix B decided; Jev p50 0.2 s, p95 0.4 s [M]); SP-1 build plan `docs/plans/fanout/2026-10-20-sp1/build.md`
  step 5 (`JevClient` endpoint, body and measured response; `var/sp1-runs/*.json` for the cost check).
- HP-1, HP-2; US-5.
- **Brief check:** serves "Production-thinking expected: system should be able to run unmanned for a month, failures
  should be observable, and failure handling must be clean (agent admits uncertainty and hands off rather than
  guessing)."; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] **Every** request body carries `provider: {"data_collection": "deny"}` and `model` equal to the constructor value, on success and failure fixtures alike — verify: `tests/contract/test_jev_adapter.py::test_every_request_denies_data_collection` (captures bodies from a mocked transport across every fixture) — evidence: the flag and model present in every captured body.
- [ ] AC-2 [invariant] One HTTP attempt per call, **never raises** for any fixture (including malformed JSON, unmapped statuses and raised exceptions before and after a response), `record` is always a `ProviderCall` with `record.model` equal to the constructor value and `provider` `"openrouter_jev"`; constructing with a model that has no `JEV_PRICES` row raises `ValueError` — verify: `::test_never_raises_and_always_records` and `::test_model_bound_at_construction` — evidence: one request seen per call; an `Attempt` with a `ProviderCall` each time; `ValueError` on an unknown model.
- [ ] AC-3 [failure/refusal] An `error` object inside an HTTP 200 returns `BODY_ERROR` with `http_status` = the inner code, `retryable` true only when that code is in `{408, 429, 500, 502, 503, 504, 529}` — verify: `::test_error_inside_200` (fixtures with inner codes 503, 429, 400 and a non-integer code) — evidence: kind `BODY_ERROR` each time; `retryable` true, true, false, false; `http_status` 503, 429, 400, `None`; no value.
- [ ] AC-4 [failure/refusal] The status mapping is stage7/models.md §3's OpenRouter table: 402 → `PROVIDER_SPEND_CAP` (not retryable); 429 with `Retry-After` → `RATE_LIMITED` with `retry_after_s`; 429 without it → `RATE_LIMITED`, `retry_after_s` `None`, retryable (MOD-4); 403 → `AUTH`; 408 → `TIMEOUT` (retryable); 413 and 422 → `BAD_REQUEST`; 502/503 → `SERVER`; timeout → `TIMEOUT`; transport error → `CONNECTION`; 400/401/404 → `BAD_REQUEST`/`AUTH`/`NOT_FOUND`; an exception before / after a response → `CONNECTION` / `INVALID_OUTPUT` — verify: `::test_failure_kind_mapping` — evidence: fixture → kind table in the test output.
- [ ] AC-5 [failure/refusal] A choice outside its field's options, a missing field, or unparseable JSON returns `INVALID_OUTPUT` and no value; a valid answer carries its probabilities — verify: `::test_choice_validated_against_options` (the DANGER fixture above, plus `"emergency"`, a missing-field variant and a truncated body) — evidence: kinds and values asserted.
- [ ] AC-6 [invariant] `JevAdapter` satisfies `ChoiceModel` (including its read-only `provider` attribute, stage7/models §5) and is **not** accepted where `StructuredModel` or `ToolCallingModel` is required — verify: the project type check (AEA-01's config) over a typing test module `tests/contract/test_jev_adapter_typing.py` that assigns it to each port, with the two invalid assignments marked as expected errors — evidence: the type checker passes only with those two errors expected.
- [ ] AC-7 [negative] No key value or provider message text leaks: a distinctive sentinel in a fixture's error message (both an HTTP error body and an `error` inside a 200) and the configured OpenRouter key value are absent from `ProviderFailure`, `ProviderCall`, the `repr` of both and captured log output; the key appears only in the captured `Authorization` header — verify: `::test_no_key_or_message_in_failure` (fake key string) — evidence: both absent everywhere searched.
- [ ] AC-8 [capture] Each attempt's `ProviderCall` holds the fields DO-6's `model_call` span and the stage7/models §6 `spend_ledger` columns need (provider, model, latency, input and output tokens, `cost_usd`, `cost_source`, status, failure kind and HTTP status, provider request id when present), with cost per MOD-5 — verify: `::test_call_record_fields_and_cost` (a usage block with a finite `cost`; one with no `cost`; one with a negative `cost`; a failed fixture with no usage) — evidence: `reported` with the response's cost; `price_table` with `input_tokens × 0.042 / 1e6` for the second and third; 0.0 and zero tokens for the failure.
- [ ] AC-9 [journey] No deterministic journey reaches this code (journeys replace the provider call with the scripted adapter), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-18.md` says so and names where it is proved instead (`tests/contract/test_jev_adapter.py` and AEA-61's live smoke) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.
- [ ] AC-10 [regression/context] In the same change: `.claude/reference/area-map.md` A2 row (`adapters/models/openrouter_jev.py` planned → actual + commit); `.claude/state/icm-progress.md` A2 evidence replaced; `docs/design/code-design.md` A2 status for this file (planned → built); a dev-log entry per `.claude/reference/dev-log.md` — verify: `git diff --stat` on those paths — evidence: the diff.

### Observability
- Responsibilities: one complete `ProviderCall` per attempt for the planner and classifier roles of WF-1 (and WF-9 /
  WF-10 records tagged `eval` / `load`); the gateway (AEA-20) wraps it as `CallRecord` and turns it into the
  `model_call` span and `spend_ledger` row (stage7/models §5 rule 6). A failure on the planner or classifier is what
  AEA-37 reports as `planner_fallback` / `classifier_fallback` (DO-4 §11). The adapter writes no log line with payload or
  message text (AC-7).
- Capture evidence: AC-8 on fixtures; AEA-51's CAP-1 at CON-2, and its wiring test asserting every ledger row's `model`
  equals its role's `RoleSpec.model` (stage7/models §7).

### Evaluation
- Checks: no suite added. This adapter carries the planner and classifier decisions that E-5 scores (danger recall,
  false alarms) and E-1's trajectory items read. Its own contract file, plus AEA-51's cross-adapter contract test (same
  kinds as the Anthropic adapter for timeout, 408, rate limit, spend cap, invalid choice; DO-3 §4.3, DO-4 §12).
- Expected-answer authority: stage7/models.md §3 and research §2e for failure behaviour; the danger labels E-5 uses come
  from R-8's rule and HP-2 (evaluation plan), not from this adapter.

### Metrics
- References: M-23 (per-step latency), M-24 (failure rate by provider and role), M-25 / M-26 (cost, `cost_source`
  recorded); indirectly M-16 and M-17, whose classifier raises depend on a valid choice reaching AEA-37.
- Acceptance conditions: each stays computable from the `ProviderCall`s this adapter returns once the gateway adds role
  and attempt; an invalid or failed answer is a typed failure, never a silent default, so M-16/M-17 never count a
  failure as a decision. No target here.

### Blocked by
- AEA-02 (ports and domain types: `ChoiceModel` with its `provider` attribute, `ChoiceRequest`, `ChoiceField`,
  `ChoiceAnswer`, `ProviderCall`, `Attempt`, `TokenPrice` (R-G-5), `ProviderName`, the failure types; stage7/models
  cross-topic 2).

### Agent handoff
- Area / owner: A2 Models; file `src/meridian/adapters/models/openrouter_jev.py`, tests `tests/contract/test_jev_adapter.py`
  and `tests/contract/test_jev_adapter_typing.py`, and only its own `register_<area>()` stub in `web/container.py`
  (builds the shared `httpx.Client` and binds `Settings.openrouter_api_key`, stage7/models §7, graph-core.md §12).
- Contracts and shared surfaces: **consumes** `ports/models.py` and `domain/common.py` failure types (AEA-02).
  **Produces** `JevAdapter` and `JEV_PRICES` for AEA-20 (gateway `choice` map: `PLANNER`, `CLASSIFIER`), AEA-37 (planner
  and classifier through the gateway) and AEA-51 (`adapter_for` memoises one adapter per (provider, model); the
  cross-adapter contract test). **Must not edit:** `ports/*`, `domain/*`, `adapters/models/anthropic.py` (AEA-17),
  `agent/gateway.py` (AEA-20), `agent/prompts/routing.py` (AEA-37), `tests/contract/test_model_ports_contract.py`
  (AEA-51), another ticket's container hunk.
- Scope boundary / refusal: one attempt; no retry or backoff (the gateway's 0.5–1 s wait for a bare 429 is AEA-20's),
  no deadline, no fallback to the Sonnet planner (AEA-37 under SDQ-6, and never on a halt), no ledger, no span, no role
  or attempt stamp (AEA-20); **no redaction** — the gateway applies the JEV profile before the request reaches this
  class (AEA-20, data.md §1); no paid call in a default test.
- Wave and gates: wave 1; gates None.
- Lane: `lane::build-loop` — source and tests.
- Risk: **security** (`risk::security`, slice plan §0 and row AEA-18; MOD-14): the adapter holds the OpenRouter key and
  sends text to an endpoint with no stated retention (research §2e). A bug here could drop the `data_collection: deny`
  flag or put a key or message into a failure or log. Frozen failing tests first (AC-1 and AC-7 are the guards);
  `security-privacy-agent` at the wave merge.
- Entry points added or changed: None
- Resolved R-G-5: `TokenPrice` is imported from `meridian.ports.models`; this module declares only its price table
  (models.md §1–§2; AEA-02 writes `TokenPrice` in wave 0). This module never imports `adapters/models/anthropic.py`.
