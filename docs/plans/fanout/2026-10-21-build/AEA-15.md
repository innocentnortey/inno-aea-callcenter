# Plan — [AEA-15] checks: completion and fact checks (R-46)

**Status:** planned; refreshed 2026-10-21 against `main` `16ca639` (READY; the implementer starts once AEA-02 is on `main`; see §9)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/15 · **Base revision:** `16ca639` (main at refresh: AEA-01 merged at `07924f5`; AEA-03, AEA-04, AEA-08, AEA-25 merged; **AEA-02 not yet merged**; first planned at `5f2e1bb`)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 · **Implementer:** fanout-implementer on Sonnet · **Lane:** build-loop · **Risk:** none (no `risk::security`: no test-writer, no security review)
**Slug / branch:** `checks-completion-facts` → branch `aea-15-checks-completion-facts`, worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-15` (the orchestrator creates it)

---

## 1. Goal and sources

### Goal

From the issue (`docs/plans/tickets/AEA-15.md`, *What to build*): "`src/meridian/checks.py` is the pure code that guards
the model's words (R-46, HP-4 option B; DO-3 §4.1), typed as DO-4 §10 plus the additions of
`docs/design/contracts/stage7/graph-nodes.md` §2". It delivers `COMPLETION_WORDS`, `GENERIC_COMPLETION_WORDS`,
`check_completion`, `build_evidence`, `check_facts`, `QuoteCheck` and `check_quotes`. It builds no `CheckEvent`, no
fallback reply and no promise.

**What it does, concretely (the ticket's example pairs).**

| Input | Output |
|---|---|
| WP-8: draft `"Done, auto-renew is off."`, `settled` holds no write | sentence removed (`no_completed_action`), `passed` False |
| WP-4F turn 4: draft `"Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with Marta."`, `settled` holds turn 3's `moved` action | text unchanged, `passed` True |
| WP-2: `"The after-hours line is $149."` with invoice evidence $89, $245, $144, $478.00 | that sentence removed (`not_in_evidence`); a `$144` sentence is kept |

**How it works, in one paragraph.** Split the text into sentences (keeping their character spans). For the completion
check, find completion words in each sentence; a word names an `ActionKind` (or none), and it passes only when `settled`
holds an action of that kind (for the named record, when the sentence names one). For the fact check, pull every amount,
date, time, ID and number out of each sentence and look each one up in an `EvidenceSet` that `build_evidence` built from
the turn facts, `settled` and the lookup rows (and the chat, for the brief only). A sentence with any failing claim is
removed whole; the rest of the text is kept.

### Context

Wave 1 of the Stage 8 build. DO-3 §8 first put `checks.py` in wave 3 with its node; the slice plan moved it to wave 1
because it is a pure function over domain types (slice plan §2, row *A7a spine*). SP-1 had a single regex list
(`strip_unbacked`, branch `archive/spike/SP-1-build`, `spikes/sp1/harness/checks.py` `_CLAIMS`) checked against the
**turn's** tool calls; it failed WP-4F turn 4. The decided design (SDQ-8 option A) checks against `settled`, the whole
conversation, and the eval reads R-46 literally by passing `settled.only_turn(turn_id)`.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-15.md` (= issue #15) | AC-1…AC-14; example pairs WP-8, WP-4F, WP-2 |
| Requirements | PRD `docs/prd/inno-aea-callcenter-prd.md` R-46 (l.235), R-28 (l.234), R-13 (l.167); US-16 | Completion words "done", "cancelled", "moved", "refunded", "turned off"; every number, date, ID and amount compared; facts and claims apart in the brief |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §1 (`ActionKind`, `CompletedAction`, `Settled.only_turn`, `ChatLine`), §7 (`SourceRef`, `Quote`, `BriefExtraction`), §8 (`TurnFacts`), §10 (`Claim`, `EvidenceSet`, `build_evidence`, `Removal`, `CheckResult`, `COMPLETION_WORDS`, `check_completion`, `check_facts`; SDQ-8 A), §16 (addenda win) | Exact signatures; no scope flag; chat only for the brief |
| Stage 7 addenda (win over DO-4) | `stage7/graph-nodes.md` §1 (`CheckEvent.from_check` is AEA-02's; who builds which event), §2 (`GENERIC_COMPLETION_WORDS`, `Claim.kind` `"quote"`, `QuoteCheck`, `check_quotes`), §3 (how AEA-38 calls `check_quotes` and `check_facts` on the brief); `stage7/cases.md` §1.2 (`LookupRow`, `SourceRef(kind="lookup_log", ref=str(id))`) | `checks.py` defines `QuoteCheck`; builds no event; `LookupRow` from `meridian.domain.tools` |
| Decision ledgers | `docs/plans/7b-decisions/graph-nodes.md` GRN-1, GRN-2, GRN-3; `residuals-graph.md` R-G-8 | Generic words need a backed kind-specific claim in the same sentence; no events here; quote check here |
| AEA-02 plan (sibling, wave 0) | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.0 (module rules), §4.3 (`Settled`, `only_turn` algorithm), §4.6 (`SourceRef`, `Quote`, `BriefExtraction`), §4.8 (`Claim` with `"quote"`, `Removal`, `CheckResult`, `EvidenceSet`, `TurnFacts` **without** `account`, `missing`, `notices`), §4.9 (`LookupRow`), §4.10 (`ChatLine`), §6 (WP-4F fixture) | Import homes; `QuoteCheck` is AEA-15's (AEA-02 §2.3 line "QuoteCheck, COMPLETION_WORDS (AEA-15)"); fixture values reused |
| Code design | DO-3 `docs/design/code-design.md` §1 step 8 (WP-4F walk-through: "moved" matched, "Monday", "8:00" matched), §2.1 (pure core), §4.1 (`checks.py` row), §9 (test layout `tests/unit/test_checks.py`), §11 B-2 (lexicon inline), C-1 (no scope flag) | Module home, dependency direction (pure core → `domain` only) |
| System design | DO-2 `docs/design/system-design.md` §A.1 row *R-46 checks*, decision 9 (whole reply checked before showing) | CPU only, < 10 ms [A] |
| Hard problems | `docs/design/hard-problems.md` HP-4 (option B, Innocent ✓ 2026-10-20), HP-3 ($144 vs $149) | Over-blocking a harmless phrase is the accepted direction; it shows in the eval and the words get tuned |
| Worked pairs | `docs/data/worked-pairs.md` WP-2, WP-4 (F variant), WP-7, WP-8 | Example inputs and outputs; WP-8's honest reply must pass when a case was opened |
| SP-1 harness | `git show archive/spike/SP-1-build:spikes/sp1/harness/checks.py` (`_CLAIMS`, `sentences`) | Starting phrase list (read and adapted, never imported) |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` E-1 (WP-4F, WP-8 hard gate), E-6 (l.172: every number, date, ID and amount in the brief appears in the lookup log or chat; quote check) | The eval calls these same functions (AEA-24); numbers come from E-runs, never from these tests |
| Observability contract | DO-6 `docs/design/observability-contract.md` *Records* `check_event` (l.115), WF-1 (l.76) | No record of its own; removals carry kinds only to AEA-38's `from_check` |
| Key-metrics registry | DO-7 `docs/design/key-metrics-registry.md` M-8 (l.60), M-12 (l.64), M-21 (l.73) | M-12 live count reads `check_event` rows built from these removals; M-8, M-21 eval-computed |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3 rule 1, §4, `context-maintenance.md` rule 6, `source-authority.md` rule 7 | Affected tests only; `mock-tested` journey record; context rows in the same change; removal is the safe direction |

### Refresh against `main` `16ca639` (2026-10-21)

| Checked | Finding | Effect on this plan |
|---|---|---|
| AEA-01 tooling on `main` | `pyproject.toml` (ruff line length 110, rules `E W F I B UP S RUF`, tests ignore `S101 S105 S106 S603 S607 S311`; mypy strict with `pydantic.mypy` and `init_typed = true`; pytest `--strict-markers`, markers `journey` and `live`), `tests/unit/__init__.py`, `tests/journeys/affected.py` (prints `N journeys affected`; exit 0 and no pytest run when none) are present | Step 1.2 passes; §7.3 commands unchanged |
| AEA-02 on `main` | Not merged: `src/meridian/domain/` holds only `__init__.py`; no AEA-02 worktree or branch exists yet | blocked-on AEA-02 stays (§9) |
| AEA-02 plan, revised 12:08 | `ActionKind`, `CompletedAction`, `Settled.only_turn` (algorithm unchanged), `SourceRef`, `Quote`, `BriefExtraction`, `ChatLine`, `LookupRow`, `Claim` (with `"quote"`), `Removal` (with `"quote_not_found"`), `CheckResult`, `EvidenceSet` (in `domain/turn.py`), `TurnFacts` (still without `account`, `missing`, `notices`), `GateKind`, `Passage`, `KnowledgePoint`: shapes unchanged. `QuoteCheck` is still left to AEA-15 (its §2.3) | §4 unchanged |
| Sources (DO-4, `stage7/graph-nodes.md`, `stage7/cases.md`, the ticket, worked pairs) | No change since `5f2e1bb` (`git diff 5f2e1bb main`) | §3, §5 steps 2–8, §6, §7 unchanged |
| Context files | The ICM row *Routes verified against code and tests* now appears **twice** (the AEA-04 and AEA-03 merges each kept one). DO-3 §3 tags a built module on its own tree line (`built AEA-04 9145044`) and also has a shared `**Built:**` line (AEA-03) | Step 10 rewritten |
| Journey records | `docs/testing/journeys/2026-10-21-AEA-04.md` adds a row *Journeys that will exercise this code* below *Blocked by* | Step 9 template follows it |
| AEA-01 tests | `tests/unit/test_skeleton.py` and `tests/unit/test_import_direction.py` do not list modules, so a new `checks.py` breaks neither | Affected scope unchanged (§7.2) |

---

## 2. Boundary

### Files this slice owns (the only files the implementer may create or edit)

| File | Create / modify | Change |
|---|---|---|
| `src/meridian/checks.py` | **create** | The whole module (§5 steps 2–7) |
| `tests/unit/test_checks.py` | **create** | Every test in §7.1 |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-15.md` | **create** (date = day of the run) | AC-13 journey record |
| `.claude/reference/area-map.md` | modify **one cell** | A7c row status (AC-14) |
| `.claude/state/icm-progress.md` | modify **one row** | *Routes verified against code and tests*, its duplicate collapsed into it (AC-14; step 10.2) |
| `docs/design/code-design.md` | modify **one line** in §3 | the `checks.py` line of the §3 tree (AC-14; step 10.3) |

### Shared surfaces read only (never edit)

- `src/meridian/domain/*` (AEA-02): `actions.py`, `common.py`, `handoff.py`, `records.py`, `specialists.py`, `state.py`,
  `tools.py`, `turn.py`. A missing type, field or `Claim` kind is an AEA-02 follow-up, never a local copy (ticket
  *Agent handoff*), with the single exception of `EvidenceSet` / `QuoteCheck` in §5 step 1.4.
- `pyproject.toml`, `uv.lock`, ruff / mypy / pytest configuration, `tests/conftest.py`, `tests/unit/__init__.py`,
  `tests/journeys/affected.py` (AEA-01).
- `policy/texts.py` (AEA-03): not imported, not edited.

### Owned by other slices: do not touch

`agent/nodes/reply.py`, `agent/prompts/reply.py` (AEA-38; they call this module), `agent/nodes/compose.py` (AEA-21),
`services/handoff.py` (AEA-29), `eval/**` (AEA-24), `tests/unit/test_import_direction.py` (AEA-01 and wave-0 tickets; this
ticket's purity test lives in its own file), `tests/journeys/**`, `apps/web/**`, `docs/ux/**`,
`ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, `docs/archive/`, `docs/parked/`, the briefing and issued data. Nothing
here starts a server, so ports 4019 and 5184 are never bound.

---

## 3. Requirements table

### 3.1 Decisions this plan makes (engineering; the implementer applies them, none is a product decision)

| ID | Decision | Basis |
|---|---|---|
| **PD-1** | **One `Removal` per removed sentence**, holding that sentence's **first failing claim** (lowest `span[0]`). Several failing claims in one sentence still give one removal. | AC-2 asks for "one `Removal`" for `"Done, auto-renew is off."`, which holds a generic word **and** an auto-renew claim. The sentence is the unit removed (ticket: "a failing sentence is removed"), so `CheckEvent.removed = len(removals)` counts sentences. |
| **PD-2** | **Completion words are phrases matched as whole words, case-insensitive, any apostrophe (`'` or `’`) optional, a hyphen also matching a space or nothing.** Three lists (exact members in §5 step 3): `COMPLETION_WORDS` (per `ActionKind`), `GENERIC_COMPLETION_WORDS` (GRN-1, verbatim) and `UNBACKED_COMPLETION_WORDS` (claims no tool can back: "refunded", "turned off", …). | DO-4 §10 names a word lexicon; R-46's own examples are bare words ("moved", "cancelled"); WP-4F's "it's moved" must count as a claim, which SP-1's `I've …` patterns missed. |
| **PD-3** | **Bare "scheduled", "waived" and "credited" are not completion words.** BOOKED uses "booked" plus "I've / we've / has been … scheduled" phrases. | Reads would be removed otherwise: "Your tune-up is scheduled for today 12–4pm" (WP-4 step 2), "the diagnostic fee is credited toward the repair if approved" (WP-2 step 3, FAQ), and a Plus member's "Waived" fee line (cases.md §2 `FeeNote.waived`). |
| **PD-4** | **A completion phrase is not a claim** when one of the up-to-4 words before it, **in the same clause**, is a negation, condition, modal or wish word (exact set in §5 step 3). Clause marks: `,` `;` `:` `(` `)` `—` `–` and ` - `. | "It isn't cancelled", "once you're verified", "Would you like it moved?", "I'll let you know when it's done" state nothing completed. The window is short so "Done, your visit is booked" still counts. |
| **PD-5** | **"Names a record"** (DO-4 §10, AC-5) means, per kind: appointment kinds (`BOOKED`, `MOVED`, `CANCELLED`, `CHANGE_REQUEST_SENT`) — an `appointment <n>` reference or a calendar date in the sentence; case kinds (`CASE_OPENED`, `FOLLOWUP_SAVED`) — a `MHC-C-nnnn` reference; `VERIFIED` — a `MHC-nnnnn` reference. A claim passes when **some** action of its kind holds **every** reference the sentence names. An appointment action's dates are its own `before`/`after` `"date"` values plus those of every action in the same `settled` for the same `records["appointment"]`; dates compare by month and day. | Dates are how a reply names a visit ("your October 16 visit"); the cross-action index covers a `CANCELLED` row that carries no date. Dates never name a case, so WP-8's "before your renewal date of November 3" stays a valid `CASE_OPENED` claim. |
| **PD-6** | **Fact claims and their values:** `amount` = cents as a decimal string (`"$478.00"` → `"47800"`); `date` = ISO `YYYY-MM-DD`, or `--MM-DD` when the text gives no year; `time` = 24-hour `HH:MM`; `id` = upper case `INV-nnnnnn`, `MHC-C-nnnn`, `MHC-nnnnn`; `number` = digits with commas removed, leading zeros and trailing decimal zeros dropped (`"02"` → `"2"`, `"2.50"` → `"2.5"`). Weekday names and person names are not claims. | DO-4 §10 field types (`amounts_cents: frozenset[int]`, `dates: frozenset[date]`, `times: frozenset[str]`); the WP-4F walk-through (DO-3 §1 step 8) matches "Monday" and "8:00" as facts of the visit. |
| **PD-7** | **Yearless dates.** A text date without a year passes when any evidence date has the same month and day. An evidence string date without a year is stored as `dt.date(4, month, day)` (`_YEARLESS_YEAR = 4`, a leap year, so 29 February is valid; no issued record has year 4). | "November 1", "October 19" are how replies say dates; the evidence holds full dates from records. |
| **PD-8** | **Derived evidence numbers.** Each evidence time adds its 12-hour clock hour as a number (`"08:00"` → `"8"`, `"16:00"` → `"4"`, `"12:00"` → `"12"`, `"00:00"` → `"12"`); each evidence date adds its day of the month (`"19"`); each evidence amount with zero cents adds its whole-dollar figure (`4900` → `"49"`). | Natural phrasings: "between 8 and 12", "on the 19th", "a 49 dollar fee". The derived numbers never invent anything the record does not hold. |
| **PD-9** | **What `build_evidence` reads, and from where.** It walks the values of: each `LookupRow`'s `record_ids` and `result_seen`; each `settled.actions` item and `settled.open_case`; every field of `facts`; each `ChatLine.text` when `chat` is passed. Strings are scanned with the same extractor as the text; `int` values become numbers (amounts when the key ends in `_cents`); `float` values become numbers; `date` / `datetime` values become dates (and, for `datetime`, a time). Keys in `_SKIP_KEYS` (§5 step 6) are never read: internal identifiers, scores and write timestamps. | DO-4 §10 "amounts in cents, dates, times, ids and numbers from this turn's facts, `settled` and the lookup rows"; a generic walk works on whatever fields AEA-02 gives `TurnFacts` (it ships without `account`, `missing`, `notices`: AEA-02 §8.2), so this ticket does not wait for those types. |
| **PD-10** | **`EvidenceSet.sources` keys and refs.** Key = `"<kind>:<value>"` (`"amount:14400"`, `"date:2026-11-01"`, `"date:--11-03"`, `"time:08:00"`, `"id:INV-204411"`, `"number:24"`); first source wins, in the walk order lookups → `settled` → facts → chat. Refs: lookup row → `SourceRef(kind="lookup_log", ref=str(row.id))` (cases.md §1.2); an action (in `settled`, `facts.writes_this_turn` or `facts.handoff.action`) → `SourceRef(kind="action", ref=f"{kind}:{record_id}:{turn_id}")` from its `key`; `settled.open_case` and the rest of `facts.handoff` → `SourceRef(kind="action", ref=f"case_opened:{case_ref}")`; `facts.passages[i]` → `SourceRef(kind="policy_row", ref=passage_id)`; `facts.points[i]` → `SourceRef(kind="policy_row", ref=point.passage_id)`; any other facts field → `SourceRef(kind="rule", ref=f"turn_facts.{field}")`; a chat line → `SourceRef(kind="message", ref=str(line.turn_id))`, or `f"line:{index}"` when `turn_id` is `None`. | DO-4 §10 `sources: dict[str, SourceRef]  # value → where it came from` gives no key format; the prefix stops `number:8900` and `amount:8900` colliding. Nothing downstream parses these refs yet (AEA-38 only reads `CheckResult`). |
| **PD-11** | **Sentence splitting**: a sentence ends after `.`, `!` or `?` (one or more, plus closing quotes or brackets) that is followed by whitespace or the end, and at every newline. No split after `a.m.`, `p.m.`, `e.g.`, `i.e.`, `mr.`, `mrs.`, `ms.`, `dr.`, `st.`, `vs.`, `approx.` or a month abbreviation (`jan.` … `dec.`, `sept.`), so "Oct. 5th, 2026" stays one date. Decimals (`$478.00`) and IDs never split. Kept sentences are joined with `"\n\n"` when the original gap between them held a blank line, `"\n"` when it held a newline, else `" "`; the result is stripped. With no removal, the text is returned unchanged. | AC-1 needs "equal text"; AC-2 needs "the rest kept". Merging two sentences after an abbreviation only widens a removal (safe direction). |
| **PD-12** | **An empty quote (`text == ""`) fails** `check_quotes` with `quote_not_found`. | `""` is a substring of every string, so without this rule an empty quote would pass vacuously; `Quote.text` has no `min_length`. |
| **PD-13** | **`EvidenceSet` and `QuoteCheck` homes.** Import `EvidenceSet` from `meridian.domain.turn` (AEA-02 plan §4.8 defines it there). Define `QuoteCheck` in `checks.py` (GRN-3; AEA-02 plan §2.3 leaves it to AEA-15). If AEA-02 as merged differs, §5 step 1.4 says exactly what to do. | One definition each. |

### 3.2 Requirement → implementation → verification

| # | Requirement (source) | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 | A completion claim backed by `settled` passes: WP-4F turn 4 (SDQ-8 A) | §5 step 4 (`_backed`, PD-5) | `tests/unit/test_checks.py::test_wp4f_move_from_earlier_turn_passes` (**the WP-N worked-pair test**) → equal text, no removals |
| AC-2 | No matching action → removed, rest kept: WP-8 | §5 step 4, PD-1 | `::test_wp8_done_without_write_removed` → remaining text, one `Removal` |
| AC-3 | Generic words pass only beside a backed kind-specific claim in the same sentence; each of the 7 detected (GRN-1) | §5 step 4 sub-step 3 | `::test_generic_done_needs_backed_kind` → kept, removed, removed; 7 detections |
| AC-4 | "cancelled", "moved" are claims of their kind; "refunded", "turned off" never pass | `COMPLETION_WORDS`, `UNBACKED_COMPLETION_WORDS` | `::test_r46_words_are_claims` → one case per word |
| AC-5 | A named record must match the action's record (DO-4 §10) | PD-5 | `::test_claim_must_match_named_record` |
| AC-6 | The eval's literal reading uses the same function (`settled.only_turn`) | No scope flag; AEA-02's `only_turn` | `::test_only_turn_reading_same_function` → one removal |
| AC-7 | `check_facts` removes an unsupported value: WP-2 | §5 steps 5–7 | `::test_wp2_fact_check_amounts` → kept and removed sentences |
| AC-8 | `build_evidence` reads the chat only when passed | §5 step 6 | `::test_chat_evidence_only_for_brief` → two results |
| AC-9 | `check_quotes` keeps exact substrings, removes altered and unknown-id quotes, keeps order (GRN-3) | §5 step 7 | `::test_quote_must_be_exact_substring` |
| AC-10 | All removed → `text == ""`, `passed` False; none removed → `passed` True | PD-11 | `::test_all_removed_and_clean_results` |
| AC-11 | A removed value is absent from `text` and logs; no `CheckEvent` in the module (GRN-2; DO-6) | No logging, no print; module never names `CheckEvent` | `::test_removed_value_absent_from_text_and_logs` |
| AC-12 | Pure: no I/O, no model, no import of `services/`, `agent/`, adapters (DO-3 §2.1) | Imports per §4 only | `::test_checks_module_is_pure` |
| AC-13 | [journey] `mock-tested` record, *Blocked by* AEA-57, names J-2 | §5 step 9 | The record's fields; `uv run python -m tests.journeys.affected --base main` prints `0 journeys affected` |
| AC-14 | Context in the same change | §5 step 10 | `git diff --name-only main...HEAD` lists the three context files |
| US-16 "'cancel my membership' → no completion claim, a case with a promise" | in-ticket (US) | WP-8's honest reply passes with a `CASE_OPENED` action and loses its claim sentence without one | **added**: `::test_wp8_honest_limit_reply_passes_with_case` |
| DO-3 §1 step 8: "Monday", "8:00" and the visit matched to the evidence | in-ticket (*Source* DO-3 §1) | PD-6, PD-7, PD-9 | **added**: `::test_wp4f_facts_match_settled` |
| Negated and conditional words are not claims | **added** (PD-4) | §5 step 3 `_NOT_A_CLAIM_BEFORE` | **added**: `::test_negated_and_conditional_words_are_not_claims` |
| Each fact kind is extracted with the PD-6 value | **added** | §5 step 5 | **added**: `::test_fact_claim_kinds_and_values` |
| Abbreviations and decimals do not split sentences | **added** (PD-11) | §5 step 2 | **added**: `::test_sentence_split_keeps_abbreviations_and_decimals` |
| Evidence comes from passages, writes and lookups with the PD-10 sources; internal ids never become evidence | **added** | §5 step 6 | **added**: `::test_evidence_sources_and_skipped_keys` |
| Derived numbers (PD-8) | **added** | §5 step 6 | **added**: `::test_numbers_derived_from_times_dates_amounts` |
| One removal per removed sentence (PD-1) | **added** | §5 step 4, step 7 | **added**: `::test_one_removal_per_removed_sentence` |
| Empty inputs give clean empty results; empty facts give empty evidence | **added** | §5 | **added**: `::test_empty_inputs` |
| An empty quote fails (PD-12) | **added** | §5 step 7 | **added**: `::test_empty_quote_removed` |
| Building `CheckEvent`s from these results | other-ticket: AEA-38 via AEA-02's `CheckEvent.from_check` (graph-nodes §1) | — | AEA-38 AC-11 |
| Fallback reply when everything is removed (`CheckedReply.fallback_used`) | other-ticket: AEA-38 (reply node), AEA-21 (compose) | — | AEA-38 |
| Promise and reference appended after the checks | other-ticket: AEA-21 | — | AEA-21 |
| Calling order on the brief (`check_quotes`, `check_facts(open_decision, …, chat)`) | other-ticket: AEA-38 (graph-nodes §3) | — | AEA-38 |
| Responder prompt rule "no completion word unless backed" | other-ticket: AEA-38 (`agent/prompts/reply.py`) | — | AEA-38 |
| CAP-1 `check_event` for R-46 at WF-1's entry point | other-ticket: AEA-51 | — | AEA-51 |
| M-8, M-12, M-21 values | other-ticket: E-runs via AEA-24 | — | never from these tests |

### 3.3 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (a pure library; WF-1 reaches it through AEA-38's reply node) | — | — | — |

---

## 4. Shared code to use

All of these are written by **AEA-02** (homes per its plan §4.0–§4.10). Do **not** redefine any of them.

```python
# meridian/domain/actions.py
class ActionKind(StrEnum):
    BOOKED = "booked"; MOVED = "moved"; CANCELLED = "cancelled"
    CHANGE_REQUEST_SENT = "change_request_sent"; CASE_OPENED = "case_opened"
    FOLLOWUP_SAVED = "followup_saved"; VERIFIED = "verified"
class ActionKey(MeridianModel):   thread_id: ThreadId; turn_id: TurnId; kind: ActionKind; record_id: str
class CompletedAction(MeridianModel):
    key: ActionKey
    kind: ActionKind
    records: dict[Literal["appointment", "slot", "old_slot", "case", "customer", "promise"], str]
    before: dict[str, str] | None = None
    after: dict[str, str] | None = None
    at: dt.datetime
    source: Literal["actions_table"] = "actions_table"
class Settled(MeridianModel):
    actions: tuple[CompletedAction, ...]; open_case: OpenCase | None; read_at: dt.datetime
    def has(self, kind: ActionKind, record_id: str | None = None) -> bool: ...
    def only_turn(self, turn_id: TurnId) -> Settled: ...   # keeps actions whose key.turn_id == turn_id

# meridian/domain/handoff.py
class SourceRef(MeridianModel):   kind: Literal["lookup_log", "message", "action", "policy_row", "rule"]; ref: str
class Quote(LLMFacing):           message_id: int; text: str = Field(max_length=300)
class BriefExtraction(LLMFacing): needs: list[Quote] (1–2); claims: list[Quote] (≤ 5); open_decision: str (≤ 200)

# meridian/domain/state.py
class ChatLine(MeridianModel):
    speaker: Literal["customer", "assistant", "representative", "event"]; text: str; turn_id: TurnId | None; at: dt.datetime

# meridian/domain/tools.py
class LookupEntry(MeridianModel): tool: str; record_ids: tuple[str, ...]; passage_ids: tuple[PassageId, ...]
                                  result_seen: str; message_id: int; turn_id: TurnId
class LookupRow(LookupEntry):     id: int; thread_id: ThreadId

# meridian/domain/turn.py
class Claim(MeridianModel):
    kind: Literal["completion", "number", "date", "time", "id", "amount", "quote"]
    span: tuple[int, int]
    value: str
    action_kind: ActionKind | None = None
class Removal(MeridianModel):     claim: Claim; reason: Literal["no_completed_action", "not_in_evidence", "quote_not_found"]
class CheckResult(MeridianModel): text: str; removals: tuple[Removal, ...]; passed: bool
class EvidenceSet(MeridianModel):
    amounts_cents: frozenset[int]; dates: frozenset[dt.date]; times: frozenset[str]
    ids: frozenset[str]; numbers: frozenset[str]; sources: dict[str, SourceRef]
class TurnFacts(MeridianModel):   # AEA-02 ships it WITHOUT account, missing, notices (AEA-02 plan §8.2)
    turn_id: TurnId; gate_kind: GateKind; plan_mode: Literal["talk", "act"] | None
    points: tuple[KnowledgePoint, ...]; passages: tuple[Passage, ...]; no_source_tasks: tuple[TaskIntent, ...]
    windows_shown: tuple[ShownSlot, ...]; writes_this_turn: tuple[CompletedAction, ...]
    change_request: ChangeRequestDraft | None; handoff: HandoffResult | None
    escalation: EscalationDecision | None; identity_step: IdentityStep | None; quick_checks: tuple[PassageId, ...] = ()

# meridian/domain/common.py
class MeridianModel(BaseModel): model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True,
                                                         str_strip_whitespace=True)
ThreadId, TurnId (canonical lower-case UUID4 str subclasses), CaseRef, PassageId
# Other test-only homes: GateKind (domain/turn.py), Passage (domain/records.py), KnowledgePoint (domain/specialists.py)
```

**Note `str_strip_whitespace=True`:** every `str` field of these models is stripped on construction, so
`CheckResult.text` and `Quote.text` never carry outer whitespace.

**The exact imports in `src/meridian/checks.py`** (nothing else from `meridian`; drop any name ruff reports unused):

```python
from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Final, Literal

from meridian.domain.actions import ActionKind, CompletedAction, Settled
from meridian.domain.common import MeridianModel
from meridian.domain.handoff import BriefExtraction, Quote, SourceRef
from meridian.domain.state import ChatLine
from meridian.domain.tools import LookupRow
from meridian.domain.turn import CheckResult, Claim, EvidenceSet, Removal, TurnFacts
```

**The public surface this ticket adds** (consumers: AEA-38 reply node; AEA-24 eval for the literal reading):

```python
COMPLETION_WORDS: Final[dict[ActionKind, tuple[str, ...]]]
GENERIC_COMPLETION_WORDS: Final[tuple[str, ...]] = ("done", "all set", "taken care of", "sorted", "finished",
                                                    "completed", "that's handled")
UNBACKED_COMPLETION_WORDS: Final[tuple[str, ...]]

class QuoteCheck(MeridianModel):
    needs: tuple[Quote, ...]          # the quotes that passed, original order
    claims: tuple[Quote, ...]
    removals: tuple[Removal, ...]     # reason "quote_not_found"
    passed: bool                      # no removals

def check_completion(text: str, settled: Settled) -> CheckResult: ...
def build_evidence(facts: TurnFacts, settled: Settled, lookups: Sequence[LookupRow],
                   chat: Sequence[ChatLine] | None = None) -> EvidenceSet: ...
def check_facts(text: str, evidence: EvidenceSet) -> CheckResult: ...
def check_quotes(extraction: BriefExtraction, shown: Mapping[int, str]) -> QuoteCheck: ...
```

All four functions are pure and never raise on any well-typed input (empty strings and empty collections included).

---

## 5. Steps

The slice implements one pure-core module (DO-3 §2.1: `checks.py` → `domain` only). It adds no seam, no Protocol, no
injected dependency; AEA-38 calls the functions directly. Module rules from AEA-02 plan §4.0 apply: `from __future__
import annotations` first, `import datetime as dt`, one statement per line, absolute imports, `[0-9]` never `\d` in
regexes, no module-level instance except immutable constants and compiled regexes, no clock read.

### Step 1. Preconditions (stop if any fails)

1. `cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-15 && export UV_LINK_MODE=hardlink && uv sync` (never copy a
   venv; no `node_modules`).
2. AEA-01 is on the base (merged at `07924f5`; this is a guard): `ls pyproject.toml src/meridian/__init__.py tests/unit/__init__.py tests/journeys/affected.py`
   all exist. If not: **stop, report `blocked-on AEA-01`**.
3. AEA-02 is on the base. Run:
   ```bash
   uv run python - <<'EOF'
   import typing
   from meridian.domain.actions import ActionKind, CompletedAction, Settled
   from meridian.domain.handoff import BriefExtraction, Quote, SourceRef
   from meridian.domain.state import ChatLine
   from meridian.domain.tools import LookupRow
   from meridian.domain.turn import CheckResult, Claim, Removal, TurnFacts, GateKind
   from meridian.domain.records import Passage
   print("claim kinds:", typing.get_args(Claim.model_fields["kind"].annotation))
   print("removal reasons:", typing.get_args(Removal.model_fields["reason"].annotation))
   print("only_turn:", hasattr(Settled, "only_turn"))
   print("TurnFacts fields:", list(TurnFacts.model_fields))
   import meridian.domain.turn as t
   print("EvidenceSet in turn:", hasattr(t, "EvidenceSet"), "QuoteCheck in turn:", hasattr(t, "QuoteCheck"))
   EOF
   ```
   It must import cleanly, list `"quote"` among the claim kinds, `"quote_not_found"` among the reasons, and print
   `only_turn: True`. If an import fails or `"quote"` / `only_turn` is missing: **stop, report `blocked-on AEA-02`**
   (name the missing piece; a missing `Claim` kind is an AEA-02 follow-up, ticket *Agent handoff*). If a name exists
   but in another `meridian.domain` module, find it with `grep -rn "^class <Name>" src/meridian/domain` and import it
   from its defining module (re-exports with `as Name` also work); record the change in the report.
4. Type homes (PD-13):
   - `EvidenceSet in turn: True` → import it from `meridian.domain.turn` (the expected case).
   - `EvidenceSet in turn: False` → define it in `checks.py` exactly as DO-4 §10 writes it (six fields of §4, a
     `MeridianModel`); record that in the report.
   - `QuoteCheck in turn: False` → define it in `checks.py` as §4 writes it (the expected case).
   - `QuoteCheck in turn: True` → import it from `meridian.domain.turn` and do not define it.
5. Note the printed `TurnFacts` field list: the test helper in §7.1 passes exactly those fields.

### Step 2. Sentences (private helpers)

```python
_BOUNDARY: Final = re.compile(r"[.!?]+[\"'”’)\]]*(?=\s|$)|\n")
_NO_SPLIT: Final = re.compile(
    r"(?i)(?:\b(?:a\.m|p\.m|e\.g|i\.e|mr|mrs|ms|dr|st|vs|approx|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\.)$"
)

def _sentences(text: str) -> list[tuple[int, int]]: ...
def _rejoin(text: str, spans: Sequence[tuple[int, int]], removed: set[int]) -> str: ...
```

`_sentences(text)`, numbered:
1. `pos = 0`, `spans = []`.
2. For each `m` in `_BOUNDARY.finditer(text)`:
   1. If `m.group() == "\n"`: `end = m.start()`.
   2. Else, if `m.group() == "."` and `_NO_SPLIT.search(text[max(0, m.start() - 8):m.end()])` → `continue` (no split).
   3. Else `end = m.end()`.
   4. If `text[pos:end].strip()`: append `(pos, end)`. Then `pos = m.end()`.
3. If `text[pos:].strip()`: append `(pos, len(text))`.
4. Trim each span: move `start` right over whitespace and `end` left over whitespace. Return the list.
*Invariant: the spans are in order, never overlap, and each holds non-blank text; `text[s:e]` is the sentence.*

`_rejoin(text, spans, removed)` (PD-11): walk the kept indexes in order; between kept spans `(s1, e1)` and `(s2, e2)`
the gap is `text[e1:s2]`; joiner `"\n\n"` if `"\n\n"` in the gap, `"\n"` if `"\n"` in the gap, else `" "`. Return
the joined string `.strip()`; `""` when nothing is kept.

### Step 3. Completion lexicon (module constants, exact members)

```python
COMPLETION_WORDS: Final[dict[ActionKind, tuple[str, ...]]] = {
    ActionKind.BOOKED: ("booked", "i've scheduled", "i have scheduled", "we've scheduled", "we have scheduled",
                        "has been scheduled", "have been scheduled", "is now scheduled"),
    ActionKind.MOVED: ("moved", "rescheduled"),
    ActionKind.CANCELLED: ("cancelled", "canceled"),
    ActionKind.CHANGE_REQUEST_SENT: ("sent your change request", "sent a change request", "sent the change request",
                                     "change request has been sent", "change request is sent",
                                     "recorded your change request", "logged your change request",
                                     "passed your change request"),
    ActionKind.CASE_OPENED: ("opened a case", "created a case", "created a request", "case is open",
                             "case has been opened", "case has been created", "request has been created"),
    ActionKind.FOLLOWUP_SAVED: ("saved your email", "saved your phone", "saved your number", "saved your contact",
                                "saved how to reach you", "saved your preference"),
    ActionKind.VERIFIED: ("you're verified", "you are verified", "you've been verified", "you have been verified",
                          "verified your identity", "identity is verified", "identity has been verified",
                          "identity is confirmed", "confirmed your identity"),
}
GENERIC_COMPLETION_WORDS: Final[tuple[str, ...]] = ("done", "all set", "taken care of", "sorted", "finished",
                                                    "completed", "that's handled")
UNBACKED_COMPLETION_WORDS: Final[tuple[str, ...]] = ("refunded", "turned off", "switched off", "auto-renew is off",
                                                     "auto-renewal is off", "auto-renew is now off",
                                                     "auto-renewal is now off", "e-mailed")
_NOT_A_CLAIM_BEFORE: Final = frozenset({
    "not", "no", "never", "cant", "cannot", "couldnt", "wont", "wouldnt", "isnt", "wasnt", "arent", "werent",
    "hasnt", "havent", "hadnt", "didnt", "dont", "doesnt",
    "if", "once", "until", "unless", "when", "whether", "before", "after",
    "will", "would", "can", "could", "should", "shall", "may", "might",
    "want", "wants", "need", "needs",
})
_CLAUSE_MARK: Final = re.compile(r"[,;:()—–]|\s-\s")
_WORD: Final = re.compile(r"[a-z]+(?:['’][a-z]+)?")
```

Sources: R-46 words ("done", "cancelled", "moved", "refunded", "turned off"); GRN-1 (generic, verbatim); SP-1
`_CLAIMS` (booked/scheduled phrases, "auto-renew is off", "e-mailed"); WP-8 required output ("I've created a request");
PD-3 (what is left out).

Helpers:

1. `_phrase_rx(phrase: str) -> re.Pattern[str]`: build the pattern character by character: `'` → `['’]?`;
   space → `\s+`; `-` → `[-\s]?`; anything else → `re.escape(ch)`. Wrap as `(?<!\w)` + body + `(?!\w)`, flag
   `re.IGNORECASE`. Compile every phrase of the three lists once at import into
   `_KIND_RX: Final[tuple[tuple[ActionKind, re.Pattern[str]], ...]]` (in dict order, then phrase order),
   `_GENERIC_RX: Final[tuple[re.Pattern[str], ...]]`, `_UNBACKED_RX: Final[tuple[re.Pattern[str], ...]]`.
2. `_suppressed(sentence: str, start: int) -> bool` (PD-4): `before = sentence[:start]`;
   `cut = max((m.end() for m in _CLAUSE_MARK.finditer(before)), default=0)`;
   `words = [w.replace("'", "").replace("’", "") for w in _WORD.findall(before[cut:].lower())]`;
   return `any(w in _NOT_A_CLAIM_BEFORE for w in words[-4:])`.
   *Invariant: only words of the same clause, at most 4 back, can cancel a claim.*

### Step 4. `check_completion(text, settled) -> CheckResult`

Private helpers first:

- `_APPT_KINDS: Final = frozenset({ActionKind.BOOKED, ActionKind.MOVED, ActionKind.CANCELLED,
  ActionKind.CHANGE_REQUEST_SENT})`, `_CASE_KINDS: Final = frozenset({ActionKind.CASE_OPENED,
  ActionKind.FOLLOWUP_SAVED})`.
- `_APPT_REF: Final = re.compile(r"\bappointment\s+(?:#\s*|no\.?\s*|number\s+)?([0-9]+)(?![0-9:])", re.I)`,
  `_CASE_REF: Final = re.compile(r"\bMHC-C-[0-9]{4}\b", re.I)`,
  `_CUSTOMER_REF: Final = re.compile(r"\bMHC-[0-9]{5}\b", re.I)`.
- `_named_refs(kind, sentence) -> frozenset[str]` (PD-5):
  - `kind in _APPT_KINDS`: `{"appointment:" + str(int(g)) for each _APPT_REF match group 1}` ∪
    `{f"md:{d.month:02d}-{d.day:02d}"` for every **date** claim `_fact_claims(sentence)` returns (step 5; parse the
    claim value: `"--MM-DD"` → month, day; else `dt.date.fromisoformat`)`}`.
  - `kind in _CASE_KINDS`: `{"case:" + m.group().upper() for m in _CASE_REF.finditer(sentence)}`.
  - `kind is ActionKind.VERIFIED`: `{"customer:" + m.group().upper() for m in _CUSTOMER_REF.finditer(sentence)}`.
- `_action_refs(a, settled) -> frozenset[str]`:
  1. `refs = set()`; for `key, prefix` in `(("case", "case:"), ("customer", "customer:"))`: if `key in a.records`, add
     `prefix + a.records[key].upper()`.
  2. If `"appointment" in a.records`: `appt = a.records["appointment"]`; add
     `"appointment:" + (str(int(appt)) if appt.isdigit() else appt)`; then for `x` in `(a, *[b for b in
     settled.actions if b.records.get("appointment") == appt])`, for `d` in `(x.before, x.after)` when `d` is not
     `None` and `"date" in d`: try `day = dt.date.fromisoformat(d["date"])` (skip on `ValueError`) and add
     `f"md:{day.month:02d}-{day.day:02d}"`.
  3. Return `frozenset(refs)`.
- `_backed(kind, sentence, settled) -> bool`: `actions = [a for a in settled.actions if a.kind == kind]`; if none →
  `False`; `named = _named_refs(kind, sentence)`; if not `named` → `True`; return
  `any(named <= _action_refs(a, settled) for a in actions)`. *Invariant: a claim passes only on a stored action of its
  kind, for the record the sentence names (R-46; SDQ-8 A).*

`check_completion`, numbered:
1. `spans = _sentences(text)`; `removed: set[int] = set()`; `removals: list[Removal] = []`.
2. For each index `i`, `(s, e)` in `spans`: `sentence = text[s:e]`; collect `found: list[tuple[Claim, str, bool]]`
   (claim, group, passes):
   1. For each `(kind, rx)` in `_KIND_RX`, each `m` in `rx.finditer(sentence)` with `not _suppressed(sentence,
      m.start())`: `Claim(kind="completion", span=(s + m.start(), s + m.end()), value=m.group(), action_kind=kind)`,
      group `"specific"`, passes `_backed(kind, sentence, settled)`.
   2. For each rx in `_UNBACKED_RX`, each unsuppressed match: claim with `action_kind=None`, group `"unbacked"`,
      passes `False`.
   3. For each rx in `_GENERIC_RX`, each unsuppressed match: claim with `action_kind=None`, group `"generic"`, passes
      `any(p for _, g, p in found if g == "specific")` computed **after** sub-steps 1–2 (GRN-1).
   4. `failing = sorted((c for c, _, p in found if not p), key=lambda c: c.span[0])`. If `failing`: add `i` to
      `removed`; append `Removal(claim=failing[0], reason="no_completed_action")` (PD-1).
3. If no removal: `return CheckResult(text=text, removals=(), passed=True)`.
4. Else `return CheckResult(text=_rejoin(text, spans, removed), removals=tuple(removals), passed=False)`.
*Invariant: text survives only in whole sentences whose every claim is backed; `passed` is exactly "no removals".*

### Step 5. Fact claims (private extractor shared by `check_facts` and `build_evidence`)

`_fact_claims(text: str, offset: int = 0) -> list[Claim]`: run the extractors below **in this order**; keep a list of
taken spans and skip any match that overlaps a taken span; each kept match becomes a `Claim` with `span=(offset +
start, offset + end)`; return the claims sorted by `span[0]`. Regexes (compile once; `re.I` where marked):

| # | Kind | Pattern | Value |
|---|---|---|---|
| 1 | `id` | `\b(?:INV-[0-9]{6}|MHC-C-[0-9]{4}|MHC-[0-9]{5})\b` (`re.I`) | `m.group().upper()` |
| 2 | `date` | `\b([0-9]{4})-([0-9]{2})-([0-9]{2})\b` | ISO `YYYY-MM-DD` if `dt.date(y, m, d)` is valid, else skip |
| 3 | `amount` | `\$\s?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.([0-9]{2}))?(?![0-9])` | `str(int(dollars.replace(",", "")) * 100 + int(cents or 0))` |
| 4 | `time` ×2 | range: `\b([0-9]{1,2})(?::([0-5][0-9]))?\s*(?:-|–|—|to)\s*([0-9]{1,2})(?::([0-5][0-9]))?\s*(a\.?\s?m\.?|p\.?\s?m\.?)(?![a-z])` (`re.I`) | two claims: first span `(m.start(1), m.end(2) if m.group(2) else m.end(1))`, second span `(m.start(3), m.end())`; rule below |
| 5 | `time` | `\b([0-9]{1,2})(?::([0-5][0-9]))?\s*(a\.?\s?m\.?|p\.?\s?m\.?)(?![a-z])` (`re.I`) | `HH:MM` 24-hour |
| 6 | `time` | `\b([01]?[0-9]|2[0-3]):([0-5][0-9])\b` | `f"{h:02d}:{mm}"` |
| 7 | `time` | `\b(noon|midday|midnight)\b` (`re.I`) | `"12:00"`, `"12:00"`, `"00:00"` |
| 8 | `date` | `\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\.?\s+([0-9]{1,2})(?:st|nd|rd|th)?(?:,?\s+([0-9]{4}))?(?![0-9])` (`re.I`) | year given → ISO; else `f"--{month:02d}-{day:02d}"`; skip when invalid (check with `dt.date(year or 4, month, day)`) |
| 9 | `date` | `\b([0-9]{1,2})/([0-9]{1,2})(?:/([0-9]{4}|[0-9]{2}))?\b` | month/day; a 2-digit year means `2000 + yy`; same output and validity rule as #8 |
| 10 | `number` | `(?<![\w.,])[0-9]+(?:[.,][0-9]+)*(?![0-9])` | `_norm_number(m.group())` |

Month map: `jan`/`january` → 1 … `sep`/`sept`/`september` → 9 … `dec`/`december` → 12 (lower-cased key).

**12-hour conversion** `_to_24(h, mm, meridiem)`: `h` must be 1–12, else the match is skipped (left for the number
extractor). `am`: `h % 12`; `pm`: `h % 12 + 12`. Value `f"{h24:02d}:{mm or '00'}"`. The meridiem is `"am"` when the
captured text (lower-cased, dots and spaces removed) starts with `a`, else `"pm"`.

**Range rule (#4):** the second time takes the captured meridiem. The first takes the **same** meridiem unless that
makes it later than the second (in minutes), in which case it takes the other (`"8-12pm"` → `08:00`, `12:00`;
`"12–4pm"` → `12:00`, `16:00`). Skip the whole match if either hour is outside 1–12.

`_norm_number(s: str) -> str`: `s = s.replace(",", "")`; `ip, _, fp = s.partition(".")`; `ip = ip.lstrip("0") or "0"`;
`fp = fp.rstrip("0")`; return `f"{ip}.{fp}" if fp else ip`. (`"02"` → `"2"`, `"2.50"` → `"2.5"`, `"10.0"` → `"10"`.)

*Invariant: each character of the text belongs to at most one fact claim, so "$478.00" is one amount, never also a
number, and "2026-11-01" is one date.*

Worked example: `"Marta arrives 8:00 a.m. to 12:00 p.m. on October 19; the fee is $89.00."` → claims `time 08:00`,
`time 12:00`, `date --10-19`, `amount 8900` (no number claims).

### Step 6. `build_evidence(facts, settled, lookups, chat=None) -> EvidenceSet`

Constants:

```python
_YEARLESS_YEAR: Final = 4
_SKIP_KEYS: Final = frozenset({
    "score", "confidence", "probabilities",                      # model and ranking scores, never facts
    "thread_id", "turn_id", "request_id", "task_id", "opened_turn", "shown_turn", "message_id", "tool_call_id",
    "run_id", "key", "version",                                  # internal identifiers (UUIDs, row keys, versions)
    "passage_id", "passage_ids", "quick_checks",                 # KB locators ("faq/x.md#3")
    "at", "read_at",                                             # write and read timestamps, not stated facts
})
```

A private collector class (plain class, not pydantic), `_Collector`, with `amounts: set[int]`, `dates: set[dt.date]`,
`times: set[str]`, `ids: set[str]`, `numbers: set[str]`, `sources: dict[str, SourceRef]`, and:

- `add(kind, value, source)`: put the value in its set (amount → `int(value)`; date → `dt.date.fromisoformat(value)`,
  or `dt.date(_YEARLESS_YEAR, mm, dd)` for `"--MM-DD"`; others as strings); `sources.setdefault(f"{kind}:{value}",
  source)`. Then the PD-8 derived numbers: a time adds `str(int(hh) % 12 or 12)`; a date adds `str(day)`; an amount
  with `cents % 100 == 0` adds `str(cents // 100)` (each via `add("number", …, source)`).
- `add_text(text, source)`: `for c in _fact_claims(text): add(c.kind, c.value, source)`.
- `walk(value: object, key: str, source: SourceRef)`, in this order of checks:
  1. `key in _SKIP_KEYS` → return.
  2. `value is None` or `isinstance(value, bool)` → return.
  3. `isinstance(value, str)` (enums included) → `add_text(value, source)`.
  4. `isinstance(value, int)` → `add("amount", str(value), source)` if `key.endswith("_cents")` else
     `add("number", str(value), source)`.
  5. `isinstance(value, float)` → `add("number", _norm_number(f"{value:.2f}"), source)`.
  6. `isinstance(value, dt.datetime)` → `add("date", value.date().isoformat(), source)` and
     `add("time", f"{value.hour:02d}:{value.minute:02d}", source)` (as stored; no time-zone conversion). This check
     comes **before** the `dt.date` check (a `datetime` is a `date`).
  7. `isinstance(value, dt.date)` → `add("date", value.isoformat(), source)`.
  8. `isinstance(value, MeridianModel)` → `walk(value.model_dump(mode="python"), key, source)` (every domain model,
     `LLMFacing` included, derives from `MeridianModel`; `pydantic` itself is not imported, AC-12).
  9. `isinstance(value, Mapping)` → `walk(v, str(k), source)` for each item.
  10. `isinstance(value, (list, tuple, set, frozenset))` → `walk(v, key, source)` for each item.
  11. Anything else (`SecretStr`, bytes, …) → ignored.

`build_evidence`, numbered (walk order = source precedence, PD-10):
1. `col = _Collector()`.
2. For each `row` in `lookups`: `ref = SourceRef(kind="lookup_log", ref=str(row.id))`;
   `col.walk(row.record_ids, "record_ids", ref)`; `col.walk(row.result_seen, "result_seen", ref)`.
3. For each `a` in `settled.actions`: `col.walk(a.model_dump(mode="python"), "action", _action_source(a))` where
   `_action_source(a) = SourceRef(kind="action", ref=f"{a.key.kind.value}:{a.key.record_id}:{a.key.turn_id}")`.
4. If `settled.open_case` is not `None`: `col.walk(settled.open_case.model_dump(mode="python"), "open_case",
   SourceRef(kind="action", ref=f"case_opened:{settled.open_case.case_ref}"))`.
5. For each `name` in `type(facts).model_fields` (declaration order), skipping names in `_SKIP_KEYS`;
   `value = getattr(facts, name)`:
   - `name == "writes_this_turn"`: each action as step 3.
   - `name == "handoff"` and `value` is not `None`: `col.walk(value.action.model_dump(mode="python"), "action",
     _action_source(value.action))`, then `col.walk(value.model_dump(mode="python", exclude={"action"}), "handoff",
     SourceRef(kind="action", ref=f"case_opened:{value.case.case_ref}"))`.
   - `name == "passages"`: each passage `p`: `col.walk(p.model_dump(mode="python"), "passage",
     SourceRef(kind="policy_row", ref=str(p.passage_id)))`.
   - `name == "points"`: each point `k`: `col.walk(k.model_dump(mode="python"), "point",
     SourceRef(kind="policy_row", ref=str(k.passage_id)))`.
   - otherwise: `col.walk(value, name, SourceRef(kind="rule", ref=f"turn_facts.{name}"))` (the walk dumps models
     itself, rule 8).
6. If `chat` is not `None`: for `index, line` in `enumerate(chat)`: `col.add_text(line.text, SourceRef(kind="message",
   ref=str(line.turn_id) if line.turn_id is not None else f"line:{index}"))`.
7. Return `EvidenceSet(amounts_cents=frozenset(col.amounts), dates=frozenset(col.dates), times=frozenset(col.times),
   ids=frozenset(col.ids), numbers=frozenset(col.numbers), sources=dict(col.sources))`.
*Invariant: every value in the set traces to a lookup row, a stored action, the turn's facts or (brief only) the chat;
the chat never enters a reply's evidence.*

### Step 7. `check_facts` and `check_quotes`

`_supported(claim, ev) -> bool`:
- `amount` → `int(claim.value) in ev.amounts_cents`.
- `date` → value `"--MM-DD"`: `any(d.month == mm and d.day == dd for d in ev.dates)`; else
  `day = dt.date.fromisoformat(value)`: `day in ev.dates or dt.date(_YEARLESS_YEAR, day.month, day.day) in ev.dates`
  (PD-7).
- `time` → `claim.value in ev.times`; `id` → `claim.value in ev.ids`; `number` → `claim.value in ev.numbers`.

`check_facts(text, evidence)`, numbered:
1. `spans = _sentences(text)`; for each `i, (s, e)`: `claims = _fact_claims(text[s:e], offset=s)`;
   `bad = [c for c in claims if not _supported(c, evidence)]`; if `bad`: add `i` to `removed`, append
   `Removal(claim=bad[0], reason="not_in_evidence")` (PD-1).
2. No removal → `CheckResult(text=text, removals=(), passed=True)`; else `CheckResult(text=_rejoin(...),
   removals=tuple(removals), passed=False)`.
*Invariant: no number, date, time, ID or amount reaches the customer (or the brief's heading 7) unless the evidence
holds it (R-46; R-28 "0 invented facts").*

`check_quotes(extraction, shown)`, numbered (GRN-3):
1. `kept_needs`, `kept_claims`, `removals` empty lists.
2. For each `q` in `extraction.needs`, then each `q` in `extraction.claims` (that order):
   `ok = q.text != "" and q.message_id in shown and q.text in shown[q.message_id]` (exact, case-sensitive substring;
   PD-12). If `ok`, append `q` to its own kept list; else append
   `Removal(claim=Claim(kind="quote", span=(0, len(q.text)), value=str(q.message_id)), reason="quote_not_found")`.
3. Return `QuoteCheck(needs=tuple(kept_needs), claims=tuple(kept_claims), removals=tuple(removals),
   passed=not removals)`.
*Invariant: heading 2 and heading 4 show only words the customer actually wrote, in the message the model was shown.*

### Step 8. Tests, then commit 1

Write `tests/unit/test_checks.py` (§7.1). Iterate with §7.3 rows 1–4 until green. If a §7.1 expectation fails, fix
`checks.py` toward this plan; **never change an expected value**. If an expectation looks wrong, stop and send the
plan back to the planner.

`git add src/meridian/checks.py tests/unit/test_checks.py`, then commit:

```
checks: R-46 completion, fact and quote checks (AEA-15)

check_completion against settled (SDQ-8 A), build_evidence, check_facts,
check_quotes (GRN-3); generic completion words need a backed claim (GRN-1).
Refs #15

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```

Note the short SHA (`git rev-parse --short HEAD`); steps 9 and 10 cite it.

### Step 9. Journey record `docs/testing/journeys/<YYYY-MM-DD>-AEA-15.md` (AC-13)

Create the folder if missing. Content (fields of `integrated-journeys.md` §4; fill `<…>`):

```markdown
# Journey record: AEA-15 R-46 checks

| Field | Value |
|---|---|
| Claim | `checks.py` removes unbacked completion claims, unsupported numbers, dates, times, IDs and amounts, and quotes not in the customer's message (AEA-15). No journey runs it yet. |
| Level | `mock-tested` |
| Tested revision | `<commit-1 short SHA>` |
| Environment | VPS worktree `inno-aea-callcenter-wt/AEA-15`; Python 3.12 via `uv`; no server, no database, no model |
| Command | `uv run pytest tests/unit/test_checks.py -q` |
| Result | <N passed> |
| Evidence location | GitLab issue #15 comment; this file |
| Remaining limitations | Unit level only: the reply node that calls these checks (AEA-38), the events built from the removals, and a real responder draft through the server are not exercised |
| Blocked by | AEA-57 (journey harness, wave 2) |
| Journeys that will exercise this code | **J-2** (the completion and fact checks on grounded answers), once AEA-57 and AEA-51 land |
```

No secrets, phone numbers or transcript text in it.

### Step 10. Context rows (AC-14), then commit 2

1. `.claude/reference/area-map.md`, row
   `| 3 | **A7c Reply** | Turn facts, responder, brief extraction, R-46 checks | `agent/nodes/reply.py`, `checks.py`, `agent/prompts/reply.py` | AEA-15, 38 | planned |`:
   change **only the last cell** to `` `checks.py` actual (AEA-15, `<commit-1 SHA>`); `nodes/reply.py`, `prompts/reply.py` planned ``.
2. `.claude/state/icm-progress.md`: on `main` the row *Routes verified against code and tests* appears **twice** (one
   line starts `| Routes verified against code and tests | provisional | 2026-10-21: first backend slice AEA-04`, the
   other `| Routes verified against code and tests | provisional | 2026-10-21: area map A0 →`). Context-maintenance rule 6
   wants one row whose evidence is replaced. Replace **every** line that starts `| Routes verified against code and
   tests |` with this single line, at the position of the first one (≤ 400 characters; fill `<…>`):
   `| Routes verified against code and tests | provisional | 2026-10-21: area map A7c → `checks.py` checked by `tests/unit/test_checks.py` (AEA-15, `<commit-1 SHA>`; <N> pass); earlier slices' evidence in `docs/testing/journeys/` | Each slice replaces this evidence; verified when every area-map row is actual |`
   If the base shows a status higher than `provisional` (`established`, `verified`), keep that status. Touch no other
   row and not the `Last reconciled` line.
3. `docs/design/code-design.md` §3 tree: append three spaces and `built AEA-15 <commit-1 SHA>` to the end of the line
   `├── checks.py                                    R-46: evidence, completion check (lexicon inline), facts    A7c   3`
   (the same form as the `privacy/redact.py` line's `   built AEA-04 9145044`). Change nothing else in that line (the
   wave column stays `3`; see §8), and do not touch the shared `**Built:**` line or the status paragraph at the top of
   the file (slice plan §3: "each ticket changes only its own row").
4. `git add docs/testing/journeys/<YYYY-MM-DD>-AEA-15.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`;
   message `docs: AEA-15 journey record and context rows` + blank line + `Refs #15` + blank line +
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
5. `git diff --name-only main...HEAD` must list exactly the six owned files of §2 (AC-14 evidence).

### What the implementer must NOT do

- Define or copy `Claim`, `Removal`, `CheckResult`, `CheckEvent`, `Settled`, `TurnFacts`, `LookupRow`, `Quote` or any
  other domain type (only `QuoteCheck`, and `EvidenceSet` in the one case of step 1.4). Import nothing from `meridian`
  except the §4 lines. Never mention `CheckEvent` in `checks.py` (AC-11 greps the source for it).
- Import `logging`, call `print`, `open` or any clock (`now`, `today`, `utcnow`); read files; call a model; import
  `meridian.services`, `meridian.agent`, `meridian.adapters`, `meridian.web`, `meridian.policy` or `docs/parked/**`.
- Rewrite the model's words: only whole sentences (or whole quotes) are removed; nothing is appended (no fallback, no
  promise, no reference).
- Add "scheduled", "waived" or "credited" as bare completion words (PD-3), or loosen PD-4's window.
- Put a full phone number, card-like number, verification code or transcript text in the tests; test ids are short
  case names, never message text.
- Edit `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/unit/test_import_direction.py`, any `domain/*` file,
  another ticket's file, `apps/web/**`, `docs/ux/**` or the OpenAPI file; run the full suite (not required: no shared
  fixture, setting, dependency or widely-imported module changes; nothing imports `checks.py` yet); run pytest with
  `-n` above 2; `git add -A`; push; force-push.

---

## 6. Data and fixtures

All synthetic, built inline in `tests/unit/test_checks.py`; values come from the worked pairs and the AEA-02 plan's
§6 fixtures so the two tickets describe the same WP-4F turn. No file fixture, no seed, no issued data read.

| Fixture | Value | Source |
|---|---|---|
| `THREAD` | `ThreadId("3f1c2a4e-8b7d-4e21-9a6b-5c0d7e8f9a10")` | AEA-02 plan §6 |
| `TURN_3`, `TURN_4` | `TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")`, `TurnId("a2b4c6d8-1e3f-4a5b-8c7d-9e0f1a2b3c4d")` | AEA-02 plan §6 |
| `DIGIT_THREAD` | `ThreadId("12345678-1234-4123-8123-123456789012")` (all-digit groups, a valid UUID4) | synthetic: proves skipped keys never become numbers |
| `NOW` | `dt.datetime(2026, 10, 16, 10, 12, tzinfo=ZoneInfo("America/Chicago"))` | DEMO_START 2026-10-16 10:00 (cases.md §1.1) |
| `MOVED_T3` (WP-4F) | `kind=MOVED`, key `(THREAD, TURN_3, MOVED, "159")`, `records={"appointment": "159", "slot": "56", "old_slot": "159"}`, `before={"date": "2026-10-22", "window": "08:00-12:00"}`, `after={"date": "2026-10-19", "window": "08:00-12:00", "technician": "Marta Kowalski", "service_type": "hvac_repair", "fee_line": "fee line (fixture)"}`, `at=NOW` | AEA-02 plan §6 (issued appointment 159, slot 56) |
| WP-4F draft | `"Yes, it's moved: Monday, October 19, 8:00 am to 12:00 pm with Marta."` | DO-3 §1 *Output* |
| WP-8 drafts | `"Done, auto-renew is off. Auto-renewal can be cancelled any time before the renewal date."`; honest reply `"I can't switch off auto-renewal from this chat. I've created a request for a representative to do it before your renewal date of November 3."` | WP-8 *Must never*, required output step 4 |
| WP-2 invoice lookup row | `LookupRow(tool="account_read", record_ids=("INV-204411",), passage_ids=(), result_seen="INV-204411 2026-10-02 due 2026-11-01 $89.00 $245.00 $144.00 total $478.00", message_id=5, turn_id=TURN_3, id=7, thread_id=THREAD)` (73 characters of `result_seen`) | WP-2 required output step 2 (seeded MHC-10002, INV-204411) |
| WP-7 customer message | `shown = {3: "I want a full refund on the repair. It didn't fix anything and I had to call another company."}` | WP-7 (AEA-05 plan's WP-7 input) |
| Fee passage | `Passage(passage_id=PassageId("pricing/2026_fee_schedule.pdf#2"), file="pricing/2026_fee_schedule.pdf", section="Fees", version_label="undated", version_date=None, text="Late cancellation (<24h) $49", score=0.82)` | KB fee schedule line quoted in cases.md §2 |

**Builders** (in the test file; build models with `Model.model_validate({...})` where a dict literal would upset
mypy's `init_typed`, IDs as `ThreadId("…")` / `TurnId("…")`, enums as `ActionKind.X`):

- `_action(kind: ActionKind, record_id: str, *, turn: TurnId = TURN_3, records: dict[str, str] | None = None,
  before: dict[str, str] | None = None, after: dict[str, str] | None = None, thread: ThreadId = THREAD) ->
  CompletedAction` via `CompletedAction.model_validate({"key": {...}, "kind": kind, "records": records or {},
  "before": before, "after": after, "at": NOW})`.
- `_settled(*actions: CompletedAction) -> Settled` → `Settled(actions=actions, open_case=None, read_at=NOW)`.
- `_facts(**overrides: object) -> TurnFacts` → `TurnFacts.model_validate({"turn_id": TURN_4, "gate_kind":
  GateKind.FREE_TEXT, "plan_mode": "talk", "points": [], "passages": [], "no_source_tasks": [], "windows_shown": [],
  "writes_this_turn": [], "change_request": None, "handoff": None, "escalation": None, "identity_step": None,
  **overrides})`. If step 1.5's field list differs (a field added or removed by AEA-02), pass exactly the printed
  fields with their empty value (`[]` / `None`); change nothing else.
- `_every_kind_settled()` → one action per `ActionKind` (record ids `"1"`…`"7"`; `records` holding the matching key:
  appointment kinds `{"appointment": "<id>"}`, `CASE_OPENED`/`FOLLOWUP_SAVED` `{"case": "MHC-C-0009"}`, `VERIFIED`
  `{"customer": "MHC-10001"}`).

---

## 7. Checks

### 7.1 `tests/unit/test_checks.py`: the tests to write with the code

Imports: `datetime as dt`, `logging`, `subprocess`, `sys`, `ast`, `pathlib.Path`, `zoneinfo.ZoneInfo`, `pytest`;
`import meridian.checks as checks_mod`; `from meridian.checks import COMPLETION_WORDS, GENERIC_COMPLETION_WORDS,
UNBACKED_COMPLETION_WORDS, build_evidence, check_completion, check_facts, check_quotes` (plus `QuoteCheck` /
`EvidenceSet` from wherever step 1.4 put them); the domain types from their §4 homes. Use `pytest.mark.parametrize` with
short `ids=`. Assertion messages name case ids, never message text.

| Test | Cases and expected result |
|---|---|
| `test_wp4f_move_from_earlier_turn_passes` (AC-1, **WP-4F worked pair**) | `check_completion(WP4F_DRAFT, _settled(MOVED_T3))` → `text == WP4F_DRAFT`, `removals == ()`, `passed is True` |
| `test_wp8_done_without_write_removed` (AC-2, **WP-8 worked pair**) | `check_completion(WP8_DRAFT, _settled())` → `text == "Auto-renewal can be cancelled any time before the renewal date."`, `len(removals) == 1`, `removals[0].reason == "no_completed_action"`, `removals[0].claim.kind == "completion"`, `passed is False`. (The second sentence's "cancelled" follows "can be": "can" is in the PD-4 window, so it is not a claim.) |
| `test_generic_done_needs_backed_kind` (AC-3) | `booked = _settled(_action(BOOKED, "5", records={"appointment": "5"}, after={"date": "2026-10-20", "window": "08:00-12:00"}))`. `"Done, your visit is booked."` + `booked` → kept, `passed`; `"Done, auto-renew is off."` + `booked` → `text == ""`, one removal; `"Done!"` + `booked` → `text == ""`. Then `assert GENERIC_COMPLETION_WORDS == ("done", "all set", "taken care of", "sorted", "finished", "completed", "that's handled")` and, for each word `w`, `check_completion(w[0].upper() + w[1:] + ".", _settled())` gives one removal whose `claim.action_kind is None` and `claim.value.lower() == w`; plus `"That’s handled."` (curly apostrophe) → one removal |
| `test_r46_words_are_claims` (AC-4) | `"Your visit is cancelled."` + `_settled()` → removed, `claim.action_kind is ActionKind.CANCELLED`; + `_settled(_action(CANCELLED, "1", records={"appointment": "1"}))` → kept. `"Your visit is moved."` same pair with `MOVED`. `"Your payment has been refunded."` and `"Auto-renew has been turned off."` + `_every_kind_settled()` → removed, `claim.action_kind is None`. Also `"cancelled" in COMPLETION_WORDS[ActionKind.CANCELLED]`, `"moved" in COMPLETION_WORDS[ActionKind.MOVED]`, `{"refunded", "turned off"} <= set(UNBACKED_COMPLETION_WORDS)`, `set(COMPLETION_WORDS) == set(ActionKind)` |
| `test_claim_must_match_named_record` (AC-5) | `cancel_1 = _settled(_action(CANCELLED, "1", records={"appointment": "1"}, before={"date": "2026-10-16", "window": "12:00-16:00"}))`: `"Your October 16 visit is cancelled."` → kept; `"Your October 22 visit is cancelled."` → removed (`action_kind CANCELLED`); `"Appointment 1 is cancelled."` → kept; `"Appointment 2 is cancelled."` → removed. Cross-action index: `_settled(_action(BOOKED, "3", records={"appointment": "3"}, after={"date": "2026-10-23", "window": "08:00-12:00"}), _action(CANCELLED, "3", records={"appointment": "3"}))` + `"Your October 23 visit is cancelled."` → kept |
| `test_only_turn_reading_same_function` (AC-6) | `check_completion(WP4F_DRAFT, _settled(MOVED_T3).only_turn(TURN_4))` → `text == ""`, `len(removals) == 1`, `removals[0].claim.action_kind is ActionKind.MOVED`, `passed is False` |
| `test_wp2_fact_check_amounts` (AC-7, **WP-2 worked pair**) | `ev = build_evidence(_facts(), _settled(), [WP2_ROW])`; text `"Invoice INV-204411 is due November 1. The total is $478.00. The after-hours dispatch line is $144. The after-hours line is $149."` → `text == "Invoice INV-204411 is due November 1. The total is $478.00. The after-hours dispatch line is $144."`, one removal, `claim.kind == "amount"`, `claim.value == "14900"`, `reason == "not_in_evidence"` |
| `test_chat_evidence_only_for_brief` (AC-8) | `chat = (ChatLine(speaker="customer", text="The tech has come out 3 times already.", turn_id=TURN_3, at=NOW), ChatLine(speaker="assistant", text="I'm sorry to hear that.", turn_id=TURN_3, at=NOW))`; text `"The technician has visited 3 times."`: with `build_evidence(_facts(), _settled(), [])` → removed (`claim.kind == "number"`, `value == "3"`); with `build_evidence(_facts(), _settled(), [], chat)` → kept, and `ev.sources["number:3"] == SourceRef(kind="message", ref=str(TURN_3))` |
| `test_quote_must_be_exact_substring` (AC-9) | `extraction = BriefExtraction(needs=[Quote(message_id=3, text="I want a full refund on the repair.")], claims=[Quote(message_id=3, text="It didn't fix anything"), Quote(message_id=3, text="It did not fix anything"), Quote(message_id=4, text="I had to call another company"), Quote(message_id=3, text="I had to call another company")], open_decision="Decide whether to refund the repair.")`; `q = check_quotes(extraction, SHOWN)` → `q.needs == (extraction.needs[0],)`, `q.claims == (extraction.claims[0], extraction.claims[3])`, `len(q.removals) == 2`, each `reason == "quote_not_found"` and `claim.kind == "quote"`, values `("3", "4")` in order, spans `(0, len(text))`, `q.passed is False` |
| `test_all_removed_and_clean_results` (AC-10) | `check_completion("Done! It's moved.", _settled())` → `text == ""`, `len(removals) == 2`, `passed is False`; `check_completion("Thanks for waiting.", _settled())` → `passed is True`, `removals == ()`; `check_facts("The fee is $12.", build_evidence(_facts(), _settled(), []))` → `text == ""`, `passed is False`; `check_facts("Thanks.", <same>)` → `passed is True` |
| `test_removed_value_absent_from_text_and_logs` (AC-11) | Inside `caplog.at_level(logging.DEBUG)`: `r = check_facts("Your balance is $913.37. Thanks for waiting.", build_evidence(_facts(), _settled(), []))` and `check_completion("Done, your $913.37 refund is sorted.", _settled())`. Assert `r.text == "Thanks for waiting."`, `"913.37" not in r.text`, `"913" not in caplog.text`, `caplog.records == []`, `capsys.readouterr()` out and err both `""`. Source `Path(checks_mod.__file__).read_text(encoding="utf-8")`: `"CheckEvent" not in src`, `"import logging" not in src`, `"print(" not in src` |
| `test_checks_module_is_pure` (AC-12) | AST of the source: for every `ast.Import` / `ast.ImportFrom` (assert `level == 0`), each name's top-level part is in `sys.stdlib_module_names` or is `__future__`, or the name is `meridian.domain` / starts with `meridian.domain.`; none of the top-level parts is in `{"logging", "os", "io", "pathlib", "subprocess", "socket", "sqlite3", "shutil", "tempfile", "urllib", "http", "asyncio", "time", "random", "sys"}`; no call to a bare name in `{"open", "print", "input", "exec", "eval", "__import__"}`; source has no `".now("`, `".today("`, `"utcnow"`. Then `out = subprocess.run([sys.executable, "-c", "import sys, meridian.checks; print('\\n'.join(sorted(m for m in sys.modules if m.startswith('meridian'))))"], capture_output=True, text=True, check=True).stdout.split()` → no entry starts with `meridian.services`, `meridian.agent`, `meridian.adapters` or `meridian.web`. Print the import list |
| `test_wp8_honest_limit_reply_passes_with_case` (plan-added, US-16) | `case = _settled(_action(CASE_OPENED, "MHC-C-0009", turn=TURN_4, records={"case": "MHC-C-0009"}))`; `check_completion(WP8_HONEST, case)` → unchanged, `passed`; `check_completion(WP8_HONEST, _settled())` → `text == "I can't switch off auto-renewal from this chat."`, one removal with `action_kind is ActionKind.CASE_OPENED`; `check_facts(WP8_HONEST, build_evidence(_facts(), case, [LookupRow(tool="account_read", record_ids=("MHC-10001",), passage_ids=(), result_seen="MHC-10001 standard renewal 2026-11-03", message_id=5, turn_id=TURN_3, id=8, thread_id=THREAD)]))` → `passed` |
| `test_wp4f_facts_match_settled` (plan-added, DO-3 §1 step 8) | `check_facts(WP4F_DRAFT, build_evidence(_facts(), _settled(MOVED_T3), []))` → unchanged, `passed`; and with `_settled()` → `text == ""` (October 19, 8:00, 12:00 have no source) |
| `test_negated_and_conditional_words_are_not_claims` (plan-added, PD-4) | Each with `_settled()` → unchanged, `passed`: `"Your visit has not been moved."`, `"It isn't cancelled yet."`, `"Once you're verified, I can read your invoice."`, `"Would you like it moved to Monday?"`, `"Do you want it cancelled?"`, `"I'll let you know when it's done."`, `"There's no visit booked for that day."`, `"I can't switch off auto-renewal from this chat."`, `"Your tune-up is scheduled for today."` (PD-3), `"The diagnostic fee is credited toward the repair if approved at the same visit."` (PD-3) |
| `test_fact_claim_kinds_and_values` (plan-added, PD-6) | Each text checked with `check_facts(text, empty_ev)` gives one removal with `(claim.kind, claim.value)`: `"It costs $1,250.50."` → `("amount", "125050")`; `"Your invoice is INV-999999."` → `("id", "INV-999999")`; `"See mhc-c-0042 for details."` → `("id", "MHC-C-0042")`; `"See you October 5."` → `("date", "--10-05")`; `"See you Oct. 5th, 2026."` → `("date", "2026-10-05")`; `"It was on 2026-10-05."` → `("date", "2026-10-05")`; `"It was on 10/5."` → `("date", "--10-05")`; `"Arrive at 4pm."` → `("time", "16:00")`; `"Arrive at 4:30 p.m."` → `("time", "16:30")`; `"The window is 12–4pm."` → `("time", "12:00")`; `"Arrive at 14:30."` → `("time", "14:30")`; `"Arrive at noon."` → `("time", "12:00")`; `"You have 17 visits."` → `("number", "17")`; `"It takes 2.50 hours."` → `("number", "2.5")`. `empty_ev = build_evidence(_facts(), _settled(), [])` |
| `test_sentence_split_keeps_abbreviations_and_decimals` (plan-added, PD-11) | `check_facts("Marta arrives 8:00 a.m. to 12:00 p.m. on October 19. The fee is $89.00.\nThanks!", build_evidence(_facts(), _settled(MOVED_T3), []))` → `text == "Marta arrives 8:00 a.m. to 12:00 p.m. on October 19.\nThanks!"`, one removal `("amount", "8900")` |
| `test_evidence_sources_and_skipped_keys` (plan-added, PD-9, PD-10) | `write = _action(BOOKED, "6", turn=TURN_4, thread=DIGIT_THREAD, records={"appointment": "6"}, after={"date": "2026-10-20", "window": "12:00-16:00"})`; `ev = build_evidence(_facts(passages=[FEE_PASSAGE], writes_this_turn=[write]), _settled(), [WP2_ROW])` → `4900 in ev.amounts_cents`, `47800 in ev.amounts_cents`, `"INV-204411" in ev.ids`, `dt.date(2026, 10, 20) in ev.dates`, `"24" in ev.numbers`; `ev.sources["id:INV-204411"] == SourceRef(kind="lookup_log", ref="7")`; `ev.sources["amount:4900"] == SourceRef(kind="policy_row", ref="pricing/2026_fee_schedule.pdf#2")`; `ev.sources["date:2026-10-20"].kind == "action"`; `"12345678" not in ev.numbers` and `"123456789012" not in ev.numbers` (thread id skipped); `"0.82" not in ev.numbers` (score skipped); and `check_facts("A $49 fee applies to changes within 24 hours.", ev).passed is True` |
| `test_numbers_derived_from_times_dates_amounts` (plan-added, PD-8) | `ev = build_evidence(_facts(), _settled(MOVED_T3), [LookupRow(tool="account_read", record_ids=(), passage_ids=(), result_seen="late change fee $49.00", message_id=5, turn_id=TURN_3, id=9, thread_id=THREAD)])`; `check_facts("Marta will arrive between 8 and 12 on the 19th.", ev).passed is True`; `check_facts("That is a 49 dollar fee.", ev).passed is True`; `check_facts("That is a 48 dollar fee.", ev).passed is False` |
| `test_one_removal_per_removed_sentence` (plan-added, PD-1) | `check_completion("Done, it's cancelled and refunded.", _settled())` → one removal, `claim.value == "Done"`; `check_facts("It's $5 on October 2.", empty_ev)` → one removal, `claim.kind == "amount"` |
| `test_empty_inputs` (plan-added) | `check_completion("", _settled())` and `check_facts("", empty_ev)` → `text == ""`, `removals == ()`, `passed is True`; `build_evidence(_facts(), _settled(), [])` → all five sets empty and `sources == {}`; `check_quotes(BriefExtraction.model_construct(needs=[], claims=[], open_decision=""), {})` → `passed is True`, all tuples empty |
| `test_empty_quote_removed` (plan-added, PD-12) | `check_quotes(BriefExtraction.model_construct(needs=[Quote.model_construct(message_id=3, text="")], claims=[], open_decision=""), SHOWN)` → `needs == ()`, one removal `quote_not_found` |

### 7.2 Affected scope

Nothing imports `checks.py` yet; the affected tests are the new file only. Prove it with §7.3 row 5. No journey exists
before AEA-57.

### 7.3 Commands (cheapest first; stop at the first red)

Run from the worktree root with `export UV_LINK_MODE=hardlink`:

| # | Check | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check src/meridian/checks.py tests/unit/test_checks.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check src/meridian/checks.py tests/unit/test_checks.py` | `2 files already formatted` (run without `--check` to fix, then re-run) |
| 3 | Type check | `uv run mypy src/meridian/checks.py tests/unit/test_checks.py` | `Success: no issues found in 2 source files` |
| 4 | Affected tests (while iterating and before the final commit) | `uv run pytest tests/unit/test_checks.py -q` | all pass, no skips (about 22 test functions plus parametrised cases) |
| 5 | Affected scope proof | `grep -rln "meridian.checks\|meridian import checks" src tests eval` | only `tests/unit/test_checks.py` |
| 6 | Affected journeys | `uv run python -m tests.journeys.affected --base main` | `0 journeys affected`, exit 0 (AEA-57 not landed). Record "no journey gate yet" in the report |
| 7 | Diff scope (after commit 2) | `git diff --name-only main...HEAD` | exactly the six owned files of §2 |

No pytest-xdist needed (the file runs in about a second plus one short subprocess); if used at all, `-n 2` at most.
**Full suite: not run** (build-loop rule: no `conftest.py`, setting, dependency or widely-imported module changes).
No test calls a model, a network or a database.

### 7.4 Evidence the implementer reports

Per criterion: AC-1…AC-12 and the plan-added tests as pass lines from row 4; AC-12's printed import list; AC-13 the
record path with its Level and Blocked-by lines and row 6's output; AC-14 row 7's output; the four gate outputs (rows
1–4) with the commands run; step 1's probe output (and any step 1.3 / 1.4 deviation). Verification level for every
claim: `mock-tested`.

---

## 8. Risks and requests

**Collisions with other slices**

- `.claude/reference/area-map.md` A7c row is shared with **AEA-38** (wave 3, later); AEA-15 changes only its last cell.
  `.claude/state/icm-progress.md` row *Routes verified…* is touched by every wave-0/1 ticket's context criterion and
  already appears twice on `main`; step 10.2 collapses it to one row with AEA-15's evidence. A merge conflict there is
  resolved by keeping one row with the newest evidence (context rule 6). In DO-3 §3 AEA-15 edits only its own
  `checks.py` tree line, so it does not collide with the shared `**Built:**` line other tickets append to.
- **Wave column drift (not fixed here):** DO-3 §3's tree and the area map still put `checks.py` / A7c in wave 3, while
  slice plan §2 (row *A7a spine*) moved `checks.py` to wave 1. DO-3 reconciliation is AEA-08's; this ticket leaves the
  column alone. The orchestrator may raise it as an AEA-08 follow-up.
- No source file is shared: `checks.py` and `tests/unit/test_checks.py` are AEA-15's alone (slice plan §1, DO-3 §9).
  This plan deliberately does **not** append to `tests/unit/test_import_direction.py` (the purity test lives in
  `test_checks.py`), so it adds nothing to the wave-0 conflict there.

**Shared primitives needed (none new):** every type in §4 from AEA-02, with `Claim.kind` including `"quote"`,
`Removal.reason` including `"quote_not_found"`, and `Settled.only_turn` (AEA-02 plan §4.3, §4.8 already have all
three). AEA-01 provides `pyproject.toml` (ruff, mypy strict, pytest), `tests/unit/__init__.py` and
`tests/journeys/affected.py`.

**Notes for downstream planners (not this ticket's work)**

- **AEA-38 (reply node and responder prompt):** generic words are claims whatever the context (GRN-1, decided), so a
  sentence like "The contactor replacement was completed at the visit" (WP-2 invoice explanation) or "You're all set."
  after a booking is removed unless the same sentence holds a backed kind-specific claim ("You're all set: your visit
  is booked."). Over-blocking is HP-4's accepted direction, but the responder prompt should steer away from these words
  (DO-4 §9 `ResponderRules`: "no completion word unless backed by `settled`"); the E-1 / E-3 runs show the rate.
- **AEA-38 / AEA-27 (HP-3, $149):** `check_facts` passes `$149` if a fee-schedule passage holding `$149` is in
  `facts.passages`. Keeping $149 out of a WP-2 reply is the upstream job (staff notes to the brief only; which passages
  the responder sees), as WP-2 "wp2 144" decides; this module only guarantees nothing the evidence lacks gets through.
- **AEA-29 / AEA-38:** `EvidenceSet.sources` keys and refs follow PD-10. Nothing parses them yet; if a brief item later
  wants them, read PD-10 rather than re-deriving.
- **AEA-24 (eval):** the literal R-46 reading is `check_completion(text, settled.only_turn(turn_id))` (AC-6).

**Known, accepted behaviour (recorded so reviewers do not read it as a bug)**

- Fail-open gaps: a completion phrase not in the lexicon is not detected (e.g. "your visit is all lined up"). The lists
  are tuned from E-run failures (HP-4), never widened here by guesswork.
- Over-blocks: "Monday is fully booked" (BOOKED word, no booking) and "sorted by date" are removed when no matching
  action exists; a date in a sentence with an appointment claim must belong to that appointment, so a compound sentence
  that also mentions an unrelated date is removed. All are removals, the safe direction.
- Yearless dates match on month and day only; a text date with a year also matches a yearless evidence date of the
  same month and day (PD-7).
- Person names (the technician) and weekday names are never fact claims; DO-3 §1's "technician's name" match is not a
  removal rule here (R-46 lists numbers, dates, IDs and amounts).

**Spec gaps, none blocking**

- DO-4 §10 does not define "names a record", the claim value formats, the evidence key format or the sentence rule;
  PD-5, PD-6, PD-10 and PD-11 fix them inside the ticket's latitude.
- `TurnFacts` ships without `account`, `missing`, `notices` (AEA-02 plan §8.2). The generic walk (PD-9) reads whatever
  fields exist, so when AEA-38's follow-up adds `account`, its amounts and dates join the evidence with no change here.

**Contract problems:** none. No signed contract (OpenAPI, `UI_CONTRACTS.md`) is touched; no decision D-4…D-15 is
answered differently (`docs/plans/stage7-signoff.md`).

**Gates:** none (no human, external, paid or live gate).

---

## 9. Readiness

**READY**, with merge-order prerequisites: **blocked-on AEA-02** for the imports of `ActionKind`, `CompletedAction`,
`Settled` (with `only_turn`), `Claim` (with kind `"quote"`), `Removal`, `CheckResult`, `EvidenceSet`, `TurnFacts`,
`SourceRef`, `Quote`, `BriefExtraction`, `ChatLine` and `LookupRow`, which every function here takes or returns.
**AEA-01** (package skeleton, tooling, the affected-journeys command) is on `main` since `07924f5`. Start the
implementer when AEA-02 is on `main`; step 1 stops it cleanly otherwise. Refreshed 2026-10-21 against `main`
`16ca639` (§1 *Refresh*): nothing in the sources or in AEA-02's revised plan changes §3–§7; only the context-file
steps (9 and 10) changed. No
`NEEDS-DECISION`: every open choice (PD-1…PD-13) is engineering inside the ticket's latitude, and none changes a signed
contract or a decided item (SDQ-8 A, GRN-1, GRN-2, GRN-3, HP-4 B are followed as written).
