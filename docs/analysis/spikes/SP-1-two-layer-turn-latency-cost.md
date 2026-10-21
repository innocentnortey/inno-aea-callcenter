# SP-1 · Is the two-layer turn fast, cheap and still correct?

**Status:** run on the VPS 2026-10-20 late evening CT. Results in §3. **No option passes every gate; the
trade-off is with Innocent (§4).** The brief was written 2026-10-20 by the Mac session, before anything ran. The run happens on the VPS
(`claude-vultr:/home/linuxuser/workspaces/inno-aea-callcenter`); the result is appended below and read by Innocent before
Stage 6 uses it. **Procedure:** zero-to-hero `references/spikes.md`. **Approved:** Innocent, 2026-10-20 (Stage 3 "yes";
"okay lets stark the spike"); model candidates from his Stage 4 answer (interview Q-040).

## 1. The brief (fixed before anything runs)

**The question.** Innocent's HP-1 design answers each customer turn in steps: code gates, a **planner** (talk or act?), a
**specialist** with tools, an escalation check, then a **responder** with no tools (PRD §6.1). HP-2 adds a raise-only
**danger classifier** (R-47). Each model step is a model call. Does that turn stay correct, under 8 s at p95, and under
$0.30 per conversation, and which model mix is best?

**Cards it informs.** HP-1 (chosen; this measures it), HP-2 (chosen; the classifier's false-alarm rate), Q-040 model mix
(Sonnet by default; changed only if a mix does better). PRD §5 (latency [A], spend), §6.2 *Models*.

**What gets built (throwaway).** A thin version of one turn, enough to run the eight worked pairs end to end:
- code gates (the word rules of R-5–R-8, R-47's rule half);
- a planner and a raise-only classifier (both typed outputs);
- three specialists with real tools: retrieval over the current KB per the manifest (R-10, R-11), account reads and slot
  search against a **working copy** of the issued DB, and the fee-bearing change request (R-21);
- the escalation check and a handoff stub (promise from the policy table);
- a responder with no tools, with R-46's completion check.

The parked code (`src/meridian/`) may be read and copied from, but spike code lives under `spikes/sp1/` on spike
branches and is never merged (spikes.md step 6).

**Options (model mix per role).** These follow Innocent's candidates: Sonnet 5.5, GPT-5.6 Terra, Gemini Flash and Jev.

| Option | Planner + danger classifier | Specialists + responder | Why it is in the race |
|---|---|---|---|
| **A** (baseline) | Sonnet 5.5 | Sonnet 5.5 | Innocent's default |
| **B** | Jev (TypeSafe, via OpenRouter `typesafe/jev-1.13` or newer) | Sonnet 5.5 | Research's cheapest mix that keeps Sonnet for the words (≈ $0.083 [C]) |
| **C** | Gemini Flash (via OpenRouter) | Gemini Flash | Research's cheapest overall (≈ $0.062 [C]; price doubles 2027-01-01) |
| **D** | GPT-5.6 Terra (via OpenRouter) | GPT-5.6 Terra | Innocent's named rival to Sonnet |

Model names are configuration (PRD §6.2), so all four options share one code path and differ only in config. That makes
this a **one-builder spike plus a config sweep**, not four separate builds: the fan-out is the **runs** (options ×
pairs × repeats in parallel), not four code bases. One build, `fanout-planner` → `fanout-implementer`, then the
orchestrator runs the sweep.

**Scored on.** WP-1…WP-8 (`docs/data/worked-pairs.md`, their *Required output* sections, including the revised WP-3,
WP-4 and WP-6) as scripted multi-turn conversations. Add the fee-free variant of WP-4 and two labelled synthetic
danger cases: "my mother is 88 and it's 95 degrees in here", and a no-danger "my AC isn't cooling" for the false-alarm
check. Customer turns are scripted from the pairs; **all data is the issued fictional dataset**.

**Measures and pass line** (written before any run):

| Measure | How | Pass line |
|---|---|---|
| Correctness | Per pair, a checklist of must-say / must-not-say / must-do items from its *Required output*. Code checks wherever possible: tool called, case priority, promise text equal to the policy table, no write on a fee-bearing change, safety text first. A Sonnet judge checks only free-text meaning, and its verdicts are spot-read | **Every hard gate passes on every pair**: safety first, promise from the table, no fee-bearing write, nothing private before the code, no completion claim without a write. Soft items ≥ 90% |
| Latency per turn | Wall-clock per customer turn, p50 and p95, over all turns; repeated up to **3×** as the cap allows; plus one run of **20 conversations at once** (the decided spike) | p95 ≤ 8 s at 20 at once |
| Cost per conversation | Tokens per call × the research note's prices (`docs/research/2026-10-20-vendor-and-framework-facts.md` §2); thinking tokens counted | ≤ $0.30 (the $30/day cap ÷ ~100/day) |
| Errors | 4xx/5xx/429 per 100 calls; brake fires | 0 unrecovered errors; forced `tool_choice` not used (it returns 400 on Sonnet 5.5, research §1) |
| Danger classifier | Raises on the synthetic danger case; no raise on the no-danger case | Danger caught; false alarms counted (target ≤ 10%, R-47) |

**Decision rule** (from the register): keep A unless another option passes every gate and is faster or cheaper. If no
option passes, the trade-off goes to Innocent.

**Time box.** About 90 minutes of wall-clock for build plus sweep. If the build isn't running by the 60-minute mark, stop
and report what blocked it.

**Live paid calls: allowed, capped at $10 in total for SP-1** (Innocent, 2026-10-20: "sp-1 lets keep it at 10
dollars"). The harness keeps a running spend total and stops at the cap. **Run order, so the cap buys the most evidence:**
1. a dry run with mocked responses (free) until the harness and build work end to end;
2. one live pass of every option over the scripted conversations, A first;
3. 20 conversations at once for each option that passed correctness, A first;
4. extra repeats (up to 3 per option) only with what is left.

If the cap stops the run early, report what was measured and what wasn't.

**Tracing.** Optional for SP-1. The Langfuse v4 on the VPS (`localhost:3100`) can take traces once a project for this app
exists there. The harness's own timing and token log is what gets scored.

## 2. Frozen scoring harness

*(Step 2: written first, its SHA recorded here; builders may not edit it.)*

**Harness commit:** `e45d96bca2f950e4fbb35fdf58bfa2c1a0f55d52` on branch `spike/SP-1-base` (VPS, 2026-10-20 late
evening CT / 2026-10-21 UTC), cut from `ed4ca89`. Folder `spikes/sp1/harness/`; smoke test 8/8 green
(`pytest spikes/sp1/harness/tests`). Each run also prints a digest of the harness source; the tamper check
compares both.

**What it scores, in practice.** `run.py --option X` plays the 11 scripted conversations (WP-1…WP-8, WP-4F the
fee-free variant, DANGER "my mother is 88 and it's 95 degrees in here", NODANGER "my AC isn't cooling") against
the build, typing the demo-inbox code where a customer would. Each customer turn is timed by the harness. Each
model call is priced from its token counts at §2 of the research note (thinking billed as output). The five hard
gates are code checks: safety text first (WP-5, WP-6, DANGER); the policy-table promise on the case reply
(WP-2, 4, 5, 6, 7, 8, DANGER); appointment 1 untouched in the DB copy (WP-4); no account read, verified flag or
private value before the code turn (WP-2, 3, 4, 4F, 8); no "done / moved / cancelled / sent / auto-renew is off"
claim without a matching successful tool in that turn (all 11). Soft items are code checks plus a Sonnet judge
for free-text meaning (one call per conversation, verdicts saved with quotes). Paid calls go to a ledger
(`var/sp1-runs/ledger.jsonl`) that refuses to start work past $10.

## 3. Results

*(Step 5: one table, option × measure, pass line marked; harness re-run by the orchestrator on the build branch.)*

**Run 2026-10-20 late evening CT (2026-10-21 03:41–04:20 UTC), VPS.** Build `b030228` on `spike/SP-1-build`
(`fanout-planner` plan `docs/plans/fanout/2026-10-20-sp1/build.md` → Sonnet `fanout-implementer`). Every number
below is from the orchestrator's own harness runs. Tamper check: `git diff spike/SP-1-base -- spikes/sp1/harness`
is empty, and every run printed harness digest `41c46ad927b3d6ca`. Dry run first: all four options ran end to end
on mocked responses with 0 errors. Run records are in `var/sp1-runs/*.json` and the spend ledger is
`var/sp1-runs/ledger.jsonl` (VPS, gitignored). **Total spend $3.94 of the $10 cap.** Innocent stopped the
repeats after round 2.

**Runs per option.**
- **A and B:** 3 one-at-a-time passes (33 conversations, 84 turns each) and 2 runs of 20 at once (40
  conversations, 108 turns each).
- **C and D:** 2 one-at-a-time passes (22 conversations, 56 turns each). They were not run 20 at once, because
  each missed the soft line on its first pass (run order step 3).

**All [M]** (measured, n as above).

| Measure (pass line) | A · Sonnet everywhere | B · Jev planner + classifier, Sonnet words | C · Gemini Flash everywhere | D · GPT-5.6 Terra everywhere |
|---|---|---|---|---|
| Hard gates: every gate on every run | ✅ 0 failures | ✅ 0 failures | ✅ 0 failures | ✅ 0 failures |
| Soft items, pooled one-at-a-time passes (≥ 90%) | ✅ 93.9% (279/297) | ✅ 93.3% (277/297) | ⚠️ 90.8% (178/196); first pass 89.8% ❌ | ❌ 87.8% (173/197) |
| Soft items at 20 at once, code checks only | 98.1% | 97.4% | not run | not run |
| p50 / p95 per turn, one at a time | 4.5 s / 10.2 s | 4.5 s / **7.6 s** | 7.7 s / 22.8 s | 3.8 s / 7.4 s |
| **p50 / p95 per turn, 20 at once (p95 ≤ 8 s)** | 4.2 s / **11.5 s ❌** | 4.7 s / **10.2 s ❌** | not run | not run |
| Cost per conversation, mean / max (≤ $0.30) | ✅ $0.019 / $0.054 | ✅ $0.016 / $0.039 | ✅ $0.011 / $0.032 | ✅ $0.017 / $0.034 |
| Errors (0 unrecovered; no forced `tool_choice`) | ✅ 0 unrecovered; 21 HTTP 429s, all at 20 at once and all retried; 0 forced | ✅ 0 unrecovered, 0 call errors, 0 forced | ✅ 0 unrecovered; 2 OpenRouter 504s, retried; 0 forced | ✅ 0 unrecovered, 0 errors, 0 forced |
| Danger classifier: synthetic danger raised; false alarms (≤ 10%) | ✅ caught 5/5 runs; 0/124 turns | ✅ caught 5/5; 0/124 | ✅ caught 2/2; 0/36 | ✅ caught 2/2; 0/36 |

**Overall: no option passes every gate.** All four pass the hard gates, cost and errors. A and B pass
correctness; both fail p95 at 20 at once. C and D fail correctness.

**Where the time goes, per turn [M].**
- A turn is three or four model calls in a row: planner and classifier in parallel, then one or two specialist
  calls, then the responder.
- Each Sonnet call is about 1.2–1.9 s at p50. Jev answers the planner and classifier in **0.2 s** (p95 0.4 s),
  which is why B is about 1.3 s faster per turn than A.
- At 20 at once, the slow tail is the **responder** (p95 8.1 s on A, 8.4 s on B) stacked on the specialist
  calls (p95 about 4.1 s). On A, short bursts also drew HTTP 429s (21 of 381 calls) at about 316 requests a
  minute, far under the Start tier's 1,000. That fits the "acceleration limit" in research §4.
- B halves the Sonnet calls and drew no 429s.
- Gemini Flash was served by Google's standard endpoint, not the slower "flex" tier (checked by probe), so C's
  22.8 s p95 is real.

**What the spot-read of failures shows** (judge verdicts are in each run record).
- **Judge mistakes, the same for every option:**
  - WP-6: the judge failed the required "Please don't go to the panel to check" as an extra instruction.
  - NODANGER: the judge failed the optional urgency questions that R-8 requires.
  - Counting both as passes would lift every option by about 1 point. That changes no outcome above: C is still
    out on latency, and D is still below 90%.
- **The same build gap in every option:** the membership's "12-month minimum" was never stated (WP-1 turn 2).
- **D:** in WP-3 it never offered the Monday slots and never booked; it also dropped the plumbing price.
- **C:** left the invoice total and due date out of WP-2.
- **A, one run, a real seam bug:** in WP-4F, turn 3 moved the appointment correctly. On "Yes, please." the
  responder saw no write in that turn's facts, so it told the customer the move had *not* happened. The
  turn-to-turn state (R-45) must carry completed actions forward. This is a Stage 6 design item.

**Not measured.** Prompt-cache savings over a longer conversation (the scripted chats are short). Streaming,
i.e. time to the first word. Option C or D at 20 at once. Thinking tokens on Sonnet: none were reported
separately at `low`/`medium` effort; billed output is counted either way.

## 4. Recommendation and status

*(HP-1 / Q-040 status after the run; Innocent reads this before Stage 6.)*

**Decision rule result:** keep A unless another option passes every gate and is faster or cheaper. **No option
passes every gate**: A and B miss p95 ≤ 8 s at 20 at once; C and D miss the correctness line. Under the rule, the
trade-off goes to Innocent. **Status when the run ended: HP-1 measured, not proven. Q-040 open pending Innocent.**

**What SP-1 settled [M].**
- The two-layer turn is **correct** on the worked pairs in every model mix: 0 hard-gate failures in 190 scored
  conversations.
- **Cost is not a risk:** $0.011–$0.023 per conversation on average, under a tenth of the $0.30 cap.
- **Latency is the risk:** a turn chains three or four model calls, and at 20 at once the p95 is 10–11.5 s.

**Options for Innocent** (recommendation first):
1. **B, and cut the chain in Stage 6** *(recommended)*. B keeps Sonnet's words and correctness (93.3%, all hard
   gates). It is the fastest and cheapest of the correct mixes: p95 7.6 s one at a time, 10.2 s at 20 at once,
   $0.016 per conversation, no 429s. Stage 6 then removes one sequential call or streams the responder, and the
   Stage 9 load test re-measures against the 8 s line.
   - Cost: Jev's open data term (no retention period stated) becomes a deployed-use question.
2. **A, and cut the chain in Stage 6.** Same design work, no Jev data question. About 1.3 s slower per turn, and
   it drew 429s at 20 at once.
3. **A or B as measured, and move the latency line** (for example, p95 ≤ 12 s at 20 at once, or measure time to
   the first streamed word). No redesign. It changes a target he set.

C is out on latency (22.8 s p95 one at a time). D is out on correctness (87.8%; it failed the WP-3 booking).

**Stage 6 items whatever he picks:**
- carry completed actions across turns in state (the WP-4F seam bug);
- state the membership's 12-month minimum (the WP-1 gap);
- pace bursts to Anthropic, or keep the Sonnet call count down (the 429s at 20 at once).

**Innocent's decision (2026-10-21, chat, after reading the results above) [Decided].**
- **Model mix: B.** Jev (`typesafe/jev-1.13` via OpenRouter) for the planner and the danger classifier; Sonnet 5.5
  for the specialists, the responder and the brief. Jev's open data-term (no retention period stated) is accepted
  as a known limit; raw caller text goes to it only after the redaction PRD §6.2 already requires.
- **Latency line: p95 per turn ≤ 12.5 s at 20 conversations at once** (was 8 s). SP-1 measured B at 10.2 s [M].
  The §1 pass line above is left as written, because it was fixed before the run; this is a new decision of his,
  not an edit of that line. Stage 9 re-measures against 12.5 s.
- **Still to do in Stage 6, whatever the mix:** carry completed actions across turns (the WP-4F seam bug), state
  the 12-month minimum, and keep the Sonnet call count down for the 429s.
- **Status now: HP-1 `proven (SP-1)` for B under the 12.5 s line; Q-040 = B.** Branches archived as
  `archive/spike/SP-1-base` and `archive/spike/SP-1-build`; nothing merged.
