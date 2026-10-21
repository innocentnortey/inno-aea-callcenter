# System Design Readiness — inno-aea-callcenter (Meridian AI service agent)

**Last audited:** 2026-10-20 (after SP-1 closed and Innocent's 2026-10-21 chat decision on the model mix and latency line)
**Verdict:** **READY.** Every required item is Found, Decided, Assumed (Measure items only, each with the test that replaces it) or N/A. Nothing is Missing.
**Gates:** interview complete **yes** (`interview.py check --complete`: 60/60 items, gate holds) · design ready **READY** · ticket ready **no** (all seven outputs are `planned`; `design_outputs.py --gate tickets` will fail until DO-1…DO-7 are written and approved). The four gates are kept separate (`DESIGN-OUTPUTS.md`).
**Design outputs register:** [`docs/prd/inno-aea-callcenter-interview.md#design-outputs`](../prd/inno-aea-callcenter-interview.md#design-outputs) (`design_outputs.py check … --gate readiness`: "register holds at the readiness gate (structure)").
**Checklist:** `Gauntlet AI/.claude/skills/system-design-readiness/CHECKLIST.md` (60 items)
**Sources read:** issued briefing `docs/source/aea-call-center-briefing.md`; PRD 0.4 `docs/prd/inno-aea-callcenter-prd.md` (§4, §5, §6, §8, §10); interview `docs/prd/inno-aea-callcenter-interview.md` (coverage table, observability map, Q-061, Q-062, batch log); spike `docs/analysis/spikes/SP-1-two-layer-turn-latency-cost.md` §1–§4 and its run records on the VPS (`var/sp1-runs/*-B-live-*.json`, read over SSH 2026-10-20); research `docs/research/2026-10-20-vendor-and-framework-facts.md`; framing `docs/delivery/2026-10-20-angle-and-demo-framing.md` §2; consolidated direction §10; hard-problems GP walk; brief audit (C-1, D-5, D-9, G-9, L-9); `SUBMISSION.md`; `.claude/rules/verification-evals-observability.md` rules 18–21; `docs/source/source-register.md`.

**How this report was built.** The interview's *Checklist coverage* table already dispositions all 60 items. This run
did not redo that sweep. It (1) spot-verified the citations of every Core and AI item against the source they name,
(2) replaced six `assumed` Measure items with SP-1's measurements where SP-1 actually measured them, and (3) checked
the one new dependency that option B put on the request path (Jev through OpenRouter). Item-level evidence for every
row not discussed below is in the interview's coverage table and is not repeated here.

## Hardest uncertainty and depth

**SD-1.9 (Innocent, 2026-10-20, PRD §10):** "that every number we report is honest: correct answers, correct escalations, no stale-document answers".

| Step | Depth | Why |
|---|---|---|
| 1 Frame | full | Always |
| 2 Promises | full | SD-1.9: correctness and safety promises are what is graded |
| 3 Workload | light | ~100 conversations/day, ~20 at once [T]: one instance, no queue (GP-108) |
| 4 Logical flow | full | HP-1 two-layer turn; model decision points and half-success must be explicit |
| 5 Resource demand | light | SP-1 measured it; cost is under a tenth of the cap |
| 6 Overload and failure | full | Safety-critical: every failure ends in a handoff |
| 7 Deployment | light | One Railway service; survive a restart (SD-7.2) |
| 8 Validation | full | SD-1.9: every reported number honest |

Which tiers apply: Core ✓ · Full (steps 1, 2, 4, 6, 8; plus the Full items of steps 3, 5, 7 at light depth) · AI ✓ · Legacy ✗ (greenfield; SD-4.6 N/A)

## 1. Go find — blocks the design

None.

One External gap was found and closed in this run, so it does not appear here: option B (decided after the research
note was written) puts **Jev through OpenRouter** on every turn's request path, but the research note covers only
Anthropic's errors and rate limits. OpenRouter's error and limit pages were read 2026-10-20 and registered as S-229 and
S-230 (see SD-5.5 and SD-6.3 below).

## 2. Decide — closed in the interview

None open. All five foundation answers are Innocent's, recorded in PRD §10: SD-3.1 (~100/day, written 10× path,
Q-029 = A), SD-3.4 (about 20 at once), SD-7.2 (survive a restart), SD-1.6 ($30/day model cap, Railway existing plan,
VPS Langfuse; Q-061, Q-062), SD-1.9 (honest numbers). Decisions taken since the interview, now recorded:

| ID | Question | Decision | Recorded in |
|---|---|---|---|
| SD-2.3 | Latency line per turn | **p95 ≤ 12.5 s at 20 conversations at once** (was 8 s [A]); Innocent, 2026-10-21, after SP-1 measured option B at 10.2 s [M] | PRD §5 *Latency*; SP-1 §4 |
| SD-5.3 / Q-040 | Model mix | **Option B:** Jev (`typesafe/jev-1.13` via OpenRouter) for planner and danger classifier; Sonnet 5.5 for specialists, responder and brief. Jev's unstated retention accepted as a known limit; raw caller text reaches it only after redaction | PRD §6.2 *Models*; SP-1 §4 |

Left to the design itself (not decisions for Innocent): where per-turn timing starts and stops (Q-016 → DO-1/DO-6),
operational status values (Q-022 → DO-6), timeout and retry values (SD-6.2 → DO-1/DO-4), load-test tool (SD-8.3 → DO-5).

## 3. Assumptions — replaced by measurement later

| ID | Assumed value | Basis for the guess | Test that replaces it |
|---|---|---|---|
| SD-7.3 | One Railway replica holds 20 conversations at once inside p95 ≤ 12.5 s | SP-1 held 20 at once **in one process on the VPS** at p95 10.2 s [M]; not yet on a Railway replica | Stage 9 20-conversation load test against the deployed Railway service (GP-113, GP-118) |
| SD-3.2 (length only) | Real conversations are longer than SP-1's 2.6 turns | SP-1's conversations are scripted worked pairs and short by design | Turns per conversation from the first eval run on the ~60 transcript cases, then the monitoring page |

## 4. Full audit

Statuses for all 60 items: the interview's coverage table (52 answered = Found or Decided, 6 assumed, 2 N/A) as of
batch 8. This run changes the rows below. **Changed by SP-1** (all [M] = measured; option B unless stated; n = 73
conversations, 192 turns: 3 one-at-a-time passes + 2 runs of 20 at once, matching SP-1 §3; per-call aggregates
computed by this audit from the VPS run records).

| ID | Status | Evidence | Note |
|---|---|---|---|
| SD-2.3 | **Decided** (changed) | PRD §5 *Latency*: p95 ≤ 12.5 s at the 20-conversation spike [Decided, Innocent 2026-10-21]; SP-1 §4 | The interview's coverage row said 8 s; corrected in the interview this run. Start/stop points: DO-1 (Q-016). SP-1 timed "wall-clock per customer turn" in the harness |
| SD-3.2 | **Found [M]** (was assumed) | SP-1 run records: **2.63 turns per conversation**; **3.34 model calls per turn** (p95 5), excluding the brief call | Scripted conversations; real length is the §3 assumption above. At ~100 conversations/day ≈ 260 turns ≈ 870 model calls/day [C] |
| SD-3.3 | **Found [M]** (was assumed) | Model-call mix per 192 turns: planner 129, classifier 129 (Jev, in parallel), specialist 225, responder 159, brief 28 (Sonnet). Tool calls **1.82 per turn** (max 5): kb_search 84, account_read 70, identity locate/send/verify 35 each, case_create 47, slot_search 22; writes book 7, reschedule 7, change_request 7. Topic mix of real calls: inventory §3.1 (booking 31.4%, billing 16.0%, …) [M on the 420 issued calls] | The SP-1 mix is the worked pairs' mix, not live traffic; the monitoring page's volume by topic replaces it after launch |
| SD-5.1 | **Found [M], upper bound** (was assumed) | Non-model time per turn (turn wall time minus the parallel planner/classifier call minus the sequential Sonnet calls): **p50 0.003 s, p95 0.05 s** | CPU was not sampled separately; this residual bounds code gates, retrieval, embedding and SQLite together. Model wait dominates (Sonnet call 1.2–1.9 s p50; Jev 0.2 s p50, 0.4 s p95; SP-1 §3) |
| SD-5.2 | **Found [M]** (was assumed) | 1.82 tool calls per turn, each one or a few SQLite reads; 21 write transactions in 192 turns (book, reschedule, change request) plus 47 case creations; all inside the 0.05 s p95 non-model residual | SQLite: one file, one writer, no pool to size. Connection hold time not timed separately; bounded by the residual |
| SD-5.3 | **Found [M]** (was assumed) | Mean tokens in/out per call: planner 1,088/179, classifier 501/42 (Jev; output free), specialist 539/197, responder 640/158, brief 602/139. **Cost per conversation $0.016 mean / $0.039 max** (SP-1 §3), vs the ≈ $0.30 budget. p50/p95 per turn at 20 at once 4.7 s / 10.2 s | Research §2c's assumed turn shape (planner ~2,000 in) is superseded. Prompt-cache savings and streaming not measured (SP-1 §3 *Not measured*) |
| SD-5.5 | **Found** (was N/A) | OpenRouter *Limits* (S-230, read 2026-10-20): paid model variants have "no platform-level request cap"; limits can differ by model; upstream-provider 429s; an in-flight spending budget can return 402 on prepaid accounts. SP-1: 0 call errors in B's 258 Jev calls | The interview row said "no third-party API besides the model providers"; OpenRouter is now a router on every turn, so its limits are cited here |
| SD-6.3 | **Found** (extended) | Anthropic: research §4 (unchanged). OpenRouter *Errors* (S-229, read 2026-10-20): 402 credits, 408 timeout, 429 with `Retry-After` when available, 502 model down, 503 no provider; **errors can arrive inside a 200 body or stream**; automatic provider fallback before the first token; SDKs never auto-retry a 402 | Design notes for DO-4: check the body for `error` even on 200; a Jev failure on the raise-only classifier must fail toward "raise or hand off", never toward "normal" |
| SD-7.3 | Assumed (unchanged, evidence added) | See §3 | — |

**Citation spot-check (Core and AI items).** Each named section or ID was opened and matched its claim:

- Brief Part A §PRD, §Technology, §Required Deliverables; Part B §Overview, §6 Deployment, §Deliverables, §What we are looking for (SD-1.1, 1.2, 1.4, 7.1) ✓
- Audit C-1, D-5, D-9, G-9, L-9 (SD-1.2, 8.1, 3.6, 1.10, 1.6) ✓
- PRD R-5, R-9–R-13, R-15, R-19, R-21, R-24–R-26, R-28, R-29, R-33–R-36, R-38–R-41, R-45–R-47; §6.1 flow; §6.2 tracing and models; §8 test set (~60 transcript + ~15 synthetic); §10 foundation table ✓
- Framing §2: north star, V1–V5, health list with decision lines, signed status (SD-2.7, 2.8, 2.9) ✓
- Consolidated §10: `thread_id` checkpointer, idempotent case creation, lookup-log wrapper, brakes (SD-4.5, 4.7, 6.2) ✓
- Hard-problems GP-107, 108, 111, 113, 114, 116, 117, 118 (SD-1.7, 6.1, 6.4, 7.5, 8.3) ✓
- `verification-evals-observability.md` rules 18–21 (SD-8.4, 8.7, 1.10) ✓; `SUBMISSION.md` goal-to-evidence table (SD-8.5) ✓
- Research §1 (forced `tool_choice` is a 400 on Sonnet 5.5), §2a (Sonnet $2/$10, cache hit $0.10), §2b (Start tier 1,000 RPM / 2M ITPM / 400K OTPM, $500/month cap), §3 (AnyIO limiter 40; `async def` blocks), §4 (429/500/504/529; SDK 2 retries, `min(0.5×2^n, 8)` backoff, uncapped `retry-after`), §5 (Hobby volume 5 GB, no replicas with a volume); sources S-187…S-226 present in the register (SD-4.2, 5.4, 5.6, 6.3, 7.4) ✓

**Citations that are now stale** (the owner was updated after the citing text; not edited here because other agents
own these files tonight; the DO authors should carry the current value):

- Framing §2 health list still reads "p95 above **8 s** (assumption)"; PRD §5 now says 12.5 s [Decided]. DO-7 should use 12.5 s.
- PRD §5 *Latency* and *Spend* bullets still describe "all Sonnet 5.5 by default" and the Sonnet-everywhere estimate; PRD §6.2 *Models* records option B. Measured cost is $0.016 per conversation.
- Hard-problems GP-107 and the interview's SD-1.7 row cite "~$0.10 per conversation [C]"; measured $0.016 [M].
- Research §2c's per-turn token shape is an assumption superseded by SD-5.3 above.

## Audit log

- 2026-10-20: first audit, after Stage 4 and SP-1. Verified the interview's 60 dispositions instead of re-sweeping; spot-checked every Core and AI citation. Changed SD-2.3 (8 s → 12.5 s, Decided), SD-3.2, SD-3.3, SD-5.1, SD-5.2, SD-5.3 (assumed → measured, SP-1); extended SD-5.5 and SD-6.3 for the Jev/OpenRouter route (S-229, S-230 added to the source register). Result: 58 Found or Decided, 1 Assumed (SD-7.3; SD-3.2 is Found with a conversation-length caveat), 1 N/A (SD-4.6; SD-5.5 was N/A and is now Found because OpenRouter is on the request path), 0 Missing. Design outputs register relocated DO-3, DO-5, DO-6, DO-7 to their own files; check holds at the readiness gate. Verdict READY.
