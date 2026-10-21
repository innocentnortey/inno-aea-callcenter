## [AEA-20] models: the gateway

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

**What it does in practice.** Every model call in a turn (planner, danger classifier, planner fallback, specialist step,
responder, brief) goes through **one** object, `ModelGateway` (DO-3 §4.5, S-2). A node asks for a role; the gateway
looks up the adapter and `RoleSpec` that the typed role maps hold for it, so Jev can never be asked to write a reply (the
`structured` and `tools` maps cannot hold it; `ModelSettings` validation is AEA-02's). Before a call it asks the ledger
whether that **provider** is admitted, checks how much of the turn's 60 s is left, counts the per-turn Sonnet brake, and
redacts the request with the role's profile. It makes at most two attempts, wraps each adapter `ProviderCall` into a
`CallRecord` with the role and attempt number, and writes one ledger row and one span per attempt. A provider spend-cap
failure trips that provider's circuit. Our own $30/day cap is **not** checked here: `TurnService` checks
`allow_turn()` before the turn (AEA-40), because DO-1 §8.2 lets a running turn finish (MOD-11).

**`agent/gateway.py`**: the constructor and the three methods `choose`, `structured`, `tool_step` exactly as DO-4 §12
(`ModelGateway(*, choice, structured, tools, ledger, trace, redact: Redactor, limits: Limits)`), applying the rules of
stage7/models.md §5 **in this order**:
1. **Provider admission** (MOD-11, MOD-13). `adm = ledger.admit_call(adapter.provider)`. `REFUSE` → `ModelOutcome(value=None,
   calls=(), failure=None, halt=Halt(reason=PROVIDER_SPEND_CAP, …))`: no adapter call, no ledger row, no span, no brake
   count. The gateway never emits `SPEND_CAP` and never calls `allow_turn()` or `models_disabled()`.
2. **Deadline.** `timeout = ctx.budget.timeout_for(spec.cap_s)` (DO-4 §2: `min(cap_s, remaining())`, `None` under the
   1.0 s `min_call_s`); `None` → `halt=DEADLINE`, no call. Role caps (proposal, DO-4 §12 `RoleSpec.cap_s`): Jev 3 s,
   specialist 8 s, responder 12 s, brief 12 s.
3. **Sonnet-call brake** (MOD-12). Counts **logical calls**: one per gateway method call that reaches an attempt on an
   adapter whose `provider == "anthropic"` (any role, `PLANNER_FALLBACK` included); a retry is the same call. At
   `limits.brakes.sonnet_calls` (6, proposal; `policy/limits.py`, AEA-01) already made this turn run → `halt=
   BRAKE_SONNET_CALLS`, no request. Keyed by `(ctx.ids.turn_id, ctx.budget.started)`, so a *Try again* on the same
   `turn_id` with a new `TurnBudget` starts at zero; an entry is pruned once its deadline is more than 1 s past.
4. **Redaction.** `redact(text, spec.redaction)`: `JEV` for planner and classifier, `SONNET` for the rest (DO-4 §12
   `RoleSpec.redaction`; profiles and placeholder tokens stage7/data.md §1; SONNET masks contact details, DAT-5).
5. **Attempts.** At most 2 (DO-4 §12; C-8). The second only for `failure.retryable` when its wait (`retry_after_s`, or a
   0.5–1 s backoff when it is `None`, MOD-4) plus 1 s still fits the time left; never a wait past the deadline. When
   `adm == PROBE`, **exactly one** attempt.
6. **Record every attempt** (MOD-1, MOD-10). `rec = CallRecord.from_provider(attempt.record, role=role, attempt=n)`
   (`n` = 1, 2), then `ledger.record(rec, ctx.ids)` and `trace.model_call(ctx.span, rec, masked_in, masked_out)` with
   masked text (no full phone, code, card-like number or key; DO-6 *Content and redaction*). `ModelOutcome.calls` holds
   every `rec`.
7. **Circuit** (MOD-11, MOD-13). A failure of kind `PROVIDER_SPEND_CAP` **or** `OUR_SPEND_LIMIT` →
   `ledger.trip_provider_cap(failure)`, no retry, outcome `halt=PROVIDER_SPEND_CAP`. If `adm == PROBE` and the attempt
   ended in anything else → `ledger.close_provider_cap(adapter.provider)`.

The three model port Protocols carry a read-only `provider: ProviderName` attribute (models.md §5, cross-topic 2;
AEA-02 writes it); test doubles set it. A gateway halt of any reason ends the turn through the halt path (AEA-21,
graph-core §5); the gateway never falls back to another role or provider (models.md §5 *Halt → customer*). The Sonnet
planner fallback for a Jev **failure** is chosen by the plan node (AEA-37, SDQ-6), not here.

**Example pair (WP-2, first turn).** Input: the planner role is called for "I got an invoice … and I'm not sure what it's
for." with 60 s left, and the recent chat holds "This is Omar Patel, 512-555-0102, customer MHC-10002, invoice
INV-204411". Expected: the `ChoiceRequest` the Jev double receives has `[name]`, `[phone]`, `[customer id]`,
`[invoice id]` in place of those values (JEV profile, data.md §1); the adapter is called with `timeout_s = 3`; one
`ledger.record` call and one `trace.model_call(ctx.span, …)` call carry a `CallRecord` with `role=planner`, `attempt=1`
and the double's `model`. The same text sent for the responder role keeps the name and both IDs and shows the phone
as `[phone ending 02]` (SONNET profile, DAT-5).

### Source
- stage7/models.md §1 (`ProviderCall`, `CallRecord.from_provider`, `Attempt.record`, MOD-1), §4 (`SpanHandle`, `TraceSink`,
  MOD-10), §5 (gateway rules restated, MOD-1, 10–13), §6 (`LedgerService.admit_call`, `CallAdmission`,
  `close_provider_cap`, circuit table), §7 (container wiring); ledger `docs/plans/7b-decisions/models.md` MOD-1, MOD-4,
  MOD-10, MOD-11, MOD-12, MOD-13, MOD-14.
- stage7/data.md §1 (`redact`, `Redactor`, profiles, placeholder tokens; DAT-1, DAT-5, DAT-28) and §9 item 7;
  stage7/graph-core.md §2 (`TurnContext.span`), §5 (halt routing); merge-clashes MC-22 (`Limits` owner AEA-01), MC-23
  (`Redactor`), MC-28 (`ProviderCall` in fakes).
- DO-4 §2 (`TurnBudget.timeout_for`), §11 (`ProviderFailure`, `HaltReason`, failure → customer table), §12 (`Role`,
  `RoleSpec`, `ModelSettings`, `ModelOutcome`, `ModelGateway`, role caps under the 60 s deadline).
- DO-3 §4.5 (`agent/gateway.py`), §6 S-2, §2.1 (no model SDK in `agent/`), §2.3 rules 1–2.
- DO-1 §8.1 (60 s deadline, Decided SDQ-1; role caps; one retry), §8.2 (*Spend cap*), §10 *Redaction*, §11 decisions 5
  and 7; PRD R-41, §5 *Reliability*, *Spend*; HP-1; US-16.
- `pydantic-ai-agents.md` §7–§8; `agent-architecture.md` rules 5, 20.
- **Brief check:** serves "Production-thinking expected: system should be able to run unmanned for a month, failures
  should be observable, and failure handling must be clean (agent admits uncertainty and hands off rather than
  guessing)."; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] Role maps decide the adapter and spec: each `Role` reaches the adapter its map names with that role's `RoleSpec` (`cap_s`, `max_tokens`, `effort`, `redaction`), and `choose`/`structured`/`tool_step` accept only their DO-4 §12 role literals — verify: `tests/unit/agent/test_gateway.py::test_role_maps_route_each_role` (scripted doubles honouring the DO-4 port signatures, each with a `provider` attribute) — evidence: per-role adapter and spec values asserted; mypy rejects a `StructuredRole` call with `Role.PLANNER`.
- [ ] AC-2 [failure/refusal] Admission: with `admit_call` returning `REFUSE` the outcome is `halt=PROVIDER_SPEND_CAP` with `calls=()`, zero adapter calls, zero `ledger.record` and `trace.model_call` calls and no brake count; the gateway never calls `allow_turn()` or `models_disabled()` and never returns `SPEND_CAP` (MOD-11) — verify: `::test_refused_provider_halts_without_call` — evidence: call counters on the adapter, ledger and sink doubles all 0; halt reason asserted.
- [ ] AC-3 [invariant] `timeout_s` given to the adapter equals `min(spec.cap_s, remaining)`; with less than 1.0 s left the outcome is `halt=DEADLINE` and no adapter call is made — verify: `::test_timeout_is_min_of_cap_and_remaining` and `::test_deadline_halts_without_call` (a controllable `TurnBudget`) — evidence: recorded timeouts 3/8/12/12 s with 60 s left and the remaining time when smaller; zero calls on the halt case.
- [ ] AC-4 [failure/refusal] Retry: at most 2 attempts; the second only for a retryable failure whose wait plus 1 s fits; a 429 `RATE_LIMITED` with `retry_after_s=60` and 20 s left is returned with no sleep (DO-1 §11 decision 5); a `RATE_LIMITED` with `retry_after_s=None` waits 0.5–1 s when that plus 1 s fits (MOD-4); a non-retryable kind is never retried; under `PROBE` exactly one attempt is made even for a retryable failure (MOD-13) — verify: `::test_retry_at_most_once_and_only_if_it_fits` (fake clock and sleeper) — evidence: attempt counts and recorded waits per case; no wait past the deadline.
- [ ] AC-5 [capture] **Every** attempt, successful or failed, produces exactly one `ledger.record(rec, ctx.ids)` and one `trace.model_call(ctx.span, rec, …)` where `rec` is `CallRecord.from_provider(attempt.record, role=role, attempt=n)`: `role` is the called role, `attempt` is 1 then 2, and every `ProviderCall` field is carried unchanged; `ModelOutcome.calls` equals the recorded tuple — verify: `::test_every_attempt_records_ledger_and_span` (ledger double with the stage7/models.md §6 methods; in-memory sink double yielding a `SpanHandle`) — evidence: counts equal the attempt count for success, retried success and two failures; `role`/`attempt`/`model` asserted on each record; the span parent is `ctx.span`.
- [ ] AC-6 [failure/refusal] Circuit: a `PROVIDER_SPEND_CAP` failure and, separately, an `OUR_SPEND_LIMIT` failure each call `trip_provider_cap` once, are not retried and return `halt=PROVIDER_SPEND_CAP`; under `PROBE`, a non-cap attempt (success or another failure) calls `close_provider_cap(provider)` once and a cap failure calls `trip_provider_cap` instead — verify: `::test_spend_cap_kinds_trip_and_probe_closes` — evidence: trip and close call counts per scenario; one attempt in each.
- [ ] AC-7 [failure/refusal] Sonnet-call brake (MOD-12): six logical Anthropic calls in one turn run are made and the seventh returns `halt=BRAKE_SONNET_CALLS` with no request; six calls of which one was retried still allow the sixth; Jev calls never count; a *Try again* (same `turn_id`, new `TurnBudget`) starts at zero; after 1,000 sequential turns the counter map holds no entry whose deadline is more than 1 s past — verify: `::test_sonnet_call_brake_counts_logical_calls` — evidence: request counts per case; map size asserted bounded.
- [ ] AC-8 [negative] Redaction by role: with the WP-2 seeds (introduction "This is Omar Patel", 512-555-0102, MHC-10002, INV-204411), a synthetic card-like number, a six-digit code, an email and a street line in the request, the JEV-profile request the choice double receives contains none of them; the SONNET-profile request contains no card-like number, code, email, street line or full phone (`[phone ending 02]` instead) and keeps the name and both IDs; no `masked_in`/`masked_out` given to the sink and no captured log line contains the full phone, the code, the card-like number or an API key value — verify: `::test_redaction_profile_per_role` (values generated at run time, never in test names) — evidence: absence and presence asserted over captured requests, sink calls and `caplog`.
- [ ] AC-9 [invariant] The gateway returns a `ModelOutcome` for every adapter result and never raises into a node: a failed `Attempt` yields `value=None` with `failure` set and is still recorded per AC-5 — verify: `::test_failed_attempt_returns_outcome` — evidence: outcome fields asserted for each `ProviderFailureKind` the doubles return.
- [ ] AC-10 [invariant] `agent/gateway.py` imports no provider SDK or HTTP client (`anthropic`, `httpx`, `openai`, `langfuse`) and opens no unit of work (DO-3 §2.1, §2.3 rule 1) — verify: `tests/unit/agent/test_gateway.py::test_gateway_imports_no_sdk` (AST scan of the module) — evidence: empty list of offending imports; no `UnitOfWorkFactory` in the constructor.
- [ ] AC-11 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-20.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1…J-5 and J-9 (the gateway runs above the scripted adapter) as the journeys that will exercise this code once AEA-57 and AEA-51 land, so the seam audit knows where to look (pattern C, `docs/plans/ux-join/backend-amendments.md` §3) — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-12 [regression/context] In the same change: `.claude/reference/area-map.md` A2 row (`agent/gateway.py` planned → actual + commit); `.claude/state/icm-progress.md` affected row; DO-4 §12's *Gateway rules, in order* paragraph gains a pointer to stage7/models.md §5 (the restated rules this ticket built); DO-3 code-design status for `agent/gateway.py`; a dev-log entry — verify: `git diff --name-only` — evidence: those paths in the diff.

### Observability
- Responsibilities: for WF-1 (and the same turns tagged `eval`/`load` under WF-9 and WF-10): per attempt, one
  `spend_ledger` row through `ledger.record` (columns stage7/models.md §6: role, provider, model, attempt, latency,
  tokens, cost and `cost_source`, status, `failure_kind`, `http_status`, `provider_request_id`, `stop_reason`, the
  `TurnIds`) and one masked `model_call` span under `ctx.span` (DO-6 *Records*, rule 18); the halts
  `PROVIDER_SPEND_CAP`, `DEADLINE` and `BRAKE_SONNET_CALLS` that AEA-21's compose turns into `degrade_reason`
  `spend_cap`, `timeout` and `brake` (DO-4 §11). Retries are countable as `attempt = 2` rows.
- Capture evidence: AC-5 (records per attempt) and AC-8 (forbidden values absent) here with doubles; AEA-51's CAP-1
  drives CON-2 through the real gateway and finds nested model spans and spend rows per turn with the seeded values
  absent, and asserts each ledger row's `model` equals its role's `RoleSpec.model` (stage7/models.md §7).

### Evaluation
- Checks: none added to a suite; every E-1, E-3, E-4 and E-8 conversation runs through this gateway, and E-8's p95
  depends on its role caps and its one bounded retry. Its own unit tests above.
- Expected-answer authority: DO-1 §8.1–§8.2 and stage7/models.md §5 (rules in order) decide correct gateway behaviour;
  Innocent's SDQ-1 (60 s) and the proposal role caps and brake (DO-4 §12, `policy/limits.py`).

### Metrics
- References: M-23 (latency per step from spans), M-24 (model failures and retried calls per provider and role), M-25
  (cost per conversation), M-26 (spend per day against the $30 cap).
- Acceptance conditions: one ledger row and one span per attempt (AC-5) keep M-25 and M-26 complete and M-24's
  retries countable apart; a tripped circuit stops model calls to that provider (AC-2, AC-6), so M-26 cannot run past a
  provider cap; our own cap is enforced before the turn by AEA-40. No new target.

### Blocked by
- AEA-01 (`policy/limits.py` `Limits`, incl. `brakes.sonnet_calls`), AEA-02 (ports with `ProviderCall`/`CallRecord`,
  `TurnContext` with `span`, `ModelSettings`/`RoleSpec` in `config.py`, failure and halt types), AEA-04
  (`privacy/redact.py`, `Redactor`).
- Not a merge blocker: AC-11's journey record names *Blocked by* AEA-57 (harness, wave 2) and AEA-51 (journey landing,
  wave 3); this issue merges on its unit and contract tests.

### Agent handoff
- Area / owner: A2 Models; file `src/meridian/agent/gateway.py`, tests `tests/unit/agent/test_gateway.py` (own doubles in
  its own test folder; AEA-11's shared fakes are a same-wave sibling), and only its own `register_<x>()` stub in
  `web/container.py`.
- Contracts and shared surfaces: **consumes** the three model ports, `ProviderCall`, `CallRecord`, `ProviderName`
  (AEA-02, stage7/models.md §1), `TraceSink` and `SpanHandle` (AEA-02; real sink AEA-19), `Limits` (AEA-01),
  `redact`/`Redactor` (AEA-04), and `LedgerService.admit_call`, `record`, `trip_provider_cap`, `close_provider_cap` by
  their stage7/models.md §6 signatures (real service AEA-26, injected; the slice plan row's `models_disabled` is replaced
  by `admit_call`, MOD-11). **Produces** `ModelGateway` for AEA-35 (`tool_step`), AEA-37 (planner, classifier,
  planner-fallback `choose`), AEA-38 (responder and brief `structured`), AEA-21 (`GraphDeps.gateway`) and AEA-51 (wires
  real adapters, ledger and sink). **Must not edit:** `adapters/models/*` (AEA-17, AEA-18), `services/ledger.py` (AEA-26),
  `config.py` and `ports/*` (AEA-02), `policy/limits.py` (AEA-01), `privacy/redact.py` (AEA-04).
- Scope boundary / refusal: no provider SDK import, no failure classification (adapters own it, S-24), no planner
  fallback choice (AEA-37), no prompt wording, no ledger storage or circuit state (AEA-26), no `$30` cap check (AEA-40),
  no database transaction held across a call (DO-3 §2.3 rule 1).
- Wave and gates: wave 1; gates None.
- Lane: `lane::build-loop` — source and tests that the turn path runs.
- Risk: **security** (`risk::security`, slice plan §1 row AEA-20 and MOD-14): this is where the JEV and SONNET
  redaction profiles are applied before text leaves for a provider; a bug sends a phone, code or card-like number to
  Jev or Sonnet, or writes one into a span. Frozen failing tests first (AC-8 among them); `security-privacy-agent` at the
  wave merge.
- Entry points added or changed: None
- Awaiting Innocent: DAT-1 — built on the recommended option (A: introduction patterns and a street-address pattern
  inside `redact(text, profile)`, signature unchanged); if he picks B, `redact` gains a keyword-only
  `known: Sequence[KnownValue]` and the gateway must pass the located customer's known values on every call (a
  models-topic signature change, stage7/data.md §1 and §9 item 7), and AC-8 adds the customer's name without an
  introduction.
