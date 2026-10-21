# Signatures and types added at Stage 7 (2026-10-21), models

**Status:** DRAFT, written by the Stage 7b resolver for the models topic (AEA-17, 18, 19, 20, 26). It adds to
[`../internal-components.md`](../internal-components.md) (DO-4) §11–§14. It does not replace them. Where a line here
changes a DO-4 line, the DO-4 line is quoted and the change is named. The decision behind each item is in
[`docs/plans/7b-decisions/models.md`](../../../plans/7b-decisions/models.md) (MOD-n). Nothing is built yet.

**Labels:** [Decided §7, engineering] = an interface, name or internal rule decided at Stage 7 with no requirement
behind it. [A] = a number a measurement can replace (the measurement is named). [M] = measured. [C] = calculated.
Sketch style is the same as DO-4: field names, types and validators are the agreement. Method bodies are not.

**Module homes** (DO-3 §3, unchanged): `ports/models.py` and `ports/runtime.py` (AEA-02 writes the files;
`SpanHandle` itself sits in `domain/turn.py` and `ports/runtime.py` re-exports it, graph-core.md §1);
`adapters/models/anthropic.py` (AEA-17); `adapters/models/openrouter_jev.py` (AEA-18); `adapters/tracing_langfuse.py`
(AEA-19); `agent/gateway.py` (AEA-20); `services/ledger.py` + `adapters/sqlite/repos_spend.py` (AEA-26);
`adapters/sqlite/schema/20_spend.sql` (AEA-10, slice plan §0 deviation 1).

---

## 1. What an adapter reports vs what the gateway adds (MOD-1)

**What it does.** An adapter knows the HTTP facts of one request: which provider, which model, how long it took,
the tokens, the cost and how it failed. It does not know which role asked or whether this was the first or second
attempt. Only the gateway knows those. So the adapter returns a `ProviderCall`, and the gateway wraps it into the
`CallRecord` that the ledger and the trace receive.

**Example.** The responder role calls Sonnet. The first attempt gets a 529. The `AnthropicAdapter` returns
`ProviderCall(provider="anthropic", model="claude-sonnet-5-5", status="error", failure.kind=OVERLOADED, …)`. The
gateway writes `CallRecord(role=RESPONDER, attempt=1, …same fields…)` to the ledger and the span, retries, and writes
`attempt=2` for the second request.

```python
# ports/models.py (AEA-02 writes it; definition owned here)       [Decided §7, engineering] consumers: 17, 18, 20, 26, 19, 11, 51
ProviderName = Literal["anthropic", "openrouter_jev"]             # same literal as ProviderFailure.provider (DO-4 §11)

class ProviderCall(MeridianModel):                                # NEW: one per HTTP attempt, built by the adapter
    provider: ProviderName
    model: str                                                    # the adapter's constructor-bound model ID (§2)
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0); output_tokens: int = Field(ge=0)      # output includes thinking (Anthropic)
    cache_read_tokens: int = Field(ge=0); cache_write_tokens: int = Field(ge=0)
    thinking_tokens: int = Field(ge=0)                            # information only; NEVER added to cost (MOD-16)
    cost_usd: float = Field(ge=0)
    cost_source: Literal["reported", "price_table"]               # NEW field (MOD-5)
    status: Literal["ok", "error"]
    failure: ProviderFailure | None                               # set exactly when status == "error"
    provider_request_id: str | None                               # Anthropic `request-id`; OpenRouter response `id` when present
    stop_reason: str | None

class CallRecord(ProviderCall):                                   # CHANGED: DO-4 §12 "role: Role; provider: str; model: str;
    role: Role                                                    #   attempt: int" + the rest. Same fields, now built by
    attempt: int = Field(ge=1, le=2)                              #   the gateway; provider typed as ProviderName
    @classmethod
    def from_provider(cls, call: ProviderCall, *, role: Role, attempt: int) -> "CallRecord": ...

class Attempt(MeridianModel, Generic[T]):                         # CHANGED: DO-4 §12 "record: CallRecord"
    value: T | None
    record: ProviderCall                                          #   → ProviderCall (adapters cannot know role/attempt)
    failure: ProviderFailure | None

class ProviderMessages(MeridianModel):                            # NEW fields (MOD-17): DO-4 §12 named it "opaque, owned by
    provider: ProviderName                                        #   the adapter" without fields. The adapter that built it
    model: str                                                    #   (its constructor-bound model, §2)
    items: tuple[JsonValue, ...]                                  # the provider's own message objects, in order, exactly as
                                                                  #   sent and received: Anthropic content blocks keep their
                                                                  #   thinking blocks and signatures untouched. Only the adapter
                                                                  #   that built the list reads or extends `items`; the runner
                                                                  #   and the gateway pass the whole object through.
    # ToolCallingModel.append (and graph-tools ToolTranscript.append) raises ValueError when `messages.provider` or
    # `.model` differs from the adapter's own: a wiring bug, never a provider failure, so it is not an Attempt.failure.
    # Built only by ToolCallingModel.start / append; never logged, traced or stored (it holds SONNET-profile text).
    # THE one field set (residual pass, R-G-4): graph-tools GRT-9's `provider: Literal["anthropic"]` / `payload` set is
    # withdrawn there. Only Anthropic implements ToolCallingModel today, so `provider` is "anthropic" in practice.

# ports/models.py (AEA-02 writes it; definition owned here)       [Decided §7, engineering] R-G-5; consumers: 17, 18
@dataclass(frozen=True)
class TokenPrice:                                                 # US dollars per million tokens. MOVED (R-G-5) from
    input: float; output: float; cache_write_5m: float; cache_read: float   #   adapters/models/anthropic.py: both
                                                                  #   adapters' price tables use it (§2), and two wave-1
                                                                  #   adapters may not import each other. The tables stay
                                                                  #   per adapter (MOD-5); only the row type is shared.
```

`ModelOutcome.calls`, `LedgerService.record(call: CallRecord, …)` and `TraceSink.model_call(…, record: CallRecord, …)`
keep `CallRecord`. The three port Protocols (`ChoiceModel`, `StructuredModel`, `ToolCallingModel`) keep their DO-4
method signatures; only the type inside `Attempt.record` changes. `ToolSchema` and `ToolCall` stay in `ports/models.py`
as DO-4 §12 has them, and `ToolCallingModel.start` / `append` are unchanged (graph-tools.md C-8 relies on this); the
`ProviderMessages` they return and take now has the fields above (MOD-17).

**Time of the attempt.** Neither type carries a timestamp. `LedgerService.record` stamps `recorded_at` from its injected
wall clock (§6). One clock, one place.

---

## 2. Adapter constructors and the prices they own (MOD-1, MOD-5, MOD-16)

**What it does.** Each adapter object is bound to one model ID when it is built, and carries that provider's price
row. The container builds **one adapter per distinct (provider, model)** that some `RoleSpec.model` names, and hands
the same object to every role that names the same model. So the model ID in every `CallRecord` is the configured
one, never a value the response reports (SP-1 build plan step 5 did the same: "`model` is always `spec.model`").

```python
# adapters/models/anthropic.py (AEA-17)                           [Decided §7, engineering] consumers: 51 (container), 20 (tests)
# TokenPrice is imported from ports/models.py (§1, R-G-5); neither adapter imports the other's module.

ANTHROPIC_PRICES: Mapping[str, TokenPrice] = {                    # research §2a (S-187), read 2026-10-20
    "claude-sonnet-5-5": TokenPrice(input=2.00, output=10.00, cache_write_5m=2.50, cache_read=0.10),
}

class AnthropicAdapter:                                           # implements ChoiceModel, StructuredModel, ToolCallingModel
    provider: ClassVar[ProviderName] = "anthropic"
    def __init__(self, client: anthropic.Anthropic, *, model: str) -> None: ...
        # client built once by the container with max_retries=0 (research §4); shared by every Anthropic adapter.
        # Raises ValueError at construction when `model` has no ANTHROPIC_PRICES row (start-up fails; no silent $0).
    model: str                                                    # read-only, the constructor value

# adapters/models/openrouter_jev.py (AEA-18)
JEV_PRICES: Mapping[str, TokenPrice] = {                          # research §2e (S-223, S-219): output tokens are free
    "typesafe/jev-1.13": TokenPrice(input=0.042, output=0.0, cache_write_5m=0.0, cache_read=0.0),
}

class JevAdapter:                                                 # implements ChoiceModel only
    provider: ClassVar[ProviderName] = "openrouter_jev"
    def __init__(self, http: httpx.Client, *, api_key: SecretStr, model: str) -> None: ...   # ValueError as above
    model: str
```

**Cost rule, per attempt** [Decided §7, engineering]:

| Provider | `cost_usd` | `cost_source` |
|---|---|---|
| Anthropic | `(input × p.input + output × p.output + cache_write × p.cache_write_5m + cache_read × p.cache_read) / 1e6`. `output_tokens` already holds the thinking tokens (research §1: thinking "billed as output tokens"), so `thinking_tokens` is never priced again | `price_table` |
| Jev via OpenRouter | The response's `usage.cost` when it is a finite number ≥ 0; otherwise `input × 0.042 / 1e6` | `reported`, else `price_table` |
| Any failed attempt with no usage block (timeout, connection error, 4xx/5xx) | `0.0`, all token counts `0` | `price_table` |

Why the reported Jev cost wins: it is what OpenRouter bills, and the $30 cap guards billed money. Evidence that the two
agree today: in SP-1, all **258 of 258** Jev calls had `usage.cost` equal to `input_tokens × $0.042/M` [M]
(`var/sp1-runs/*.json`, checked 2026-10-21). A future price change then shows in the ledger before anyone edits the table.

Known undercount [A]: a request cut off by our client timeout may still be billed by the provider for tokens it
generated. We cannot see that bill, so the row says `0.0`. Replace with: the Anthropic console's daily usage compared with
`spend_today()` for the same Chicago day, once a week while deployed.

---

## 3. Failure mapping, complete (MOD-2, MOD-3, MOD-4)

Each adapter maps its own inputs (DO-4 §12: no shared classifier). The two tables below are the whole mapping. A
status not listed falls to the last rows. `retryable` follows DO-4 §11 unchanged: true only for `TIMEOUT`,
`CONNECTION`, `RATE_LIMITED`, `OVERLOADED`, `SERVER`, and `BODY_ERROR` when its inner code is retryable.

**Anthropic (`AnthropicAdapter`, from SDK exceptions and `error.type`; research §4 table)**

| Input | Kind | `retryable` | Basis |
|---|---|---|---|
| `APITimeoutError` | `TIMEOUT` | yes | DO-4 §11 |
| `APIConnectionError` | `CONNECTION` | yes | DO-4 §11 |
| 400 `invalid_request_error` whose message matches the spend-limit pattern below | `OUR_SPEND_LIMIT` | no | research §4; pattern [A] (MOD-3) |
| other 400 | `BAD_REQUEST` | no | DO-4 §11 |
| 401 | `AUTH` | no | DO-4 §11 |
| **402 `billing_error`** | **`PROVIDER_SPEND_CAP`** | no | MOD-2: no call works until a person fixes billing, the same as OpenRouter's 402 |
| **403 `permission_error`** | **`AUTH`** | no | MOD-2: the key lacks permission, a configuration fault like 401 |
| 404 | `NOT_FOUND` | no | DO-4 §11 |
| **408** | **`TIMEOUT`** (`http_status=408`) | yes | MOD-2: DO-1 §8.1 retries 408 |
| **409 `conflict_error`** | **`SERVER`** (`http_status=409`) | yes | MOD-2: DO-1 §8.1 retries 409; a transient provider-side state |
| **413 `request_too_large`** | **`BAD_REQUEST`** | no | MOD-2: over 32 MB is our bug, never transient |
| 429 with `retry-after` (or `retry-after-ms`) | `RATE_LIMITED`, `retry_after_s` set | yes | DO-4 §11 |
| 429 with neither header | `PROVIDER_SPEND_CAP` | no | DO-4 §11, research §2b |
| 529 `overloaded_error` | `OVERLOADED` | yes | DO-4 §11 |
| 500, 504, any other 5xx | `SERVER` | yes | DO-4 §11 |
| any other 4xx | `BAD_REQUEST` | no | MOD-2 |
| HTTP 200, `stop_reason == "refusal"` / `"max_tokens"` | `REFUSAL` / `MAX_TOKENS` | no | DO-4 §11 (checked before content) |
| HTTP 200 whose body or output fails parsing or `output_model` validation; a choice outside its options | `INVALID_OUTPUT` | no | DO-4 §11 |
| **any other exception raised before a response arrived** | **`CONNECTION`** | yes | MOD-2 catch-all: never raises |
| **any other exception raised after a response arrived** | **`INVALID_OUTPUT`** | no | MOD-2 catch-all |

**Spend-limit pattern (MOD-3)** [A]: `error.type == "invalid_request_error"` and the lower-cased `error.message`
contains one of `"spend limit"`, `"usage limit"`, `"credit balance"`. The message is read to classify and is then
dropped: it never reaches `ProviderFailure`, `CallRecord`, a log or a span (AEA-17 AC-7). Research §4 records the case
but no distinguishing field, so this is the best available test. If it misses, the failure is `BAD_REQUEST`, which ends
the turn in the `model_error` handoff and counts toward the 2% failure-rate alert (DO-6). Nothing is retried and no
money is spent. Replace with the recorded `error.message` of the first real spend-limit 400. The adapter logs the
fixed string `anthropic_400_unclassified` with the request ID (never the message) when a 400 matches no rule, so that
case can be looked up in the Anthropic console.

**OpenRouter / Jev (`JevAdapter`, from raw status and body; S-229, S-230)**

| Input | Kind | `retryable` | Basis |
|---|---|---|---|
| `httpx.TimeoutException` | `TIMEOUT` | yes | DO-4 §11 |
| `httpx.TransportError` | `CONNECTION` | yes | DO-4 §11 |
| 400 | `BAD_REQUEST` | no | DO-4 §11 |
| 401 | `AUTH` | no | DO-4 §11 |
| 402 | `PROVIDER_SPEND_CAP` | no | DO-4 §11; S-230 (prepaid balance below threshold) |
| 403 | `AUTH` | no | MOD-2 (same reasoning as Anthropic 403) |
| 404 | `NOT_FOUND` | no | DO-4 §11 |
| 408 | `TIMEOUT` (`http_status=408`) | yes | MOD-2; S-229 lists 408 |
| 413, 422, other 4xx | `BAD_REQUEST` | no | MOD-2 |
| 429 with `Retry-After` | `RATE_LIMITED`, `retry_after_s` set | yes | DO-4 §11 |
| **429 without `Retry-After`** | **`RATE_LIMITED`, `retry_after_s = None`** | yes | **MOD-4**: S-229 sends `Retry-After` "when available" and puts credit exhaustion on 402, so a bare 429 is a rate limit (often an upstream provider's, S-230). The gateway then uses its 0.5–1 s backoff |
| 502, 503, other 5xx | `SERVER` | yes | DO-4 §11 |
| HTTP 200 whose body has an `error` object | `BODY_ERROR`; `http_status` = inner `error.code` when it is an int | yes only when the inner code is in `{408, 429, 500, 502, 503, 504, 529}` | DO-4 §11; MOD-2 names the set |
| HTTP 200, a field missing or a choice outside its options, or unparseable JSON | `INVALID_OUTPUT` | no | DO-4 §11 |
| any other exception before / after a response | `CONNECTION` / `INVALID_OUTPUT` | yes / no | MOD-2 catch-all |

DO-4 §11's comment `RATE_LIMITED = "rate_limited"  # 429 with retry-after` becomes
`# a 429 that is a rate limit; retry_after_s when the provider sent one`. Anthropic's bare 429 stays
`PROVIDER_SPEND_CAP`. Only OpenRouter's bare 429 is a rate limit.

**Risk recorded (MOD-13 limits it).** Research §4 says "Not every 429 carries [`retry-after`]; the spend-cap 429 never
does". SP-1 drew 21 Anthropic 429s from burst ("acceleration") limits at 20 conversations at once [M], and its client
did not record whether they carried `retry-after`. If an acceleration 429 ever arrives bare, the adapter calls it a spend
cap and the circuit trips by mistake. The probe in §6 ends a false trip within `probe_after_s` (10 minutes [A]).

---

## 4. Trace types (MOD-8, MOD-9, MOD-10, MOD-6, MOD-7)

```python
# domain/turn.py (AEA-02 writes it; fields owned here; file per graph-core.md §1)   [Decided §7, engineering]
#   consumers: 19, 20, 21, 40, 42, 11, 51
@dataclass(frozen=True)
class SpanHandle:                                                 # NEW: DO-4 §13 used the name without defining it
    turn_id: TurnId
    trace_id: str | None                                          # 32-hex trace ID → turn.trace_id; None from NullTraceSink
    native: object = field(default=None, compare=False, repr=False)   # the sink's own span; opaque to every caller

# ports/runtime.py (AEA-02 writes it; definitions owned here). Imports SpanHandle from domain/turn.py and re-exports it
#   (domain/ may not import ports/, DO-3 §2.1; TurnContext in domain/turn.py carries a SpanHandle).
ExportStatus = Literal["off", "sent", "failed"]

class TraceSink(Protocol):
    def turn(self, ids: TurnIds) -> ContextManager[SpanHandle]: ...                                    # unchanged
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ...
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...          # unchanged
        # Also carries tool spans (R-G-17): name "tool:<registry name>" (or "tool:unknown"), status ok / refused /
        #   failed, emitted by the specialist runner (graph-tools §2). No new method; sinks treat them as node spans.
    def export_status(self, turn: SpanHandle) -> ExportStatus: ...  # CHANGED: DO-4 §13 took no argument (MOD-9)
```

**Why `export_status` takes the handle.** One sink serves up to 30 turns at once (SDQ-9). A method with no argument
cannot say which turn's spans it is reporting on. `TurnService` (AEA-40) calls it after the `with trace.turn(ids) as
span:` block closes and writes the result to `turn.trace_export`.

**What each status means (MOD-9)** [Decided §7, engineering]:

| Status | Meaning when the `turn` row is written |
|---|---|
| `off` | Export is switched off: `NullTraceSink`, keys missing, the project check failed or found another project |
| `sent` | Every span of this turn was **accepted into the export queue**, none was dropped, and the exporter's most recent batch before the turn closed did not fail |
| `failed` | At least one span of this turn was dropped (queue full), or the exporter's most recent batch failed or timed out |

`sent` therefore means "handed to a healthy exporter", not "confirmed stored in Langfuse". The row is not updated
afterwards: the sink never writes to the database, and `turn` belongs to AEA-40. The blind window is the turns that
close between Langfuse going down and the first failed batch (one batch interval, 5 s [A], plus the export timeout,
5 s [A]). After that, every turn reads `failed` until a batch succeeds. M-29's caveat line should say this.

**The turn's span reaches the gateway through `TurnContext` (MOD-10).** `TurnService` opens `trace.turn(ids)`, builds
`TurnContext(…, span=handle)` inside it, and runs the graph. The gateway calls `trace.model_call(ctx.span, …)` for each
attempt. `PersonRequestService` (AEA-42, the CON-4 path) does the same for its turn: it builds its `TurnContext` inside
`with trace.turn(ids) as span:` and writes `span.trace_id` and `trace.export_status(span)` to its `turn` row
(web.md §8, MC-17). `TurnContext` and its `span` field are defined in graph-core.md §2 (cross-topic assumption 1).

```python
# adapters/tracing_langfuse.py (AEA-19)                           [Decided §7, engineering] consumers: 51, 50, 32 (via container)
TraceAlertReason = Literal["wrong_project", "project_check_failed"]
TraceAlert = Callable[[TraceAlertReason], None]                   # MOD-7: the reason code only; never a key, URL or body

@dataclass(frozen=True)
class LangfuseExportSettings:                                     # built by the container from Settings' four langfuse_*
                                                                  #   fields when Settings.langfuse_complete() (§7). Settings
                                                                  #   has no langfuse_export(): config.py may not import
                                                                  #   this adapter (R-G-6, graph-core §12)
    public_key: SecretStr; secret_key: SecretStr; base_url: str   # LANGFUSE_PUBLIC_KEY / _SECRET_KEY / _BASE_URL (research §6)
    project_id: str                                               # LANGFUSE_PROJECT_ID: this app's project ID on the VPS Langfuse
    queue_max_spans: int = 1024                                   # [A] MOD-8
    batch_interval_s: float = 5.0                                 # [A]
    export_timeout_s: float = 5.0                                 # [A]; the exporter's own, never a turn's
    check_timeout_s: float = 5.0                                  # [A]; the start-up project check
    recheck_after_s: float = 600.0                                # [A]; only after project_check_failed

class LangfuseTraceSink:                                          # implements TraceSink
    def __init__(self, settings: LangfuseExportSettings, redact: Redactor, on_alert: TraceAlert) -> None: ...
        # Redactor: defined in stage7/data.md §1 (privacy/redact.py), the type of redact(text, profile) -> Redacted
    def start(self) -> None: ...                                  # runs the project check (below); never raises
    def dropped_spans(self) -> int: ...                           # trace_export_dropped (DO-1 §8.2), since start

class NullTraceSink:                                              # implements TraceSink
    # turn() yields SpanHandle(turn_id, trace_id=None); model_call/node do nothing; export_status → "off"
```

**The start-up project check (MOD-6)** [Decided §7, engineering]:
1. `GET {LANGFUSE_BASE_URL}/api/public/projects` with HTTP Basic auth (public key as user, secret key as password),
   timeout `check_timeout_s`. Langfuse's Public API documents that "A successful response returns the project
   associated with your API key": a `data` array holding `id`, `name` and `organization`
   (https://langfuse.com/docs/api-and-data-platform/features/public-api, read 2026-10-21; AEA-19 registers it as the
   next free `S-N` before citing it, context-maintenance rule 5).
2. Export turns on **only if** the response is 200 and `data` holds **exactly one** project whose `id` equals
   `LANGFUSE_PROJECT_ID`. The ID is compared, not the name: two projects on one instance can share a name, never an ID.
   An organisation-scoped key that lists several projects fails the check.
3. Any other answer (another ID, several projects, 401/403) → export off for the life of the process,
   `on_alert("wrong_project")` once. The keys only change with a redeploy, so there is no re-check.
4. Langfuse unreachable, a timeout or a 5xx → export off, `on_alert("project_check_failed")` once, and the check runs
   again every `recheck_after_s` on the exporter thread until it passes or finds the wrong project. Spans created
   while export is off are not queued.
5. Missing keys or a missing `LANGFUSE_PROJECT_ID` → the container builds `NullTraceSink`; `on_alert` is not called,
   but every turn records `trace_export = off`, so AEA-32's evaluator shows `trace_export_failed` (DO-6 :237;
   cases.md §8 owns that rule, MC-24). This is the deployed default until Innocent's yes to the route (SDQ-3).

**The export queue (MOD-8).** A `BatchSpanProcessor`-style queue of `queue_max_spans = 1024` [A] spans, sitting
between the mask hook and the OTLP exporter. Adding a span never blocks. When the queue is full, the span is dropped
and `dropped_spans()` rises. Sizing [C]: one turn makes about 15 spans [A] (1 turn, ~6 nodes, up to ~8 model
attempts; SP-1's mix B made at most 6 Sonnet calls in a turn [M]). 30 turns in flight (SDQ-9) × 15 = 450 spans, so
1,024 holds a little over two full loads of backlog. Memory [C]: if a model-call span carries ~50 KB of masked context
[A], 1,024 spans is ~50 MB at worst. Replace with: span sizes from the first traced run, and the process RSS during
AEA-50's load run (`resource-pressure-agent`). If the Langfuse SDK v5 exposes no queue-size setting, AEA-19 wraps its
own processor with these values. The planner checks this, and records `blocked-on` only if neither path works.

---

## 5. The gateway, rules restated with the decisions applied (MOD-1, 10, 11, 12, 13)

The constructor and the three methods are DO-4 §12 unchanged. The rules, in order, now read
[Decided §7, engineering, except where a source is cited]:

1. **Provider admission.** `adm = ledger.admit_call(adapter.provider)` (§6). `REFUSE` → return
   `ModelOutcome(value=None, calls=(), failure=None, halt=Halt(reason=PROVIDER_SPEND_CAP, …))`, with no adapter call,
   no ledger row, no span, and no brake count. **Our $30/day cap is not checked here** (MOD-11). DO-1 §8.2 checks it
   "before each turn" and lets "a turn in progress … overrun by one turn's cost", and DO-4 §14 and AEA-26's example say
   the same. That is `TurnService`'s admission check (`allow_turn()`, AEA-40). The gateway never emits `SPEND_CAP`.
2. **Deadline.** `timeout = ctx.budget.timeout_for(spec.cap_s)`; `None` → `halt=DEADLINE`, no call (DO-4 §12).
3. **Sonnet-call brake (MOD-12).** The brake counts **logical calls**, one per gateway method call that reaches an
   attempt and whose adapter's `provider == "anthropic"` (any role, including `PLANNER_FALLBACK`). A retry is part of
   the same call and is not counted again. When the count for this turn run is already `limits.brakes.sonnet_calls`
   (6, proposal), return `halt=BRAKE_SONNET_CALLS` with no request. The counter is keyed by
   `(ctx.ids.turn_id, ctx.budget.started)`, so a "Try again" on the same `turn_id` starts at zero. An entry is pruned
   once `ctx.budget.deadline` is more than 1 s in the past, which keeps the map no bigger than the turns in flight.
4. **Redaction.** As DO-4 / AEA-20 rule 3 (`RoleSpec.redaction`): `redact(text, spec.redaction)` with the
   `RedactionProfile` `SONNET` or `JEV` per role (data.md §1, cross-topic 7 there).
5. **Attempts.** At most 2 (DO-4 §12). When `adm == PROBE`, **exactly 1** attempt and no retry (§6).
6. **Record every attempt.** `rec = CallRecord.from_provider(attempt.record, role=role, attempt=n)` (MOD-1), then
   `ledger.record(rec, ctx.ids)` and `trace.model_call(ctx.span, rec, masked_in, masked_out)` (MOD-10).
7. **Circuit.** If the failure's kind is `PROVIDER_SPEND_CAP` **or `OUR_SPEND_LIMIT`** → `ledger.trip_provider_cap(failure)`,
   no retry, and the outcome carries `halt=PROVIDER_SPEND_CAP` (MOD-11). If `adm == PROBE` and the attempt was anything
   else → `ledger.close_provider_cap(adapter.provider)` (MOD-13).

`ModelGateway` reads `adapter.provider` (a `ClassVar` on each adapter, §2), so it needs one more attribute than the
three port Protocols name. The three Protocols gain `provider: ProviderName` as a read-only attribute (cross-topic 2).
Test doubles set it.

**Halt → customer.** `halt=PROVIDER_SPEND_CAP` is composed as DO-4 §11's row "Provider spend cap": `degraded_handoff` /
`spend_cap`, notice `SPEND_CAP_REACHED`, signal `provider_spend_cap`. A halt from the gateway is never a reason to fall
back to another role or provider (cross-topic 4).

---

## 6. LedgerService, with the circuit rule (MOD-11, MOD-13)

```python
# policy/limits.py (AEA-01 owns the file; the field is this topic's; MC-22)        consumers: 26, 32, 53, 51 (container)
@dataclass(frozen=True)
class SpendLimits:                                                # Limits.spend, beside Limits.web (web.md §5)
    daily_cap_usd: float = 30.0                                   # our cap, US dollars per America/Chicago day
                                                                  #   [T] system design §2 "$30/day"; the ONE literal

# services/ledger.py (AEA-26)                                     [Decided §7, engineering] consumers: 20, 40, 53, 51, 32
class CallAdmission(StrEnum):
    ALLOW = "allow"; PROBE = "probe"; REFUSE = "refuse"

class SpendGuard(Protocol):                                       # NEW (MOD-18): DO-3 §4 names `SpendGuard.allow_turn`; the
    def allow_turn(self) -> bool: ...                             #   ONE method TurnService's admission step 2 needs (AEA-40),
                                                                  #   so it depends on this, not on the whole LedgerService

class LedgerService:                                              # implements SpendGuard (the container passes the same
                                                                  #   LedgerService object as TurnService's `spend`)
    def __init__(self, uow: UnitOfWorkFactory, *, wall_clock: Callable[[], datetime],
                 daily_cap_usd: float, probe_after_s: float = 600.0) -> None: ...
                 # wall_clock: real time, never the demo Clock (AEA-26); the container passes web.md §4
                 #   get_wall_clock(), which returns datetime.now(UTC) (MC-20).
                 # daily_cap_usd: no default; the container passes limits.spend.daily_cap_usd (AEA-01
                 #   SpendLimits above, 30.0; MC-22), never a second literal. probe_after_s: 10 minutes [A].
    def record(self, call: CallRecord, ids: TurnIds) -> None: ...            # DO-4 §14; stamps recorded_at (UTC) here
    def spend_today(self) -> float: ...                                       # DO-4 §14 (Chicago day)
    def allow_turn(self) -> bool: ...                                         # DO-4 §14: our cap ONLY, never the circuit
    def trip_provider_cap(self, failure: ProviderFailure) -> None: ...       # DO-4 §14; kinds PROVIDER_SPEND_CAP and
                                                                             #   OUR_SPEND_LIMIT open failure.provider's
                                                                             #   circuit; any other kind is ignored
    def admit_call(self, provider: ProviderName) -> CallAdmission: ...       # NEW (replaces the gateway's use of
                                                                             #   models_disabled)
    def close_provider_cap(self, provider: ProviderName) -> None: ...        # NEW
    def open_circuits(self) -> tuple[ProviderName, ...]: ...                 # NEW; monitoring (AEA-53) and alerts (AEA-32)
    def models_disabled(self) -> bool: ...                                    # DO-4 §14, kept: not allow_turn() or any
                                                                             #   circuit open ("handoff-only mode" on CON-19)
```

**The circuit, per provider, in memory** [Decided §7, engineering; probe interval [A]]:

| State of `provider`'s circuit | `admit_call(provider)` returns |
|---|---|
| closed | `ALLOW` |
| open, less than `probe_after_s` since the trip | `REFUSE` |
| open, `probe_after_s` or more since the trip, no probe in flight | `PROBE`, once. The probe is marked in flight; a probe in flight for more than 60 s (the turn deadline) is treated as lost |
| open, a probe in flight | `REFUSE` |

- `trip_provider_cap` opens the circuit, or re-opens it with a new trip time when a probe meets the cap again.
- `close_provider_cap` closes it. The gateway calls it when the probe's attempt ended in anything but a cap kind.
- **Release:** only by a successful probe. Not by the demo reset (CON-9): the reset cannot change the provider's
  account. Not by Chicago midnight: Anthropic's cap lasts until "00:00 UTC on the 1st of next month" (research §2b).
- **Restart:** state is not persisted. A restarted process starts closed, and its first call to a capped provider meets
  the cap again (a 429 or 402 with no usage block, so $0 in the ledger [A]) and re-trips. The trip history stays in `spend_ledger` (failure kind per
  row), so nothing is lost for monitoring.
- **Per provider:** with Anthropic capped, a turn still makes its Jev planner and classifier calls (≈ $0.00002 [C]) and
  halts at the first Sonnet call. With OpenRouter capped, the turn halts at the Jev planner. Either way the customer
  gets the spend-cap handoff that DO-4 §11 describes. The per-provider split exists so the probe always reaches the
  capped provider. If all model calls were refused while Anthropic was capped, the turn would halt at the Jev planner,
  no Sonnet call would ever run, and the circuit could never close.
- Cost of a real cap [C]: one failed request every 10 minutes, 144 a day, each with no usage block ($0 in the ledger
  [A]; the provider's usage page confirms it). Cost of a false trip: at most
  10 minutes of handoff-only mode.

**`spend_ledger` columns** (AEA-10 writes `20_spend.sql`; AEA-26 writes `repos_spend`) [Decided §7, engineering]:
`id INTEGER PRIMARY KEY`, `recorded_at TEXT` (UTC ISO-8601 with `+00:00`, from the ledger's wall clock, written by the
one formatter in `adapters/sqlite/db.py`: cases.md §1.1, MC-20), `thread_id`, `turn_id`,
`request_id`, `run_tag`, `run_id`, `agent_version` (from `TurnIds`), `role`, `provider`, `model`, `attempt`,
`latency_ms`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `thinking_tokens`,
`cost_usd REAL`, `cost_source`, `status`, `failure_kind` (null on success), `http_status` (from `failure`, null on
success), `provider_request_id`, `stop_reason`. Indexes on `recorded_at`, `turn_id`, `thread_id`. `spend_today()`
turns the Chicago day into UTC bounds with `zoneinfo` and queries `recorded_at >= ? AND recorded_at < ?`, so the 25-hour
day on 2026-11-01 needs no special case.

**`repos_spend.py`, the methods `LedgerService` calls** (MOD-19) [Decided §7, engineering]. AEA-02 creates the shell with
its constructor (the one constructor every repository has: cases.md §1.0); AEA-26 writes the bodies.

```python
# adapters/sqlite/repos_spend.py (AEA-26 body)                    consumers: 26 (LedgerService), 51 (wiring test), 53 (via ledger)
class SpendRow(CallRecord):                                       # one spend_ledger row; CallRecord's fields (§1) plus:
    id: int | None = None                                         # None before insert; the INTEGER PRIMARY KEY after
    recorded_at: datetime                                         # UTC, from LedgerService's wall clock
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId   # from TurnIds
    run_tag: Literal["live", "eval", "load"]; run_id: str | None; agent_version: str
    # `failure` is stored as the failure_kind and http_status columns (null on success) and rebuilt on read.

class SpendRepo:                                                  # adapters/sqlite/repos_spend.py; = UnitOfWork.spend (DO-4 §13)
    def __init__(self, conn: sqlite3.Connection) -> None: ...     # the unit of work's one connection (cases.md §1.0)
    def append(self, row: SpendRow) -> int: ...                   # INSERT; returns the new id. LedgerService.record's only write
    def total_between(self, start_utc: datetime, end_utc: datetime) -> float: ...
        # SUM(cost_usd) over recorded_at >= start_utc AND recorded_at < end_utc; 0.0 when no row. spend_today()'s read
    def for_turn(self, turn_id: TurnId) -> tuple[SpendRow, ...]: ...
        # this turn's rows, id ascending; AEA-51's wiring assertion (§7) and AEA-26's tests read them
```

---

## 7. Container wiring this implies (for AEA-51 and the owners' `register_*` hunks)

```python
# web/container.py, illustrative
sonnet_client = anthropic.Anthropic(api_key=…, max_retries=0)         # one SDK client
adapters: dict[tuple[ProviderName, str], object] = {}                   # one adapter per (provider, model)
def adapter_for(provider: ProviderName, spec: RoleSpec) -> AnthropicAdapter | JevAdapter: ...
    # AnthropicAdapter(sonnet_client, model=spec.model) / JevAdapter(http, api_key=…, model=spec.model); memoised in
    # `adapters` by (provider, spec.model), so roles naming the same model share one object (§2, MOD-19)
wall_clock = get_wall_clock()                                           # web.md §4: datetime.now(UTC) (MC-20)
ledger = LedgerService(uow, wall_clock=wall_clock, daily_cap_usd=limits.spend.daily_cap_usd)   # MC-22
export_settings = LangfuseExportSettings(public_key=settings.langfuse_public_key,          # R-G-6: the four Settings
    secret_key=settings.langfuse_secret_key, base_url=settings.langfuse_base_url,         #   fields, read only when
    project_id=settings.langfuse_project_id)                                              #   langfuse_complete()
trace = (LangfuseTraceSink(export_settings, redact,                     # redact: data.md §1, a Redactor (MC-23)
                           on_alert=lambda reason: alert_writer.fire("trace_export_failed", reason))  # cases.md §8
         if <all four LANGFUSE_* settings are set>                       # settings: AEA-02 config.py Settings (MC-21;
         else NullTraceSink())                                          #   graph-core.md GRC-19 table), cross-topic 3
gateway = ModelGateway(choice=…, structured=…, tools=…, ledger=ledger, trace=trace, redact=redact, limits=limits)
```

AEA-51 adds one assertion to its wiring test: after a driven turn, every ledger row's `model` equals its role's
`RoleSpec.model`.

---

## Cross-topic assumptions

These are types or behaviours that another topic owns. MOD's decisions assume them. If the owner decides otherwise,
the named MOD item reopens.

1. **graph (AEA-02 `TurnContext`, AEA-21 node spans), settled:** `TurnContext.span: SpanHandle` is in graph-core.md §2
   (`domain/turn.py`), set by `TurnService` inside `trace.turn(ids)` (MOD-10) and, on the CON-4 path, by
   `PersonRequestService` (web.md §8, MC-17). AEA-21's node spans use the same field (graph-core GRC-6). MOD needs
   nothing else from `TurnContext`.
2. **graph (AEA-02 writes `ports/models.py`, `ports/runtime.py` and `domain/turn.py`):** AEA-02 transcribes §1 and §4
   of this file: the types `ProviderName`, `ProviderCall`, `CallRecord(ProviderCall)`, `Attempt.record: ProviderCall`,
   `ProviderMessages` with its fields (MOD-17), `TokenPrice` (§1, R-G-5), `ExportStatus`, `TraceSink.export_status(turn)`, the read-only `provider: ProviderName` attribute on the three model
   port Protocols, and `SpanHandle` (in `domain/turn.py`, re-exported by `ports/runtime.py`; graph-core.md §1, X-1).
   AEA-11's ticket (data topic) carries: "Scripted model fakes put a `ProviderCall` in `Attempt.record` (no `role`, no
   `attempt`) and set `provider`; `InMemoryTraceSink.turn()` yields a `SpanHandle` and `export_status(turn)` takes it
   (stage7/models §1, §4)." AEA-11 AC-2's "carry a `CallRecord`" becomes "carry a `ProviderCall`" (MC-28).
3. **graph (AEA-02 `config.py`) and AEA-01 (`policy/limits.py`):** AEA-02's `Settings` declares `LANGFUSE_PUBLIC_KEY`,
   `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `LANGFUSE_PROJECT_ID` (all optional; the sink is Langfuse only when all
   four are set), and data.md §9 item 1 lists all four for Railway (MC-21). **Settled:** graph-core.md's GRC-19 table
   ("models 3, data 1") accepts this `Settings` field list for AEA-02. AEA-01's frozen `Limits` holds the $30
   daily cap as `limits.spend.daily_cap_usd` (`SpendLimits`, defined in §6, MC-22); `LedgerService`
   receives it from the container. `probe_after_s` defaults in `LedgerService` unless AEA-01 adds it to
   `policy/limits.py`. `Limits.brakes.sonnet_calls = 6` is AEA-01's (proposal). See the note in the decisions file:
   SP-1's mix B reached exactly 6 Sonnet calls in 7 of 192 turns [M].
4. **graph (AEA-21 halt routing, AEA-37 planner fallback):** a gateway `halt` (any reason) ends the turn through the
   halt path. AEA-37 uses the Sonnet planner fallback only for a `failure` (`BODY_ERROR` and the other Jev failures,
   SDQ-6), never for a `halt`. Otherwise, with OpenRouter capped, the system would run without the danger classifier.
   That would be a safety choice for Innocent, not a fallback.
5. **web (AEA-40 `TurnService`, AEA-42 `PersonRequestService`):** `TurnService` checks `ledger.allow_turn()` at
   admission (step 2) and nothing about circuits; it receives the ledger typed as the `SpendGuard` Protocol (§6, MOD-18). Both pass the handle to `trace.export_status(span)` after the turn
   span closes and write `span.trace_id` to `turn.trace_id` and the status to `turn.trace_export` (web.md §8, MC-17),
   as `TurnRecord.trace_id` / `trace_export` (graph-core.md §2, GRC-21).
   The wall clock every service here receives is web.md §4 `get_wall_clock()` (UTC, MC-20).
6. **cases (AEA-10, AEA-32, AEA-53), settled:** AEA-10 writes `20_spend.sql` with the §6 columns (cases.md §1.1).
   AEA-32's writer is cases.md §8 `AlertWriter.fire(alert_type, reason_code)`, callable from a non-request thread at
   start-up; the container binds `on_alert=lambda reason: alert_writer.fire("trace_export_failed", reason)` (UXR-23).
   cases.md §8's evaluator also fires `trace_export_failed` when the latest live turn's `trace_export` is `off`
   (MC-24). AEA-53 may read `ledger.open_circuits()` to show handoff-only mode.
7. **data (AEA-56 / deploy):** turning export on in the deployed app sets `LANGFUSE_PROJECT_ID` to this app's project
   ID. That project is created on the VPS Langfuse by Innocent (a `lane::human` step, SDQ-3). It is not a decision
   in this file.
