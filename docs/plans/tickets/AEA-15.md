## [AEA-15] checks: completion and fact checks (R-46)

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

> **US-16 · Never be told something happened when it didn't.** "As a homeowner, I need the assistant never to say 'done',
> 'cancelled' or 'refunded' unless it really did it, and to hand me to a person when it hits a limit, so that I can
> believe what it says." Acceptance: "'cancel my membership' → no completion claim, a case with a promise".

`src/meridian/checks.py` is the pure code that guards the model's words (R-46, HP-4 option B; DO-3 §4.1), typed as DO-4
§10 plus the additions of `docs/design/contracts/stage7/graph-nodes.md` §2 (*graph-nodes §2*; GRN-1, GRN-3), which win
where they differ (DO-4 §16):

- **`COMPLETION_WORDS: dict[ActionKind, tuple[str, ...]]`**, inline (its only reader; code-design review B-2), covering at
  least R-46's "cancelled" and "moved". **`GENERIC_COMPLETION_WORDS`** = ("done", "all set", "taken care of", "sorted",
  "finished", "completed", "that's handled"), inline beside it (GRN-1). "Refunded" and "turned off" are completion
  claims with no `ActionKind`, because no tool can refund or switch off auto-renew, so such a claim never passes.
- **`check_completion(text, settled) -> CheckResult`**: a kind-specific claim passes only when `settled` holds an action
  of the matching kind, and of the named record when the sentence names one. A generic word yields
  `Claim(kind="completion", action_kind=None)` and passes only when the **same sentence** also holds a kind-specific
  claim that passes (GRN-1). A failing sentence is removed with reason `no_completed_action`; the rest is kept. `settled`
  covers the whole conversation including this turn's writes [Decided SDQ-8 option A, Innocent 2026-10-21]; there is no
  scope flag: the eval shows R-46's literal "this turn" reading by passing `settled.only_turn(turn_id)` to the same
  function (DO-4 §10, review C-1).
- **`build_evidence(facts, settled, lookups: Sequence[LookupRow], chat=None) -> EvidenceSet`** (`LookupRow` from
  `meridian.domain.tools`, cases §1.2, R-G-8; this pure module imports no adapter or repository): amounts in cents, dates,
  times, ids and numbers from this turn's facts, `settled` and the lookup rows, each with its `SourceRef`; the chat only
  when passed (the brief).
- **`check_facts(text, evidence) -> CheckResult`**: every number, date, time, ID and amount in the text must be in the
  evidence; a sentence with one that is not is removed with reason `not_in_evidence` (R-46 fact check; R-28).
- **`check_quotes(extraction: BriefExtraction, shown: Mapping[int, str]) -> QuoteCheck`** (GRN-3): `shown` is message_id
  → the exact text the brief extraction call was given for that customer message. A quote passes when its `message_id`
  is in `shown` and its text is an exact substring of `shown[message_id]`; anything else is removed with reason
  `quote_not_found`. `QuoteCheck(needs, claims, removals, passed)`; `Claim.kind` gains `"quote"` (span `(0,
  len(quote.text))`, value `str(quote.message_id)`).

`checks.py` builds no `CheckEvent`: AEA-38 calls `CheckEvent.from_check` (AEA-02, `domain/turn.py`) on these results
(GRN-2). What happens when everything is removed (`CheckedReply.fallback_used`, a code reply from the facts plus a person
offer) is the reply node's (AEA-38); appending the promise and reference after the checks is compose's (AEA-21).

**Example pair.** Input: WP-8, the draft "Done, auto-renew is off." with no write in `settled`. Expected output: the
sentence removed (`no_completed_action`), `passed` False. Input: WP-4F turn 4, the draft "Yes, it's moved: Monday, October
19, 8:00 am to 12:00 pm with Marta." with turn 3's `moved` action in `settled`. Expected output: unchanged, `passed` True
(DO-3 §1 step 8). Input: WP-2, a draft saying the after-hours line is $149 when the invoice evidence holds $89, $245,
$144 and $478.00. Expected output: that sentence removed (`not_in_evidence`); "$144" would pass (HP-3: no unprompted $149).

### Source
- stage7/graph-nodes.md §1 (`CheckEvent.from_check`, who builds which event), §2 (`GENERIC_COMPLETION_WORDS`, `Claim`
  kind `quote`, `QuoteCheck`, `check_quotes`), §3 (how the reply node calls `check_quotes` and `check_facts` on the
  brief); decision ledger `docs/plans/7b-decisions/graph-nodes.md` GRN-1, GRN-2, GRN-3; stage7/cases.md §1.2 (`LookupRow`,
  CAS-38; it lives in `domain/tools.py`, written by AEA-02, residuals-graph R-G-8).
- DO-4 internal-components §10 (`Claim`, `EvidenceSet`, `build_evidence`, `Removal`, `CheckResult`, `COMPLETION_WORDS`,
  `check_completion`, `check_facts`; SDQ-8 A), §1 (`Settled`, `only_turn`), §7 (`Quote`, `BriefExtraction`), §8
  (`TurnFacts`), §16; DO-3 code-design §1 (WP-4F walk-through), §4.1 (`checks.py`), §11 B-2, C-1; DO-2 system-design §A.1
  (*R-46 checks*), §11 decision 9 (whole reply checked before showing).
- PRD R-46, R-28, R-13; HP-4 (option B, Innocent ✓ 2026-10-20); HP-3 ($144 vs $149); WP-2, WP-4F, WP-8; US-16; DO-6
  observability-contract `check_event` record.
- Slice plan §1 row AEA-15 (links M-8).
- **Brief check:** serves "Do not let the agent guess. A confident wrong answer is worse than a handoff."; touches
  nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] A completion claim backed by `settled` passes: WP-4F turn 4's draft with turn 3's `moved` action → text unchanged, `passed` True (SDQ-8 A) — verify: `tests/unit/test_checks.py::test_wp4f_move_from_earlier_turn_passes` — evidence: equal text, no removals.
- [ ] AC-2 [failure/refusal] A completion claim with no matching action is removed and the rest kept: WP-8's "Done, auto-renew is off." followed by an explanation sentence → the first sentence gone, the second kept, reason `no_completed_action` — verify: `test_checks.py::test_wp8_done_without_write_removed` — evidence: the remaining text and one `Removal`.
- [ ] AC-3 [invariant] Generic completion words pass only beside a backed kind-specific claim in the same sentence: "Done, your visit is booked." with a `BOOKED` action kept; WP-8's "Done, auto-renew is off." removed; a bare "Done!" removed; each of the seven `GENERIC_COMPLETION_WORDS` detected (GRN-1) — verify: `test_checks.py::test_generic_done_needs_backed_kind` — evidence: kept, removed, removed; one detection per word.
- [ ] AC-4 [invariant] R-46's "cancelled" and "moved" are completion claims of their `ActionKind`; "refunded" and "turned off" are completion claims that never pass, whatever `settled` holds — verify: `test_checks.py::test_r46_words_are_claims` — evidence: one case per word.
- [ ] AC-5 [invariant] When the sentence names a record, the action must be for that record: "cancelled" naming an appointment other than the one in a `cancelled` action is removed (DO-4 §10) — verify: `test_checks.py::test_claim_must_match_named_record` — evidence: removal for the wrong record, pass for the right one.
- [ ] AC-6 [invariant] The eval's literal reading uses the same function: WP-4F turn 4 checked against `settled.only_turn(turn_4)` removes the "moved" sentence (DO-4 §10, review C-1) — verify: `test_checks.py::test_only_turn_reading_same_function` — evidence: one removal.
- [ ] AC-7 [failure/refusal] `check_facts` removes a sentence with a number, date, time, ID or amount absent from the evidence: WP-2's "$149" removed (`not_in_evidence`), "$144", "$478.00", "INV-204411" and "November 1" kept — verify: `test_checks.py::test_wp2_fact_check_amounts` — evidence: the kept and removed sentences.
- [ ] AC-8 [invariant] `build_evidence` takes values from facts, `settled` and the `LookupRow`s, and from the chat only when the chat is passed: a number said only by the customer passes for the brief and is removed from the reply — verify: `test_checks.py::test_chat_evidence_only_for_brief` — evidence: the two results.
- [ ] AC-9 [failure/refusal] `check_quotes` keeps a quote that is an exact substring of `shown[message_id]` and removes, with reason `quote_not_found`, one with an altered word and one whose `message_id` is not in `shown` (a non-customer message); `needs` and `claims` keep the passing quotes in their original order (GRN-3) — verify: `test_checks.py::test_quote_must_be_exact_substring` — evidence: the kept quotes, two removals, `passed` False.
- [ ] AC-10 [invariant] When every sentence is removed, `CheckResult.text` is empty and `passed` False; with no removals `passed` is True (DO-4 §10) — verify: `test_checks.py::test_all_removed_and_clean_results` — evidence: both results.
- [ ] AC-11 [negative] A removed claim's text (a distinctive amount) is absent from `CheckResult.text` and from captured logs (the module logs nothing), and the module defines and imports no `CheckEvent` builder, so only claim kinds can reach a `check_event` (GRN-2; DO-6 *Content and redaction*) — verify: `test_checks.py::test_removed_value_absent_from_text_and_logs` — evidence: the value absent from both; no `CheckEvent` reference in the module.
- [ ] AC-12 [invariant] The module is pure: no I/O, no model, no import of `services/`, `agent/` or adapters (DO-3 §2.1) — verify: `test_checks.py::test_checks_module_is_pure` — evidence: forbidden modules absent from its imports.
- [ ] AC-13 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-15.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-2 (the completion and fact checks on grounded answers) as the journeys that will exercise this code once AEA-51 lands, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-14 [regression/context] Docs updated in the same change: `.claude/reference/area-map.md` A7c row (`checks.py`, built in wave 1 by this ticket) planned → actual with the commit, `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §3 status planned → built — verify: `git diff --name-only` — evidence: the three files in the diff.

### Observability
- Responsibilities: no record of its own (pure). It supplies the removals from which AEA-38 builds WF-1's R-46
  `check_event` rows with `CheckEvent.from_check` (`completion`, `fact`, `brief_fact`, `brief_quote`; graph-nodes §1):
  claim kinds and counts only, never the removed text. M-12's live count of brief removals reads those rows.
- Capture evidence: AC-11 (removed values never leave the result); at WF-1's real entry point, CAP-1's `check_event` for
  R-46 in AEA-51.

### Evaluation
- Checks: E-1's hard gate "no completion claim without a successful write" (WP-4F, WP-8), E-6's "every number, date, ID
  and amount in the brief appears in the lookup log or chat" and its quote check, and the R-46 slice of E-3/E-4.
- Expected-answer authority: the `actions` table (`settled`) for completions; the lookup log and the chat for facts (DO-5
  *Expected-answer authority*, handoff-brief row: "any number, date, ID or amount not in the lookup log or the chat is an
  invented fact"); the customer message text for quotes (DO-4 §10).

### Metrics
- References: M-8 (wrong-answer rate), M-12 (invented facts in briefs), M-21 (action-rule violations: completion claim
  without a write).
- Acceptance conditions: M-12's live count stays computable from `check_event` rows built from these removals (AC-11
  keeps them value-free); M-8 and M-21 are eval-computed. Targets are DO-7's (≤ 5%, 0, 0), measured at Stage 9.

### Blocked by
AEA-02

### Agent handoff
- Area / owner: A7c checks (`src/meridian/checks.py`; wave 1 by the slice plan).
- Contracts and shared surfaces: consumes `Settled`, `ActionKind`, `TurnFacts`, `ChatLine`, `Quote`, `BriefExtraction`
  and the DO-4 §10 types (AEA-02), and `LookupRow` from `meridian.domain.tools` (cases §1.2, R-G-8; written by AEA-02 in
  wave 0, so tests build real `LookupRow`s). Produces `build_evidence`, `check_completion`, `check_facts`, `check_quotes`,
  `COMPLETION_WORDS`, `GENERIC_COMPLETION_WORDS`, `QuoteCheck` for the reply node's checks and brief path (AEA-38) and for
  eval scoring of the literal reading (AEA-24). Must not edit `domain/*` (a missing `Claim` kind or type is a follow-up
  on AEA-02) or `policy/texts.py`.
- Scope boundary / refusal: no rewriting of the model's text beyond removing whole failing sentences or quotes; no
  `CheckEvent` building (AEA-38 via AEA-02's builder); no fallback reply (AEA-38); no promise or reference appended
  (AEA-21); no model call.
- Wave and gates: wave 1; no gate.
- Lane: build-loop — source and tests.
- Risk: None.
- Entry points added or changed: None
