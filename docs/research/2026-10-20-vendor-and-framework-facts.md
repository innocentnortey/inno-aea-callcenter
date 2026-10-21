# Vendor and framework facts for the PRD interview (SD-4.2, SD-5.4, SD-5.6, SD-6.3, SD-7.4, Langfuse)

**Researched:** 2026-10-20 (America/Chicago). Every page below was read on 2026-10-20. **Status:** DERIVED
research notes; the facts quote vendor pages and pinned package source, the judgments are ours.
**Owner of:** nothing new. Sources are registered as **S-187…S-226** in the
[source register](../source/source-register.md); this file cites them by ID and gives each URL once per section.

**Labels.** A number with no label is quoted from the cited page or file on the read date.
**[M]** measured by us. **[A]** an assumption we chose. **[C]** a calculation from quoted numbers and [A]s.
"Not stated" means the page does not give it; the line says where it would be found.

**Pinned versions** (from `uv.lock`, read 2026-10-20): `langgraph` 1.2.16, `langgraph-checkpoint` 4.3.0,
`langgraph-checkpoint-sqlite` 3.1.2, `fastapi` 0.156.4, `starlette` 1.9.0, `uvicorn` 0.54.0, `anyio` 4.15.1,
`aiosqlite` 0.22.1, `anthropic` 1.17.0, `fastembed` 0.9.0, `onnxruntime` 1.31.0, `langchain-core` 1.6.12.
Where a fact depends on the version, it was read from the installed package in `.venv/` (same versions) and
from the matching upstream tag.

---

## 1. SD-4.2 Model API contract (Anthropic Messages API)

Sources: S-191 https://platform.claude.com/docs/en/api/overview · S-192
https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview and
https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools · S-193
https://platform.claude.com/docs/en/build-with-claude/structured-outputs · S-190
https://platform.claude.com/docs/en/api/errors · S-195 https://platform.claude.com/docs/en/build-with-claude/thinking
and https://platform.claude.com/docs/en/build-with-claude/effort · S-196 `anthropic` 1.17.0 source. All read 2026-10-20.

**Authentication and headers (S-191).** One endpoint, `POST /v1/messages`. Required headers: `Authorization: Bearer
<token>` (the API key or a short-lived Workload Identity Federation token; "Yes, unless `x-api-key` is set"), or the
legacy `x-api-key: <key>` ("still supported"); `anthropic-version` (for example `2023-06-01`); `content-type:
application/json`. The SDK sends all three itself. The pinned SDK sends `anthropic-version: 2023-06-01`
(`anthropic/_constants.py`, S-196).

**Tool use, request → response (S-192).**
- Request: `tools: [{name, description, input_schema}]` plus `messages`. Default `tool_choice` is `{"type": "auto"}`:
  Claude decides each turn whether to call a tool.
- Response when Claude wants a tool: `stop_reason: "tool_use"` and one or more content blocks shaped
  `{"type": "tool_use", "id": "toolu_…", "name": "get_weather", "input": {…}}`.
- Our next request appends that assistant message, then a user message holding
  `{"type": "tool_result", "tool_use_id": <id>, "content": …}`. A failed tool returns a `tool_result` with `is_error: true`.
- `strict: true` on a tool definition "ensure[s] Claude's tool calls always match your schema exactly".
- **Forced tool use is rejected on Sonnet 5.5.** `tool_choice` `any` and `tool` "return a 400 error" on Claude Opus 5.5,
  Claude Sonnet 5.5, Claude Fable 5.1 and Claude Mythos 5.1; the documented replacement is `auto` with strict tool use, or
  structured outputs. Haiku 5.5 is not in that row; it accepts forced tool use, but "a forced call skips thinking" (S-192,
  define-tools table).
- Tool use adds a hidden system prompt: 286 tokens on Sonnet 5.5 (`auto`/`none`), 286 on Haiku 5.5 (406 for `any`/`tool`)
  (S-187, pricing page "Tool use" table).

**Structured output options (S-193).**
- JSON outputs: `output_config: {format: {type: "json_schema", schema: …}}`. In Python, `client.messages.parse()` with a
  Pydantic model "sends it as `output_config.format`, validates the response, and returns the parsed model in
  `parsed_output`".
- Strict tool use (`strict: true`) for schema-valid tool inputs.
- Limits: "a subset of the JSON Schema language"; the first request with a new schema has "additional latency while the
  grammar compiles", and compiled grammars "are cached for 24 hours from last use". Incompatible with citations
  ("Returns 400 error if citations enabled with `output_config.format`") and with message prefilling.

**Thinking is on by default and is billed (S-195).** "the tokens Claude spends reasoning are billed as output tokens,
even when the thinking text isn't returned to you, and they count toward `max_tokens`". Effort defaults: `high` on
Sonnet 5.5, `medium` on Haiku 5.5. To turn up-front thinking off on Sonnet 5.5, send `thinking: {"type":
"between_tools"}` (works at `low`, `medium`, `high`); `{"type": "disabled"}` is a 400 on Sonnet 5.5. For "chat and other
latency-sensitive work, start with `medium` or `low`".

**What an error looks like (S-190).** Always JSON with a top-level `error` object:
```json
{"type": "error",
 "error": {"type": "not_found_error", "message": "The requested resource could not be found."},
 "request_id": "req_011CSHoEeqs5C35K2UUqR7Fy"}
```
Every response carries a `request-id` header; the Python SDK exposes it as `message._request_id`. On a streamed
response, an error "can occur after the API returns a 200 response" and arrives as an SSE error event instead. A safety
decline is not an HTTP error: HTTP 200 with `stop_reason: "refusal"` (S-195 / models overview).

**What this means for the design.** Our classifier and planner cannot force a tool on Sonnet 5.5, so they should return
their decision through `output_config.format` (or `auto` + `strict: true`). Check `stop_reason` before reading content,
including `refusal` and `max_tokens`. The current call in `src/meridian/agent/graph.py` sets `max_tokens=900` with
Sonnet 5.5's default `high` effort; thinking counts toward that cap, so a long think can end the reply at `max_tokens`.
Set effort explicitly per role (`low`/`medium` for chat-style roles, or `between_tools`) and log `request_id` with every
trace.

---

## 2. SD-5.4 Model limits and prices

Sources: S-187 https://platform.claude.com/docs/en/about-claude/pricing · S-188
https://platform.claude.com/docs/en/about-claude/models/overview · S-189 https://platform.claude.com/docs/en/api/rate-limits
· S-194 https://platform.claude.com/docs/en/build-with-claude/prompt-caching · S-217
https://developers.openai.com/api/docs/pricing and https://developers.openai.com/api/docs/models/gpt-5.6-terra · S-218
https://ai.google.dev/gemini-api/docs/pricing and https://ai.google.dev/gemini-api/docs/models · S-219
https://openrouter.ai/api/v1/models (+ `/models/{slug}/endpoints`) · S-220 https://openrouter.ai/docs/faq. All read 2026-10-20.

### 2a. Anthropic prices and context (S-187, S-188)

| Model (ID) | Input /MTok | Output /MTok | 5-min cache write | 1-h cache write | Cache hit | Context | Max output |
|---|---|---|---|---|---|---|---|
| Claude Sonnet 5.5 (`claude-sonnet-5-5`) | $2 | $10 | $2.50 | $4 | **$0.10** (0.05× input) | 1M | 128K |
| Claude Haiku 5.5 (`claude-haiku-5-5`), prompts ≤100,000 tokens | $0.10 | $0.50 | $0.125 | $0.20 | $0.01 | 1M | 128K |
| Claude Haiku 5.5, prompts >100,000 tokens | $0.50 | $2.50 | $0.625 | $1 | $0.05 | 1M | 128K |

- Batch API: 50% off (Sonnet 5.5 $1/$5; Haiku 5.5 $0.05/$0.25 up to 100K). US-only inference (`inference_geo`) costs 1.1×.
- Minimum cacheable prefix: 512 tokens for Sonnet 5.5 and Haiku 5.5 (S-194). Shorter prompts are silently not cached.
- Note: a locally bundled reference (cached 2026-10-06) listed the Sonnet 5.5 cache hit as $0.20; the live pricing page
  read today says $0.10. The live page wins.

### 2b. Anthropic rate limits and how the tier is set (S-189)

- Limits are per organization, per model, in RPM, ITPM (input tokens/min) and OTPM (output tokens/min), enforced with a
  token bucket ("continuously replenished … rather than being reset at fixed intervals"); a 60 RPM limit "might be
  enforced as 1 request per second".
- Tier: "Organizations are placed on a tier automatically based on usage history and account standing". New
  organizations "may start in the Evaluation tier, with limits below the standard limits". The current tier is shown at
  `platform.claude.com/usage/limits`.
- Standard limits per tier, Sonnet 5.5 and Haiku 5.5 (each model its own bucket): **Start** 1,000 RPM / 2,000,000 ITPM /
  400,000 OTPM; **Build** 5,000 / 5,000,000 / 1,000,000; **Scale** 10,000 / 10,000,000 / 2,000,000.
- Monthly spend caps: Start $500, Build $1,000, Scale $200,000. At the cap, requests get HTTP 429 with **no
  `retry-after`** until 00:00 UTC on the 1st of next month.
- Cached reads (`cache_read_input_tokens`) do **not** count toward ITPM on these models; `max_tokens` does not count
  toward OTPM.
- **[M]** One probe call per model on this project's key, 2026-10-20 (coordinator's report): Sonnet 5.5 and Haiku 5.5
  each allow 1,000 RPM, 2,000,000 ITPM, 400,000 OTPM. **[C]** Those equal the published Start-tier row, so the key is
  most likely on Start (spend cap $500/month); the console page would confirm it.

### 2c. Cost per conversation [C]

**Turn shape** (from the brief for this task) [A]: planner ~2,000 in / 200 out; classifier ~1,000 in / 20 out;
specialist with tools ~6,000 in / 400 out (one call; a real tool round trip is two requests, so this assumes both fit in
that total, including the 286-token tool prompt); responder ~3,000 in / 300 out. **5 turns per conversation** [A].
Input per turn is flat [A] (in reality history grows each turn). Base case: no caching, and **no thinking tokens** [A].
Budget: $10/day for ~100 conversations = **$0.10/conversation**.

| Scenario | Per turn [C] | Per conversation [C] | 100 conv/day [C] | vs $0.10 |
|---|---|---|---|---|
| A. Haiku 5.5 planner + classifier, Sonnet 5.5 specialist + responder | $0.0254 | **$0.127** | $12.70 | 27% over |
| A + 50% of every input read from cache [A] | | $0.084 | $8.36 | under |
| A + 500 thinking tokens on each Sonnet call [A] | | $0.177 | $17.71 | 77% over |
| **B. Sonnet 5.5 in all four roles (current default)** | $0.0332 | **$0.166** | $16.60 | 66% over |
| B + 50% cached input [A] | | $0.109 | $10.90 | 9% over |
| B + 200 thinking tokens on every call [A] | | $0.206 | $20.60 | 2× |
| B + 500 thinking tokens on every call [A] | | $0.266 | $26.60 | 2.7× |
| B + 50% cached + 200 thinking/call [A] | | $0.149 | $14.90 | 49% over |
| B with Jev doing planner + classifier [A], no caching | | $0.126 | $12.56 | 26% over |
| B with Jev doing planner + classifier, 50% cached on the Sonnet calls [A] | | $0.083 | $8.29 | under |
| GPT-5.6 Terra in all four roles | $0.0350 | $0.175 | $17.52 | 75% over |
| Gemini 3.8 Flash in all four roles, price to 2026-12-31 | $0.0124 | $0.062 | $6.22 | under |
| Gemini 3.8 Flash, price from 2027-01-01 (doubles) | | $0.125 | $12.45 | 25% over |

How B's base number is built [C]: per turn input 12,000 × $2/M = $0.024; output 920 × $10/M = $0.0092; total $0.0332;
× 5 = $0.166. The classifier alone on Sonnet is 1,000 × $2/M + 20 × $10/M = $0.0022/turn ($0.011/conversation); the
planner is $0.006/turn ($0.030/conversation). The specialist + responder are 75% of the cost.

**What drives it.** Input tokens on Sonnet (72% of scenario B), then thinking. Caching the stable prefix (system prompt,
tool list, KB instructions) is the cheapest lever: a Sonnet 5.5 cache hit costs 5% of input. Thinking is the biggest
unknown: it is on by default at `high` effort and billed as output; it is not stated how many tokens it adds for our
prompts, so it must be measured from `usage.output_tokens` in SP-1.

### 2d. The other SP-1 candidates

| Model | Price /MTok (standard) | Cached input | Context | Max output | Source |
|---|---|---|---|---|---|
| OpenAI GPT-5.6 Terra (`gpt-5.6-terra`) | $2.00 in / $12.00 out (≤272K input); $4.00 / $18.00 above 272K | $0.20 (≤272K) | 1,050,000 | 128,000 | S-217 |
| Google Gemini 3.8 Flash (`gemini-3.8-flash`), "Our most intelligent Flash model" | $0.75 in / $3.75 out (incl. thinking) through 2026-12-31; $1.50 / $7.50 from 2027-01-01; no >200K tier listed | $0.075 (then $0.15) + storage $0.50/MTok/hour | Not stated on the models page; 1,048,576 per OpenRouter (S-219) | Not stated (model detail page) | S-218 (page "Last updated 2026-10-19 UTC") |

- GPT-5.6 Terra standard rate limits (S-217): Build 5,000 RPM / 1,000,000 TPM; Launch 10,000 / 4,000,000; Grow 15,000 /
  40,000,000. Our OpenAI tier: not known (OpenAI console).
- Gemini 3.8 Flash is listed as "Stable", "New Stable" (S-218 models page). Its rate limits: not read (Gemini rate-limit page).
- **OpenRouter (S-219, S-220).** The project's OpenRouter key could reach all three. Listed prices per token, converted to
  /MTok: `openai/gpt-5.6-terra` $2 / $12 (plus other endpoints at $1/$6, $2.20/$13.20 via Azure and Bedrock, and $4/$24 —
  OpenRouter's JSON does not label which tier each is); `google/gemini-3.8-flash` headline $0.825 / $4.125, with Google
  endpoints at $0.75 / $3.75 and others at $0.375/$1.875 and $1.35/$6.75 (tiers unlabelled); `anthropic/claude-sonnet-5.5`
  $2 / $10 (Anthropic endpoint), $2.20 / $11 on some Google and Azure endpoints. OpenRouter states "there is no markup on
  inference pricing"; its credit-purchase fee is not stated on the FAQ page (the text is an unrendered placeholder; it
  would be on the pricing or billing page). BYOK above $25,000/month carries a 5% fee.

### 2e. Jev (TypeSafe AI), the fourth candidate

Sources: S-222 https://typesafe.ai and https://typesafe.ai/blog/introducing-system-one-models-and-jev · S-223
https://docs.typesafe.ai/models, /introduction, /introduction/quickstart, /concepts/system-one,
/model-jaggedness/jev-1.13, /primitives/choice · S-224 https://typesafe.ai/legal/privacy-policy,
https://typesafe.ai/legal/terms, https://typesafe.ai/legal/mca, https://typesafe.ai/legal/data-processing,
https://docs.typesafe.ai/legal · S-219 OpenRouter endpoints · S-221 OpenRouter privacy docs · S-225 third-party
articles · S-226 "Open Jev" repositories. All read 2026-10-20.

**What it is.** A "System One" model that "returns typed decisions with calibrated probabilities" instead of text
(S-222). One endpoint, `POST https://api.typesafe.ai/v1/systemone`, `Authorization: Bearer <key>`; the request sends a
`state` (text or JSON) and `questions` of type `choice`, `score` or `noul` (a 0–1 yes/no); the answer per question is
`choice` + `confidence` + `probabilities` (S-223 quickstart).

**Access.** Early access: "Try our first System One Model, Jev, in early access"; the company is "bringing developers
off the waitlist as quickly as we can" (S-222). API keys come from `console.typesafe.ai/keys` (S-223). Also on
OpenRouter as `typesafe/jev-1.13` and `typesafe/jev-1.14` (S-219). **No self-hosted "Open Jev" from TypeSafe:** the
"Open Jev" repositories found are community re-implementations, one of them stating it is "not affiliated with Jev"
(S-226); MindStudio describes Open Jev as "an open-source implementation of the same choice/score/null classification
pattern" (S-225). TypeSafe's own open repo `system-one-adapter-python` is a "Drop-in TypeSafeClient replacement backed by
LLM APIs", not Jev's weights (S-226).

**Models and price (S-223 models page).** Jev 1.14 (`jev-1.14.0`, "available from October 14, 2026") and Jev 1.13
(`jev-1.13.0`); both $42 per billion = **$0.042 per million input tokens; "Output tokens are free"**. Alias `jev-latest`
→ 1.13.0, `jev-preview` → 1.14.0. OpenRouter lists both at prompt $0.000000042/token, completion 0 (S-219). The launch
post: "We can't prove it isn't subsidized" (S-222). [C] A 1,000-token classifier call costs $0.000042; 5 per conversation
= $0.00021.

**Latency.** Vendor-reported only: "End-to-end response time is 70ms-500ms", with evals "generally run from our laptops
on the West Coast" (S-222). Not measured by us. OpenRouter shows no recent latency for either endpoint (`null`, S-219).

**Limits (S-223).**
- No generated text: "System One models do not write replies, produce code, or generate explanations of their reasoning."
- Choice cap: "A Choice question accepts up to 255 options" (S-223 choice page; the launch post says "a cardinality up
  to 255", S-222).
- Context: 64k per request / 32k per question by default; 262k with the `TypeSafe-Danger-Zone-Long-Context: true`
  header, which is "slower and less accurate". OpenRouter lists `context_length` 262,144 for both endpoints (S-219);
  Equinox recorded `max_prompt_tokens` 32,000 on 2026-10-11, so this field has changed since.
- Documented weaknesses, "Jev 1.13 jaggedness", "Last reviewed 2026-10-02": "Jev is not a calculator"; it "does not count
  reliably"; it "reads dates as text, not as ordered quantities. Asking which of two dates comes first … is unreliable";
  also literal reading, indirection, large state, choice-order bias ("leans toward the option that comes first"), and
  adversarial content ("State is data, and `jev-1.13` does not treat it as hostile by default"). English is the primary
  training language. Text input only.
- Third-party report: in an independent evaluation "a single planted sentence changed Jev's answer on 73.5% of tickets"
  (Pulumi post, S-225; secondary, not verified by us).

**Privacy and data use (re-checked 2026-10-20 at the coordinator's request).**
- Prompts go to an external endpoint (`api.typesafe.ai`, or OpenRouter then TypeSafe). Region: not stated by TypeSafe
  (would be in the DPA annex or the subprocessor list at `trust.typesafe.ai/subprocessors`, not read); OpenRouter's
  provider record has `headquarters: null`, `datacenters: null` (S-221).
- **Training on inputs: now excluded in writing.** Privacy Policy ("Last updated Nov 19, 2025"): "We will not train or
  fine tune any artificial intelligence or machine learning models on your prompts or other Input." Master Customer
  Agreement ("Last updated Sep 23, 2026") §4.1: TypeSafe "will not, include Customer Data in a dataset used to train
  (i.e., to modify the model weights of) any artificial intelligence or machine learning models without Customer's prior
  consent." Models page: "Jev is not trained on customer requests or responses." (S-223, S-224)
- **Retention period: still not stated.** Privacy Policy: "We retain personal data about you for as long as reasonably
  necessary to provide you with the Services, or otherwise in support of our business or commercial purposes." MCA §4.1(c)
  grants a licence "in perpetuity" to use Customer Data "to derive and generate Telemetry", for fraud and abuse
  monitoring, and for legal compliance; §10.3: TypeSafe "may delete Customer Data at any time in its sole discretion" and
  may keep it "in TypeSafe's standard backups". Zero data retention exists only "for enterprise customers. Contact
  sales@typesafe.ai" (S-224).
- **"Improve the service" carve-out remains, via telemetry.** MCA §4.3: Telemetry includes "summary statistics and
  classifications, metrics, and learnings related to Customer's use of the Services. TypeSafe may Process Telemetry
  without restriction, including to improve the Services". (The site Terms of Use, "Last updated Sep 19, 2026", cover the
  website and Feedback, not API inputs.)
- **Which terms apply through OpenRouter.** The MCA and DPA are TypeSafe's customer contracts; a call through OpenRouter
  makes OpenRouter the customer. OpenRouter's provider record for TypeSafe links only the Privacy Policy and the site Terms
  of Use, and the endpoint's `data_policy` field is `null` (S-219, S-221).
- **OpenRouter's own policy (S-221).** "OpenRouter does not store your prompts or responses, unless you opt in"; it
  stores metadata (token counts, latency). Account settings can block providers that train; per request,
  `provider.data_collection: "deny"` uses "only providers which do not collect user data" and `zdr: true` routes "only to
  endpoints that have a Zero Data Retention policy". OpenRouter "doesn't route based on provider retention policies".
  Whether the TypeSafe endpoint passes `deny` or `zdr` is not stated (its `data_policy` is `null`); a test call with
  those flags would show it.
- **Against our bar (PRD §5, audit L-9: "paid model APIs whose terms exclude training on inputs").** [C] The training
  half passes on TypeSafe's own documents read today. Equinox's check of 2026-10-11 found no such exclusion; the MCA
  wording is dated 2026-09-23 and the Privacy Policy 2025-11-19, so that check most likely read only the site Terms of
  Use, which cover the website and Feedback, not API inputs (not confirmed). It does not meet a stricter reading: no retention period, a perpetual telemetry licence with an
  "improve the Services" use, ZDR enterprise-only, and through OpenRouter no `data_policy` record.

**What this means for the design.** Default Sonnet 5.5 everywhere costs about $0.17 per conversation before thinking,
66% over the $0.10 budget [C]. Prompt caching of the stable prefix is required, effort must be set low for chat-style
roles, and SP-1 must measure thinking tokens. Gemini 3.8 Flash is the only full-stack candidate under budget, and only
until its price doubles on 2027-01-01. Jev could take two narrow decisions where a fixed answer set is natural: the
**planner's talk/act choice** and the **HP-2 danger classifier, used raise-only** (Jev can escalate to a human, never
clear a case; dates, counts and amounts are computed in code before it is asked). It saves about $0.04 per conversation
[C] but adds an external endpoint for raw caller text, so it needs PII redaction before the call and Innocent's call on
the retention gap.

---

## 3. SD-5.6 Concurrency at the pinned versions (target ~20 concurrent conversations, one instance)

Sources: S-197 https://fastapi.tiangolo.com/async/ · S-198 https://anyio.readthedocs.io/en/stable/threads.html · S-199
`starlette` 1.9.0 `concurrency.py`, `fastapi` 0.156.4 `routing.py`, `anyio` 4.15.1 `_backends/_asyncio.py` (installed
source) · S-200 https://uvicorn.dev/settings/ · S-201 https://docs.langchain.com/oss/python/langgraph/checkpointers and
https://docs.langchain.com/oss/python/langgraph/persistence · S-202 `langgraph-checkpoint-sqlite` 3.1.2 source
(`langgraph/checkpoint/sqlite/__init__.py`, `aio.py`) · S-203
https://docs.python.org/3.12/library/asyncio-task.html#asyncio.to_thread · S-204 `onnxruntime` v1.31.0
`onnxruntime/python/onnxruntime_pybind_state.cc` and `fastembed` 0.9.0 source. All read 2026-10-20.

**Uvicorn workers (S-200).** `--workers`: "Number of worker processes. Defaults to the `$WEB_CONCURRENCY` environment
variable if available, or 1." `--limit-concurrency`: "Maximum number of concurrent connections or tasks to allow, before
issuing HTTP 503 responses" (no default listed). Pinned source: `self.workers = workers or 1` (`uvicorn/config.py`).

**Sync vs async endpoints (S-197, S-199).** FastAPI: "When you declare a path operation function with normal `def`
instead of `async def`, it is run in an external threadpool that is then awaited, instead of being called directly (as
it would block the server)." An `async def` endpoint runs on the event loop itself, so any blocking call inside it stops
every other request on that worker. Pinned source: Starlette's `run_in_threadpool` is `anyio.to_thread.run_sync(func)`.

**Threadpool size (S-198, S-199).** "The default AnyIO worker thread limiter has a value of 40". Pinned source:
`CapacityLimiter(40)` in `anyio/_backends/_asyncio.py`.

**LangGraph checkpointers (S-201, S-202).**
- `SqliteSaver` (sync): "meant for lightweight, synchronous use cases (demos and small projects) and does not scale to
  multiple threads". It guards its connection with a `threading.Lock()` and is opened with `check_same_thread=False`.
  Its async methods raise `NotImplementedError` ("The SqliteSaver does not support async methods. Consider using
  AsyncSqliteSaver instead."), so it cannot back `graph.ainvoke`.
- `AsyncSqliteSaver` (needs `aiosqlite`, pinned 0.22.1): uses an `asyncio.Lock()`; its sync methods raise
  `asyncio.InvalidStateError` if called from the event-loop thread. Its docstring: "not recommended for production
  workloads due to limitations in SQLite's write performance … consider a more robust database like PostgreSQL."
- Docs: SQLite is "Ideal for experimentation and local workflows"; Postgres "Ideal for using in production"; with
  `.ainvoke`/`.astream`, "asynchronous versions of the above methods will be used", so use `AsyncSqliteSaver` or
  `AsyncPostgresSaver`.
- Does the sync saver block the event loop? It blocks whichever thread calls it. In a `def` endpoint that is a pool
  thread (fine). In an `async def` endpoint it is the event loop (blocks everything).

**CPU-bound local embedding (S-203, S-204).** Python: "Due to the GIL, asyncio.to_thread() can typically only be used to
make IO-bound functions non-blocking. However, for extension modules that release the GIL … asyncio.to_thread() can
also be used for CPU-bound functions." ONNX Runtime 1.31.0's Python `run` wraps inference in `py::gil_scoped_release`
with the comment "release GIL to allow multiple python threads to invoke Run() in parallel." fastembed 0.9.0's
`TextEmbedding` takes `threads` (sets ONNX `intra_op_num_threads`/`inter_op_num_threads`) and `embed(…, parallel=…)`
("If > 1, data-parallel encoding will be used, recommended for offline encoding of large datasets"). So a query
embedding can run in a thread (`asyncio.to_thread` or a `def` endpoint) without holding the GIL during inference.

**The current code (read 2026-10-20, not edited).** `src/meridian/web/app.py` declares `async def api_chat(...)` and calls
`graph.handle(tid, text)` synchronously. `graph.handle` runs the sync Anthropic client (`anthropic.Anthropic()`), the sync
`SqliteSaver`, and fastembed. **[C]** On one Uvicorn worker, every chat turn therefore blocks the event loop for the whole
turn (four model calls in sequence); 20 concurrent conversations would be served one turn at a time, and `/healthz`
would also wait.

**Rate-limit headroom for 20 conversations [C].** [A] each active user sends a message every 30 s; 4 calls per turn.
20 × 2 turns/min × 4 = 160 RPM (limit 1,000 [M]); input 20 × 2 × 12,000 = 480,000 ITPM if all on Sonnet (limit 2,000,000
[M]); output 36,800 OTPM plus thinking (limit 400,000 [M]). Rate limits are not the bottleneck at this scale.

**What this means for the design.** Either change `api_chat` to a plain `def` (FastAPI runs it in the 40-thread pool;
sync `SqliteSaver` serialises its writes behind its lock but releases the pool between calls), or go fully async
(`AsyncAnthropic`, `graph.ainvoke`, `AsyncSqliteSaver`, fastembed via `asyncio.to_thread`). The first is the smaller
change and is enough for ~20 conversations; either way it needs a load test (SP) at 20 concurrent threads, measured, not
assumed. Keep one Uvicorn worker while state lives in SQLite files on one volume.

---

## 4. SD-6.3 Model API errors and retries

Sources: S-190 https://platform.claude.com/docs/en/api/errors · S-189 https://platform.claude.com/docs/en/api/rate-limits ·
S-196 `anthropic` 1.17.0 source, `src/anthropic/_constants.py`, `_base_client.py`, `_exceptions.py`
(https://github.com/anthropics/anthropic-sdk-python/blob/v1.17.0/src/anthropic/_constants.py). All read 2026-10-20.

| HTTP | `error.type` | Meaning (S-190) | SDK class (S-196) | SDK retries? |
|---|---|---|---|---|
| 400 | `invalid_request_error` | bad request; also returned when usage reaches a spend limit **you** set | `BadRequestError` | no |
| 401 | `authentication_error` | key malformed, revoked or expired | `AuthenticationError` | no |
| 402 | `billing_error` | billing or payment problem | `APIStatusError` | no |
| 403 | `permission_error` | key lacks permission | `PermissionDeniedError` | no |
| 404 | `not_found_error` | unknown resource or model | `NotFoundError` | no |
| 409 | `conflict_error` | resource-state conflict | `ConflictError` | **yes** |
| 413 | `request_too_large` | over 32 MB for Messages | `RequestTooLargeError` | no |
| 429 | `rate_limit_error` | rate limit, **or** the tier's monthly spend cap | `RateLimitError` | yes |
| 500 | `api_error` | internal error; "Retry the request with exponential backoff" | `InternalServerError` | yes |
| 504 | `timeout_error` | request timed out while processing; consider streaming | `DeadlineExceededError` | yes |
| 529 | `overloaded_error` | "The API is temporarily overloaded" (high traffic across all users) | `OverloadedError` | yes |

- **`retry-after`** (S-189): "The number of seconds to wait until you can retry the request. Earlier retries will fail.
  Not every 429 carries it; the spend-cap 429 never does." Other headers: `anthropic-ratelimit-requests-*`,
  `-tokens-*`, `-input-tokens-*`, `-output-tokens-*` (limit, remaining, reset in RFC 3339).
- Sharp traffic increases can produce 429s from "acceleration limits" even under the per-minute limits (S-190).
- **SDK defaults, `anthropic` 1.17.0 (S-196):** `DEFAULT_MAX_RETRIES = 2` (3 attempts in all);
  `DEFAULT_TIMEOUT` 600 s total, 5 s connect; `DEFAULT_CONNECTION_LIMITS` 1,000 connections, 100 keep-alive. Retries on
  connection errors, 408, 409, 429 and every status ≥ 500, and obeys a server `x-should-retry: true|false` header.
  Backoff: `min(0.5 × 2^n, 8.0)` seconds × a jitter factor between 0.75 and 1.0. If the response carries
  `retry-after-ms` or `retry-after`, it waits exactly that long, capped only at 4,294,967 s (no 60-second ceiling).
  Timeouts are retried too. Errors docs: the SDK retries "twice by default, honoring the `retry-after` header when
  present", configurable with `max_retries` (S-190).

**What this means for the design.** The SDK already retries 429/5xx/529 twice. Our code adds a per-turn deadline (the
caller is waiting) rather than more retries: set a client `timeout` well below 600 s and `max_retries` per role, then
fall back to a handoff message when a turn cannot finish. Treat a 429 with no `retry-after` as the spend cap (no retry
will work until the 1st), and a 400 "spend limit" as our own cap. Errors inside a stream arrive after HTTP 200 and need
their own handling.

---

## 5. SD-7.4 Railway pricing

Sources: S-205 https://docs.railway.com/reference/pricing/plans · S-206 https://docs.railway.com/reference/volumes. Read
2026-10-20; no "last updated" date shown on either page.

- Plans: Free $0, Hobby **$5/month** (includes $5 of resource usage), Pro $20/month (includes $20), Enterprise custom.
- Resource prices: RAM **$10 per GB per month** ($0.000231/GB/minute); CPU **$20 per vCPU per month**
  ($0.000463/vCPU/minute); network egress $0.05/GB; **volume storage $0.15 per GB per month**. Volumes are "billed at a
  rate per GB / minutely"; volume metadata uses "roughly 2-3% of total storage". Railway storage buckets (used by its
  Langfuse guide) are "$0.015 per GB per month with free egress" (S-207).
- Hobby per-service limits: 6 replicas, 48 GB RAM, 48 vCPU, 100 GB ephemeral storage, **5 GB volume**, 100 GB image.
  Pro: 1 TB volume (self-serve; the volumes page says 50 GB by default).
- Volumes: "Each service can only have a single volume"; "Replicas cannot be used with volumes"; expect "a small amount
  of downtime when re-deploying a service that has a volume attached". Backup availability by plan: not stated on the
  volumes page (in Railway's backups guide).

**What this means for the design.** The app keeps SQLite (checkpoints, the DB copy, our tables) on one volume, so it
runs as one replica and redeploys cause a short outage. Storage is cheap (5 GB ≈ $0.75/month [C]); RAM is what costs
money. The Hobby 5 GB-per-volume cap matters more for Langfuse than for the app.

---

## 6. Langfuse self-hosted inside our Railway project

Sources: S-209 https://langfuse.com/self-hosting and https://langfuse.com/self-hosting/deployment/docker-compose · S-210
https://langfuse.com/self-hosting/upgrade/upgrade-guides/upgrade-v3-to-v4 · S-211
https://langfuse.com/self-hosting/deployment/railway · S-212 https://langfuse.com/docs/compatibility · S-213
https://github.com/langfuse/langfuse/releases, https://raw.githubusercontent.com/langfuse/langfuse/main/docker-compose.yml,
https://pypi.org/pypi/langfuse/json · S-207 https://docs.railway.com/guides/langfuse-llm-observability and
https://railway.com/deploy/langfuse · S-208 https://railway.com/deploy/langfuse-v3 · S-214
https://langfuse.com/integrations/frameworks/langchain · S-215 https://langfuse.com/docs/observability/features/masking ·
S-216 https://langfuse.com/integrations/model-providers/anthropic. All read 2026-10-20.

**Current version.** The self-hosting docs are "Version: v4" (S-209); the latest server release is **v4.66.0**, published
2026-10-20 (S-213). The latest Python SDK is **5.0.3** (2026-10-20); latest 4.x is 4.18.0 (2026-10-14) (S-213).

**Services it needs (S-209, S-210).** Six: **Langfuse Web** (UI + APIs), **Langfuse Worker** (async event processing),
**PostgreSQL** (≥15, 16 recommended), **ClickHouse** (≥25.12, 26.4 recommended for v4), **Redis/Valkey** (≥7.0, 7.2
recommended), and **S3/blob storage** (raw events, attachments). An LLM API is optional (playground, evals). The
official compose file runs `langfuse:4`, `langfuse-worker:4`, `clickhouse-server:25.12`, MinIO, `redis:7` with
`--maxmemory-policy noeviction`, and `postgres:17` (S-213). "Fresh installs need none of the above [migration steps]:
deploy Langfuse v4 following the regular guides" (S-210).

**Minimum resources.** The self-hosting overview gives none. The Docker Compose page: "We recommend that you use at
least 4 cores and 16 GiB of memory … choose a sufficient amount of storage, e.g. 100GiB", and compose "lacks
high-availability, scaling capabilities, and backup functionality" (S-209). Railway's official template page: minimum
"2 vCPU, 4 GB RAM", storage 10 GB Postgres, 20 GB ClickHouse, 10 GB MinIO; recommended "4+ vCPU, 8–16 GB RAM" (S-207).

**Railway templates: all deploy v3.**
- Railway's own guide and template (`railway.com/deploy/langfuse`, creator "Heimdall", 14 deploys): `langfuse/langfuse:3`,
  `langfuse/langfuse-worker:3`, `clickhouse/clickhouse-server:24`, Postgres 18, Redis 8.2.1, MinIO; six services;
  run one ClickHouse with `CLICKHOUSE_CLUSTER_ENABLED=false`; `ENCRYPTION_KEY` "must be exactly 64 hex characters";
  monthly cost not stated (S-207).
- Langfuse's Railway page: "The Railway template currently deploys **Langfuse v3**", "maintained outside the Langfuse
  organization … support is best-effort"; for v4 use another option (S-211).
- Community "langfuse v3" template (INAPP, 3 deploys) claims "roughly $8.50/mo on Railway's Hobby plan" for ~2.2 GB
  memory (S-208). Its per-service figures ($2/month for 512 MB) do not match Railway's $10/GB/month (S-205); [C] 2.2 GB
  alone is $22/month.
- **Version trap (S-212).** "Python SDK v5 requires … self-hosted Langfuse v4.59.0+"; "Python SDK v5 and JS/TS SDK v6
  require Langfuse v4". Python SDK v4 works against a v3 server ≥ 3.63.0 for tracing. So a v3 Railway template pairs with
  `langfuse` 4.x; the current SDK 5.0.3 needs a v4 server, which needs ClickHouse ≥ 25.12 (the official Railway template
  ships ClickHouse 24). Langfuse v3 gets security patches "until end of January 2027" (S-210).

**Rough monthly cost on Railway [C]** (prices from S-205; usage-based, so actual draw decides):

| Case | RAM [A] | CPU avg [A] | Volumes [A] | Monthly [C] |
|---|---|---|---|---|
| Low: the community template's own memory estimate | 2.2 GB → $22 | 0.3 vCPU → $6 | 5 GB → $0.75 | **≈ $29** |
| Middle: Railway template minimum RAM, light CPU | 4 GB → $40 | 0.5 vCPU → $10 | 5 GB → $0.75 | **≈ $51** |
| High: Railway template minimum, fully used | 4 GB → $40 | 2 vCPU → $40 | 5 GB → $0.75 | **≈ $81** |
| Langfuse's compose recommendation (16 GB, 4 cores), fully used | 16 GB → $160 | 4 vCPU → $80 | 100 GB → $15 | ≈ $255 (and over Hobby's 5 GB volume cap) |

[C] The middle case is about $1.70/day, on top of the $10/day model budget, and above Hobby's $5 included usage.
Measure the real draw for a day on Railway's usage page before quoting a number.

**LangGraph integration (S-214, S-216).**
- `from langfuse.langchain import CallbackHandler`; `langfuse_handler = CallbackHandler()` ("No constructor args");
  pass `config={"callbacks": [langfuse_handler]}` to `graph.invoke(...)`. Session and user go in the invocation
  metadata as `langfuse_session_id` and `langfuse_user_id`, or via `propagate_attributes(user_id=…, session_id=…)`.
  Env vars: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` (the page does not mention
  `LANGFUSE_HOST`). The page targets Python SDK v5 ("Python SDK v5 requires `langchain-core>=1`"; pinned
  `langchain-core` is 1.6.12).
- Our nodes call the Anthropic SDK directly, not a LangChain chat model. The callback handler sees graph and node spans;
  for the model calls themselves Langfuse documents `opentelemetry-instrumentation-anthropic`'s
  `AnthropicInstrumentor().instrument()`. Whether that captures token usage and cost is not stated on the page (S-216);
  check in the first traced run.

**Masking before sending (S-215).** Client-side, in our process: pass a hook to the Langfuse client. "For new Python SDK
setups, prefer `mask_otel_spans`" (keyword-only `params`, runs "at the export stage … usually … on the OpenTelemetry
batch span processor worker thread"); the legacy `mask` (keyword-only `data`) "runs synchronously when Langfuse SDK
attributes are created" and "applies only to data set through Langfuse SDK APIs". Examples on the page redact card-like
numbers, emails and phone numbers. No server-side masking feature is described; an OpenTelemetry Collector can redact,
but "Collector-side masking happens after telemetry leaves the application".

**What this means for the design.** Self-hosting is six services, not one, and every Railway template found deploys v3.
Two workable paths: (a) the Railway v3 template with `langfuse` 4.x pinned (quick; v3 is patched to January 2027), or
(b) v4 from the official images with ClickHouse ≥ 25.12 (current SDK, more setup). Either way, ClickHouse wants more than
Hobby's 5 GB volume over time, so set a short trace retention. Redaction (R-36) must run in our process through
`mask_otel_spans` and also cover the direct-Anthropic instrumentation spans, tested with seeded names and numbers.

---

## Risks found

1. **Cost per conversation is over budget by default.** Sonnet 5.5 in every role ≈ $0.166/conversation [C] before any
   thinking tokens (66% over $0.10); with 200 thinking tokens per call ≈ $0.21 [C]. It gets under $0.10 only with prefix
   caching plus a cheaper path for the planner and classifier (Haiku 5.5, Jev or Gemini Flash), or lower effort, measured
   in SP-1.
2. **Thinking is on by default and unmeasured.** It is billed as output and counts toward `max_tokens`; the current call
   uses `max_tokens=900` at the default `high` effort, so replies can be cut off (`stop_reason: max_tokens`).
3. **Forced tool use 400s on Sonnet 5.5.** Any classifier written with `tool_choice: {"type": "tool"}` breaks when the
   default model is Sonnet 5.5.
4. **The chat endpoint blocks the event loop.** `async def api_chat` calls the sync graph, so one worker serves one turn
   at a time; 20 concurrent conversations would queue.
5. **SQLite checkpointer is documented as demo-grade.** Both SQLite savers say they are not for production; fine for one
   instance at ~20 conversations if load-tested, not beyond.
6. **Spend-cap 429.** At Start tier [C from M] the org cap is $500/month; reaching it stops every call until the 1st with
   no `retry-after`. Eval runs and demo traffic share that cap.
7. **SDK honors any `retry-after` with no ceiling** (1.17.0), so a long server-sent wait can stall a caller's turn unless
   we set our own per-turn deadline.
8. **Langfuse needs more than expected.** Six services; Railway templates are v3 while current docs and SDK are v4/v5;
   ClickHouse 24 in the official template is below v4's 25.12 minimum; ≈ $29–$81/month [C]; template storage minimums
   (20 GB ClickHouse) exceed Hobby's 5 GB per volume.
9. **Jev's data terms are better than on 2026-10-11 but not clean.** Training on inputs is now excluded in writing; no
   retention period, a perpetual telemetry licence used "to improve the Services", ZDR enterprise-only, and OpenRouter
   shows no `data_policy` for the route. Vendor latency and price are unverified by us; it is weak at dates, counts and
   adversarial text, which are exactly what a danger classifier sees, so raise-only use is the safe shape.
10. **Gemini 3.8 Flash's price doubles on 2027-01-01**, so a cost case built on it expires after the challenge.
