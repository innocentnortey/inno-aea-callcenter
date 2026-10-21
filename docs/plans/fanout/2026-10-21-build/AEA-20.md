# Plan — [AEA-20] models: the gateway

**Status:** planned (READY; build starts once AEA-02 is merged on `main` — AEA-01 and AEA-04 already are)
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #20 (= `docs/plans/tickets/AEA-20.md`) · **Base revision:** `16ca639` (main, 2026-10-21; first written against `c0621de`, refreshed against `16ca639` the same day — see §8 R-11)
**Lane / risk:** `lane::build-loop` · `risk::security` (MOD-14): `test-writer-agent` freezes the tests in §3.3 first; `security-privacy-agent` reads this diff at the wave-1 merge.
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21. **Implementer:** `fanout-implementer` on Sonnet.

---

## 1. Goal and sources

### 1.1 Goal (quoted from the issue, *What to build*)

> Every model call in a turn (planner, danger classifier, planner fallback, specialist step, responder, brief) goes
> through **one** object, `ModelGateway` (DO-3 §4.5, S-2). A node asks for a role; the gateway looks up the adapter and
> `RoleSpec` that the typed role maps hold for it […]. Before a call it asks the ledger whether that **provider** is
> admitted, checks how much of the turn's 60 s is left, counts the per-turn Sonnet brake, and redacts the request with
> the role's profile. It makes at most two attempts, wraps each adapter `ProviderCall` into a `CallRecord` with the role
> and attempt number, and writes one ledger row and one span per attempt. A provider spend-cap failure trips that
> provider's circuit. Our own $30/day cap is **not** checked here.

In practice: AEA-37's planner node calls `gateway.choose(Role.PLANNER, req, ctx)`. The gateway finds the Jev adapter and
its `RoleSpec` (cap 3 s, JEV profile), asks `ledger.admit_call("openrouter_jev")`, computes `timeout = min(3, time left)`,
replaces "Omar Patel", "512-…-0102", "MHC-10002", "INV-204411" with `[name]`, `[phone]`, `[customer id]`, `[invoice id]`,
calls the adapter once (twice if a retryable failure leaves time), writes one `spend_ledger` row and one masked span per
attempt, and returns a `ModelOutcome` the node reads. It never raises on a provider failure and never chooses a fallback.

### 1.2 Context

Wave 1, area A2 (DO-3 §8). The adapters (AEA-17, 18) and the trace sink (AEA-19) are wave-1 siblings; the ledger
service (AEA-26) is **wave 2**. The gateway therefore receives all of them by injection and is tested with its own
doubles (slice plan §0 rule 1; ticket conventions). **On `main` at `16ca639`:** AEA-01 (`policy/limits.py`,
`web/container.py` stubs, `pyproject.toml`, `tests/conftest.py`, `tests/journeys/affected.py`; merged `07924f5`) and
AEA-04 (`privacy/redact.py`, `9145044`; merged `ef03e05`). **Not on `main`:** AEA-02 (`domain/*`, `ports/*`,
`config.py`); its worktree `inno-aea-callcenter-wt/AEA-02` sits at `16ca639` with no commits yet. `src/meridian/domain/`
and `src/meridian/ports/` hold only `__init__.py`. The §4.1–§4.2 shapes are copied from the code on `main`; the §4.3
shapes are copied from the AEA-02 plan (refreshed 2026-10-21 12:08 and re-checked for this refresh: every name the
gateway uses is unchanged), which transcribes DO-4 and the stage7 addenda.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-20.md` | AC-1…AC-12, the seven rules in order, WP-2 pair, owned files, must-not-edit list |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-20, §3 collision map | Owns `agent/gateway.py`; `web/container.py` hunk is AEA-20's only; context files row-only |
| Requirements | PRD R-41 (limits/brakes), §5 *Reliability*, *Spend*; US-16; HP-1 | Rate/spend limit → handoff, not an error: the gateway returns a halt or failure, never raises |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §2 (`TurnBudget.timeout_for`), §11 (`ProviderFailure`, `HaltReason`, `Halt`), §12 (`Role`, role literals, `RoleSpec`, `ModelOutcome`, `ModelGateway`) | Constructor and three methods exactly; `ModelOutcome` fields |
| Addendum (wins over DO-4) | `docs/design/contracts/stage7/models.md` §1 (`ProviderCall`, `CallRecord.from_provider`, `Attempt.record`), §4 (`SpanHandle`, `TraceSink.model_call`), §5 (rules restated), §6 (`admit_call`, `CallAdmission`, circuit table), §7 (container) | Rule order; MOD-1, 10–13 |
| Addendum | `stage7/data.md` §1 (`redact`, `Redactor`, profiles, tokens), §9 items 7–8 | JEV/SONNET per role; TRACE for spans; `Redactor` type |
| Addendum | `stage7/graph-core.md` §1–§2 (`TurnContext.span`, `TurnBudget` in `domain/turn.py`), §5 (halt routing) | `ctx.span` is the span parent; any halt ends the turn (AEA-21) |
| Decisions | `docs/plans/7b-decisions/models.md` MOD-1, 4, 10–14; `stage7-signoff.md` D-14 (DAT-1 = option A) | `redact(text, profile)` signature unchanged; no `known=` argument |
| Code design | DO-3 `docs/design/code-design.md` §2.1 (no SDK in `agent/`), §2.3 rules 1–2, §4.5, §6 S-2, S-20, §9 | No SDK import; no unit of work; injected collaborators |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` | None added (ticket *Evaluation*: E-1/3/4/8 run through this code later) |
| Observability contract | DO-6 `docs/design/observability-contract.md` WF-1 row; `model_call` span row (line 113, "full rendered context and raw output **after masking**"); *Content and redaction* table | One ledger row + one masked span per attempt; traces mask names, phones (last 2 kept), emails, addresses, codes, cards |
| Key-metrics registry | DO-7 M-23, M-24, M-25, M-26 | Per-attempt rows keep M-25/M-26 complete; `attempt=2` rows make M-24 retries countable |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md` | Frozen tests first; affected tests; journey record at `mock-tested`; context rows in the same change |

---

## 2. Boundary

### 2.1 Owned files (the only files the implementer and test-writer may create or edit)

| File | Create / modify | Who | Change |
|---|---|---|---|
| `src/meridian/agent/gateway.py` | create | implementer | `CallLedger`, `ModelOutcome`, `ModelGateway` and private helpers (§4.5, §5) |
| `tests/unit/agent/_gateway_doubles.py` | create | **test-writer (frozen)** | Test doubles and builders (§3.4) |
| `tests/unit/agent/test_gateway.py` | create | **test-writer (frozen)** | The 15 tests of §3.3 plus the mypy static check |
| `docs/testing/journeys/<run-date>-AEA-20.md` | create | implementer | Journey record, level `mock-tested` (AC-11; §7.4) |
| `.claude/reference/area-map.md` | modify (A2 row, **Status** cell only) | implementer | `planned` → `` partly built: `agent/gateway.py` actual (AEA-20, `<feat sha>`); the rest planned `` (§5 step 9; same convention as the A0 row) |
| `.claude/state/icm-progress.md` | modify (one row) | implementer | The **first** row named *Routes verified against code and tests*: replace its evidence cell (§5 step 9) |
| `docs/design/code-design.md` | modify (one line of the §3 tree, line ~265) | implementer | Append `   built AEA-20 <feat sha>` to the `gateway.py` line |
| `docs/design/contracts/internal-components.md` | modify (§12, one sentence) | implementer | Pointer after the *Gateway rules, in order* paragraph (§5 step 9) |
| `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<run-date>-aea-20-gateway-claude-01.md` | create (outside this repo; **not committed** by this ticket) | implementer | One dev-log run file (AC-12) |

`<run-date>` is the build day in America/Chicago (`TZ=America/Chicago date +%F`).

### 2.2 Shared surfaces read, never edited

`src/meridian/policy/limits.py` (AEA-01), `src/meridian/web/container.py` (AEA-01; see §8 R-3: AEA-20 leaves its
`register_gateway` stub untouched), `src/meridian/domain/*`, `src/meridian/ports/*`, `src/meridian/config.py` (AEA-02),
`src/meridian/privacy/redact.py` (AEA-04), `pyproject.toml`, `uv.lock`, `tests/conftest.py`, every `__init__.py`
(AEA-01), `tests/journeys/**` (AEA-01, AEA-57), DO-4 and the stage7 addenda except the one pointer sentence above.

### 2.3 Owned by other tickets — do not create or edit

`adapters/models/*` (AEA-17, AEA-18), `adapters/tracing_langfuse.py` (AEA-19), `services/ledger.py`,
`adapters/sqlite/repos_spend.py` (AEA-26), `tests/fakes/*` (AEA-11), `tests/contract/*` (AEA-17, 18, 51),
`agent/context.py`, `agent/graph.py`, `agent/routers.py` (AEA-21), any node or prompt, any `register_<x>()` hunk.
Never edit: the briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`,
`ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`. Never read `.env`.

---

## 3. Requirements

### 3.1 Acceptance criteria → implementation → verification

All tests are in `tests/unit/agent/test_gateway.py` (prefix `::` below). All are **frozen** (written by the
test-writer before the implementer starts).

| AC | Requirement (issue, abridged; full text in the ticket) | Implemented by (§5) | Verified by |
|---|---|---|---|
| AC-1 [invariant] | Each `Role` reaches the adapter its map names with that role's `RoleSpec` (`cap_s`, `max_tokens`, `effort`, `redaction`); methods accept only their role literals; mypy rejects `structured(Role.PLANNER, …)` | Typed maps; `_route`; spec's `max_tokens`/`effort` overwrite the request's (structured, tool); `timeout_s` from `cap_s`; request redacted with `spec.redaction` | `::test_role_maps_route_each_role`; `uv run mypy` passes **with** the `# type: ignore[arg-type]` in `_mypy_rejects_planner_as_structured_role` (an unused ignore would fail strict mypy) |
| AC-2 [failure/refusal] | `admit_call` → `REFUSE`: `halt=PROVIDER_SPEND_CAP`, `calls=()`, zero adapter/ledger.record/model_call calls, no brake count; never `allow_turn()`/`models_disabled()`; never `SPEND_CAP` | Rule 1 (§5 step 5.1) | `::test_refused_provider_halts_without_call` |
| AC-3 [invariant] | `timeout_s == min(spec.cap_s, remaining)`; under 1.0 s left → `halt=DEADLINE`, no call | Rule 2 via `ctx.budget.timeout_for(spec.cap_s)` | `::test_timeout_is_min_of_cap_and_remaining`, `::test_deadline_halts_without_call` |
| AC-4 [failure/refusal] | ≤ 2 attempts; second only for retryable whose wait + 1 s fits; 429 `retry_after_s=60` with 20 s left → no sleep; `retry_after_s=None` → 0.5–1 s backoff when it fits; non-retryable never retried; `PROBE` → exactly 1 attempt | Rule 5 (§5 step 5.5) | `::test_retry_at_most_once_and_only_if_it_fits` (parametrised) |
| AC-5 [capture] | Every attempt → exactly one `ledger.record(rec, ctx.ids)` and one `trace.model_call(ctx.span, rec, …)`; `rec = CallRecord.from_provider(attempt.record, role=role, attempt=n)`; `ModelOutcome.calls` = recorded tuple | Rule 6 | `::test_every_attempt_records_ledger_and_span` |
| AC-6 [failure/refusal] | `PROVIDER_SPEND_CAP` and `OUR_SPEND_LIMIT` → `trip_provider_cap` once, no retry, `halt=PROVIDER_SPEND_CAP`; under `PROBE` a non-cap result → `close_provider_cap(provider)` once; a cap result → trip instead | Rule 7 | `::test_spend_cap_kinds_trip_and_probe_closes` |
| AC-7 [failure/refusal] | Sonnet brake: 6 logical Anthropic calls, 7th → `BRAKE_SONNET_CALLS` with no request; retries not counted; Jev never counts; *Try again* (same `turn_id`, new budget) starts at 0; 1,000 sequential turns leave no entry > 1 s past its deadline | Rule 3 + pruning | `::test_sonnet_call_brake_counts_logical_calls` |
| AC-8 [negative] | JEV request carries none of the WP-2 seeds, card, code, email, street line; SONNET request keeps name and IDs, masks the rest (`[phone ending 02]`); no `masked_in`/`masked_out` and no log line holds the full phone, code, card or an API key value | Rule 4 + TRACE masking of span text; no logging in the module | `::test_redaction_profile_per_role` |
| AC-9 [invariant] | A `ModelOutcome` for every adapter result; a failed `Attempt` → `value=None`, `failure` set, still recorded | §5 step 5.5–5.7 | `::test_failed_attempt_returns_outcome` (parametrised over all 14 `ProviderFailureKind`) |
| AC-10 [invariant] | No `anthropic`, `httpx`, `openai`, `langfuse` import; no unit of work | Imports in §4.5 only | `::test_gateway_imports_no_sdk` (AST scan + constructor signature) |
| AC-11 [journey] | No journey yet; record at level `mock-tested`, *Blocked by* AEA-57 (and AEA-51), names J-1…J-5 and J-9; affected-journeys command prints `0 journeys affected` | §5 step 8 | `uv run python -m tests.journeys.affected --base main`; the record file |
| AC-12 [regression/context] | Area map A2 row, ICM row, DO-4 §12 pointer, DO-3 status, dev-log entry | §5 step 9 | `git diff --name-only main...HEAD` lists the four repo paths; the dev-log file exists |
| **WP-2** (worked pair) | Planner with 60 s left: Jev double gets `[name]`, `[phone]`, `[customer id]`, `[invoice id]`; `timeout_s == 3`; one ledger row + one span with `role=planner`, `attempt=1`, the double's `model`; responder keeps name and IDs, phone → `[phone ending 02]` | Whole flow | `::test_wp2_first_turn_planner_and_responder` |

### 3.2 Plan-added criteria (reconciliation found them; post a comment on issue #20 proposing them)

| ID | Criterion | Why (source) | Verified by |
|---|---|---|---|
| P-1 [invariant] | The constructor raises `ValueError` when a role sits in the wrong map, a Jev (`openrouter_jev`) adapter sits in `structured` or `tools`, a Jev adapter's spec is not `JEV`, or any spec's `redaction` is not `JEV`/`SONNET`; calling a role with no entry raises `ValueError` | DO-3 S-2 "Jev as responder unconfigurable"; DO-6 "Raw caller text goes to Jev only after redaction" (SP-1 condition); a `LOG` profile would send empty text | `::test_constructor_rejects_misconfigured_maps` |
| P-2 [invariant] | The brake counter is safe under concurrent calls in one turn (responder ∥ brief run in parallel, DO-3 §2.2): 8 concurrent Sonnet calls in one turn make exactly 6 requests and 2 halts | DO-3 §2.2; MOD-12 | `::test_brake_counter_is_thread_safe` |
| P-3 [capture] | Span text is the full rendered request and output after TRACE masking (names masked even where SONNET kept them; IDs kept); `ProviderMessages.items` never appear in span text | DO-6 line 113 rule 21; data.md §1 TRACE row; MOD-17 "never logged, traced or stored" | `::test_span_text_is_trace_masked_rendered_request` |

### 3.3 Frozen tests (test-writer writes these first; the implementer must not edit them)

File `tests/unit/agent/test_gateway.py` imports `import meridian.agent.gateway as gateway_module` and
`from meridian.agent.gateway import CallLedger, ModelGateway, ModelOutcome`, plus the doubles of §3.4. Every test that
uses a clock applies `monkeypatch.setattr(gateway_module, "_monotonic", clock.now)`,
`monkeypatch.setattr(gateway_module, "_sleep", clock.sleep)` (the module seams of §4.5). Before the implementer
starts, every test fails with `ModuleNotFoundError: No module named 'meridian.agent.gateway'` (red for the right reason).

| # | Test | Setup | Assertions |
|---|---|---|---|
| 1 | `test_role_maps_route_each_role` | Six distinct doubles, one per role, with distinct specs: PLANNER `JevChoice` (cap 3.0, max_tokens 101, effort None, JEV); CLASSIFIER `JevChoice` (3.0, 102, None, JEV); PLANNER_FALLBACK `SonnetChoice` (8.0, 103, "low", SONNET); RESPONDER `SonnetStructured` (12.0, 104, "low", SONNET); BRIEF `SonnetStructured` (12.0, 105, "medium", SONNET); SPECIALIST `SonnetTools` (8.0, 106, "high", SONNET). 60 s left. Each call's request text holds `wp2_line()`; structured/tool requests are built with `max_tokens=9999, effort=None` | Each double received exactly one request; `timeouts == [spec.cap_s]`; structured/tool request `max_tokens`/`effort` equal the spec's (not 9999/None); the role's main text field equals `redact(original, spec.redaction).text` (real `redact`); each ledger record has `role == role`, `model == double.model` |
| 1b | `def _mypy_rejects_planner_as_structured_role(gw: ModelGateway, req: StructuredRequest[Reply], ctx: TurnContext) -> None:` (module-level function, **never called**, name starts with `_` so pytest ignores it). **All three parameters must be annotated:** `tests.*` has `disallow_untyped_defs = false`, so an unannotated `gw` would be `Any`, mypy would report nothing, and the ignore would be "unused" | body: `gw.structured(Role.PLANNER, req, ctx)  # type: ignore[arg-type]` | Static: `uv run mypy` passes only if mypy reports `arg-type` there (strict mode has `warn_unused_ignores`) |
| 2 | `test_refused_provider_halts_without_call` | Ledger scripted `REFUSE` for the first call; then `ALLOW` | Outcome `value is None`, `calls == ()`, `failure is None`, `halt.reason == HaltReason.PROVIDER_SPEND_CAP`, `halt.node == "responder"`; adapter requests 0; `ledger.records == []`; `sink.model_calls == []`; then 6 further responder calls in the same turn all reach the adapter (no brake count was taken); `ledger.allow_turn_calls == 0`, `ledger.models_disabled_calls == 0`; source text of `gateway.py` has no `allow_turn`, no `models_disabled`, and `re.search(r"(?<!PROVIDER_)SPEND_CAP\b", source) is None` |
| 3 | `test_timeout_is_min_of_cap_and_remaining` | Default doubles (§3.4 `build_gateway`); fake clock | 60 s left: PLANNER 3.0, SPECIALIST 8.0, RESPONDER 12.0, BRIEF 12.0 (exact equality); 5.0 s left: RESPONDER 5.0, PLANNER 3.0 |
| 4 | `test_deadline_halts_without_call` | 0.5 s left; call each of the six roles | Each outcome: `halt.reason == DEADLINE`, `halt.node == role.value`, `calls == ()`, `value is None`; adapter requests 0; ledger records 0; sink calls 0; `gateway._sonnet_calls == {}` (no brake count) |
| 5 | `test_retry_at_most_once_and_only_if_it_fits` | Parametrised `ids=` below, RESPONDER role (cap 12) | Per case below; for every recorded wait `w` started at clock time `t0`: `t0 + w + 1.0 <= budget.deadline` |
| 6 | `test_every_attempt_records_ledger_and_span` | Three scripts on RESPONDER: `[ok]`, `[OVERLOADED, ok]`, `[SERVER, SERVER]`; plus `[ok]` on PLANNER | `len(ledger.records) == len(sink.model_calls) == attempts` (1, 2, 2, 1); record i has `attempt == i+1`, `role == called role`; `rec.model_dump(exclude={"role", "attempt"}) == double.calls_returned[i].model_dump()`; ledger ids `is ctx.ids`; sink parent `is ctx.span`; `outcome.calls == tuple(r for r, _ in ledger.records) == tuple(c[1] for c in sink.model_calls)` |
| 7 | `test_spend_cap_kinds_trip_and_probe_closes` | Scenarios: (a) ALLOW + `PROVIDER_SPEND_CAP` (anthropic responder); (b) ALLOW + `OUR_SPEND_LIMIT`; (c) ALLOW + `PROVIDER_SPEND_CAP` on the Jev planner (provider `openrouter_jev`); (d) PROBE + ok; (e) PROBE + `OVERLOADED`; (f) PROBE + `PROVIDER_SPEND_CAP` | (a)(b)(c): `trips == [that failure]`, `closes == []`, 1 attempt, `halt.reason == PROVIDER_SPEND_CAP`, `failure.kind` = scripted kind; (d)(e): `closes == [provider]`, `trips == []`, 1 attempt, `halt is None` ((e) carries the failure); (f): `trips` has 1, `closes == []`, 1 attempt |
| 8 | `test_sonnet_call_brake_counts_logical_calls` | `limit = Limits().brakes.sonnet_calls` (6); sub-cases in order, each with a fresh gateway | (i) one turn: `limit` Anthropic calls mixing PLANNER_FALLBACK, RESPONDER, BRIEF, SPECIALIST all reach adapters; call `limit+1` (RESPONDER) → `halt.reason == BRAKE_SONNET_CALLS`, `halt.node == "responder"`, its adapter got no extra request; (ii) first call scripted `[OVERLOADED, ok]`: `limit` logical calls succeed with `limit+1` adapter requests, call `limit+1` halts; (iii) 10 PLANNER (Jev) calls then `limit` Sonnet calls all succeed; (iv) after `limit` calls on budget A, a budget B with the **same** `turn_id` and a later `started` → next call succeeds; (v) 1,000 turns, each: new budget (60 s), one RESPONDER call, then **immediately** assert `len(gateway._sonnet_calls) <= 2` and no entry has `deadline < clock.now() - 1.0` (pruning runs at the start of each call), then `clock.advance(61.5)` |
| 9 | `test_redaction_profile_per_role` | Seeds from §6 (generated at run time). PLANNER request: seeds in `system`, in `state["recent_chat"]` (a list of str) and in one `ChoiceField.instructions`. RESPONDER request: seeds in `user` and `system_dynamic`; the responder double's returned value echoes `phone` and `code` in its text. SPECIALIST request: seeds in `system_dynamic`. Every double carries `api_key = key_sentinel()`. `caplog.set_level(logging.DEBUG)` | JEV request dump (`req.model_dump_json()`) contains none of: `"Omar Patel"`, full phone, `"MHC-10002"`, `"INV-204411"`, card, code, email, street line; contains `"[name]"`, `"[phone]"`, `"[customer id]"`, `"[invoice id]"`. SONNET request dumps contain no card, code, email, street line or full phone; contain `"[phone ending 02]"`, `"Omar Patel"`, `"MHC-10002"`, `"INV-204411"`. Every `masked_in`/`masked_out` in `sink.model_calls` contains none of: full phone, code, card, key sentinel. `caplog.text` contains none of them |
| 10 | `test_failed_attempt_returns_outcome` | Parametrised over `list(ProviderFailureKind)` (`ids=lambda k: k.value`); RESPONDER double scripted `[failure(kind, retryable=False)]` | No exception; `value is None`; `failure.kind == kind`; `len(calls) == 1`; `halt.reason == PROVIDER_SPEND_CAP` when kind in {PROVIDER_SPEND_CAP, OUR_SPEND_LIMIT}, else `halt is None`; one ledger record with `status == "error"` |
| 11 | `test_gateway_imports_no_sdk` | `ast.parse` of `src/meridian/agent/gateway.py` (path from `Path(__file__).resolve().parents[3] / "src" / "meridian" / "agent" / "gateway.py"`) | Offending imports list (top-level name in `{"anthropic", "httpx", "openai", "langfuse", "sqlite3", "fastembed"}` or module starting `meridian.adapters` / `meridian.services`) `== []`; `list(inspect.signature(ModelGateway.__init__).parameters) == ["self", "choice", "structured", "tools", "ledger", "trace", "redact", "limits"]`; `"UnitOfWork" not in source` |
| 12 | `test_wp2_first_turn_planner_and_responder` | 60 s left; PLANNER `ChoiceRequest(system="Route this turn.", state={"recent_chat": [wp2_line()], "new_message": "I got an invoice … and I'm not sure what it's for."}, fields=(ChoiceField(name="topic", instructions="Pick one.", options={"billing": "Billing", "other": "Other"}),))`; then the same `wp2_line()` as RESPONDER `user` | Jev double's received request dump contains `"[name]"`, `"[phone]"`, `"[customer id]"`, `"[invoice id]"` and none of the four raw values; `jev.timeouts == [3.0]`; exactly one ledger record and one sink call for the planner, record `role == Role.PLANNER`, `attempt == 1`, `model == jev.model`, sink parent `is ctx.span`; responder's received `user` contains `"Omar Patel"`, `"MHC-10002"`, `"INV-204411"`, `"[phone ending 02]"` and not the full phone |
| 13 | `test_constructor_rejects_misconfigured_maps` (P-1) | Use `cast(Any, …)` for deliberately wrong maps | `pytest.raises(ValueError)` for: `structured={Role.PLANNER: …}`; `choice={Role.RESPONDER: …}`; `tools={Role.BRIEF: …}`; a `JevChoice` in `structured`; a Jev adapter in `tools`; PLANNER `JevChoice` with SONNET profile; any spec with `RedactionProfile.LOG` / `STORE` / `TRACE`. A gateway built with `choice={Role.PLANNER: …}` only raises `ValueError` on `choose(Role.CLASSIFIER, …)` |
| 14 | `test_brake_counter_is_thread_safe` (P-2) | Real clock seams (no monkeypatch); a real `TurnBudget(started=time.monotonic(), deadline=time.monotonic() + 60)`; 8 threads, `threading.Barrier(8)` waited **before** each thread's `gateway.structured(Role.RESPONDER, …)` | Exactly `limit` adapter requests; exactly `8 - limit` outcomes with `halt.reason == BRAKE_SONNET_CALLS` |
| 15 | `test_span_text_is_trace_masked_rendered_request` (P-3) | PLANNER_FALLBACK (SONNET) choose with `system = "PLANNER-SYSTEM-MARKER " + wp2_line()`; SPECIALIST tool_step whose `messages.items` hold the marker string `"MESSAGES-ITEM-MARKER"` | Adapter request keeps `"Omar Patel"`; sink `masked_in` contains `"PLANNER-SYSTEM-MARKER"`, `"This is [name]"`, `"MHC-10002"`, `"[phone ending 02]"` and not `"Omar Patel"`; tool_step `masked_in` and `masked_out` do not contain `"MESSAGES-ITEM-MARKER"` |

**Test 5 cases** (`pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])`):

| id | Admission | Script | Seconds left | Expect attempts | Expect waits | Expect outcome |
|---|---|---|---|---|---|---|
| `overloaded_then_ok` | ALLOW | `[OVERLOADED(retry_after None), ok]` | 60 | 2 | one, `0.5 <= w <= 1.0` | value set |
| `rate_limited_60s_with_20s_left` | ALLOW | `[RATE_LIMITED(retry_after 60.0)]` | 20 | 1 | none | `failure.kind == RATE_LIMITED`, `halt is None` |
| `rate_limited_no_header_backoff` | ALLOW | `[RATE_LIMITED(None), ok]` | 20 | 2 | one, `0.5 <= w <= 1.0` | value set |
| `backoff_does_not_fit` | ALLOW | `[RATE_LIMITED(None)]` | 1.4 | 1 | none | failure returned |
| `retry_after_fits` | ALLOW | `[RATE_LIMITED(5.0), ok]` | 10 | 2 | `[5.0]` | value set; second `timeout_s == 5.0` |
| `non_retryable` | ALLOW | `[BAD_REQUEST]` | 60 | 1 | none | failure returned |
| `two_retryable_failures` | ALLOW | `[SERVER, SERVER, ok]` | 60 | 2 | one | `failure.kind == SERVER`; third script item unused |
| `probe_single_attempt` | PROBE | `[OVERLOADED, ok]` | 60 | 1 | none | failure returned; `ledger.closes == ["anthropic"]` |

### 3.4 What the doubles file must provide (`tests/unit/agent/_gateway_doubles.py`, frozen)

Exact names; the test-writer writes the bodies.

- `class FakeAdmission(StrEnum)`: `ALLOW = "allow"`, `PROBE = "probe"`, `REFUSE = "refuse"` (mirrors models.md §6
  `CallAdmission`; proves a StrEnum return satisfies the gateway's string comparison).
- `@dataclass class FakeClock`: `t: float = 1_000.0`; `waits: list[tuple[float, float]]` (start time, seconds);
  `now() -> float`; `sleep(seconds: float) -> None` (records `(t, seconds)`, then `t += seconds`); `advance(seconds)`.
- `@dataclass(frozen=True) class ClockedBudget(TurnBudget)`: extra field
  `clock: FakeClock = field(default_factory=FakeClock, compare=False, repr=False)`; overrides only
  `remaining() -> float: return max(0.0, self.deadline - self.clock.now())` (the base `timeout_for` calls
  `self.remaining()`, per the AEA-02 plan §4.8).
- `budget(clock: FakeClock, seconds_left: float) -> ClockedBudget`: `started=clock.now()`, `deadline=clock.now() + seconds_left`.
- `context(budget: TurnBudget, *, turn_id: TurnId | None = None) -> TurnContext`: `TurnIds(thread_id=ThreadId(str(uuid.uuid4())), turn_id=turn_id or TurnId(str(uuid.uuid4())), request_id=RequestId(str(uuid.uuid4())), run_tag="live", run_id=None, agent_version="test")`, `now=dt.datetime(2026, 10, 21, 15, 0, tzinfo=dt.UTC)`, `demo_session="demo-test"`, `span=SpanHandle(turn_id=<same turn_id>, trace_id="0" * 32)`.
- `spec(*, cap_s: float, redaction: RedactionProfile, model: str = "model-test", max_tokens: int = 500, effort: Literal["low", "medium", "high"] | None = "low") -> RoleSpec`.
- `failure(kind: ProviderFailureKind, provider: ProviderName = "anthropic", *, retry_after_s: float | None = None, retryable: bool | None = None) -> ProviderFailure`: `retryable` defaults to `kind in {TIMEOUT, CONNECTION, RATE_LIMITED, OVERLOADED, SERVER}`; `http_status=None`; `provider_request_id="req-test"`.
- `provider_call(provider: ProviderName, model: str, fail: ProviderFailure | None) -> ProviderCall`: `latency_ms=120`, `input_tokens=40`, `output_tokens=12`, cache/thinking 0, `cost_usd=0.0002` (0.0 when failed), `cost_source="price_table"`, `status="error" if fail else "ok"`, `failure=fail`, `provider_request_id="req-test"`, `stop_reason=None if fail else "end_turn"`.
- Scripted adapters, each with `model: str`, `script: list[ProviderFailure | None]` (popped from the front; empty → success), `requests: list[...]`, `timeouts: list[float]`, `calls_returned: list[ProviderCall]`, `api_key: str` (a sentinel the gateway must never touch):
  - `class JevChoice`: `provider: ClassVar[ProviderName] = "openrouter_jev"`; `choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]` returning `ChoiceAnswer(choices={f.name: next(iter(f.options)) for f in req.fields}, probabilities=None)` on success.
  - `class SonnetChoice(JevChoice)`: `provider: ClassVar[ProviderName] = "anthropic"`.
  - `class SonnetStructured`: `provider: ClassVar[ProviderName] = "anthropic"`; `next_value: BaseModel`; `structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]` returning `cast(T, self.next_value)` on success.
  - `class SonnetTools`: `provider: ClassVar[ProviderName] = "anthropic"`; `start(user) -> ProviderMessages(provider="anthropic", model=self.model, items=({"role": "user", "content": user},))`; `tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]` returning `ToolStep(text="checking", tool_calls=(), raw={"role": "assistant"}, stop_reason="end_turn")`; `append(...)` returns `messages`.
  - A failed attempt is `Attempt[ChoiceAnswer](value=None, record=provider_call(..., fail), failure=fail)` (and
    `Attempt[ToolStep]`, `Attempt[T]` for the others). Always parametrise `Attempt[...]` explicitly: pydantic-mypy has
    `init_typed = true`, and an unparametrised call would be inferred as `Attempt[Never]`/`Attempt[Any]`.
- `class Reply(LLMFacing)`: `text: str` (the structured output model in tests).
- `@dataclass class RecordingLedger`: `admissions: list[FakeAdmission]` (popped; empty → ALLOW); `admitted: list[str]`;
  `records: list[tuple[CallRecord, TurnIds]]`; `trips: list[ProviderFailure]`; `closes: list[str]`;
  `allow_turn_calls: int = 0`; `models_disabled_calls: int = 0`; methods `admit_call(provider) -> FakeAdmission`,
  `record(call, ids)`, `trip_provider_cap(failure)`, `close_provider_cap(provider)`, `allow_turn() -> bool` (counts,
  returns True), `models_disabled() -> bool` (counts, returns False).
- `@dataclass class RecordingSink` (satisfies `TraceSink`): `model_calls: list[tuple[SpanHandle, CallRecord, str, str]]`;
  `turn(ids)` a `contextlib.contextmanager` yielding `SpanHandle(turn_id=ids.turn_id, trace_id="0" * 32)`;
  `model_call(parent, record, masked_input, masked_output)`; `node(...)` no-op; `export_status(turn) -> "off"`.
- `build_gateway(*, ledger: RecordingLedger | None = None, sink: RecordingSink | None = None, limits: Limits | None = None, **adapters) -> tuple[ModelGateway, Doubles]` where `Doubles` is a dataclass holding the six adapters, ledger and sink. Default specs = the AEA-02 code defaults, built locally with `spec(...)` (the doubles never call `default_model_settings()`, so they do not depend on its exact `max_tokens`/`effort`): PLANNER and CLASSIFIER cap 3.0 JEV `effort=None`; PLANNER_FALLBACK 8.0 SONNET; RESPONDER 12.0, BRIEF 12.0, SPECIALIST 8.0 SONNET; `redact=redact` (the real AEA-04 function on `main`); `limits=Limits()`.
- Seed builders (§6): `wp2_phone()`, `wp2_line()`, `card_like()`, `six_digit_code()`, `email_seed()`, `street_seed()`, `key_sentinel()`.

### 3.5 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Constructor and three methods exactly as DO-4 §12 | DO-4 §12; models.md §5 | AC-1, AC-10 | in-ticket | §4.5; test 11 |
| Rule order 1→7 | models.md §5 | rules list | in-ticket | §5 step 5 |
| Our $30 cap not checked; never `SPEND_CAP` | MOD-11; DO-1 §8.2 | AC-2 | in-ticket | step 5.1 |
| `DO-4 §12` "refuse at once if models are disabled (our cap or …)" | DO-4 §12 vs MOD-11 | AC-12 pointer | in-ticket (pointer sentence) | step 9 |
| `ledger` typed so AEA-26 (wave 2) is not imported | S-20; ticket conventions | implicit | added: `CallLedger` Protocol (§4.5; §8 R-1) | step 2 |
| `ModelOutcome` defined here | AEA-02 plan §8.3 | implicit | added (definition home) | step 2 |
| Spec's `max_tokens`/`effort` reach the adapter | AC-1 | AC-1 | in-ticket; choice roles have no such fields (ChoiceRequest) — only `cap_s` and `redaction` apply there | step 4 |
| Jev never writes text or calls tools; Jev only with JEV profile | S-2; DO-6 *What leaves* (SP-1 condition) | partly | added P-1 | step 3 |
| Concurrent calls in one turn | DO-3 §2.2 | no | added P-2 (lock) | step 5.3 |
| Span carries full rendered context after masking | DO-6 line 113 / rule 21; MOD-17 | AC-8 (absence only) | added P-3 | step 4, 5.6 |
| No SDK, no unit of work, no transaction across a call | DO-3 §2.1, §2.3 rule 1 | AC-10 | in-ticket | test 11 |
| One retry, deadline-bound | DO-1 §11 decision 5; MOD-4 | AC-4 | in-ticket | step 5.5 |
| PROBE: one attempt, then close or trip | MOD-13 | AC-4, AC-6 | in-ticket | steps 5.5, 5.7 |
| Halt routing, compose of halt replies | graph-core §5 | no | other-ticket: AEA-21 (AC on halt routes), AEA-38 (re-wraps `node="responder"`) | — |
| Planner fallback on Jev failure | SDQ-6 | scope note | other-ticket: AEA-37 | — |
| Failure classification | S-24 | scope note | other-ticket: AEA-17, AEA-18 | — |
| Circuit state, `spend_ledger` storage | MOD-13, MOD-19 | scope note | other-ticket: AEA-26 | — |
| Container wiring of the real gateway | models.md §7 | handoff note | other-ticket: AEA-51 (`register_graph` builds `ModelGateway`, its ticket's first bullet) | §8 R-3 |
| `model` in each ledger row equals the role's `RoleSpec.model` | models.md §7 | Observability | other-ticket: AEA-51 wiring assertion (the gateway does not see `adapter.model`) | — |
| WF-1 records per attempt (ledger row + span) | DO-6 WF-1 | AC-5 | in-ticket | step 5.6 |
| M-23…M-26 inputs | DO-7 | Metrics | in-ticket via AC-5 | — |
| Stable placeholders across turns | rule `context-management-multi-turn` 5 | no | n/a here: `redact` (AEA-04) is deterministic and the gateway applies it on every call | — |
| Evaluation suite | DO-5 | "none added" | n/a: no suite added (ticket *Evaluation*) | — |
| DAT-1 option B (`known=` values) | data.md §1, D-14 | Awaiting note | n/a: D-14 took option A; `redact(text, profile)` unchanged | — |

### 3.6 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — |

---

## 4. Shared code to use (copied from the current code and the AEA-02 plan; import from exactly these homes)

### 4.1 `meridian.policy.limits` (AEA-01, **on `main`**, commit `893b825`)

```python
@dataclass(frozen=True)
class Brakes:
    tasks_per_turn: int = 3
    tool_rounds: int = 2
    sonnet_calls: int = 6      # proposal (models.md cross-topic 3)

@dataclass(frozen=True)
class Limits:
    turn: TurnLimits; admission: Admission; brakes: Brakes; identity: IdentityLimits; booking: BookingLimits
    spend: SpendLimits; web: WebLimits; context: ContextLimits      # all with default_factory
```
The gateway reads only `limits.brakes.sonnet_calls`.

### 4.2 `meridian.privacy.redact` (AEA-04, **on `main`**, commit `9145044`)

```python
class RedactionProfile(StrEnum):
    STORE = "store"; SONNET = "sonnet"; JEV = "jev"; TRACE = "trace"; LOG = "log"

@dataclass(frozen=True)
class Redacted:
    text: str; replaced: Mapping[RedactionKind, int]; length: int

def redact(text: str, profile: RedactionProfile) -> Redacted: ...
Redactor: TypeAlias = Callable[[str, RedactionProfile], Redacted]
```
Tokens: JEV `[name]` (the introduction stays: "This is [name]"), `[phone]`, `[customer id]`, `[invoice id]`, `[email]`,
`[address]`, `[code]`, `[card number removed]`; SONNET and TRACE phone `[phone ending NN]`. SONNET keeps names and IDs;
TRACE masks names, keeps IDs. Pure and idempotent. Also exported: `RedactionKind`, `UnknownRedactionProfile(ValueError)`.

**Checked on `main` 2026-10-21 (planner scratch run, `redact` only) with the §6 seeds** — the line
`This is Omar Patel, <phone>, customer MHC-10002, invoice INV-204411. card <card> code <code> mail <email> at 4410 Bluebonnet Ln` gives:
- JEV: `This is [name], [phone], customer [customer id], invoice [invoice id]. card [card number removed] code [code] mail [email] at [address]`
- SONNET: `This is Omar Patel, [phone ending 02], customer MHC-10002, invoice INV-204411. card [card number removed] code [code] mail [email] at [address]`
- TRACE, and TRACE applied to the SONNET output: `This is [name], [phone ending 02], customer MHC-10002, invoice INV-204411. …` (the rest as SONNET)
- `"Route this turn."`, `"Pick one."` and `"I got an invoice … and I'm not sure what it's for."` pass through JEV unchanged.

So the assertions of tests 1, 9, 12 and 15 hold against the merged `redact`.

### 4.3 AEA-02 types (from `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.1, §4.8, §4.12–§4.14; transcribing DO-4 + models.md)

```python
# meridian.domain.common
class MeridianModel(BaseModel):   # extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True
class LLMFacing(MeridianModel)
class ThreadId(_PatternId) / TurnId / RequestId      # UUID4 str subclasses; build as TurnId("…")
class ProviderFailureKind(StrEnum):   # 14: TIMEOUT, CONNECTION, RATE_LIMITED, OVERLOADED, SERVER, PROVIDER_SPEND_CAP,
                                      #     OUR_SPEND_LIMIT, BAD_REQUEST, AUTH, NOT_FOUND, BODY_ERROR, REFUSAL,
                                      #     MAX_TOKENS, INVALID_OUTPUT
class ProviderFailure(MeridianModel):
    kind: ProviderFailureKind; provider: ProviderName; http_status: int | None
    retry_after_s: float | None; retryable: bool; provider_request_id: str | None
class HaltReason(StrEnum):            # DEADLINE, BRAKE_TASKS, BRAKE_TOOL_ROUNDS, BRAKE_SONNET_CALLS,
                                      # BRAKE_IDENTICAL_CALL, RECURSION_LIMIT, SPEND_CAP, PROVIDER_SPEND_CAP
class Halt(MeridianModel):
    reason: HaltReason; node: str; elapsed_ms: int

# meridian.ports.models (re-exports Role, ProviderName, ProviderCall, CallRecord from domain.common)
class Role(StrEnum): PLANNER="planner"; CLASSIFIER="classifier"; PLANNER_FALLBACK="planner_fallback"
                     SPECIALIST="specialist"; RESPONDER="responder"; BRIEF="brief"
ProviderName = Literal["anthropic", "openrouter_jev"]
class ProviderCall(MeridianModel): provider; model; latency_ms; input_tokens; output_tokens; cache_read_tokens;
    cache_write_tokens; thinking_tokens; cost_usd; cost_source; status: Literal["ok","error"];
    failure: ProviderFailure | None; provider_request_id: str | None; stop_reason: str | None
class CallRecord(ProviderCall):
    role: Role; attempt: int = Field(ge=1, le=2)
    @classmethod
    def from_provider(cls, call: ProviderCall, *, role: Role, attempt: int) -> CallRecord: ...
ChoiceRole = Literal[Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK]
StructuredRole = Literal[Role.RESPONDER, Role.BRIEF]
ToolRole = Literal[Role.SPECIALIST]
class ChoiceField(MeridianModel):  name: str; instructions: str; options: dict[str, str]
class ChoiceRequest(MeridianModel): system: str; state: dict[str, JsonValue]; fields: tuple[ChoiceField, ...]
class ChoiceAnswer(MeridianModel):  choices: dict[str, str]; probabilities: dict[str, dict[str, float]] | None
class StructuredRequest[T: BaseModel](MeridianModel):
    system_prefix: str; system_dynamic: str; user: str; output_model: type[T]; max_tokens: int
    effort: Literal["low", "medium", "high"] | None
class ToolSchema(MeridianModel): name: str; description: str; input_schema: dict[str, JsonValue]; strict: bool = True
class ToolCall(MeridianModel): id: str; name: str; args: dict[str, JsonValue] | None
class ProviderMessages(MeridianModel): provider: ProviderName; model: str; items: tuple[JsonValue, ...]
class ToolStepRequest(MeridianModel):
    system_prefix: str; system_dynamic: str; messages: ProviderMessages; tools: tuple[ToolSchema, ...]
    max_tokens: int; effort: Literal["low", "medium", "high"] | None
class ToolStep(MeridianModel): text: str; tool_calls: tuple[ToolCall, ...]; raw: ProviderTurn; stop_reason: str | None
class Attempt[T: BaseModel](MeridianModel): value: T | None; record: ProviderCall; failure: ProviderFailure | None
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
    def append(self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]) -> ProviderMessages: ...

# meridian.domain.turn
@dataclass(frozen=True)
class TurnBudget:
    started: float; deadline: float
    def remaining(self) -> float: ...                       # max(0.0, deadline - time.monotonic())
    def timeout_for(self, cap_s: float, min_call_s: float = 1.0) -> float | None: ...   # None if remaining() < min_call_s
class TurnIds(MeridianModel): thread_id; turn_id; request_id; run_tag; run_id; agent_version
@dataclass(frozen=True)
class SpanHandle: turn_id: TurnId; trace_id: str | None; native: object = field(default=None, compare=False, repr=False)
@dataclass(frozen=True)
class TurnContext: ids: TurnIds; budget: TurnBudget; now: dt.datetime; demo_session: str; span: SpanHandle
                   intake: Intake | None = None

# meridian.ports.runtime
class TraceSink(Protocol):
    def turn(self, ids: TurnIds) -> AbstractContextManager[SpanHandle]: ...
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ...
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...
    def export_status(self, turn: SpanHandle) -> ExportStatus: ...

# meridian.config
class RoleSpec(MeridianModel):
    model: str; effort: Literal["low", "medium", "high"] | None; cap_s: float; max_tokens: int
    redaction: RedactionProfile
```
Also in `meridian.ports.models` (not needed by the gateway; the doubles use it for `ToolStep.raw`):
`ProviderTurn = JsonValue`. `ChoiceField.options` carries `Field(max_length=255)`. Code defaults in
`default_model_settings()` (AEA-02 plan §4.14): PLANNER 3.0/1500/None/JEV, CLASSIFIER 3.0/800/None/JEV,
PLANNER_FALLBACK 8.0/1500/"low"/SONNET, RESPONDER 12.0/1500/"low"/SONNET, BRIEF 12.0/1200/"low"/SONNET,
SPECIALIST 8.0/3000/"medium"/SONNET (cap_s / max_tokens / effort / redaction).

If the merged AEA-02 code differs from these names, the **merged code wins**; stop and report only if a name the
gateway needs is missing.

### 4.4 Ledger methods the gateway calls (models.md §6; the real `LedgerService` is AEA-26, wave 2)

```python
def admit_call(self, provider: ProviderName) -> CallAdmission: ...   # CallAdmission(StrEnum): ALLOW="allow", PROBE="probe", REFUSE="refuse"
def record(self, call: CallRecord, ids: TurnIds) -> None: ...
def trip_provider_cap(self, failure: ProviderFailure) -> None: ...
def close_provider_cap(self, provider: ProviderName) -> None: ...
```

### 4.5 What `src/meridian/agent/gateway.py` exposes (exact)

```python
"""The one model-call path (DO-3 §4.5, S-2; DO-4 §12; stage7/models.md §5). …"""
from __future__ import annotations

import json
import random
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final, Protocol

from pydantic import BaseModel, JsonValue

from meridian.config import RoleSpec
from meridian.domain.common import Halt, HaltReason, MeridianModel, ProviderFailure, ProviderFailureKind
from meridian.domain.turn import TurnContext, TurnIds
from meridian.policy.limits import Limits
from meridian.ports.models import (
    Attempt, CallRecord, ChoiceAnswer, ChoiceModel, ChoiceRequest, ChoiceRole, ProviderName, Role,
    StructuredModel, StructuredRequest, StructuredRole, ToolCallingModel, ToolRole, ToolStep, ToolStepRequest,
)
from meridian.ports.runtime import TraceSink
from meridian.privacy.redact import RedactionProfile, Redactor

__all__ = ["CallLedger", "ModelGateway", "ModelOutcome"]

class CallLedger(Protocol):
    """The four LedgerService methods the gateway calls (models.md §6). LedgerService (AEA-26) satisfies it
    structurally; its CallAdmission is a StrEnum, so comparing with the strings below works."""
    def admit_call(self, provider: ProviderName) -> str: ...
    def record(self, call: CallRecord, ids: TurnIds) -> None: ...
    def trip_provider_cap(self, failure: ProviderFailure) -> None: ...
    def close_provider_cap(self, provider: ProviderName) -> None: ...

class ModelOutcome[T: BaseModel](MeridianModel):      # DO-4 §12
    value: T | None
    calls: tuple[CallRecord, ...]
    failure: ProviderFailure | None
    halt: Halt | None

class ModelGateway:
    def __init__(self, *, choice: Mapping[ChoiceRole, tuple[ChoiceModel, RoleSpec]],
                 structured: Mapping[StructuredRole, tuple[StructuredModel, RoleSpec]],
                 tools: Mapping[ToolRole, tuple[ToolCallingModel, RoleSpec]],
                 ledger: CallLedger, trace: TraceSink, redact: Redactor, limits: Limits) -> None: ...
    def choose(self, role: ChoiceRole, req: ChoiceRequest, ctx: TurnContext) -> ModelOutcome[ChoiceAnswer]: ...
    def structured[T: BaseModel](self, role: StructuredRole, req: StructuredRequest[T],
                                 ctx: TurnContext) -> ModelOutcome[T]: ...
    def tool_step(self, role: ToolRole, req: ToolStepRequest, ctx: TurnContext) -> ModelOutcome[ToolStep]: ...
```

**Module constants and test seams** (call them by their global name at call time, never bind them as default
arguments, so `monkeypatch.setattr(gateway_module, "_sleep", …)` works):

```python
_REFUSE: Final = "refuse"          # = CallAdmission.REFUSE.value (models.md §6)
_PROBE: Final = "probe"            # = CallAdmission.PROBE.value
_ANTHROPIC: Final = "anthropic"
_CAP_KINDS: Final = frozenset({ProviderFailureKind.PROVIDER_SPEND_CAP, ProviderFailureKind.OUR_SPEND_LIMIT})
_MAX_ATTEMPTS: Final = 2
_RETRY_MARGIN_S: Final = 1.0       # "wait plus 1 s still fits" (DO-4 §12)
_BACKOFF_MIN_S: Final = 0.5        # MOD-4
_BACKOFF_MAX_S: Final = 1.0
_PRUNE_AFTER_S: Final = 1.0        # MOD-12
_CHOICE_ROLES: Final = frozenset({Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK})
_STRUCTURED_ROLES: Final = frozenset({Role.RESPONDER, Role.BRIEF})
_TOOL_ROLES: Final = frozenset({Role.SPECIALIST})
_REQUEST_PROFILES: Final = frozenset({RedactionProfile.JEV, RedactionProfile.SONNET})

def _monotonic() -> float: return time.monotonic()
def _sleep(seconds: float) -> None: time.sleep(seconds)
def _backoff_s() -> float: return random.uniform(_BACKOFF_MIN_S, _BACKOFF_MAX_S)  # noqa: S311 - retry jitter, not security

@dataclass
class _SonnetCount:
    deadline: float
    calls: int = 0
```

Instance attributes (names are read by tests 4 and 8): `self._sonnet_calls: dict[tuple[str, float], _SonnetCount]`
keyed by `(str(ctx.ids.turn_id), ctx.budget.started)`; `self._lock = threading.Lock()`.

**Strings that must never appear anywhere in `gateway.py` — code, docstrings or comments** (tests 2 and 11 scan the raw
source text): `allow_turn`, `models_disabled`, `UnitOfWork`, and `SPEND_CAP` unless directly preceded by `PROVIDER_`
(regex `(?<!PROVIDER_)SPEND_CAP\b`). Describe our own cap in prose ("our $30/day cap is checked before the turn by
TurnService, MOD-11"), never by those names. No `import logging`, no `print`.

---

## 5. Steps (build order; each step ends with a check)

**Step 0 — worktree.** The orchestrator creates `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-20` on branch
`aea-20-gateway` from `main` **after** AEA-02 is merged (AEA-01 and AEA-04 already are, at `16ca639`). In it: `export UV_LINK_MODE=hardlink;
uv sync` (never copy a venv; no `node_modules`). Check: `uv run python -c "import meridian.ports.models, meridian.config,
meridian.privacy.redact, meridian.policy.limits"` exits 0, and the frozen test commit
(`test(agent): frozen failing tests for AEA-20`) is on the branch.

**Step 1 — confirm red.** `uv run pytest tests/unit/agent/test_gateway.py -q` fails at collection with
`ModuleNotFoundError: No module named 'meridian.agent.gateway'`. Record the frozen files' SHA-256
(`sha256sum tests/unit/agent/test_gateway.py tests/unit/agent/_gateway_doubles.py`) for the tamper check.

**Step 2 — module skeleton.** Create `src/meridian/agent/gateway.py` with the docstring, imports, `__all__`, constants,
seams, `_SonnetCount`, `CallLedger` and `ModelOutcome` of §4.5. Check: `uv run python -c "from meridian.agent.gateway
import ModelOutcome, CallLedger"`.

**Step 3 — constructor (P-1).** Store `MappingProxyType(dict(choice))` etc. Validate, raising `ValueError` with a
message that names roles and profile values only (never request text):
1. every key of `choice` is in `_CHOICE_ROLES`, of `structured` in `_STRUCTURED_ROLES`, of `tools` in `_TOOL_ROLES`
   (*invariant:* Jev can never be asked to write a reply, S-2);
2. every adapter in `structured` and `tools` has `adapter.provider == "anthropic"`;
3. every spec's `redaction in _REQUEST_PROFILES`; and every adapter whose `provider == "openrouter_jev"` has
   `spec.redaction is RedactionProfile.JEV` (*invariant:* raw caller text reaches Jev only JEV-redacted);
4. keep `ledger`, `trace`, `redact`; `self._sonnet_limit = limits.brakes.sonnet_calls`; `self._sonnet_calls = {}`;
   `self._lock = threading.Lock()`.

Private `_route(mapping, role) -> tuple[adapter, RoleSpec]`: `mapping[role]`, or
`raise ValueError(f"no adapter configured for role {role.value}") from None`. Check: test 13 passes.

**Step 4 — redaction and rendering helpers** (module-level, pure; `redact` passed in):
- `_redact_json(value: JsonValue, profile, redact) -> JsonValue`: `str` → `redact(value, profile).text`; `list` →
  each item; `dict` → same keys, each value; anything else unchanged. **Keys are never redacted** (they are identifiers
  the consumer validates against).
- `_redact_choice(req, profile, redact) -> ChoiceRequest`: `req.model_copy(update={"system": r(system), "state":
  {k: _redact_json(v) …}, "fields": tuple(f.model_copy(update={"instructions": r(f.instructions), "options":
  {k: r(v) for k, v in f.options.items()}}) for f in req.fields)})`. `ChoiceField.name` and option keys unchanged
  (the adapter validates answers against them).
- `_redact_structured(req, spec, redact)`: `model_copy(update={"system_prefix", "system_dynamic", "user"` each
  redacted with `spec.redaction`, `"max_tokens": spec.max_tokens, "effort": spec.effort})` (*invariant:* the spec is
  authoritative for the role, AC-1).
- `_redact_tool(req, spec, redact)`: same for `system_prefix`, `system_dynamic`, `max_tokens`, `effort`; **`messages`
  and `tools` pass through untouched** (MOD-17: only the adapter reads `items`; thinking-block signatures must stay
  byte-identical). The runner already SONNET-redacts the text it gives `start()` (graph-nodes §9 `customer_text`).
- Span text, always `RedactionProfile.TRACE` applied to the already role-redacted request (P-3):
  - choose in: `_redact_choice(sent, TRACE, redact).model_dump_json()`;
  - structured in: `"\n\n".join(redact(x, TRACE).text for x in (sent.system_prefix, sent.system_dynamic, sent.user))`;
  - tool in: `"\n\n".join([redact(sent.system_prefix, TRACE).text, redact(sent.system_dynamic, TRACE).text,
    "tools: " + ", ".join(t.name for t in sent.tools)])` (never `messages`);
  - out, `value is None` → `""`; choose/structured → `json.dumps(_redact_json(value.model_dump(mode="json"), TRACE,
    redact), ensure_ascii=False, sort_keys=True)`; tool → the same over `{"text": v.text, "tool_calls": [{"name":
    c.name, "args": c.args} for c in v.tool_calls], "stop_reason": v.stop_reason}` (never `raw`).
  Redact each string leaf **before** serialising, so a JSON `\n` escape cannot glue a name to the previous word.

**Step 5 — the shared run loop.** One private generic method
`_run[V: BaseModel](self, role: Role, provider: ProviderName, spec: RoleSpec, ctx: TurnContext,
prepare: Callable[[], tuple[Callable[[float], Attempt[V]], str]], render_out: Callable[[V | None], str]) -> ModelOutcome[V]`.
`prepare()` does the role-profile redaction and returns `(send, masked_in)`; it is called only after rules 1–3 pass.
Each public method is: `adapter, spec = self._route(map, role)` → `return self._run(role, adapter.provider, spec, ctx,
prepare, render_out)`. Build every outcome as `ModelOutcome[V](value=…, calls=tuple(calls), failure=…, halt=…)`
(prototyped 2026-10-21 on pydantic 2.14.1 / mypy strict: runtime parametrisation with a method type parameter works).
`_halt(reason, role, ctx)` returns `Halt(reason=reason, node=role.value, elapsed_ms=max(0, int((_monotonic() -
ctx.budget.started) * 1000)))`.

1. **Admission (MOD-11, MOD-13).** `adm = self._ledger.admit_call(provider)`. If `adm == _REFUSE`: return
   `ModelOutcome(value=None, calls=(), failure=None, halt=_halt(PROVIDER_SPEND_CAP))`. *Invariant:* no adapter call,
   no ledger row, no span, no brake count; `allow_turn`/`models_disabled` are never referenced in the module.
2. **Deadline.** `timeout = ctx.budget.timeout_for(spec.cap_s)`; `None` → return the `DEADLINE` halt outcome
   (`calls=()`). *Invariant:* `timeout_s == min(cap_s, remaining)`, never a call under 1.0 s.
3. **Sonnet brake (MOD-12, P-2).** Under `self._lock`: prune every entry whose `deadline < _monotonic() -
   _PRUNE_AFTER_S` (runs on **every** call, any provider); then, only if `provider == _ANTHROPIC`, get or create
   `self._sonnet_calls[(str(ctx.ids.turn_id), ctx.budget.started)] = _SonnetCount(deadline=ctx.budget.deadline)`; if
   `calls >= self._sonnet_limit` → release the lock and return the `BRAKE_SONNET_CALLS` halt outcome; else
   `calls += 1`. *Invariant:* check-and-increment is atomic; a retry never increments (it happens inside step 5);
   refusals and deadline halts never increment (they return before this step); a new `TurnBudget` for the same
   `turn_id` has a new `started`, so a *Try again* starts at 0; the map never holds an entry more than 1 s past its
   deadline after any call.
4. **Redaction.** `send, masked_in = prepare()` (role profile = `spec.redaction`).
5. **Attempts.** `n = 1`, `calls: list[CallRecord] = []`. Loop:
   - `attempt = send(timeout)`;
   - step 6 (record);
   - `f = attempt.failure`. If `f is None`: if `adm == _PROBE`, `close_provider_cap(provider)`; return
     `value=attempt.value, failure=None, halt=None`.
   - If `f.kind in _CAP_KINDS`: step 7 (trip), return `value=None, failure=f, halt=_halt(PROVIDER_SPEND_CAP)`.
   - If `adm == _PROBE`: `close_provider_cap(provider)`; return `value=None, failure=f, halt=None` (exactly one
     attempt under PROBE).
   - If `n == _MAX_ATTEMPTS` or not `f.retryable`: return `value=None, failure=f, halt=None`.
   - `wait = f.retry_after_s if f.retry_after_s is not None else _backoff_s()`; if `wait + _RETRY_MARGIN_S >
     ctx.budget.remaining()`: return the failure outcome (no sleep). *Invariant:* never a wait past the deadline.
   - `_sleep(wait)`; `timeout = ctx.budget.timeout_for(spec.cap_s)`; if `None`, return the failure outcome; `n = 2`.
6. **Record every attempt (MOD-1, MOD-10).** `rec = CallRecord.from_provider(attempt.record, role=role, attempt=n)`;
   `calls.append(rec)`; `self._ledger.record(rec, ctx.ids)`; then `self._trace.model_call(ctx.span, rec, masked_in,
   render_out(attempt.value))`. Ledger before span, one each per attempt, success or failure.
7. **Circuit (MOD-11, MOD-13).** `self._ledger.trip_provider_cap(f)` once; no retry. Under PROBE the cap kind also
   takes this branch (trip, not close).

The module never logs (no `logging` import) and never catches exceptions from the adapter, ledger or sink: adapters
never raise by contract (DO-4 §12), and a raising collaborator is a bug the caller must see. Check: tests 2–10, 12,
14, 15 pass.

**Step 6 — the three public methods.**
- `choose`: `prepare` = `sent = _redact_choice(req, spec.redaction, self._redact)`; `send = lambda t:
  adapter.choose(sent, timeout_s=t)`; `masked_in` per step 4. `render_out` for `ChoiceAnswer`.
- `structured`: `sent = _redact_structured(req, spec, self._redact)`; `send = lambda t: adapter.structured(sent,
  timeout_s=t)`.
- `tool_step`: `sent = _redact_tool(req, spec, self._redact)`; `send = lambda t: adapter.tool_step(sent, timeout_s=t)`.
Ruff `B023` (loop-variable closures) does not apply (no loop); if ruff flags `E731` for lambdas, use small nested
`def`s. Check: the whole frozen file passes.

**Step 7 — gates.** §7.2 commands, cheapest first.

**Step 8 — journey record (AC-11).** Run `uv run python -m tests.journeys.affected --base main` and write §7.4.

**Step 9 — context (AC-12).** One commit `docs(AEA-20): journey record and context for agent/gateway.py`:
- `.claude/reference/area-map.md` A2 row (the line starting `| 1 | **A2 Models** |`): change only the last cell
  (Status). If it reads `planned`, make it `` partly built: `agent/gateway.py` actual (AEA-20, `<feat sha>`); the rest planned ``.
  If a sibling (AEA-17/18/26) already made it `partly built: …; the rest planned`, insert
  `` `agent/gateway.py` actual (AEA-20, `<feat sha>`); `` before `the rest planned`. Same convention as the A0 row on
  `main`. Leave the Owns cell unchanged.
- `docs/design/code-design.md` §3 tree line `│   ├── gateway.py   ModelGateway: typed role maps; deadline, retry, ledger, span A2    1`: append `   built AEA-20 <feat sha>`.
- `docs/design/contracts/internal-components.md` §12: directly after the paragraph that starts `**Gateway rules, in order:**`, add one paragraph: `> Built (AEA-20, \`src/meridian/agent/gateway.py\`, <feat sha>) to the rules as restated in [stage7/models.md](stage7/models.md) §5: provider admission through \`ledger.admit_call\` replaces "refuse at once if models are disabled (our cap …)"; our $30 cap is checked before the turn (MOD-11).`
- `.claude/state/icm-progress.md`: `main` has **two** rows named *Routes verified against code and tests* (AEA-04's and
  AEA-03's, kept by a merge). Edit only the **first** one (today its evidence starts `2026-10-21: first backend slice
  AEA-04`): replace its evidence cell with
  `<run-date>: latest slice AEA-20 \`agent/gateway.py\` (<feat sha>): \`tests/unit/agent/test_gateway.py\` passes (<N> passed)`
  (keep the row ≤ 400 characters; status stays `provisional`). Do not add a row; do not touch the second row or the
  *Last reconciled* line.
- Dev log (outside the repo, not committed): §2.1 path, header per `.claude/reference/dev-log.md` (project, date/TZ,
  topic, writer `Claude (Sonnet 5.5, claude-sonnet-5-5)`, host `claude-vultr`, branch `aea-20-gateway`, base SHA) and
  one entry with **Changed / Why / Checked / Remaining** (Remaining: integrated level waits on AEA-57 and AEA-51; the
  real ledger arrives with AEA-26).
- Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` → no FAIL.

**Commits** (explicit `git add <paths>`, never `-A`; last line of every message
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`):
1. `feat(agent): ModelGateway, the one model-call path (AEA-20)` — `git add src/meridian/agent/gateway.py`.
2. `docs(AEA-20): journey record and context for agent/gateway.py` — `git add docs/testing/journeys/<run-date>-AEA-20.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md docs/design/contracts/internal-components.md`.
No push (the merge step pushes `main`); no force-push.

---

## 6. Data and fixtures (synthetic only; generated at run time, never in a test name or id)

Source: the WP-2 worked pair (`docs/data/worked-pairs.md`, issue *Example pair*), the fictional issued customer
MHC-10002 / INV-204411. Builders in `_gateway_doubles.py`:

| Builder | Returns | Note |
|---|---|---|
| `wp2_phone()` | `"-".join(("512", "555", "01" + "02"))` | assembled, never a literal phone |
| `wp2_line()` | `f"This is Omar Patel, {wp2_phone()}, customer MHC-10002, invoice INV-204411"` | the issue's recent-chat line |
| `card_like()` | `" ".join(str(n) for n in (5005, 1234, 9876, 4321))` | 16 digits, matches the card pattern |
| `six_digit_code()` | `"".join(str(d) for d in (9, 1, 4, 2, 7, 6))` | standalone six digits |
| `email_seed()` | `"omar.p" + "@" + "example.test"` | |
| `street_seed()` | `"4410 Bluebonnet Ln"` | matches AEA-04's street pattern |
| `key_sentinel()` | `"sk-test-" + secrets.token_hex(8)` | stands in for an API key value held by a double |

All other test values are fixed synthetic strings (model ids `"model-test"`, request id `"req-test"`). No issued file
is read; no network; no paid call; no `.env`.

---

## 7. Checks

### 7.1 Tests the implementer must make pass

`tests/unit/agent/test_gateway.py`: the 15 tests in §3.3 (24 test items with parametrisation of tests 5 and 10, plus
the static check). These are **frozen**: if one looks wrong, stop and report; do not edit it.

**Affected tests** = `tests/unit/agent/` (mirrors the changed package) plus `grep -rl "meridian.agent.gateway" tests/`
(only this file today). Nothing else imports the new module, so no other suite is affected. No full-suite trigger
applies (no shared fixture, settings, dependency or cross-package module changes).

### 7.2 Commands (run from the worktree; `export UV_LINK_MODE=hardlink`)

| Order | Check | Command | Passing looks like |
|---|---|---|---|
| iterate | Affected tests | `uv run pytest tests/unit/agent/ -q` | all pass (≈ 26 items), no skips |
| 1 | Format | `uv run ruff format --check src/meridian/agent/gateway.py tests/unit/agent/` | `would reformat` count 0 |
| 2 | Lint | `uv run ruff check src/meridian/agent/gateway.py tests/unit/agent/` | `All checks passed!` |
| 3 | Types | `uv run mypy` (config `files` = `src/meridian`, `tests`, `eval`) | `Success: no issues found`; proves AC-1's static check |
| 4 | Affected tests | `uv run pytest tests/unit/agent/ -q` | all pass |
| 5 | Affected journeys | `uv run python -m tests.journeys.affected --base main` | prints `0 journeys affected`, exit 0 |
| 6 | Tamper check | `sha256sum tests/unit/agent/test_gateway.py tests/unit/agent/_gateway_doubles.py` | equals step 1's hashes |
| 7 | Context | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL |
| 8 | Diff scope | `git diff --name-only main...HEAD` | exactly the §2.1 repo paths (plus the two frozen test files) |

Never use more than `-n 2` if adding `--with pytest-xdist` (not needed for this file). Never bind ports 4019 or 5184
(no server is started).

### 7.3 Capture and evaluation checks

| Check | Command | Evidence |
|---|---|---|
| Capture (WF-1 model_call + spend row per attempt) | tests 6, 9, 15 | counts and masked text asserted with doubles; integrated CAP-1 is AEA-51's |
| Evaluation | n/a | ticket *Evaluation*: none added |

### 7.4 Journey record — `docs/testing/journeys/<run-date>-AEA-20.md`

```markdown
# Journey record: AEA-20 model gateway

| Field | Value |
|---|---|
| Claim | AEA-20 AC-11: `agent/gateway.py` (ModelGateway) has no server path yet; its evidence is its unit tests with doubles. Journeys that will exercise it: J-1, J-2, J-3, J-4, J-5, J-9 (the gateway runs above the scripted adapter) |
| Level | `mock-tested` |
| Tested revision | `<feat sha>` |
| Environment | VPS, `uv run`, Python 3.12; no server, no database, no model; scripted doubles in `tests/unit/agent/_gateway_doubles.py` |
| Command | `uv run pytest tests/unit/agent/ -q`; `uv run python -m tests.journeys.affected --base main` |
| Result | <N> passed. Affected: `changed files: <k> (base main)` then `0 journeys affected`, exit 0 |
| Evidence location | this record |
| Remaining limitations | Real `LedgerService` (AEA-26), adapters (AEA-17/18) and sink (AEA-19) not wired; no seam exercised end to end |
| Blocked by | AEA-57 (journey harness, wave 2) and AEA-51 (integrated turn, wave 3) |
| Journeys that will exercise this code | J-1, J-2, J-3, J-4, J-5 and J-9 (the gateway runs above the scripted adapter), once AEA-57 and AEA-51 land; seam-audit pattern C (`docs/plans/ux-join/backend-amendments.md` §3) |
```

Same field set as `docs/testing/journeys/2026-10-21-AEA-04.md` on `main`. The affected-journeys tool prints
`changed files: <k> (<label>)` then `0 journeys affected`; copy both lines into *Result*.

### 7.5 Implementer report must include

Per AC (1–12, WP-2, P-1…P-3): verified / not, the command, the result line. The two commit SHAs. The tamper-check
hashes. The dev-log path (uncommitted).

---

## 8. Risks and requests

- **R-1 `CallLedger` Protocol (decision made here, engineering).** DO-4 §12 types the parameter `ledger:
  LedgerService`, but `services/ledger.py` is AEA-26, **wave 2**; importing it would block this ticket a wave. The
  gateway types the parameter with a four-method `CallLedger` Protocol in its own module (interface segregation, the
  same move as `SpendGuard`, MOD-18, and `ModelsStatus`, R-G-13). `admit_call` returns `str`; `CallAdmission` is a
  StrEnum, so `LedgerService` satisfies it structurally and `== "refuse"` holds. **Request to AEA-51:** its wiring test
  passes the real `LedgerService` as `ledger=` (mypy then proves structural fit). No contract field changes.
- **R-2 Module test seams.** The constructor stays exactly DO-4's (the ticket and models.md §5 say "unchanged"), so
  time, sleep and jitter are module-level functions tests monkeypatch, not constructor arguments.
- **R-3 `web/container.py`.** AEA-20 leaves its `register_gateway` stub as AEA-01 wrote it (no-op). The gateway needs
  the ledger (wave 2) and the adapters and sink under keys no sibling has fixed; AEA-51's ticket already builds
  `ModelGateway` inside `register_graph`. **Request to the orchestrator:** confirm AEA-51 owns the construction; the
  `register_gateway` stub stays empty (or AEA-51's plan names a follow-up).
- **R-4 JEV redaction of prompt text.** The gateway redacts `ChoiceRequest.system`, state values and field
  instructions/option labels with the JEV profile. A code-written prompt line matching an introduction pattern ("this
  is …", "I'm …" followed by capitalised words, other than "Meridian") would be masked as `[name]`. **Note for AEA-37
  and AEA-60:** check rendered planner/classifier prompts through `redact(…, JEV)`; option **keys** and field names are
  never redacted.
- **R-5 Tool-step text.** `ProviderMessages.items` pass through untouched (MOD-17). Tool results appended by the runner
  (AEA-35) reach Sonnet without gateway redaction; their redaction, if any, is AEA-22/35's. Span text for tool steps
  therefore omits the conversation items (MOD-17 "never traced").
- **R-6 PROBE then halt.** If `admit_call` returns `PROBE` and the deadline or brake then halts before an attempt, no
  close or trip is sent; the ledger treats a probe in flight over 60 s as lost (models.md §6 table), so one more
  probe follows. Accepted.
- **R-7 Halt fields.** `Halt.node = role.value` (e.g. `"responder"`), matching AEA-38's re-wrapped halt; `elapsed_ms` =
  time since `ctx.budget.started`. Nodes may rebuild the halt; the reason is what routes (graph-core §5).
- **R-8 Shared context files.** AEA-17, 18, 19, 26 edit the same A2 area-map row and the same ICM row. Expect a
  textual merge conflict on those lines; the merge agent keeps every ticket's annotation.
- **R-9 AEA-02 drift.** This plan copies AEA-02's **plan** (re-checked against its 12:08 refresh); if the merged code renamed a type (e.g. `ProviderTurn`, the
  `ClassVar` provider), the merged code wins. If `TurnBudget.timeout_for` does not call `self.remaining()`, the frozen
  `ClockedBudget` double breaks: stop and send back to the planner, do not edit the frozen file.
- **R-10 Ordering of wave-0 merges.** The test-writer cannot run before AEA-02 is on `main` (the doubles file imports
  `meridian.ports.*`, `meridian.domain.*`, `meridian.config`). AEA-01 and AEA-04 are already on `main`.
- **R-11 Refresh against `16ca639` (2026-10-21).** What changed since `c0621de`: AEA-01 and AEA-04 merged (imports now
  from `main`, not branches); the area map's convention is a Status-cell annotation (step 9 changed); `icm-progress.md`
  holds two *Routes verified* rows (step 9 names which one); journey records gained a *Journeys that will exercise
  this code* field (§7.4); `observability-contract.md` recorded DAT-1 option A's name-masking limit (consistent with
  R-4 and §6). Test 1b now spells out annotated parameters; §4.5 lists the strings the source must never contain.
  DO-4, stage7/models.md, stage7/data.md, the ticket and the slice plan are unchanged since `c0621de`.
- No signed contract (OpenAPI, `UI_CONTRACTS.md`) is touched; no decision D-4…D-15 is answered differently.

---

## 9. Readiness

**READY**, blocked on one wave-0 import set only: **AEA-02** (`meridian.ports.models`, `meridian.ports.runtime`,
`meridian.domain.common`, `meridian.domain.turn`, `meridian.config.RoleSpec`). AEA-01 (`meridian.policy.limits.Limits`)
and AEA-04 (`meridian.privacy.redact`) are on `main` at `16ca639`. Same-wave and later siblings (AEA-17, 18, 19, 26,
11) are injected and replaced by this ticket's own doubles. No `NEEDS-DECISION`.

## Gates

None (no human, paid or live gate). `risk::security`: frozen tests first; `security-privacy-agent` at the wave-1 merge.
