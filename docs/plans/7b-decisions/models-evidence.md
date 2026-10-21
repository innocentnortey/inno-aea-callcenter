# 7B model and trace decisions: evidence sweep

Scope: the `needs-decision` items in AEA-17, AEA-18, AEA-19, AEA-20 and AEA-26 (`docs/plans/tickets/AEA-NN.md`), searched against `docs/design/*.md`, `docs/design/contracts/*.md`, `docs/ux/03-structure/*.md` and `ui-contracts.openapi.yaml`, `docs/prd/*.md`, `docs/analysis/*.md`, `docs/analysis/spikes/*.md`, `docs/research/*.md`, `docs/data/*.md` and `docs/data/issued/` (non-PDF, non-XLSX). Quotes are verbatim; paths are relative to `inno-aea-callcenter/`. Nothing here is a decision.

Short names used below: `DO-4` = `docs/design/contracts/internal-components.md`, `research` = `docs/research/2026-10-20-vendor-and-framework-facts.md`, `SP-1` = `docs/analysis/spikes/SP-1-two-layer-turn-latency-cost.md`, `obs` = `docs/design/observability-contract.md`, `code-design` = `docs/design/code-design.md`, `sys-design` = `docs/design/system-design.md`.

## AEA-17 #1: how the adapter learns model ID, role and attempt for CallRecord

**Item** (AEA-17.md:126-128): `needs-decision: how the adapter learns the model ID, the role and the attempt number that `CallRecord` holds — the port methods (DO-4 §12) receive none of them (constructor-bound model? gateway stamps role/attempt?). Shared with AEA-18 and AEA-20; decide once in DO-4 §12.`

**Evidence**
- `DO-4:790-791`: "class CallRecord(MeridianModel):                      # one per HTTP attempt → spend_ledger + span" / "role: Role; provider: str; model: str; attempt: int"
- `code-design:369`: "`agent/gateway.py` | Be the one place every model call goes through: typed role maps, redaction profile, timeout = min(role cap, time left), one bounded retry, ledger row, span."
- `code-design:332`: "`adapters/models/anthropic.py` | Make one Sonnet 5.5 request and report it as a typed attempt."
- Not found: any statement that the adapter is bound to a model ID at construction (searched: constructor, bound, stamps, CallRecord, attempt).

## AEA-17 #2: kind for unmapped statuses; "spend limit" 400 vs other 400s

**Item** (AEA-17.md:129-131): `needs-decision: the kind for statuses DO-4 §11 does not map — 402 `billing_error`, 403 `permission_error`, 408, 409 (both retried by DO-1 §8.1), 413 — and how a "spend limit you set" 400 is told apart from other 400s (research §4 names the case, not the distinguishing field).`

**Evidence**
- `research:336`: "| 400 | `invalid_request_error` | bad request; also returned when usage reaches a spend limit **you** set | `BadRequestError` | no |"
- `research:338-339`: "| 402 | `billing_error` | billing or payment problem | `APIStatusError` | no |" / "| 403 | `permission_error` | key lacks permission | `PermissionDeniedError` | no |"
- `research:341-342`: "| 409 | `conflict_error` | resource-state conflict | `ConflictError` | **yes** |" / "| 413 | `request_too_large` | over 32 MB for Messages | `RequestTooLargeError` | no |"
- `DO-4:690-691`: "PROVIDER_SPEND_CAP = "provider_spend_cap"  # Anthropic 429 with no retry-after (research §2b); OpenRouter 402" / "OUR_SPEND_LIMIT = "our_spend_limit"  # Anthropic 400 "spend limit" we set"
- `sys-design:378`: "Our loop retries once, only for retryable errors (408, 409, 429 with `retry-after`, 5xx, 529), and only when the wait"
- Not found: the field that tells a "spend limit" 400 from other 400s (searched: spend limit, invalid_request_error, OUR_SPEND_LIMIT, 400). `DO-4:728-733` maps 409 and 403 only for app-side codes (`TURN_IN_PROGRESS`, `ROLE_NOT_ALLOWED`), not provider statuses.

## AEA-18 #1: model ID, role and attempt for CallRecord (same item as AEA-17 #1)

**Item** (AEA-18.md:124-125): `needs-decision: how the adapter learns the model ID, role and attempt number for `CallRecord` (not in the port call signature, DO-4 §12) — same item as AEA-17 and AEA-20; decide once.`

**Evidence** (same passages as AEA-17 #1)
- `DO-4:790-791`: "class CallRecord(MeridianModel):  # one per HTTP attempt → spend_ledger + span" / "role: Role; provider: str; model: str; attempt: int"
- `code-design:369`: "Be the one place every model call goes through: typed role maps, redaction profile ..."
- Not found: as AEA-17 #1.

## AEA-18 #2: OpenRouter 429 with no retry-after

**Item** (AEA-18.md:126-127): `needs-decision: an OpenRouter 429 with no `retry-after` — DO-4 §11 defines `RATE_LIMITED` as "429 with retry-after" and the provider spend cap for OpenRouter as 402, so this case has no kind.`

**Evidence**
- `DO-4:687`: "RATE_LIMITED = "rate_limited"  # 429 with retry-after"
- `DO-4:690`: "PROVIDER_SPEND_CAP = "provider_spend_cap"  # Anthropic 429 with no retry-after (research §2b); OpenRouter 402" (the no-retry-after 429 kind is mapped for Anthropic only)
- `docs/design/readiness-report.md:79`: "OpenRouter *Errors* (S-229, read 2026-10-20): 402 credits, 408 timeout, 429 with `Retry-After` when available, 502 model down, 503 no provider"
- `research:362-363`: "Treat a 429 with no `retry-after` as the spend cap (no retry will work until the 1st)" (Anthropic statement; no OpenRouter counterpart found)
- Not found: any OpenRouter-specific handling for a 429 without Retry-After (searched: retry-after, Retry-After, 429, OpenRouter, RATE_LIMITED).

## AEA-18 #3: cost_usd source (reported usage.cost vs tokens x price)

**Item** (AEA-18.md:128-129): `needs-decision: `cost_usd` source — the response's reported `usage.cost` (SP-1 recorded it) or tokens × research §2e price, and which wins when both exist.`

**Evidence**
- `SP-1:55`: "| Cost per conversation | Tokens per call × the research note's prices (`docs/research/2026-10-20-vendor-and-framework-facts.md` §2); thinking tokens counted | ≤ $0.30 (the $30/day cap ÷ ~100/day) |"
- `SP-1:89`: "model call is priced from its token counts at §2 of the research note (thinking billed as output)."
- `research:155`: "...prompts, so it must be measured from `usage.output_tokens` in SP-1."
- `research:167`: "**OpenRouter (S-219, S-220).** The project's OpenRouter key could reach all three. Listed prices per token, converted to"
- `research:452`: "...`AnthropicInstrumentor().instrument()`. Whether that captures token usage and cost is not stated on the page (S-216);"
- `DO-4:793`: "thinking_tokens: int; cost_usd: float; status: Literal["ok", "error"]"
- Not found: any reported `usage.cost` field or statement that SP-1 recorded one (searched: usage.cost, usage cost, reported cost, cost_usd, per million). SP-1 gives cost only as token counts times prices (`SP-1:89`), and the precedence rule is not in any source.

## AEA-19 #1: Langfuse API call that proves the keys' project; config name and value

**Item** (AEA-19.md:121-122): `needs-decision: which Langfuse API call proves the keys' project, and the config name and value of "this app's project" — research §6 does not cover it; DO-6 only says "the app asks Langfuse which project its keys belong to".`

**Evidence**
- `obs:225`: "| Records were written but to the wrong Langfuse project | At start-up, the app asks Langfuse which project its keys belong to. If it is not this app's project, export is switched off and an alert fires (CAP-9) |"
- `obs:153`: "...in **its own Langfuse project for this app** (Q-050 revised by Q-062, Innocent 2026-10-20; PRD §6.2, R-36)."
- `code-design:337`: "Startup check that the keys belong to this app's project (DO-6 CAP-9)"
- Not found: the Langfuse API call or config key/value (searched: Langfuse, project, keys, "which project", "keys belong"). `research` §6 (lines 390-470) names no key-verification call.

## AEA-19 #2: alert callable signature

**Item** (AEA-19.md:123): `needs-decision: the alert callable's signature (DO-4 has no health-event writer signature; AEA-32 owns the writer).`

**Evidence**
- `code-design:360`: "`services/health.py` | Keep the heartbeat, record health events, exit after repeated failures. | `Heartbeat`, `Watchdog` | UoW (`repos_ops`) |"
- `DO-4:909`: "ops: OpsRepos              # A10a: health_events, deploy_records, eval results (read)"
- `obs:155-156`: "Alerts stay on the monitoring page with a health check that restarts the / service; there is **no push channel** (Q-045 = A, Innocent 2026-10-20; push alerts are roadmap)."
- Not found: any alert or health-event writer signature (searched: alert, health.event, health_event, writer, signature).

## AEA-19 #3: bound of the export queue

**Item** (AEA-19.md:124): `needs-decision: the bound of the export queue — DO-1 §8.2 says "bounded" with no number.`

**Evidence**
- `sys-design:409`: "| **Langfuse on the VPS** | Bounded export queue; spans dropped when full | Unreachable → spans dropped and counted; turns unaffected | exporter's own, bounded | `trace_export_dropped` |"
- `code-design:225`: "LangfuseTraceSink (mask hook, bounded queue), NullTraceSink"
- `code-design:337`: "Export masked spans in the background, dropping when the queue is full."
- Not found: any numeric size for the queue (searched: bounded, queue, maxsize, queue size across design docs).

## AEA-19 #4: what `sent` means when the turn row is written

**Item** (AEA-19.md:125-126): `needs-decision: what `sent` means when the `turn` row is written — export is in the background, so at that moment a span is enqueued, not yet confirmed. Does `sent` mean enqueued, or does the status update after the exporter reports?`

**Evidence**
- `DO-4:891`: "def export_status(self) -> Literal["off", "sent", "failed"]: ...   # → turn.trace_export (DO-6)"
- `obs:142`: "- **App → Langfuse:** spans export in the background after masking; the trace ID is stored on the `turn` record."
- `obs:219`: "| Traces are not exported | `turn.trace_export` is `sent`, `failed` or `off` on every turn. ... Export is in the background, so a Langfuse outage never slows or fails a turn |"
- `docs/design/key-metrics-registry.md:81`: "Turns with `trace_export` = sent ÷ turns"
- Not found: a definition of `sent` as enqueued or as confirmed (searched: sent, enqueued, confirmed, export status, trace_export).

## AEA-20 #1: parent SpanHandle for TraceSink.model_call

**Item** (AEA-20.md:127-128): `needs-decision: how the gateway gets the turn's parent `SpanHandle` for `TraceSink.model_call(parent, …)` — `TurnContext` (DO-4 §2) carries no span handle. Same gap as AEA-21's node spans.`

**Evidence**
- `DO-4:157-161`: "class TurnContext:  # LangGraph runtime context" then the fields "ids: TurnIds", "budget: TurnBudget", "now: datetime", "demo_session: str" (no span handle).
- `DO-4:887-888`: "class TraceSink(Protocol):" / "def turn(self, ids: TurnIds) -> ContextManager[SpanHandle]: ..."
- `DO-4:889-890`: "def model_call(self, parent: SpanHandle, record: CallRecord, ...)" / "def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ..."
- `code-design:368`: "`agent/context.py` | Carry constructor dependencies (`GraphDeps`) and per-turn values (`TurnContext`)." (no span handle named)
- Not found: how a span handle reaches the gateway (searched: SpanHandle, span handle, parent span, TraceSink, TurnContext).

## AEA-20 #2: HaltReason for a disabled-models refusal

**Item** (AEA-20.md:129-130): `needs-decision: which `HaltReason` a disabled-models refusal uses — `models_disabled()` returns one bool, but `SPEND_CAP` and `PROVIDER_SPEND_CAP` are separate reasons (DO-4 §11).`

**Evidence**
- `DO-4:436-437`: "halt: Halt | None" / "models_disabled: bool   # our cap or the provider's"
- `DO-4:706-710`: "class HaltReason(StrEnum):" ... "SPEND_CAP = "spend_cap"; PROVIDER_SPEND_CAP = "provider_spend_cap""
- `DO-4:855`: "**Gateway rules, in order:** refuse at once if models are disabled (our cap or the provider circuit);"
- Not found: which reason a disabled-models refusal carries (searched: HaltReason, models_disabled, SPEND_CAP, PROVIDER_SPEND_CAP, Halt).

## AEA-20 #3: whether a retry attempt counts toward the 6-call Sonnet brake

**Item** (AEA-20.md:131-132): `needs-decision: whether a retry attempt counts toward the 6-call Sonnet brake ("per-turn Sonnet-call brake … counted here", DO-4 §12, does not say).`

**Evidence**
- `DO-4:859`: "the per-turn Sonnet-call brake (6, proposal) is counted here."
- `DO-4:855-858`: "...at most **2 attempts**, the second only for a retryable failure whose wait (`retry_after_s`, or backoff 0.5–1 s) plus 1 s still fits; every attempt writes a `spend_ledger` row and a masked span;"
- `DO-4:708`: "BRAKE_SONNET_CALLS = "brake_sonnet_calls""
- `sys-design` / `DO-4` have no sentence on whether a retry is a counted call (searched: brake, Sonnet call, six calls, 6-call).

## AEA-20 #4: who stamps CallRecord.role, .attempt and the model ID (same item as AEA-17 #1, AEA-18 #1)

**Item** (AEA-20.md:133-134): `needs-decision: who stamps `CallRecord.role`, `.attempt` and the model ID (the port call signature carries none) — shared with AEA-17 and AEA-18.`

**Evidence** (same passages as AEA-17 #1)
- `DO-4:790-791`: "class CallRecord(MeridianModel):  # one per HTTP attempt → spend_ledger + span" / "role: Role; provider: str; model: str; attempt: int"
- `code-design:369`: "`agent/gateway.py` | Be the one place every model call goes through ..."
- `DO-4:855-858`: "every attempt writes a `spend_ledger` row and a masked span"
- Not found: as AEA-17 #1.

## AEA-26 #1: when the provider spend-cap circuit releases, and whether a trip survives restart

**Item** (AEA-26.md:125-127): `**needs-decision:** 1. When the provider spend-cap circuit releases (process restart, demo reset CON-9, the next Chicago day, or only by hand) and whether a trip must survive a restart. DO-4 §11 says only "no further model calls until reset".`

**Evidence**
- `DO-4:746`: "| Provider spend cap (Anthropic 429 without `retry-after`; OpenRouter 402) | `degraded_handoff` / `spend_cap` | As above; `ModelGateway` trips the circuit: no further model calls until reset |"
- `DO-4:858`: "`PROVIDER_SPEND_CAP` trips the circuit (`services/ledger.py`);"
- `research:362-363`: "Treat a 429 with no `retry-after` as the spend cap (no retry will work until the 1st)" (a monthly point, not the next day)
- `docs/design/contracts/api-con-mapping.md:123`: "**Why.** The monitoring page reports what actually ran: spend resets at real Chicago midnight"
- `obs:161`: "| Spend ledger, health events, eval runs and case results, deploy records | The same SQLite file, in tables the demo reset does **not** clear |"
- `docs/design/contracts/api-con-mapping.md:53`: "| CON-9 | `resetDemo` | ... | 409 RESET_IN_PROGRESS on reset, 503 elsewhere"
- `sys-design:88`: "| Recovery | Survive a process restart without losing conversations or cases [Decided SD-7.2] |"
- Not found: whether the circuit state itself survives a restart, or a release rule other than "until reset" (searched: circuit, until reset, restart, survive, reset, trip).

## Summary of sources

- Items: 14 (AEA-17: 2; AEA-18: 3; AEA-19: 4; AEA-20: 4; AEA-26: 1). Items 17#1, 18#1 and 20#4 are one question logged three times.
- Items with no bearing source at all: 0. Every item has at least a context source (see Evidence).
- Items where the cited sources do not answer the asked question (see each "Not found" line): 14 of 14. Sources give context only.
- Not items, excluded: "Missing instrumentation" headings (AEA-19:31, 58; AEA-26:62) are DO-6 section names, not gaps. AEA-18:40, :77 ("a missing field") are validation cases. AEA-20:128 "Same gap as AEA-21's node spans" is part of AEA-20 #1.
