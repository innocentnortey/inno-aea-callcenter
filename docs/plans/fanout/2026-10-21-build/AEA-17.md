# Plan — [AEA-17] models: Anthropic adapter

**Status:** planned — READY; blocked only on **AEA-02 merged on `main`** (it supplies `meridian.ports.models` and
`meridian.domain.common`). AEA-01 is on `main`.
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #17 (= `docs/plans/tickets/AEA-17.md`; no comments on the issue as
of 2026-10-21) · **Base revision:** `16ca639` (main, 2026-10-21; AEA-01, 03, 04, 08, 25 merged)
**Lane / risk:** `lane::build-loop` · `risk::security` (MOD-14): `test-writer-agent` freezes the tests in §3.3 first;
`security-privacy-agent` reads this diff at the wave-1 merge.
**Gates:** none (wave 1; no human, paid or live gate; live compatibility is AEA-61's `gate::paid` smoke).
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21; refreshed the same day against `main` `16ca639` and AEA-02's
branch `aea-02-aea-02-domain-ports` at `de9bb42` (its frozen tests). **Implementer:** `fanout-implementer` on Sonnet.

**What changed in the refresh (read this first if you saw the earlier version):**
1. **Earlier request R-1 is withdrawn.** It asked AEA-02 to set `str_strip_whitespace=False` on `ProviderMessages` and
   `ToolStep`. AEA-02's frozen test `tests/unit/domain/test_conventions.py::test_every_model_uses_meridian_config`
   requires `str_strip_whitespace is True` on **every** model in `meridian.ports.models`, so that request would break
   AEA-02's own frozen test. The adapter now builds those two objects with `model_construct` instead (decision D-14,
   §5 step 6), which keeps provider text byte-exact without touching AEA-02. This was proved in a scratch run (§4.3).
2. Context edits follow the conventions already on `main`: the area map's A2 **Status** cell (as the A0 row does), and the
   `**Built:**` line under DO-3 §3 (as AEA-03 did and AEA-18 plans to), not the module-tree line.
3. P-1 also checks `ToolTranscript` (AEA-02 plan §4.12, graph-tools §2), which the adapter satisfies with `start`/`append`.
4. The `_EPHEMERAL` module constant is dropped (a shared mutable dict); `cache_control` is built fresh per request.

---

## 1. Goal and sources

### 1.1 Goal (quoted from the issue, *What to build*)

> Every Sonnet 5.5 call in the system (specialists, responder, brief, and the planner fallback; DO-2 §A.1, SDQ-6) goes
> through one class, `AnthropicAdapter`, which makes **exactly one HTTP request** and hands back a typed `Attempt`: the
> value, a `ProviderCall` that is always present, and a `ProviderFailure` when it failed. It **never raises** to its
> caller. Retrying, deadlines, the ledger, spans, redaction and the role/attempt stamp are the gateway's job (AEA-20);
> this class only speaks Anthropic and translates Anthropic's ways of failing into our `ProviderFailureKind`s, so a 429
> that means "monthly spend cap reached" is never retried as if it were a rate limit.

**In practice.** The gateway calls `sonnet.structured(req, timeout_s=12.0)` for the responder. The adapter sends one
`POST /v1/messages` through the SDK (no SDK retries), with the stable prompt prefix marked for caching and the reply
schema in `output_config.format`. Anthropic answers HTTP 429 with no `retry-after` header. The adapter returns
`Attempt(value=None, record=ProviderCall(provider="anthropic", model="claude-sonnet-5-5", status="error",
cost_usd=0.0, failure=…), failure=ProviderFailure(kind=PROVIDER_SPEND_CAP, retryable=False, http_status=429, …))`.
Nothing is raised, nothing is logged, and the gateway trips the circuit so the customer gets the `SPEND_CAP_REACHED`
handoff (US-16).

### 1.2 Context

Wave 1, area A2 (DO-3 §8). AEA-01 (`pyproject.toml` with `anthropic>=1.17`, `web/container.py` with the
`register_anthropic` stub at line 162) is on `main`. AEA-02 (`ports/models.py`, `domain/common.py`) is **not** merged: its
frozen tests are committed on its branch (`de9bb42`) and its implementer has started. The types below are copied from
DO-4 §11–§12, stage7/models.md §1–§3 and the AEA-02 plan §4.1/§4.12, which transcribe them. The SDK facts below were
re-checked on 2026-10-21 against the installed `anthropic` 1.17.0 / pydantic 2.14.1 in `main`'s `.venv`, in a scratch
directory with a mocked transport (no paid call, no network).

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-17.md` | AC-1…AC-12, the example pair, owned files, must-not-edit list, scope boundary |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-17 (blocked by 02, **Sec**), §3 collision map (`web/container.py`: own hunk only; `tests/contract/`: one file per adapter ticket; context files: own row only) | Boundary below |
| Requirements | PRD R-41 (limits), §6.2 *Models* (mix B: Sonnet for words); US-16; HP-1 | A spend or rate limit becomes a typed failure the gateway turns into a handoff, never an exception |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §0 (`MeridianModel`), §11 (`ProviderFailureKind`, `ProviderFailure`, retryable set), §12 (port Protocols, request/answer types, "Contract every implementation honours"), §16 (addenda win) | Method signatures exactly; never raises; one attempt; `stop_reason` first; no forced `tool_choice` |
| Addendum (wins over DO-4) | `docs/design/contracts/stage7/models.md` §1 (`ProviderCall`, `Attempt.record`, `ProviderMessages`, `TokenPrice`), §2 (constructor, `ANTHROPIC_PRICES`, cost rule), §3 (Anthropic table, spend-limit pattern), §7 (one SDK client, `max_retries=0`) | The whole mapping table; cost formula; `items` "exactly as sent and received … untouched" |
| Decisions | `docs/plans/7b-decisions/models.md` MOD-1, 2, 3, 5, 14, 16, 17 | Constructor-bound model; 402/403/408/409/413 rows; spend-limit phrases; `cost_source="price_table"`; thinking never priced; `append` raises `ValueError` on foreign messages |
| Code design | DO-3 `docs/design/code-design.md` §2.1 (no core module imports `anthropic`), §3 (`**Built:**` line; tree line 236), §4.3 table line 370, §6 S-1, S-2, S-24 (no shared classifier) | The adapter implements the three ports; maps its own failures; the composition root alone builds the client |
| Settings | stage7/graph-core.md §12 (`anthropic_api_key: SecretStr`, required) | The hunk reads `settings.anthropic_api_key` |
| Research | `docs/research/2026-10-20-vendor-and-framework-facts.md` §1 (tool use, `strict`, forced choice is a 400, structured outputs, thinking billed as output, `thinking: disabled` is a 400, `request-id`), §2a (model ID, prices), §2b (spend-cap 429 has no `retry-after`), §4 (status table, SDK retry defaults) | Request shape; failure table inputs |
| SP-1 build | `docs/plans/fanout/2026-10-20-sp1/build.md` step 5; `archive/spike/SP-1-build:spikes/sp1/app/llm_anthropic.py` line 171 | Assistant content resent as `model_dump(exclude_none=True)` blocks; "`model` is always `spec.model`" |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` | None added (ticket *Evaluation*); AEA-51's cross-adapter contract file is separate |
| Observability contract | DO-6 `docs/design/observability-contract.md` WF-1 `model_call` span row; `spend_ledger` columns in stage7/models §6 | `ProviderCall` carries every per-attempt field; the adapter writes **no** span, row or ledger entry |
| Key-metrics registry | DO-7 M-23 (latency), M-24 (failure rate: kind + HTTP status), M-25, M-26 (cost) | Fields present on every attempt; thinking never double-priced |
| Sign-off decisions | `docs/plans/stage7-signoff.md` D-4…D-15 | None concerns this adapter; none is answered differently |
| AEA-02 frozen tests | branch `aea-02-aea-02-domain-ports` `de9bb42`: `tests/unit/domain/test_conventions.py` | Every model in `ports/models.py` keeps `str_strip_whitespace=True` → D-14 |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §4, `context-maintenance.md`, workspace `code-design-solid-modularity.md`, `code-structure.md` (adapter ≤ 400 soft / 600 hard lines; tests ≤ 300 / 500) | Frozen tests first; affected tests only; journey record at `mock-tested`; context rows in the same change |

---

## 2. Boundary

### 2.1 Owned files (the only files the test-writer and implementer may create or edit)

| File | Create / modify | Who | Change |
|---|---|---|---|
| `src/meridian/adapters/models/anthropic.py` | create | implementer | `ANTHROPIC_PRICES`, `CHOICE_MAX_TOKENS`, `CHOICE_EFFORT`, `build_anthropic_client`, `AnthropicAdapter` (§4.4, §5) |
| `src/meridian/web/container.py` | modify **only the body and docstring of `register_anthropic`** | implementer | §5 step 7 |
| `tests/contract/_anthropic_fixtures.py` | create | **test-writer (frozen)** | Fixture builders, requests, mocked transport (§3.4) |
| `tests/contract/test_anthropic_adapter.py` | create | **test-writer (frozen)** | The tests of §3.3 |
| `tests/unit/web/test_container.py` | modify **two inserted lines**, only if not already on `main` (§3.5) | **test-writer (frozen)** | Let filled hunks pass `test_every_register_stub_present` |
| `docs/testing/journeys/<run-date>-AEA-17.md` | create | implementer | Journey record, level `mock-tested` (AC-11; §7.4) |
| `.claude/reference/area-map.md` | modify (A2 row **Status** cell only) | implementer | §5 step 10 |
| `.claude/state/icm-progress.md` | modify (one evidence cell) | implementer | §5 step 10 |
| `docs/design/code-design.md` | modify (the `**Built:**` line under §3 only, line 180) | implementer | §5 step 10 |
| `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<run-date>-aea-17-anthropic-adapter-claude-01.md` | create (outside this repo; **not committed** by this ticket) | implementer | One dev-log run file (AC-12) |

`<run-date>` is the build day in America/Chicago (`TZ=America/Chicago date +%F`).

### 2.2 Shared surfaces read, never edited

`pyproject.toml`, `uv.lock` (AEA-01: `anthropic>=1.17` is there; `httpx2` 2.16.0 is in the lock as the SDK's HTTP
library), `src/meridian/policy/limits.py`, every `__init__.py`, `tests/conftest.py`, `tests/journeys/**`,
`tests/unit/test_import_direction.py` (AEA-01; must stay green), `src/meridian/ports/*`, `src/meridian/domain/*`,
`src/meridian/config.py` (AEA-02), AEA-02's tests, DO-4 and the stage7 addenda.

### 2.3 Owned by other tickets — do not create or edit

`src/meridian/adapters/models/openrouter_jev.py` and `tests/contract/test_jev_adapter*.py` (AEA-18),
`src/meridian/agent/gateway.py` (AEA-20), `tests/contract/test_model_ports_contract.py` (AEA-51), every other
`register_<x>()` hunk, `ports/*`, `domain/*`, `config.py`, `tests/unit/domain/*` (AEA-02), `tests/fakes/*` (AEA-11).
Never edit: the briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`,
`ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`. Never read `.env`. Never bind ports 4019 or 5184 (nothing here starts a
server).

---

## 3. Requirements

### 3.1 Acceptance criteria → implementation → verification

All tests are in `tests/contract/test_anthropic_adapter.py` (prefix `::`). All are **frozen** (written first by the
test-writer; the implementer never edits them).

| AC | Requirement (issue, abridged) | Implemented by (§5) | Verified by |
|---|---|---|---|
| AC-1 [invariant] | One HTTP attempt per call; never raises for every port method and every fixture (SDK exceptions before and after a response, malformed bodies, unmapped statuses); `record` is a `ProviderCall` on success and failure; `failure is not None` exactly when `record.status == "error"` | `_send` (§5 step 4), `with_options(max_retries=0)` in `__init__` | `::test_never_raises_and_always_records` (3 methods × every fixture; injected client built with `max_retries=2` to prove the adapter itself enforces one attempt) |
| AC-2 [invariant] | `record.model` is the constructor value on every fixture (also when the response names another model); `provider == "anthropic"`; unknown model → `ValueError` | `__init__`, `_record` | `::test_model_bound_at_construction` |
| AC-3 [failure/refusal] | Failure mapping = stage7/models §3 Anthropic table, with `retryable`, `http_status`, `retry_after_s` | `_failure_for_status`, `_send` except-clauses | `::test_failure_kind_mapping` (prints the fixture → kind table) |
| AC-4 [failure/refusal] | 400 is `OUR_SPEND_LIMIT` only for `invalid_request_error` + phrase (any case); unmatched 400 → `BAD_REQUEST` and exactly one `anthropic_400_unclassified` log record carrying only the request ID | `_is_spend_limit`, `_failure_for_status` | `::test_spend_limit_400_pattern` |
| AC-5 [failure/refusal] | `refusal` / `max_tokens` → that kind, no value, even with valid text | `_send` stop-reason step | `::test_stop_reason_checked_first` |
| AC-6 [invariant] | `tool_choice` `{"type":"auto"}` always; tools `strict: true`; structured/choice send `output_config.format`; `cache_control` on the prefix block only; no `thinking`; per-call timeout; container client `max_retries=0` | `_system_blocks`, the three request builders, `build_anthropic_client`, `register_anthropic` | `::test_request_shape`, `::test_client_built_without_retries` |
| AC-7 [invariant] | Structured reply failing `output_model`, or a choice outside its options → `INVALID_OUTPUT`; valid choice → `ChoiceAnswer(probabilities=None)` | `choose` / `structured` readers | `::test_invalid_output_and_choice_validation` |
| AC-8 [invariant] | Tool round trip through `ProviderMessages`: thinking + two `tool_use` → two `ToolCall`s (unparseable input → `args=None`); `append` keeps assistant content unchanged (thinking signature byte-identical) then `tool_result`s with matching ids; foreign provider or model → `ValueError` | `tool_step` reader, `start`, `append`, `_messages` (D-14) | `::test_tool_step_round_trip`, `::test_append_rejects_foreign_messages` |
| AC-9 [negative] | A sentinel in the provider's error message (also inside a spend-limit match) and the API key value never reach `ProviderFailure`, `ProviderCall`, their `repr`, or any log output; `provider_request_id` holds only the request id | Fields copied one by one; message read only by `_is_spend_limit`; `_clean_request_id` | `::test_no_key_or_message_in_failure` |
| AC-10 [capture] | Every `ProviderCall` has the span/ledger fields; cost per §2 rule; thinking never priced; failed attempt with no usage → `cost_usd 0.0`, all counts 0 | `_counts`, `_cost`, `_record` | `::test_call_record_fields_and_cost` |
| AC-11 [journey] — level `mock-tested` | No deterministic journey reaches this code; affected-journeys command → `0 journeys affected`, exit 0; record names level and *Blocked by* | §5 step 9 | `uv run python -m tests.journeys.affected --base main`; `docs/testing/journeys/<run-date>-AEA-17.md` |
| AC-12 [regression/context] | Area-map A2 row, ICM row, DO-3 built line, dev-log entry | §5 step 10 | `git diff --stat main...HEAD -- .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`; the dev-log file exists |
| **Example pair** (the ticket's; no WP-N applies: "none customer-visible; the unit is provider response → typed attempt") | Bare 429 → `Attempt(value=None, failure.kind=PROVIDER_SPEND_CAP, failure.retryable=False)`, `record.model == "claude-sonnet-5-5"`, `record.status == "error"`, `record.cost_usd == 0.0`; 529 → `ProviderCall(provider="anthropic", …, failure.kind=OVERLOADED)` with no `role`/`attempt` | Whole flow | `::test_example_pair_bare_429_and_529` |

### 3.2 Plan-added criteria (reconciliation found them; post one comment on issue #17 proposing them)

| ID | Criterion | Why (source) | Verified by |
|---|---|---|---|
| P-1 [invariant] | `AnthropicAdapter` structurally satisfies `ChoiceModel`, `StructuredModel`, `ToolCallingModel` and `ToolTranscript` (mypy) | DO-4 §12 (implements all three); graph-tools §2 (`ToolTranscript`); AEA-02 decision D-4 (`ClassVar` provider on both sides) | `_ports_accept_adapter` static function in the test file + `uv run mypy` |
| P-2 [negative] | The SDK client is built with its own OpenTelemetry spans and trace propagation **off**, and the SDK's `anthropic` logger is capped at `WARNING` | The adapter "writes no span" (stage7/models §5 rule 6; MOD-17 "never logged, traced"); SDK 1.17 traces by default, and at DEBUG it logs `Request options … json_data` with the full request payload | `::test_client_built_without_retries` |
| P-3 [invariant] | The adapter imports only the standard library, `anthropic`, `pydantic`, `meridian.ports.models`, `meridian.domain.common`; no streaming call; no `exc_info` / `logger.exception` | DO-3 §2.1 dependency direction; SDQ-2 (no streaming); AC-9 hardening | `::test_adapter_imports_stay_in_bounds` |
| P-4 [invariant] | Provider message text survives untouched: a thinking block whose text has leading spaces and a trailing newline reaches the next request byte-identical after `start` → `tool_step` → `append` → `ToolStepRequest` | stage7/models §1 (MOD-17: items "exactly as sent and received … untouched"); `MeridianModel`'s `str_strip_whitespace=True` would otherwise strip strings nested in `JsonValue` (scratch-proved) | `::test_tool_step_round_trip` (its exact `step.raw` and second-request assertions) |

### 3.3 Frozen tests (test-writer writes these first; the implementer must not edit them)

**Files.** `tests/contract/_anthropic_fixtures.py` (§3.4) and `tests/contract/test_anthropic_adapter.py`. The test file
imports `import anthropic`, `import httpx2`, `from meridian.adapters.models.anthropic import ANTHROPIC_PRICES,
AnthropicAdapter, CHOICE_EFFORT, CHOICE_MAX_TOKENS`, `from meridian.web.container import Container, Key,
register_anthropic`, `from meridian.policy.limits import Limits`, the port types from `meridian.ports.models` (incl.
`ToolTranscript`, `TokenPrice`, `ProviderCall`, `ProviderMessages`, `ToolStep`, `ToolCall`, `ChoiceAnswer`, `Attempt`)
and `ProviderFailureKind` from `meridian.domain.common`, plus everything in §3.4.

**Red for the right reason.** Before the implementer starts, collecting the file fails with
`ModuleNotFoundError: No module named 'meridian.adapters.models.anthropic'`. The test-writer can only run after AEA-02
is on `main` (imports of `meridian.ports.models`); if `meridian.ports.models` itself is missing, stop and report.
Test-writer commands: `uv run pytest tests/contract/test_anthropic_adapter.py -q` (that error) and
`uv run pytest --collect-only -q tests` (every other file collects; only this one errors).
Test-writer commit: `test(AEA-17): frozen contract tests for the Anthropic adapter` — `git add
tests/contract/_anthropic_fixtures.py tests/contract/test_anthropic_adapter.py` (plus `tests/unit/web/test_container.py`
only if §3.5's lines were inserted); last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

**Fixture catalogue** (in `_anthropic_fixtures.py`, used by tests 1–3, 11). `K` = `ProviderFailureKind`.
`RID` = `REQUEST_ID`. Every status fixture sends the header `request-id: RID` and the JSON error body
`error_body(<type>, "<message> " + SENTINEL)` unless stated.

*HTTP-level fixtures (`HTTP_CASES`, same outcome for all three methods):*

| id | Response | kind | retryable | http_status | retry_after_s | provider_request_id | logs `anthropic_400_unclassified` |
|---|---|---|---|---|---|---|---|
| `timeout` | handler raises `httpx2.ReadTimeout("read timed out", request=request)` | `TIMEOUT` | True | None | None | None | no |
| `connection_error` | handler raises `httpx2.ConnectError("connection refused", request=request)` | `CONNECTION` | True | None | None | None | no |
| `status_400` | 400 `invalid_request_error` "messages.0.content: Field required" | `BAD_REQUEST` | False | 400 | None | RID | **yes** |
| `status_400_spend_limit` | 400 `invalid_request_error` "Your workspace has reached its Spend Limit." | `OUR_SPEND_LIMIT` | False | 400 | None | RID | no |
| `status_401` | 401 `authentication_error` "invalid x-api-key" | `AUTH` | False | 401 | None | RID | no |
| `status_402` | 402 `billing_error` "billing problem" | `PROVIDER_SPEND_CAP` | False | 402 | None | RID | no |
| `status_403` | 403 `permission_error` "not allowed" | `AUTH` | False | 403 | None | RID | no |
| `status_404` | 404 `not_found_error` "model not found" | `NOT_FOUND` | False | 404 | None | RID | no |
| `status_408` | 408 `timeout_error` "request timeout" | `TIMEOUT` | True | 408 | None | RID | no |
| `status_409` | 409 `conflict_error` "conflict" | `SERVER` | True | 409 | None | RID | no |
| `status_413` | 413 `request_too_large` "too large" | `BAD_REQUEST` | False | 413 | None | RID | no |
| `status_418` | 418 `teapot_error` "teapot" | `BAD_REQUEST` | False | 418 | None | RID | no |
| `status_429_retry_after` | 429 `rate_limit_error`, header `retry-after: 7` | `RATE_LIMITED` | True | 429 | 7.0 | RID | no |
| `status_429_retry_after_ms` | 429 `rate_limit_error`, header `retry-after-ms: 1500` | `RATE_LIMITED` | True | 429 | 1.5 | RID | no |
| `status_429_bare` | 429 `rate_limit_error`, neither header | `PROVIDER_SPEND_CAP` | False | 429 | None | RID | no |
| `status_529` | 529 `overloaded_error` "overloaded" | `OVERLOADED` | True | 529 | None | RID | no |
| `status_500` | 500 `api_error` "internal" | `SERVER` | True | 500 | None | RID | no |
| `status_503` | 503 `api_error` "unavailable" | `SERVER` | True | 503 | None | RID | no |
| `status_504` | 504 `timeout_error` "gateway timeout" | `SERVER` | True | 504 | None | RID | no |
| `status_302` | 302, header `location: https://example.test/`, no body | `INVALID_OUTPUT` | False | 302 | None | RID | no |
| `raised_before_request` | `ExplodingClient` (§3.4): `create` raises `RuntimeError(SENTINEL)` | `CONNECTION` | True | None | None | None | no |
| `raised_after_response` | 200, header `content-type: application/json`, body bytes `b"{not json"` (`raw.parse()` raises `JSONDecodeError`) | `INVALID_OUTPUT` | False | 200 | None | RID | no |

For every HTTP-level fixture: `record.cost_usd == 0.0` and all five token counts 0 (no usage block), `record.status ==
"error"`, `record.stop_reason is None`.

*Response-level fixtures (`body_cases(method)`, HTTP 200 with `request-id: RID`; `USAGE` from §3.4):*

| id | Body | Expected |
|---|---|---|
| `success` | `message_body(content=SUCCESS_CONTENT[method])` (`stop_reason="tool_use"` for `tool_step`) | `failure is None`, value as tests 8/9 state, `status == "ok"`, `stop_reason == "end_turn"` (`"tool_use"` for tool_step) |
| `success_other_model` | as `success` with `model="claude-other-9"` | as `success`; `record.model == MODEL` |
| `refusal_with_text` | `message_body(content=SUCCESS_CONTENT[method], stop_reason="refusal")` | `REFUSAL`, not retryable, http 200, value None, `record.stop_reason == "refusal"`, cost as `USAGE` |
| `max_tokens_with_text` | same with `stop_reason="max_tokens"` | `MAX_TOKENS`, as above with `"max_tokens"` |
| `missing_content` | `{"id": "msg_test", "type": "message", "role": "assistant"}` | `INVALID_OUTPUT`, http 200, cost 0.0, counts 0 |
| `content_not_list` | `message_body(content="oops")` (a string, not a list) | `INVALID_OUTPUT`, http 200, cost as `USAGE` |
| `invalid_output` (choose, structured only) | choose: text `{"topic": "refunds", "urgency": "today"}`; structured: text `{"txt": "x"}` | `INVALID_OUTPUT`, http 200, cost as `USAGE` |

**The tests** (14 test functions plus one static function):

| # | Test | Setup | Assertions |
|---|---|---|---|
| 1 | `test_never_raises_and_always_records` (AC-1) | `@pytest.mark.parametrize("method, case", ALL_CASES)` where `ALL_CASES` is one flat list of `pytest.param(method, case, id=f"{method}-{case.id}")` for `method in METHODS` and `case in (*HTTP_CASES, *body_cases(method))` (no skips) | The call returns (no exception); `isinstance(attempt, Attempt)`; `type(attempt.record) is ProviderCall`; `"role" not in type(attempt.record).model_fields` and `"attempt" not in …`; `(attempt.failure is None) == (attempt.record.status == "ok")`; `attempt.record.failure == attempt.failure`; `attempt.failure is not None` ⇒ `attempt.value is None`; requests seen == **1** (`recorder.requests` for transport fixtures, `ExplodingClient.calls` for `raised_before_request`) even though the injected client was built with `max_retries=2` |
| 2 | `test_model_bound_at_construction` (AC-2) | Every case of test 1 on `structured`; plus constructor calls | `attempt.record.model == "claude-sonnet-5-5"` and `attempt.record.provider == "anthropic"` for every case (incl. `success_other_model`); `AnthropicAdapter.provider == "anthropic"`; `adapter.model == "claude-sonnet-5-5"`; `pytest.raises(ValueError)` for `AnthropicAdapter(client, model="claude-unknown")`; `pytest.raises(AttributeError)` for `adapter.model = "x"  # type: ignore[misc]` (do not use `setattr`; ruff B010 rejects it) |
| 3 | `test_failure_kind_mapping` (AC-3) | `HTTP_CASES` on `structured` (one call each, fresh adapter) | For each: `failure.kind`, `failure.retryable`, `failure.http_status`, `failure.retry_after_s`, `failure.provider_request_id`, `failure.provider == "anthropic"` equal the catalogue row; then `print` one line per case `f"{case.id:28} -> {failure.kind.value}"` (the evidence table, run with `-s`) |
| 4 | `test_spend_limit_400_pattern` (AC-4) | `caplog.set_level(logging.DEBUG)`; six 400 responses on `structured`, messages each ending with `" " + SENTINEL`: (a) `invalid_request_error` "Your workspace has reached its Spend Limit."; (b) `invalid_request_error` "You hit your USAGE LIMIT for this month."; (c) `invalid_request_error` "Your Credit Balance is too low to access the Anthropic API."; (d) `invalid_request_error` "messages.0.content: Field required"; (e) `api_error` "spend limit reached"; (f) body not JSON: header `content-type: text/plain`, content `b"Bad Request"` | (a)(b)(c): `OUR_SPEND_LIMIT`, and no record from logger `"meridian.adapters.models.anthropic"`; (d)(e)(f): `BAD_REQUEST`, and **exactly one** record from that logger with `rec.levelno == logging.WARNING`, `rec.getMessage() == "anthropic_400_unclassified"`, `not rec.args`, `rec.provider_request_id == REQUEST_ID`, and `{k for k in vars(rec) if k not in STANDARD_LOG_ATTRS} == {"provider_request_id"}` (`STANDARD_LOG_ATTRS` in §3.4). Clear `caplog` between sub-cases |
| 5 | `test_stop_reason_checked_first` (AC-5) | For each method: `refusal_with_text` and `max_tokens_with_text` (their content is the method's *valid* success content) | `attempt.value is None`; kinds `REFUSAL` / `MAX_TOKENS`; `retryable is False`; `record.stop_reason` equals `"refusal"` / `"max_tokens"`; `record.status == "error"` |
| 6 | `test_request_shape` (AC-6) | One `success` call per method through `adapter_for`; read `recorder.bodies()` and `recorder.requests[0].extensions["timeout"]`. `choose(choice_request(), timeout_s=3.5)`; `structured(structured_request(effort="low"), timeout_s=12.0)`; `structured(structured_request(effort=None, system_dynamic=""), timeout_s=12.0)`; `tool_step(tool_request(adapter.start("Is my membership active?")), timeout_s=8.0)` | Every body: `body["model"] == MODEL`; `"thinking" not in body`; `"stream" not in body`; `body["system"][0]["cache_control"] == {"type": "ephemeral"}`; every other system block has no `"cache_control"` key; `extensions["timeout"]["read"]` equals the call's `timeout_s`. **choose:** `"tools" not in body`, `"tool_choice" not in body`; `body["max_tokens"] == CHOICE_MAX_TOKENS`; `body["output_config"]["effort"] == CHOICE_EFFORT`; `body["output_config"]["format"]["type"] == "json_schema"`; schema `properties["topic"]["enum"] == ["billing", "booking"]`, `properties["urgency"]["enum"] == ["today", "later"]`, `required == ["topic", "urgency"]`, `additionalProperties is False`; `body["system"] == [{"type": "text", "text": "Route this turn.", "cache_control": {"type": "ephemeral"}}]`; user content (`body["messages"] == [{"role": "user", "content": <str>}]`) parses as JSON with keys `["state", "questions"]`. **structured (effort low):** `len(body["system"]) == 2`, `body["system"][1] == {"type": "text", "text": "Turn facts: none."}`; `body["output_config"] == {"format": {"type": "json_schema", "schema": anthropic.transform_schema(Reply)}, "effort": "low"}`; `body["max_tokens"] == 1500`; `body["messages"] == [{"role": "user", "content": "What does the membership cover?"}]`. **structured (effort None, empty dynamic):** `len(body["system"]) == 1`; `"effort" not in body["output_config"]`. **tool_step:** `body["tool_choice"] == {"type": "auto"}`; `body["tools"] == [{"name": "kb_search", "description": "Search the knowledge base.", "input_schema": KB_SCHEMA, "strict": True}]`; `body["output_config"] == {"effort": "medium"}`; `body["max_tokens"] == 3000`; `body["messages"] == [{"role": "user", "content": "Is my membership active?"}]` |
| 7 | `test_client_built_without_retries` (AC-6, P-2) | `logger = logging.getLogger("anthropic")`; `before = logger.level`; `try:` `c = Container(settings=types.SimpleNamespace(anthropic_api_key=SecretStr(FAKE_KEY)), limits=Limits())`; `register_anthropic(c, FastAPI(), settings=c.settings, limits=c.limits)`; `c.build()`; `client = c.get(Key[anthropic.Anthropic]("anthropic_client"))` … `finally: logger.setLevel(before)` | `isinstance(client, anthropic.Anthropic)`; `client.max_retries == 0`; `client.open_telemetry["traces"]["enabled"] is False`; `client.open_telemetry["propagation"] is False`; `client.api_key == FAKE_KEY`; `logger.level == logging.WARNING` (read before the `finally`); `AnthropicAdapter(client, model=MODEL).model == MODEL`; after `c.close()`: `client.is_closed() is True` |
| 8 | `test_invalid_output_and_choice_validation` (AC-7) | choose with texts: (a) `{"topic": "refunds", "urgency": "today"}`; (b) `{"topic": "billing"}` (missing field); (c) `{"topic": "billing", "urgency": "today", "extra": "x"}`; (d) `not json`; (e) `{"topic": "billing", "urgency": "today"}`. structured with texts: (f) `{"txt": "x"}`; (g) `{"text": "Two tune-ups a year."}` | (a)–(d): `INVALID_OUTPUT`, `retryable is False`, `http_status == 200`, value None. (e): `failure is None`, `value == ChoiceAnswer(choices={"topic": "billing", "urgency": "today"}, probabilities=None)`. (f): `INVALID_OUTPUT`. (g): `failure is None`, `isinstance(value, Reply)`, `value.text == "Two tune-ups a year."` |
| 9 | `test_tool_step_round_trip` (AC-8, P-4) | `messages = adapter.start("Is my membership active?")`; first `tool_step` answered with `TOOL_CONTENT` (§3.4, `stop_reason="tool_use"`); `step = attempt.value`; `results = [("toolu_01", '{"ok": true}'), ("toolu_02", '{"error": "bad_arguments"}')]`; `messages2 = adapter.append(messages, step, results)`; second `tool_step(tool_request(messages2))` answered with a plain `success` text body | `messages == ProviderMessages(provider="anthropic", model=MODEL, items=({"role": "user", "content": "Is my membership active?"},))`; `step.tool_calls == (ToolCall(id="toolu_01", name="kb_search", args={"query": "membership"}), ToolCall(id="toolu_02", name="account_read", args=None))`; `step.text == "Let me check."`; `step.stop_reason == "tool_use"`; `step.raw == {"role": "assistant", "content": TOOL_CONTENT}` (**exact**, including the thinking text `"  Need the KB.\n"` with its whitespace and `SIGNATURE`); `messages2.provider == "anthropic"`, `messages2.model == MODEL`; `messages2.items == (*messages.items, {"role": "assistant", "content": TOOL_CONTENT}, {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_01", "content": '{"ok": true}'}, {"type": "tool_result", "tool_use_id": "toolu_02", "content": '{"error": "bad_arguments"}'}]})`; the **second** request body's `messages == list(messages2.items)` and `messages[1]["content"][0] == TOOL_CONTENT[0]` (thinking block byte-identical on the wire, after passing through `Attempt`, `append` and a validated `ToolStepRequest`) |
| 10 | `test_append_rejects_foreign_messages` (AC-8) | `step = ToolStep(text="", tool_calls=(), raw={"role": "assistant", "content": []}, stop_reason="end_turn")` | `pytest.raises(ValueError)` for `adapter.append(ProviderMessages(provider="openrouter_jev", model=MODEL, items=()), step, [])` and for `adapter.append(ProviderMessages(provider="anthropic", model="claude-other-9", items=()), step, [])`; neither raised message contains `"claude-other-9"` |
| 11 | `test_no_key_or_message_in_failure` (AC-9) | `caplog.set_level(logging.DEBUG)` (root, every logger incl. the SDK's); adapters built with `key=FAKE_KEY`; cases on `structured`: `status_400`, `status_400_spend_limit`, `status_401`, `status_402`, `status_429_bare`, `status_529`, `status_500`, `raised_before_request`, `raised_after_response`; plus one extra 500 whose header is `request-id: "req_ok " + SENTINEL` (space → invalid) | For each: `SENTINEL` and `FAKE_KEY` are absent from `failure.model_dump_json()`, `record.model_dump_json()`, `repr(failure)`, `repr(record)`, `repr(attempt)`, `repr(adapter)`, and `caplog.text`; `failure.provider_request_id` and `record.provider_request_id` equal `REQUEST_ID` (status/after cases) or `None` (`raised_before_request`); the extra case gives `provider_request_id is None` |
| 12 | `test_call_record_fields_and_cost` (AC-10) | (a) structured `success` with `USAGE` (input 1000, output 500, cache write 200, cache read 3000, thinking 120); (b) same with `thinking_tokens` 400; (c) `status_529` (no usage block); (d) structured `success` whose usage omits the two cache fields and `output_tokens_details` | (a): `input_tokens == 1000`, `output_tokens == 500`, `cache_write_tokens == 200`, `cache_read_tokens == 3000`, `thinking_tokens == 120`, `cost_source == "price_table"`, `status == "ok"`, `failure is None`, `provider_request_id == REQUEST_ID`, `stop_reason == "end_turn"`, `latency_ms >= 0`, `cost_usd == pytest.approx(expected, rel=1e-12)` where `p = ANTHROPIC_PRICES[MODEL]` and `expected = (1000 * p.input + 500 * p.output + 200 * p.cache_write_5m + 3000 * p.cache_read) / 1_000_000` (= 0.0078). (b): `thinking_tokens == 400` and `cost_usd ==` (a)'s. (c): `cost_usd == 0.0`, all five counts 0, `failure.kind == K.OVERLOADED`, `failure.http_status == 529`, `cost_source == "price_table"`. (d): `cache_read_tokens == cache_write_tokens == thinking_tokens == 0`. Also `ANTHROPIC_PRICES["claude-sonnet-5-5"] == TokenPrice(input=2.00, output=10.00, cache_write_5m=2.50, cache_read=0.10)` |
| 13 | `test_example_pair_bare_429_and_529` (example pair) | `status_429_bare` and `status_529` on `structured` | 429: `value is None`, `failure.kind == K.PROVIDER_SPEND_CAP`, `failure.retryable is False`, `record.model == "claude-sonnet-5-5"`, `record.status == "error"`, `record.cost_usd == 0.0`. 529: `record.provider == "anthropic"`, `record.model == "claude-sonnet-5-5"`, `record.status == "error"`, `record.failure.kind == K.OVERLOADED`; `type(record) is ProviderCall` |
| 14 | `test_adapter_imports_stay_in_bounds` (P-3) | `ast.parse` of `Path(__file__).resolve().parents[2] / "src" / "meridian" / "adapters" / "models" / "anthropic.py"` | Every import's top-level name is in `sys.stdlib_module_names ∪ {"__future__", "anthropic", "pydantic", "meridian"}`; every `meridian…` import is `meridian.ports.models` or `meridian.domain.common`; no relative import; source text contains none of `"openrouter_jev"`, `"exc_info"`, `"logger.exception"`, `".stream("`, `"stream=True"`, `"os.environ"`, `"getenv"` |
| — | `_ports_accept_adapter(adapter: AnthropicAdapter) -> tuple[ChoiceModel, StructuredModel, ToolCallingModel, ToolTranscript]: return (adapter, adapter, adapter, adapter)` (P-1; module-level, **never called**, leading `_` so pytest ignores it) | — | Static: `uv run mypy` passes |

`METHODS = ("choose", "structured", "tool_step")`. `call(method, adapter, timeout_s=5.0)` in §3.4 runs the method with its
default request (tool_step uses `tool_request(adapter.start("Is my membership active?"))`).

### 3.4 What `tests/contract/_anthropic_fixtures.py` must provide (frozen; exact names)

- Constants: `MODEL = "claude-sonnet-5-5"`; `FAKE_KEY = "sk-test-" + secrets.token_hex(12)` (generated at import,
  never a real key, never in a test id); `SENTINEL = "ZZSENTINEL-" + secrets.token_hex(4)`;
  `REQUEST_ID = "req_011TestFixture01"`; `SIGNATURE = "EqQBCkYIBhgCKkD/+=Q2xhdWRlU2lnbmF0dXJl=="`;
  `USAGE = {"input_tokens": 1000, "output_tokens": 500, "cache_creation_input_tokens": 200,
  "cache_read_input_tokens": 3000, "output_tokens_details": {"thinking_tokens": 120}}`;
  `KB_SCHEMA = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"],
  "additionalProperties": False}`; `METHODS`.
- `TOOL_CONTENT = [{"type": "thinking", "thinking": "  Need the KB.\n", "signature": SIGNATURE}, {"type": "text",
  "text": "Let me check."}, {"type": "tool_use", "id": "toolu_01", "name": "kb_search", "input": {"query":
  "membership"}}, {"type": "tool_use", "id": "toolu_02", "name": "account_read", "input": "not-json{"}]`.
- `SUCCESS_CONTENT: dict[str, list[dict[str, Any]]]`: `choose` → `[{"type": "text", "text": '{"topic": "billing",
  "urgency": "today"}'}]`; `structured` → `[{"type": "text", "text": '{"text": "Two tune-ups a year."}'}]`; `tool_step` →
  `TOOL_CONTENT`.
- `STANDARD_LOG_ATTRS = set(vars(logging.LogRecord("n", logging.INFO, "p", 1, "m", None, None))) | {"message",
  "asctime"}`.
- `class Reply(LLMFacing)`: `text: str` (`LLMFacing` from `meridian.domain.common`).
- `message_body(*, content: object, stop_reason: str | None = "end_turn", model: str = MODEL, usage: dict | None =
  USAGE) -> dict` → `{"id": "msg_test", "type": "message", "role": "assistant", "model": model, "content": content,
  "stop_reason": stop_reason, "stop_sequence": None, "usage": usage}` (omit `"usage"` when `None`).
- `error_body(etype: str, message: str) -> dict` → `{"type": "error", "error": {"type": etype, "message": message},
  "request_id": REQUEST_ID}`.
- `Handler = Callable[[httpx2.Request], httpx2.Response]`; `respond(status: int, *, json: object | None = None,
  content: bytes | None = None, headers: dict[str, str] | None = None) -> Handler` (adds `request-id: REQUEST_ID`
  unless `headers` sets `request-id`); `raises(factory: Callable[[httpx2.Request], Exception]) -> Handler`.
- `@dataclass class Recorder`: `requests: list[httpx2.Request]`; `bodies() -> list[dict]` (`json.loads(r.content)`).
- `adapter_for(handler: Handler, *, model: str = MODEL, key: str = FAKE_KEY) -> tuple[AnthropicAdapter, Recorder]`:
  `anthropic.Anthropic(api_key=key, max_retries=2, open_telemetry=False, http_client=httpx2.Client(transport=
  httpx2.MockTransport(<records then calls handler>)))` → `AnthropicAdapter(client, model=model)`. **`max_retries=2` on
  purpose** (AC-1: the adapter must enforce one attempt itself).
- `class ExplodingClient`: `calls: int = 0`; `max_retries = 2`; `with_options(self, **kwargs: object) ->
  ExplodingClient` returns `self`; attribute `messages` whose `with_raw_response.create(**kwargs)` increments `calls` and
  raises `RuntimeError(SENTINEL)`. Built into an adapter with `AnthropicAdapter(cast(anthropic.Anthropic, client),
  model=MODEL)`.
- Requests: `choice_request() -> ChoiceRequest` = `ChoiceRequest(system="Route this turn.", state={"new_message": "Can
  I move my tune-up?"}, fields=(ChoiceField(name="topic", instructions="Pick the topic.", options={"billing": "Billing
  question", "booking": "Booking or change"}), ChoiceField(name="urgency", instructions="How soon?", options={"today":
  "Today", "later": "Later"})))`; `structured_request(*, effort: Literal["low", "medium", "high"] | None = "low",
  system_dynamic: str = "Turn facts: none.") -> StructuredRequest[Reply]` with `system_prefix="You are Meridian's
  assistant."`, `user="What does the membership cover?"`, `output_model=Reply`, `max_tokens=1500`;
  `tool_request(messages: ProviderMessages) -> ToolStepRequest` with `system_prefix="Specialist rules."`,
  `system_dynamic="Verified: no."`, `tools=(ToolSchema(name="kb_search", description="Search the knowledge base.",
  input_schema=KB_SCHEMA),)`, `max_tokens=3000`, `effort="medium"`.
- `@dataclass(frozen=True) class Case`: `id: str`, `handler: Handler | None` (None = `ExplodingClient`), `kind:
  ProviderFailureKind | None`, `retryable: bool | None`, `http_status: int | None`, `retry_after_s: float | None`,
  `request_id: str | None`, `logs_unclassified: bool`; `HTTP_CASES: tuple[Case, ...]` (the HTTP-level table);
  `body_cases(method: str) -> tuple[Case, ...]` (the response-level table; `invalid_output` only for `choose` and
  `structured`; `success` and friends use `stop_reason="tool_use"` for `tool_step`).
- `make(case: Case, **kw) -> tuple[AnthropicAdapter, Recorder | ExplodingClient]` and `call(method: str, adapter:
  AnthropicAdapter, timeout_s: float = 5.0) -> Attempt[Any]`.

Keep the fixtures file ≤ 300 lines and the test file ≤ 500 lines (`code-structure.md`). The fixtures file is this
ticket's private helper (the `_anthropic` prefix collides with no other ticket; §8 R-7).

### 3.5 The AEA-01 container test (test-writer makes this edit; two lines; same text as AEA-10's plan)

`tests/unit/web/test_container.py::test_every_register_stub_present` calls every original hunk with a bare
`SimpleNamespace(name="stand-in")` settings object and asserts it leaves the container empty
(`assert not fresh._factories`). The first ticket that fills a hunk turns it red. **If these lines are not already on
`main`** (AEA-10, which fills `register_storage`, plans the identical lines; whoever merges first lands them), insert them
as the first two lines inside the loop `for name, func in originals.items():`:

```python
        if "No-op until" not in (func.__doc__ or ""):
            continue  # filled by its ticket, whose own test covers the hunk
```

Nothing else in that file changes. The docstring-ticket check above the loop (`assert ticket in …__doc__`) still applies
to every hunk, so `register_anthropic`'s new docstring must keep the token `AEA-17`. If `main` instead has another
exclusion mechanism by then (e.g. AEA-27's fallback `FILLED_HUNKS` set), add `"register_anthropic"` to it instead and
touch nothing else.

### 3.6 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| One attempt, never raises, `record` always present | DO-4 §12 contract | AC-1 | in-ticket | §5 step 4 |
| `stop_reason` before content | DO-4 §11–§12 | AC-5 | in-ticket | §5 step 4.6 |
| No forced `tool_choice`; strict tools | DO-4 §12; research §1 | AC-6 | in-ticket | §5 step 6 |
| Constructor-bound model; `ValueError` without a price row | models.md §2; MOD-1 | AC-2 | in-ticket | §5 step 2 |
| Anthropic failure table | models.md §3; MOD-2, MOD-3 | AC-3, AC-4 | in-ticket | §5 step 3 |
| Cost rule; thinking never priced; `cost_source` | models.md §2; MOD-5, MOD-16 | AC-10 | in-ticket | §5 step 3 |
| `ProviderMessages` untouched; `append` guards provider/model | models.md §1; MOD-17 | AC-8 (signature); text untouched not stated | in-ticket + added (P-4; D-14 `model_construct`, no AEA-02 change) | §5 step 6 |
| No secret or provider message in failures, logs | MOD-3; MOD-14 | AC-9 | in-ticket | §5 steps 3–4 |
| One SDK client with `max_retries=0` | models.md §7; DO-1 §8.1 | AC-6 | in-ticket | §5 step 7 |
| The adapter writes no span (gateway does, masked) | models.md §5 rule 6; DO-6 | — | added (P-2: SDK spans off, SDK debug logger capped) | §5 steps 2, 7 |
| Implements the port Protocols structurally | DO-4 §12; graph-tools §2; AEA-02 D-4 | — | added (P-1) | static function |
| Dependency direction | DO-3 §2.1 | — | added (P-3) | test 14 |
| No streaming | SDQ-2 | scope note | in-ticket (scope) + P-3 check | — |
| Retrying, deadline, ledger, span, redaction, role/attempt stamp | models.md §5 | scope note | other-ticket: AEA-20 | — |
| `adapter_for` memo per (provider, model); cross-adapter contract test | models.md §7; MOD-19 | scope note | other-ticket: AEA-51 | §8 R-3 |
| `ChoiceRequest` carries no `max_tokens` / `effort` for the planner fallback | DO-4 §12 vs `RoleSpec` | — | engineering decision D-4 (constants); note R-4 | §8 |
| Live compatibility | integrated-journeys §3 rule 4 | AC-11 | other-ticket: AEA-61 (`gate::paid`) | journey record |
| Container test asserts every hunk is a no-op | AEA-01 `test_container.py` | — | added (§3.5, test-writer edit) | §3.5 |
| Every port model keeps `str_strip_whitespace=True` | AEA-02 frozen `test_conventions.py` AC-1 | — | respected: no model config is changed; D-14 | §5 step 6 |

### 3.7 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — |

---

## 4. Shared code to use (exact shapes)

### 4.1 From AEA-02 (not yet on `main`; copied from DO-4 §11–§12, stage7/models §1, AEA-02 plan §4.1, §4.12)

```python
# meridian.domain.common
class MeridianModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)
class LLMFacing(MeridianModel): ...
class ProviderFailureKind(StrEnum):
    TIMEOUT = "timeout"; CONNECTION = "connection"; RATE_LIMITED = "rate_limited"; OVERLOADED = "overloaded"
    SERVER = "server"; PROVIDER_SPEND_CAP = "provider_spend_cap"; OUR_SPEND_LIMIT = "our_spend_limit"
    BAD_REQUEST = "bad_request"; AUTH = "auth"; NOT_FOUND = "not_found"; BODY_ERROR = "body_error"
    REFUSAL = "refusal"; MAX_TOKENS = "max_tokens"; INVALID_OUTPUT = "invalid_output"
ProviderName = Literal["anthropic", "openrouter_jev"]
class ProviderFailure(MeridianModel):
    kind: ProviderFailureKind
    provider: ProviderName
    http_status: int | None
    retry_after_s: float | None
    retryable: bool
    provider_request_id: str | None
class ProviderCall(MeridianModel):
    provider: ProviderName
    model: str
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(ge=0)
    thinking_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    cost_source: Literal["reported", "price_table"]
    status: Literal["ok", "error"]
    failure: ProviderFailure | None
    provider_request_id: str | None
    stop_reason: str | None

# meridian.ports.models (re-exports Role, ProviderName, ProviderCall, CallRecord from domain.common)
ProviderTurn = JsonValue
@dataclass(frozen=True)
class TokenPrice:
    input: float
    output: float
    cache_write_5m: float
    cache_read: float
class ChoiceField(MeridianModel):    name: str; instructions: str; options: dict[str, str] = Field(max_length=255)
class ChoiceRequest(MeridianModel):  system: str; state: dict[str, JsonValue]; fields: tuple[ChoiceField, ...]
class ChoiceAnswer(MeridianModel):   choices: dict[str, str]; probabilities: dict[str, dict[str, float]] | None
class StructuredRequest[T: BaseModel](MeridianModel):
    system_prefix: str; system_dynamic: str; user: str; output_model: type[T]; max_tokens: int
    effort: Literal["low", "medium", "high"] | None
class ToolSchema(MeridianModel):     name: str; description: str; input_schema: dict[str, JsonValue]; strict: bool = True
class ToolCall(MeridianModel):       id: str; name: str; args: dict[str, JsonValue] | None
class ProviderMessages(MeridianModel): provider: ProviderName; model: str; items: tuple[JsonValue, ...]
class ToolStepRequest(MeridianModel):
    system_prefix: str; system_dynamic: str; messages: ProviderMessages; tools: tuple[ToolSchema, ...]
    max_tokens: int; effort: Literal["low", "medium", "high"] | None
class ToolStep(MeridianModel):       text: str; tool_calls: tuple[ToolCall, ...]; raw: ProviderTurn; stop_reason: str | None
class Attempt[T: BaseModel](MeridianModel):
    value: T | None; record: ProviderCall; failure: ProviderFailure | None
class ChoiceModel(Protocol):
    provider: ClassVar[ProviderName]
    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]: ...
class StructuredModel(Protocol):
    provider: ClassVar[ProviderName]
    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]: ...
class ToolCallingModel(Protocol):
    provider: ClassVar[ProviderName]
    def start(self, user: str) -> ProviderMessages: ...
    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...
class ToolTranscript(Protocol):      # graph-tools §2 (used only by the P-1 static check)
    def start(self, user: str) -> ProviderMessages: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...
```

If the merged AEA-02 code differs in a name, **the merged code wins**; if a test then cannot be written as §3.3 says,
stop and report to the orchestrator (do not edit `ports/*` or `domain/*`). Import each name from where the merged code
defines or re-exports it (`ProviderFailureKind`, `ProviderFailure`, `LLMFacing` from `meridian.domain.common`; the rest
from `meridian.ports.models`).

### 4.2 From AEA-01 (on `main`)

`meridian.web.container`: `class Container` (`__init__(self, *, settings: Any, limits: Limits)`, `provide[T](key:
Key[T], factory: Callable[[Container], T]) -> None`, `get[T](key: Key[T]) -> T`, `on_close(closer: Callable[[], None])
-> None`, `build()` (calls every provided factory), `close()` (runs closers newest first), property `settings -> Any`,
property `limits -> Limits`), `@dataclass(frozen=True) class Key[T]: name: str`. The stub to fill (line 162):

```python
def register_anthropic(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-17 models: the Anthropic adapter (models.md §2, §7).

    No-op until AEA-17 fills it.
    """
```

Module-level imports of `container.py` must not change (`tests/unit/test_import_direction.py::
test_container_imports_only_policy_limits` checks only module-level and `TYPE_CHECKING` imports): import inside the
function body. `Settings.anthropic_api_key: SecretStr` is required (graph-core.md §12), so the hunk may read it.

### 4.3 From the `anthropic` 1.17.0 SDK and pydantic 2.14.1 (checked in scratch runs against `main`'s `.venv`)

- Exceptions (top level): `anthropic.APITimeoutError` **is a subclass of** `anthropic.APIConnectionError` (catch it
  first); `anthropic.APIStatusError` has `.status_code: int`, `.response.headers`, `.body` (the parsed JSON `dict`, or a
  `str`/`None` when the body is not JSON), `.request_id` (the `request-id` header). `str(exc)` **contains the
  provider's message**: never format, log or store an exception.
- Statuses seen with `max_retries=0`: 400 `BadRequestError`, 402 `APIStatusError`, 403 `PermissionDeniedError`, 408
  `APIStatusError`, 409 `ConflictError`, 413 `RequestTooLargeError`, 418 `APIStatusError`, 429 `RateLimitError`,
  500/503/504 `InternalServerError`, 529 `OverloadedError`, 302 `APIStatusError`. Map by `status_code`, never by class.
- A transport `ReadTimeout` → `APITimeoutError`; `ConnectError` or any exception raised inside the transport →
  `APIConnectionError`.
- `client.with_options(max_retries=0)` returns a copy sharing the HTTP client (the mock recorder still sees the request)
  and keeping `open_telemetry`; the original keeps its own `max_retries`.
- `client.messages.with_raw_response.create(**kwargs, timeout=t)` returns an `APIResponse` with `.status_code`,
  `.headers`; `.parse()` returns the `Message`. A 200 with JSON content type and an invalid body raises
  `json.JSONDecodeError` from `.parse()`; a 200 missing fields parses to a `Message` with `content=None`,
  `usage=None` (no validation); `"content": "oops"` parses with `content == "oops"`.
- `Message.usage`: `input_tokens`, `output_tokens`, `cache_creation_input_tokens: int | None`,
  `cache_read_input_tokens: int | None`, `output_tokens_details: OutputTokensDetails | None` with `thinking_tokens: int`.
- `create(...)` accepts `output_config={"effort": …, "format": {"type": "json_schema", "schema": {...}}}`, `system:
  list[TextBlockParam]` (each may carry `"cache_control": {"type": "ephemeral"}`), `tools: list[ToolParam]` (with
  `"strict": True`), `tool_choice={"type": "auto"}`. `anthropic.transform_schema(model_cls)` builds the strict schema
  (`additionalProperties: false`, `required`) the SDK's own `parse()` uses.
- Content blocks: `anthropic.types.TextBlock` (`.text`), `ToolUseBlock` (`.id`, `.name`, `.input`), thinking blocks.
  `block.model_dump(mode="json", exclude_none=True, warnings=False)` keeps `thinking` (whitespace included) and
  `signature` exactly and drops `citations: None`; `warnings=False` silences pydantic's serializer warning when `input`
  is a string.
- `anthropic.Anthropic(api_key=…, max_retries=0, open_telemetry={"traces": False, "propagation": False})` →
  `client.open_telemetry == {"propagation": False, "traces": {"enabled": False, …}}`. `client.is_closed()`,
  `client.close()`. The per-request timeout reaches the transport as `request.extensions["timeout"]["read"]`.
- Tests use `httpx2.Client(transport=httpx2.MockTransport(handler))` (the SDK's HTTP library, `httpx2` 2.16.0, typed).
- **pydantic and whitespace (the reason for D-14).** With `str_strip_whitespace=True`, validation strips strings nested
  anywhere inside a `JsonValue` field: `items=({"thinking": "  think\n"},)` is stored as `"think"`. `Model.model_construct(
  …)` skips validation and keeps the text exactly. A constructed instance then passes **unchanged** (same object, no
  re-validation, pydantic's default `revalidate_instances="never"`) into a validated parent: `ToolStepRequest(messages=pm,
  …).messages is pm`, `Attempt[ToolStep](value=step, …).value is step`, and also the unparametrised `Attempt(value=step,
  …)`. It still compares equal to a validated instance with the same values, stays frozen (assignment raises
  `ValidationError`), and survives `model_dump_json()` and `model_copy()`.

### 4.4 This module's public surface (`src/meridian/adapters/models/anthropic.py`)

```python
ANTHROPIC_PRICES: Mapping[str, TokenPrice] = MappingProxyType({
    "claude-sonnet-5-5": TokenPrice(input=2.00, output=10.00, cache_write_5m=2.50, cache_read=0.10),
})                                     # US dollars per million tokens; research §2a (S-187), read 2026-10-20
CHOICE_MAX_TOKENS: Final = 1500        # = AEA-02 default PLANNER_FALLBACK max_tokens (D-4)
CHOICE_EFFORT: Final[Literal["low", "medium", "high"]] = "low"   # = PLANNER_FALLBACK effort (D-4)

def build_anthropic_client(api_key: SecretStr) -> anthropic.Anthropic: ...

class AnthropicAdapter:                # implements ChoiceModel, StructuredModel, ToolCallingModel (and ToolTranscript)
    provider: ClassVar[ProviderName] = "anthropic"
    def __init__(self, client: anthropic.Anthropic, *, model: str) -> None: ...
    @property
    def model(self) -> str: ...
    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]: ...
    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]: ...
    def start(self, user: str) -> ProviderMessages: ...
    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...
```

---

## 5. Steps (build order; each ends with a check)

The module follows DO-3 §4.3: one adapter, one external system, no business logic; it depends only on `ports/models`
and `domain/common` (dependency inversion: the gateway sees only the Protocols). No new seam or abstraction is added.

**Step 0 — setup.** In the worktree: `export UV_LINK_MODE=hardlink`; `uv sync` (no venv copies; no `node_modules`).
Confirm AEA-02 is on the branch base: `uv run python -c "import meridian.ports.models, meridian.domain.common"` exits 0
(if not, stop: blocked on AEA-02). Record the frozen hashes: `sha256sum tests/contract/_anthropic_fixtures.py
tests/contract/test_anthropic_adapter.py tests/unit/web/test_container.py`. Check: `uv run pytest
tests/contract/test_anthropic_adapter.py -q` fails at collection with `ModuleNotFoundError: No module named
'meridian.adapters.models.anthropic'`.

**Step 1 — module skeleton.** Create `src/meridian/adapters/models/anthropic.py`: docstring (one sentence: "Anthropic
adapter: one Sonnet request per call, reported as a typed Attempt; never raises."), then `from __future__ import
annotations`; imports: `json`, `logging`, `math`, `re`, `time`, `from collections.abc import Callable, Mapping,
Sequence`, `from types import MappingProxyType`, `from typing import Any, ClassVar, Final, Literal, cast`, `import
anthropic`, `from anthropic.types import Message, MessageParam, TextBlock, TextBlockParam, ToolUseBlock`,
`from pydantic import BaseModel, JsonValue, SecretStr`, the AEA-02 names of §4.1 that are used, absolute imports only.
Module constants: §4.4 plus

```python
_LOG = logging.getLogger(__name__)
_SPEND_LIMIT_PHRASES: Final = ("spend limit", "usage limit", "credit balance")      # MOD-3 [A]
_RETRYABLE: Final = frozenset({ProviderFailureKind.TIMEOUT, ProviderFailureKind.CONNECTION,
                               ProviderFailureKind.RATE_LIMITED, ProviderFailureKind.OVERLOADED,
                               ProviderFailureKind.SERVER})                         # DO-4 §11
_REQUEST_ID: Final = re.compile(r"[A-Za-z0-9_-]{1,128}")
```

and one private exception `class _InvalidOutput(Exception): """The reply arrived but is not usable."""`. Drop any
import ruff reports unused. Check: `uv run python -c "import meridian.adapters.models.anthropic"` exits 0.

**Step 2 — constructor, `model`, client builder.**
1. `__init__`: if `model not in ANTHROPIC_PRICES`: `raise ValueError("no ANTHROPIC_PRICES row for this model ID")`
   (*invariant: start-up fails rather than recording $0; the message carries no value*). Then
   `self._client = client.with_options(max_retries=0)` (*invariant: one HTTP attempt even if a caller passes a client
   with SDK retries on, AC-1*); `self._model = model`; `self._price = ANTHROPIC_PRICES[model]`. Define no `__repr__`
   that prints the client (the default object repr carries no key; test 11 checks `repr(adapter)`).
2. `model` is a read-only `@property` returning `self._model`.
3. `build_anthropic_client(api_key)`: `return anthropic.Anthropic(api_key=api_key.get_secret_value(), max_retries=0,
   open_telemetry={"traces": False, "propagation": False})`. Docstring: the one SDK client (models.md §7); no SDK
   retries (the gateway owns retrying); no SDK spans or trace headers (the gateway owns masked tracing).
Check: test 2 passes once step 4 exists; test 7's adapter line passes now.

**Step 3 — pure helpers** (module-level private functions; each with the invariant it protects):
1. `_clean_request_id(value: object) -> str | None`: return `value` if it is a `str` and `_REQUEST_ID.fullmatch(value)`,
   else `None`. *Invariant: `provider_request_id` holds only a request id (AC-9).*
2. `_count(value: object) -> int`: `value` if `isinstance(value, int) and not isinstance(value, bool) and value >= 0`,
   else `0`. *Invariant: building `ProviderCall` (fields `ge=0`) can never raise.*
3. `_counts(usage: object) -> tuple[int, int, int, int, int]` = `(input, output, cache_read, cache_write, thinking)`
   from `getattr(usage, "input_tokens", None)`, `"output_tokens"`, `"cache_read_input_tokens"`,
   `"cache_creation_input_tokens"`, and `getattr(getattr(usage, "output_tokens_details", None), "thinking_tokens",
   None)`, each through `_count`. `usage is None` → all 0.
4. `_cost(price: TokenPrice, input_tokens: int, output_tokens: int, cache_write: int, cache_read: int) -> float`:
   `(input_tokens * price.input + output_tokens * price.output + cache_write * price.cache_write_5m + cache_read *
   price.cache_read) / 1_000_000`. **Thinking is not a parameter** (MOD-16: already inside `output_tokens`). If the
   result is not finite (`math.isfinite`) or is negative, return `0.0`.
5. `_retry_after(headers: Any) -> tuple[bool, float | None]` (*present*, *seconds*): read `headers.get("retry-after-ms")`
   and `headers.get("retry-after")`; *present* = either is a non-blank string. *seconds* = the first that parses:
   `float(ms) / 1000`, then `float(s)`; accept only finite values `>= 0`; otherwise `None`. Catch `ValueError` from
   `float` per header. (A present but unparseable header is still "present": the 429 is a rate limit with
   `retry_after_s=None`.)
6. `_is_spend_limit(body: object) -> bool`: `error = body.get("error") if isinstance(body, dict) else None`; return
   `isinstance(error, dict) and error.get("type") == "invalid_request_error" and isinstance(error.get("message"), str)
   and any(p in error["message"].lower() for p in _SPEND_LIMIT_PHRASES)`. The message is read here and nowhere else;
   it is not returned, stored or logged (*AC-9*).
7. `_failure(kind: ProviderFailureKind, *, http_status: int | None, request_id: str | None, retry_after_s: float |
   None = None) -> ProviderFailure`: `ProviderFailure(kind=kind, provider="anthropic", http_status=http_status,
   retry_after_s=retry_after_s, retryable=kind in _RETRYABLE, provider_request_id=request_id)`.
8. `_failure_for_status(exc: anthropic.APIStatusError) -> ProviderFailure` (`status = exc.status_code`, `rid =
   _clean_request_id(exc.request_id)`), **in this order** (stage7/models §3):
   - `400`: `OUR_SPEND_LIMIT` if `_is_spend_limit(exc.body)`; else `_LOG.warning("anthropic_400_unclassified",
     extra={"provider_request_id": rid})` and `BAD_REQUEST`.
   - `401` → `AUTH`; `402` → `PROVIDER_SPEND_CAP`; `403` → `AUTH`; `404` → `NOT_FOUND`; `408` → `TIMEOUT`;
     `409` → `SERVER`; `413` → `BAD_REQUEST`.
   - `429`: `present, seconds = _retry_after(exc.response.headers)`; present → `RATE_LIMITED` with
     `retry_after_s=seconds`; not present → `PROVIDER_SPEND_CAP` (research §2b).
   - `529` → `OVERLOADED`; `500 <= status <= 599` → `SERVER`; `400 <= status <= 499` → `BAD_REQUEST`;
     anything else (e.g. 302) → `INVALID_OUTPUT` (a response arrived that is not usable; MOD-2 catch-all).
   - Every branch passes `http_status=status`, `request_id=rid`.
Check: `uv run mypy src/meridian/adapters/models/anthropic.py` is clean.

**Step 4 — the one send path.** `def _send[T: BaseModel](self, build: Callable[[], dict[str, Any]], read:
Callable[[Message], T], *, timeout_s: float) -> Attempt[T]`, numbered:
1. `started = time.perf_counter()`; `arrived = False`; `status: int | None = None`; `rid: str | None = None`;
   `message: Message | None = None`.
2. `try:` `kwargs = build()`; `raw = self._client.messages.with_raw_response.create(**kwargs, timeout=timeout_s)`
   (*the only HTTP call; one per method call*).
3. `arrived = True`; `status = raw.status_code`; `rid = _clean_request_id(raw.headers.get("request-id"))`;
   `parsed = raw.parse()`.
4. If `not isinstance(parsed, Message)`: `raise _InvalidOutput`. `message = parsed`.
5. If `not isinstance(message.content, list)`: `raise _InvalidOutput`.
6. **`stop_reason` before content** (*AC-5*): `"refusal"` → return the failed attempt with `REFUSAL`;
   `"max_tokens"` → `MAX_TOKENS` (both with `http_status=status`, `rid`, the message's usage and `stop_reason`).
7. `value = read(message)` (raises `_InvalidOutput`, `ValueError` or `pydantic.ValidationError` on bad output).
8. Return `Attempt[T](value=value, record=self._record(started, usage=message.usage, failure=None, rid=rid,
   stop_reason=message.stop_reason), failure=None)`.
9. `except anthropic.APITimeoutError:` → `TIMEOUT` (`http_status=None`, `rid=None`). **This clause comes first.**
10. `except anthropic.APIConnectionError:` → `CONNECTION` (`http_status=None`, `rid=None`).
11. `except anthropic.APIStatusError as exc:` → `_failure_for_status(exc)` (no usage; `stop_reason=None`).
12. `except Exception:` → `INVALID_OUTPUT` with `http_status=status`, `rid` if `arrived`, using `message.usage` and
    `message.stop_reason` when `message is not None` (else no usage, `stop_reason=None`); if not `arrived`,
    `CONNECTION` with `http_status=None`, `rid=None` (*MOD-2 catch-all; never raises*). Do **not** bind the exception to
    a name, format it, log it or chain it.
13. A failed attempt is `Attempt[T](value=None, record=self._record(started, usage=…, failure=f,
    rid=f.provider_request_id, stop_reason=…), failure=f)`; write one private method `_failed` for it.

`_record(self, started, *, usage, failure, rid, stop_reason) -> ProviderCall`: `input, output, cache_read,
cache_write, thinking = _counts(usage)`; `ProviderCall(provider="anthropic", model=self._model, latency_ms=max(0,
int((time.perf_counter() - started) * 1000)), input_tokens=input, output_tokens=output, cache_read_tokens=cache_read,
cache_write_tokens=cache_write, thinking_tokens=thinking, cost_usd=_cost(self._price, input, output, cache_write,
cache_read), cost_source="price_table", status="error" if failure else "ok", failure=failure,
provider_request_id=rid, stop_reason=stop_reason)`. *Invariant: `model` is always the constructor value (AC-2);
`failure` set exactly when `status == "error"` (AC-1).* (Rename the local `input` to `in_tokens` if ruff flags A001.)

Check: tests 1, 3, 4, 5, 11, 12, 13 pass for `structured` once step 5 exists.

**Step 5 — `structured` and `choose`.**
1. `_system_blocks(prefix: str, dynamic: str) -> list[TextBlockParam]`: a prefix block `{"type": "text", "text":
   prefix, "cache_control": {"type": "ephemeral"}}` only if `prefix.strip()`; a dynamic block `{"type": "text", "text":
   dynamic}` (no `cache_control`) only if `dynamic.strip()` (*the API rejects empty text blocks; the cache mark sits on
   the stable prefix only, AC-6*). Build both dicts fresh on every call (no shared module-level dict).
2. `_text(message: Message) -> str`: `"".join(b.text for b in message.content if isinstance(b, TextBlock))`.
3. `structured`: `build` returns `{"model": self._model, "max_tokens": req.max_tokens, "system":
   _system_blocks(req.system_prefix, req.system_dynamic), "messages": [{"role": "user", "content": req.user}],
   "output_config": oc}` with `oc = {"format": {"type": "json_schema", "schema":
   anthropic.transform_schema(req.output_model)}}` plus `oc["effort"] = req.effort` when `req.effort is not None`.
   `read` is a nested `def` returning `req.output_model.model_validate_json(_text(m))`. Never strip code fences:
   structured outputs return bare JSON.
4. `choose`: `build` returns `{"model": self._model, "max_tokens": CHOICE_MAX_TOKENS, "system":
   _system_blocks(req.system, ""), "messages": [{"role": "user", "content": _render_choice(req)}],
   "output_config": {"format": {"type": "json_schema", "schema": _choice_schema(req)}, "effort": CHOICE_EFFORT}}`.
   - `_choice_schema(req)` = `{"type": "object", "properties": {f.name: {"type": "string", "enum": list(f.options),
     "description": f.instructions} for f in req.fields}, "required": [f.name for f in req.fields],
     "additionalProperties": False}` (enum = option **keys**, in insertion order).
   - `_render_choice(req)` = `json.dumps({"state": req.state, "questions": [{"name": f.name, "instructions":
     f.instructions, "options": f.options} for f in req.fields]}, ensure_ascii=False)`.
   - `read`: `data = json.loads(_text(m))`; `raise _InvalidOutput` unless `isinstance(data, dict)` and `set(data) ==
     {f.name for f in req.fields}` and, for every field, `isinstance(data[f.name], str) and data[f.name] in f.options`;
     return `ChoiceAnswer(choices={f.name: data[f.name] for f in req.fields}, probabilities=None)` (*Sonnet reports no
     calibrated confidence, DO-4 §0*).
Check: tests 1–8, 11–13 pass for `choose` and `structured`.

**Step 6 — tool calling (MOD-17, D-14).**
1. `_messages(self, items: tuple[JsonValue, ...]) -> ProviderMessages`: `return ProviderMessages.model_construct(
   provider="anthropic", model=self._model, items=items)`. *Invariant (P-4): provider text is never re-validated, so
   `MeridianModel`'s whitespace stripping cannot alter a thinking block; `items` is always a `tuple` of JSON-safe values
   built by this class.* Docstring: one sentence saying exactly that, citing models.md §1 / MOD-17.
2. `start(user)`: `return self._messages(({"role": "user", "content": user},))`.
3. `tool_step`: `build` returns `{"model": self._model, "max_tokens": req.max_tokens, "system":
   _system_blocks(req.system_prefix, req.system_dynamic), "messages": cast(list[MessageParam],
   list(req.messages.items)), "tools": [{"name": t.name, "description": t.description, "input_schema":
   t.input_schema, "strict": True} for t in req.tools], "tool_choice": {"type": "auto"}}` plus `"output_config":
   {"effort": req.effort}` when `req.effort is not None`. `strict` is always `True` (ticket AC-6), whatever
   `ToolSchema.strict` says. Never send `thinking`, `tool_choice` `any`/`tool`, or `stream`.
4. `read` → `ToolStep.model_construct(text=_text(m), tool_calls=tuple(ToolCall(id=b.id, name=b.name, args=b.input if
   isinstance(b.input, dict) else None) for b in m.content if isinstance(b, ToolUseBlock)), raw={"role":
   "assistant", "content": [b.model_dump(mode="json", exclude_none=True, warnings=False) for b in m.content]},
   stop_reason=m.stop_reason)`. `ToolCall` objects are built **with** validation (a bad id or args raises inside `read`
   → `INVALID_OUTPUT`); only the `ToolStep` wrapper is constructed, so `raw` keeps the provider's blocks byte-exact
   (*SP-1's measured resend shape; thinking text and signature untouched*).
5. `append(messages, step, results)`: if `messages.provider != self.provider or messages.model != self._model`:
   `raise ValueError("ProviderMessages were built by another adapter")` (*a wiring bug, not an `Attempt.failure`;
   the message names no value*). Else `return self._messages((*messages.items, step.raw, {"role": "user", "content":
   [{"type": "tool_result", "tool_use_id": call_id, "content": text} for call_id, text in results]}))`.
Check: tests 9 and 10 pass. **If test 9 fails only on whitespace in the thinking text**, a `ProviderMessages(...)` or
`ToolStep(...)` was built with validation somewhere in this module: use `_messages` / `model_construct` as above. Never
change the test, `ports/*` or `domain/*`.

**Step 7 — the container hunk.** Replace the body and docstring of `register_anthropic` (nothing else in the file):

```python
def register_anthropic(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-17 models: the Anthropic adapter (models.md §2, §7).

    Provides Key[anthropic.Anthropic]("anthropic_client"): the one SDK client, built from settings.anthropic_api_key
    with max_retries=0 and the SDK's own spans off, and closed on shutdown. AnthropicAdapter objects (one per model)
    are built from it by AEA-51's adapter_for. Caps the SDK's "anthropic" logger at WARNING, because its DEBUG lines
    carry whole request payloads.
    """
    import logging

    import anthropic

    from meridian.adapters.models.anthropic import build_anthropic_client

    logging.getLogger("anthropic").setLevel(logging.WARNING)

    def _client(c: Container) -> anthropic.Anthropic:
        client = build_anthropic_client(settings.anthropic_api_key)
        c.on_close(client.close)
        return client

    container.provide(Key[anthropic.Anthropic]("anthropic_client"), _client)
```

The docstring keeps `AEA-17` (AEA-01's docstring check) and must no longer contain `No-op until` (§3.5's guard keys on
it). The hunk reads no setting until the factory runs. Check: test 7 and `uv run pytest tests/unit/web/ -q` pass.

**Step 8 — gates.** §7.2 commands, cheapest first; fix and repeat until green. Size check: `wc -l
src/meridian/adapters/models/anthropic.py` ≤ 400 (hard cap 600).

**Step 9 — journey record (AC-11).** Run `uv run python -m tests.journeys.affected --base main` and write §7.4.

**Step 10 — context (AC-12).** Use the feature commit's SHA as `<feat sha>`.
- `.claude/reference/area-map.md`, row `| 1 | **A2 Models** | …`: change only the last (**Status**) cell from `planned`
  to `partly built: \`adapters/models/anthropic.py\` actual (AEA-17, \`<feat sha>\`); the rest planned` (the A0 row's
  pattern). If a sibling (AEA-18, 20, 26) already changed that cell, add this entry to its list and keep theirs.
- `docs/design/code-design.md`, the `**Built:**` line under §3 (line 180, today `**Built:** \`policy/texts.py\` (AEA-03,
  \`2689582\`).`): append `, \`adapters/models/anthropic.py\` (AEA-17, \`<feat sha>\`)` before the final full stop; keep
  every entry already there. Touch nothing else in the file.
- `.claude/state/icm-progress.md`, the **first** row named *Routes verified against code and tests* (line 17): replace
  its evidence cell with `<run-date>: latest slice AEA-17 \`adapters/models/anthropic.py\` (<feat sha>):
  \`tests/contract/test_anthropic_adapter.py\` passes (<N> passed)`; keep ≤ 400 characters and the status column.
- Dev log (outside the repo, not committed): `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<run-date>-
  aea-17-anthropic-adapter-claude-01.md`; header per `.claude/reference/dev-log.md` (project, date/TZ
  America/Chicago, topic, writer `Claude (Sonnet 5.5, claude-sonnet-5-5)`, host `claude-vultr`, branch, base SHA), one
  entry **Changed / Why / Checked / Remaining** (Remaining: live compatibility waits on AEA-61; cross-adapter contract
  and `adapter_for` on AEA-51; spend-limit phrases are [A] until the first real spend-limit 400).
- `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` → no FAIL.

**Commits** (explicit `git add <paths>`, never `-A`; the last line of every message is
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; commit on the ticket branch only; never push, never
force-push; the merge step alone pushes `main`):
1. `feat(models): AnthropicAdapter, one Sonnet request per call (AEA-17)` — `git add
   src/meridian/adapters/models/anthropic.py src/meridian/web/container.py`.
2. `docs(AEA-17): journey record and context for adapters/models/anthropic.py` — `git add
   docs/testing/journeys/<run-date>-AEA-17.md .claude/reference/area-map.md .claude/state/icm-progress.md
   docs/design/code-design.md`.
(The test-writer's commit comes before these; §3.3.)

### 5.1 What the implementer must **not** do

- No retry loop, no sleep, no deadline arithmetic, no ledger write, no span, no redaction, no `role`/`attempt` stamp
  (AEA-20). No shared failure classifier module (S-24). No streaming (SDQ-2). No `thinking` parameter of any kind.
- Never `str(exc)`, `repr(exc)`, `exc.message`, `logger.exception`, `exc_info=`, f-strings with an exception or body,
  or `raise … from exc`. The only log line is `anthropic_400_unclassified`.
- Never read `ANTHROPIC_API_KEY`, `os.environ` or `.env` in the adapter; the key arrives only through the hunk's settings.
- No module-level client, settings or SDK call (DO-3 §2.1). No import of `openrouter_jev`, `agent/*`, `services/*`,
  `web/*` from the adapter.
- Never build `ProviderMessages` or `ToolStep` with validation (`ProviderMessages(...)`, `.model_validate(...)`) inside
  the adapter; use `_messages` / `ToolStep.model_construct` (D-14). Do not change any model's `model_config`.
- Do not edit any frozen test, `ports/*`, `domain/*`, `config.py`, another hunk, `pyproject.toml` or `uv.lock`.
- No paid call: every test uses the mocked transport or `ExplodingClient`. Do not run `tests/live`. No server.

---

## 6. Data and fixtures

Synthetic only, hand-built from research §1/§4 shapes and the SP-1 measured response shape
(`docs/plans/fanout/2026-10-20-sp1/build.md` step 5): model ID `claude-sonnet-5-5`, request id `req_011TestFixture01`,
error bodies `{"type": "error", "error": {"type", "message"}, "request_id"}`, the WP-style user text "Can I move my
tune-up?" (no customer ID, phone, code or card). The API key is `"sk-test-" + secrets.token_hex(12)` generated at import
and the sentinel `"ZZSENTINEL-" + secrets.token_hex(4)`; neither appears in a test name or id. No issued file is read;
no network; no `.env`.

---

## 7. Checks

### 7.1 Tests the implementer must make pass

The 14 frozen tests of §3.3 (about 120 items with parametrisation) plus the static function, and the existing
`tests/unit/web/test_container.py` (with §3.5) and `tests/unit/test_import_direction.py`.

**Affected tests** = `tests/contract/test_anthropic_adapter.py` (the new module) + `tests/unit/web/` (mirrors the changed
`web/container.py`) + `tests/unit/test_import_direction.py` (reads `container.py`'s source); confirm with
`grep -rl "meridian.adapters.models.anthropic\|meridian.web.container\|web/container.py" tests/`. No full-suite trigger
applies (no shared fixture, settings, dependency or lockfile change; `container.py`'s module-level imports are
unchanged).

### 7.2 Commands (from the worktree; `export UV_LINK_MODE=hardlink`)

| Order | Check | Command | Passing looks like |
|---|---|---|---|
| iterate | Affected tests | `uv run pytest tests/contract/test_anthropic_adapter.py tests/unit/web/ tests/unit/test_import_direction.py -q` | all pass, no skips |
| 1 | Format | `uv run ruff format --check src/meridian/adapters/models/anthropic.py src/meridian/web/container.py tests/contract/ tests/unit/web/` | 0 files would be reformatted |
| 2 | Lint | `uv run ruff check src/meridian/adapters/models/anthropic.py src/meridian/web/container.py tests/contract/ tests/unit/web/` | `All checks passed!` |
| 3 | Types | `uv run mypy` | `Success: no issues found` (proves P-1) |
| 4 | Affected tests | the *iterate* command, plus `-s` once on `::test_failure_kind_mapping` for its printed table | all pass |
| 5 | Affected journeys | `uv run python -m tests.journeys.affected --base main` | prints `changed files: <k> (base main)` then `0 journeys affected`, exit 0 |
| 6 | Tamper check | `sha256sum tests/contract/_anthropic_fixtures.py tests/contract/test_anthropic_adapter.py tests/unit/web/test_container.py` | equals step 0's hashes |
| 7 | Context | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL |
| 8 | Diff scope | `git diff --name-only main...HEAD` | exactly the §2.1 repo paths (incl. the test-writer's) |

If `pytest-xdist` is ever added for a run, use `-n 2` at most (not needed here). No server is started.

### 7.3 Capture and evaluation checks

| Check | Command | Evidence |
|---|---|---|
| Capture (WF-1 `model_call` / `spend_ledger` fields per attempt) | test 12 | Every field asserted on fixtures; integrated CAP-1 is AEA-51's |
| Evaluation | n/a | Ticket *Evaluation*: none added; cross-adapter contract is AEA-51 |

### 7.4 Journey record — `docs/testing/journeys/<run-date>-AEA-17.md`

```markdown
# Journey record: AEA-17 Anthropic adapter

| Field | Value |
|---|---|
| Claim | AEA-17 AC-11: `adapters/models/anthropic.py` (AnthropicAdapter) maps every Anthropic response and failure to a typed `Attempt` (AC-1…AC-10). No deterministic journey reaches this code: journeys replace the provider call with the scripted adapter (integrated-journeys §3 rule 1). Proved instead by `tests/contract/test_anthropic_adapter.py` on a mocked transport, and later by AEA-61's live smoke |
| Level | `mock-tested` |
| Tested revision | `<feat sha>` |
| Environment | VPS (`claude-vultr`), `uv run`, Python 3.12, `anthropic` 1.17.0 with an `httpx2.MockTransport`; no server, no database, no network, no paid call; model ID `claude-sonnet-5-5` |
| Command | `uv run pytest tests/contract/test_anthropic_adapter.py tests/unit/web/ tests/unit/test_import_direction.py -q`; `uv run python -m tests.journeys.affected --base main` |
| Result | <N> passed. Affected: `changed files: <k> (base main)` then `0 journeys affected`, exit 0 |
| Evidence location | this record; GitLab issue #17 comment |
| Remaining limitations | No real Anthropic response seen; the spend-limit phrases are [A] (MOD-3); whether a burst 429 ever arrives without `retry-after` is unmeasured (models.md §3 risk); real thinking-block text is unmeasured (D-14 keeps it byte-exact either way) |
| Blocked by | AEA-61 (live smoke, wave 4, `gate::paid`) for `verified with live models`; no journey will reach this code by design; cross-adapter contract waits on AEA-51 |
| Journeys that will exercise this code | None (journeys use the scripted adapter) |
```

### 7.5 Implementer report must include

Per AC (1–12, example pair, P-1…P-4): verified / not, the command, the result line. Test 3's printed fixture → kind
table. The two commit SHAs. The tamper-check hashes. The dev-log path (uncommitted).

---

## 8. Risks and requests

### 8.1 Requests and notes (to the orchestrator; none needs Innocent)

- **R-1 (withdrawn 2026-10-21).** The earlier ask that AEA-02 set `str_strip_whitespace=False` on `ProviderMessages` and
  `ToolStep` conflicts with AEA-02's frozen `test_every_model_uses_meridian_config`. Replaced by D-14 inside this
  ticket. **Nothing is asked of AEA-02.** Note for consumers (AEA-20 gateway, AEA-35 runner, AEA-51 wiring, AEA-11
  fakes): pass `ProviderMessages` and `ToolStep` objects through as instances; never rebuild them from dicts
  (`model_validate(x.model_dump())`), which would strip whitespace from thinking text and can make Anthropic reject
  the next tool step. Putting an instance into a validated parent (`ToolStepRequest`, `Attempt`, `ModelOutcome`) is
  safe (§4.3).
- **R-2 AEA-01 container test.** §3.5. Every ticket that fills a hunk (AEA-10, 17, 27, …) hits the same assertion; AEA-10
  plans the identical two lines, so the first to merge lands them and the others find them present (a textual merge of
  identical lines). The test-writer makes this edit in AEA-01's test file; please confirm it is allowed (AEA-10's plan
  asks the same, as its R-13).
- **R-3 AEA-51 wiring.** The client is provided as `Key[anthropic.Anthropic]("anthropic_client")`. `adapter_for`
  builds `AnthropicAdapter(container.get(Key[anthropic.Anthropic]("anthropic_client")), model=spec.model)` and memoises
  by `(provider, model)`. AEA-17 builds no adapter in the container. Journeys (AEA-57) build the container with
  settings that must still carry an `anthropic_api_key` (`Settings` requires it anyway); building the client makes no
  network call.
- **R-4 Planner-fallback limits.** `ChoiceRequest` (DO-4 §12) carries no `max_tokens` or `effort`, and the gateway
  passes only `req` and `timeout_s`, so `RoleSpec(PLANNER_FALLBACK).max_tokens/effort` cannot reach the adapter.
  Decision D-4 uses constants equal to AEA-02's defaults (1500, `"low"`). If anyone changes those `RoleSpec`
  values, these constants will not follow. Note for AEA-37 / AEA-51; a later DO-4 change could add the two fields to
  `ChoiceRequest`.
- **R-5 AEA-23 logging.** The hunk caps the `anthropic` logger at `WARNING` (P-2). If AEA-23's logging setup
  reconfigures logger levels, it should keep that cap.
- **R-6 Shared context files.** AEA-17, 18, 20, 26 edit the same A2 area-map cell, the same `**Built:**` line and the same
  ICM row; expect textual merge conflicts on those lines. The merge agent keeps every ticket's entry.
- **R-7 Second file in `tests/contract/`.** The collision map gives each adapter ticket "one file" there. This plan adds
  a ticket-private `_anthropic_fixtures.py` beside the test file, because fixtures plus tests would exceed the 500-line
  test cap in one file. No other ticket names or edits it. If the orchestrator prefers strict one-file, the test-writer
  may merge both into `test_anthropic_adapter.py` only if the result stays ≤ 500 lines.

### 8.2 Decisions made in this plan (engineering; reversible)

| ID | Decision | Why |
|---|---|---|
| D-1 | Call `messages.with_raw_response.create` then `raw.parse()` | Separates "before a response" from "after a response" for the MOD-2 catch-all, and gives the `request-id` header on success |
| D-2 | The adapter applies `client.with_options(max_retries=0)` itself | One attempt is the adapter's contract (DO-4 §12), whatever client is injected |
| D-3 | Client built with `open_telemetry={"traces": False, "propagation": False}`; SDK logger capped at `WARNING` | SDK 1.17 traces by default and logs payloads at DEBUG; the adapter must write no span or payload log (P-2) |
| D-4 | `choose` uses `CHOICE_MAX_TOKENS = 1500`, `CHOICE_EFFORT = "low"` | `ChoiceRequest` has no such fields (R-4) |
| D-5 | `choose` sends `req.system` as the cached system block, `{"state", "questions"}` JSON as the user turn, and a strict enum schema (option keys) | The port gives no prompt layout for Sonnet; JSON keeps the state exact |
| D-6 | `http_status` = 200 for failures after an HTTP 200 (refusal, max tokens, invalid output); `None` when no response arrived | M-24 counts failures by kind and status |
| D-7 | `provider_request_id` kept only if it matches `[A-Za-z0-9_-]{1,128}` | AC-9 "holds only the request id" |
| D-8 | `retry-after-ms` preferred over `retry-after`; a present but unparseable header still means rate limited (`retry_after_s=None`) | Only a 429 with *no* header is the spend cap (research §2b) |
| D-9 | 3xx or any status outside 400–599 → `INVALID_OUTPUT`, not retryable | MOD-2 "after a response" catch-all |
| D-10 | Tools always sent with `strict: True` | Ticket AC-6 |
| D-11 | Empty system blocks are omitted | The API rejects empty text blocks |
| D-12 | `ToolStep.raw` = `{"role": "assistant", "content": [block.model_dump(mode="json", exclude_none=True, warnings=False)]}`; non-dict tool input → `args=None` | SP-1's live-measured resend shape; thinking signature preserved |
| D-13 | Container key name `"anthropic_client"`; the hunk provides the client only | models.md §7: one client; adapters per model are AEA-51's |
| D-14 | `ProviderMessages` and `ToolStep` are built with `model_construct` (helper `_messages`), never validated, inside the adapter | MOD-17 requires items "exactly as sent and received … untouched"; `MeridianModel` strips whitespace in nested `JsonValue` strings; AEA-02's frozen AC-1 test forbids turning that off per model. The values are JSON-safe by construction (SDK `model_dump(mode="json")` and our own literals), so skipping validation loses no check (scratch-proved, §4.3) |

### 8.3 Other risks

- **AEA-02 drift.** This plan copies AEA-02's plan; the merged code wins on names. A test that cannot be written as
  §3.3 says goes back to the planner, not around the contract.
- **A consumer re-validates provider messages** (R-1 note). If AEA-20/35 rebuild `ProviderMessages` from a dict, thinking
  whitespace is stripped there, outside this ticket. AEA-51's integrated turn would surface it only with a real
  provider; AEA-61's live smoke is the check.
- **`tool_step` does not check `req.messages.provider/model`.** Only `append` raises (MOD-17); `start`/`append` are the
  only builders, so a foreign list cannot reach `tool_step` without a wiring bug elsewhere. Accepted.
- **`append` with empty `results`** appends a user message with an empty content list, which Anthropic rejects
  (→ `BAD_REQUEST`, handoff). Pairing results with tool calls is the runner's job (AEA-35).
- **Spend-limit phrases are [A]** (MOD-3); a miss is `BAD_REQUEST` (no retry, no spend) and logs
  `anthropic_400_unclassified` with the request ID for console lookup.
- No signed contract (OpenAPI, `UI_CONTRACTS.md`) is touched; no decision D-4…D-15 of `stage7-signoff.md` is answered
  differently.

---

## 9. Readiness

**READY**, blocked only on **AEA-02 merged on `main`** (imports `meridian.ports.models`, `meridian.domain.common`; its
branch has frozen tests at `de9bb42` and its implementer has started). Nothing is asked of AEA-02 any more (R-1
withdrawn; D-14). AEA-01 is on `main`. Same-wave and later siblings (AEA-10, 18, 20, 51) are not imported. R-2 needs the
orchestrator's yes for the test-writer's two-line edit to AEA-01's test file (shared with AEA-10). No `NEEDS-DECISION`.
