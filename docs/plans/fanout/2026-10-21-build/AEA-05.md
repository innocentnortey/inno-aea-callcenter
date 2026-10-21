# Plan — [AEA-05] gates: typo-tolerant word rules

**Status:** planned: READY, blocked-on AEA-02 for the `meridian.domain` import only (see §9)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/5 · **Base revision:** `16ca639` (main at the refresh; AEA-01, 03, 04, 07, 08, 25 merged, AEA-02 not yet). First planned on `9c3e7e7`
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21, refreshed the same day against `16ca639` (§0) · **Implementer:** fanout-implementer on Sonnet · **Lane:** build-loop · **Risk:** none (no `risk::security`; no test-writer, no security review)
**Slug / branch:** `gates-word-rules` → branch `aea-05-gates-word-rules`, worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-05` (the orchestrator creates it)

---

## 0. Refresh against `16ca639` (2026-10-21): what changed and what still holds

- **Still holds:** every decision (PD-1…PD-9), every pattern in §5 step 2d, the reviewed list §6.2 and every expected
  value in §7.1. Re-checked on a scratch prototype built **from this file's text** (patterns read out of §5 step 2d):
  46/46 templates, 2,256 customer lines, exactly the 70 reviewed firings, 9/9 safety calls, 22/22 variants, every §7.1
  case, and the phrases AEA-12's plan §4.4 relies on; 0 failures; about 0.7 ms per 2,000-character message. The module
  shape of §5 step 2 passed `mypy` strict (pydantic plugin) and `ruff check` with the project's `pyproject.toml`.
- **Changed on `main`:** AEA-01 merged (`07924f5`), so `pyproject.toml`, `src/meridian/gates/__init__.py`,
  `tests/unit/gates/__init__.py` and `tests/unit/test_import_direction.py` exist; the only open prerequisite is AEA-02.
  The type checker is **mypy strict with the pydantic plugin, over `src/meridian` and `tests`** (§4 *Typing notes*).
  The affected-journeys command is `uv run python -m tests.journeys.affected --base main` (§7.3).
- **Changed context shapes** (§5 step 7): the area-map A1 row now has six columns (`… | AEA-05, 12 | planned |`); DO-3 §3
  carries a `**Built:**` line; `.claude/state/icm-progress.md` holds one *Routes verified against code and tests* row
  per landed slice (AEA-04's and AEA-03's).
- **New consumers of this plan:** AEA-12's plan §4.4 (phrases), AEA-36's plan PA-4 (first rule id = safety, then
  danger) and AEA-14 (`R2.person`, `R24.<reason>`) rely on PD-6 and §7.1. Nothing in them may change.
- **AEA-02's type homes** (its plan §4.0): `HandoffReason` is defined in `domain/common.py` and re-exported by
  `domain/handoff.py`; `SafetyKind` is defined in `domain/common.py` and re-exported by `domain/turn.py`; it has 16
  values now (D-14 added `BURNING_RULED_OUT`). The import lines of §4 are unchanged and correct.

---

## 1. Goal and sources

### Goal

From the issue (`docs/plans/tickets/AEA-05.md`, *What to build*): `gates/rules.py`: `match_rules(text) -> RuleMatches`,
"pure, typo-tolerant, run on every message wherever it sits in the chat (R-5: 'including phrases mid-chat and with
typos'). It answers which fixed rule a message matches and decides nothing else." It fills AEA-02's `RuleMatches`
(`domain/turn.py`): `safety`, `burning_unclear`, `danger_words`, `person`, `policy_trigger`, `correction`, `rule_ids`.

**What it does, concretely.** Input `"My carbon monoxide detector is going off."` → output
`RuleMatches(safety=SafetyKind.CO, burning_unclear=False, danger_words=False, person=False, policy_trigger=None,
correction=False, rule_ids=("R5.co",))`. Input `"I want to talk to a manager"` → `person=True`,
`policy_trigger=HandoffReason.COMPLAINT_OR_MANAGER`, `rule_ids=("R2.person", "R24.complaint_or_manager")`. Input
`"My AC isn't cooling."` → everything empty.

**How it works, in one line.** Normalise the text (case, apostrophes, punctuation into clause marks), correct near-miss
spellings of a fixed keyword list token by token, then run fixed regular expressions, ignoring a match that a negation
word just before it (same clause) cancels.

### Context

Wave 0 of the Stage 8 build. The parked first attempt (`docs/parked/2026-10-21-first-attempt/src_meridian/triggers.py`)
and SP-1's `gates.py` had these rules in one function with no typo tolerance beyond one CO pattern. DO-3 splits them:
`gates/rules.py` (this ticket, words only) and `gates/gate.py` (AEA-12, order and decision). The types moved to
`domain/turn.py` (AEA-02) by R-G-1, so this ticket owns `match_rules` and its phrase lists only.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-05.md` (= issue #5) | AC-1…AC-13; example pairs WP-5, WP-6, WP-3/NODANGER, DANGER, WP-7, GRC-13 |
| Requirements | PRD `docs/prd/inno-aea-callcenter-prd.md` R-2 (l.143), R-5 (l.153), R-7 (l.155), R-8 (l.156), R-24 (l.230), R-47 (l.157); §3.2 driver B | Safety first, typo-tolerant, mid-chat; burning asks; narrow danger words; person on first ask in words; policy list |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §3 (`SafetyKind`, `RuleMatches`), §6 rows 1–2, §7 (`HandoffReason`) | Exact field names and enum values |
| Stage 7 addenda (win over DO-4) | `stage7/graph-core.md` §8 (`RuleMatches.correction`, type home R-G-1), §3 (gate order, how AEA-12 consumes), §12 (wave-0 merge order 04 → 02 → 05); `stage7/graph-nodes.md` §1 (`CheckEvent.codes` = `(GateKind value, *rule_ids)`, "stable codes only"); `stage7/cases.md` §3.4 (rule ids `R2.person`, `R24.<reason>`; rows 4, 7) | `correction` field; ids are stable codes with no text; membership cancel is not a word rule |
| Code design | DO-3 `docs/design/code-design.md` §2.1 (pure core, no I/O), §2.4 (`triggers.py` row), §4.1 (`gates/rules.py` row), §7 (R-2, R-5, R-7, R-8, R-24, R-47 rows), §9 (test layout `tests/unit/gates/test_rules.py`) | Module home, dependencies (pure core → pure core) |
| KB (issued, read-only) | `docs/data/issued/meridian_dataset/knowledge_base/**/policies/escalation_and_safety.md` | The four safety kinds; *Supervisor escalation* and *Department redirects* lists |
| Hard problems | `docs/design/hard-problems.md` HP-2 (option C, Innocent ✓ 2026-10-20) | Danger has no word list; the rule half stays narrow; over-firing buries real P1 cases |
| Worked pairs | `docs/data/worked-pairs.md` WP-3, WP-5, WP-6, WP-7 | Example inputs and outputs |
| SP-1 build plan | `docs/plans/fanout/2026-10-20-sp1/build.md` §4.5 (CO typo pattern), §5 step 1 (`danger_rule` narrow list, normalisation) | Starting patterns, read and copied, never imported |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` E-1 (WP-5, WP-6 hard gates), E-5 (safety and danger slice) | This module is the rule half; numbers come from E-runs, never from these tests |
| Observability contract | DO-6 `docs/design/observability-contract.md` *Records* `check_event`; CAP-2 (AEA-51) | Stable ids only; this module logs and stores nothing |
| Key-metrics registry | DO-7 `docs/design/key-metrics-registry.md` M-14, M-15 (counts manager asks, reads `person_requested` live), M-16, M-17 | Recall first for safety; no comfort report fires |
| Call map (derived) | `docs/data/handoff-inventory-call-map.csv` (420 calls, 46 opening templates; SAF-CO 5, SAF-GAS 3, SAF-SPARK 1; SCH-BURNING 16) | AC-1 and AC-2 inputs |
| Transcripts (issued, read-only) | `docs/data/issued/meridian_dataset/call_transcripts/*.txt` (420 files, 2,256 `Customer:` lines) | AC-2 input |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md`, `synthetic-test-data.md` rule 4 | Affected tests only; `mock-tested` journey record; context rows in the same change; variants record their dimension |
| Code on `main` (`16ca639`) | `pyproject.toml`; `tests/unit/test_import_direction.py` (AEA-01, 03, 04 blocks); `tests/journeys/affected.py`; `tests/conftest.py`; `docs/testing/journeys/2026-10-21-AEA-04.md` (record precedent) | Exact gate commands; the import-check block style; the journey-record fields |
| Sibling plans (read only) | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.0 (type homes), §4.8 (`RuleMatches`); `AEA-12.md` §4.4 (phrases it relies on), step I-7.1 (A1 row text); `AEA-36.md` PA-4 (first rule id); `AEA-14.md` (`R2.person`, `R24.<reason>`) | Import paths; PD-6 ids and the §7.1 phrases are a contract for these siblings |

---

## 2. Boundary

### Files this slice owns (the only files the implementer may create or edit)

| File | Create / modify | Change |
|---|---|---|
| `src/meridian/gates/rules.py` | **create** | `match_rules` and its private phrase lists (§5 step 2) |
| `tests/unit/gates/test_rules.py` | **create** | All AC-1…AC-10 tests plus the plan-added tests (§7) |
| `tests/unit/gates/data/corpus_firings_reviewed.csv` | **create** | The reviewed corpus-firing list, copied verbatim from §6.2 |
| `tests/unit/test_import_direction.py` | **modify (append one block)**; created by AEA-01, already holds AEA-01, 03 and 04 functions | Add `test_rules_imports` (AC-11) as a self-contained block at the end of the file (§7.2); no new module-level import |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-05.md` | **create** (date = day of the run) | AC-12 journey record |
| `.claude/reference/area-map.md` | modify **one cell** | A1 row status (AC-13) |
| `.claude/state/icm-progress.md` | modify **one cell** | Evidence cell of the AEA-03 *Routes verified against code and tests* row (AC-13; §5 step 7.2) |
| `docs/design/code-design.md` | modify **one line** in §3 | The `**Built:**` line (AC-13; §5 step 7.3) |

### Shared surfaces read only (never edit)

- `src/meridian/domain/turn.py` (`RuleMatches`, `SafetyKind`) and `src/meridian/domain/handoff.py` (`HandoffReason`): AEA-02.
- `src/meridian/gates/__init__.py`, `tests/unit/gates/__init__.py` (both exist, empty), `pyproject.toml`, `uv.lock`, ruff / mypy / pytest configuration, `tests/conftest.py`, the `journey` marker and `tests/journeys/affected.py`: AEA-01.
- The AEA-01, 03 and 04 functions and helpers already in `tests/unit/test_import_direction.py` (append after them; never edit them).
- `docs/data/handoff-inventory-call-map.csv` (derived, read by tests), the issued transcripts and KB (read by tests / for reference), `docs/parked/**` (read and copied, **never imported**).

### Owned by other slices: do not touch

`src/meridian/gates/gate.py` and `tests/unit/gates/test_gate.py` (AEA-12), `src/meridian/domain/*` (AEA-02),
`src/meridian/policy/*` (AEA-01, 03, 13, 14), `src/meridian/privacy/redact.py` (AEA-04), `apps/web/**`, `docs/ux/**`,
`ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, `docs/archive/`, `docs/parked/`, the briefing and issued data. Do not
bind ports 4019 or 5184 (nothing here starts a server).

---

## 3. Requirements table

### 3.1 Decisions this plan makes (the implementer applies them; none is a product decision)

| ID | Decision | Basis |
|---|---|---|
| **PD-1** | A request for a **manager, supervisor, boss/owner or "someone in charge"** sets **both** `person = True` **and** `policy_trigger = HandoffReason.COMPLAINT_OR_MANAGER` (AC-7 asks the plan to state this). | R-2: a direct request for a person "creates a handoff on the **first** request"; a manager is a person. M-15 counts "transcript cases that ask for a person **or manager**" and reads `person_requested` turns live; with `person = True` AEA-12's gate decides it as `PERSON` by code, with no model that could fail (graph-core §3 step 6). DO-4 §6 lists rule 1 (person) before rule 2 (policy word), "first match wins", so a message matching both was anticipated. Priority and promise are the same either way (P3; `R26.unstaffed` / `R26.staffed`, cases.md §3.2–§3.3). `policy_trigger` is still set so the gate `check_event` codes carry `R24.complaint_or_manager`. |
| **PD-2** | "is this a real person?" / "am I talking to a real person" counts as a person request (`person = True`). | R-2 favours a handoff on any direct ask; a missed ask is a hard-gate miss (M-15 100%), an extra P3 handoff is not. |
| **PD-3** | `burning_unclear = (a burning word fires) and safety is None`. A stated **untripped** breaker ("the breaker has not tripped") still gives `burning_unclear = True`; an **uncertain** breaker ("I don't know if the breaker tripped") is not "tripped". | R-7 asks two things (breaker **and** smoke/sparks/flames); ruling out one leaves the card's other question open, so the card is still asked. The uncertain case must not jump to P0 on a guess; the card asks it. |
| **PD-4** | **Typo tolerance** = normalisation + token correction to a fixed keyword list (one edit, same first two letters, target ≥ 6 letters, with a never-correct list) + an explicit misspelling map for short words. No general fuzzy matcher. | Predictable and reviewable; a general fuzzy match turned "spoke" into "smoke" and "turning" into "burning" in the prototype. The tests decide whether it is enough (ticket). |
| **PD-5** | **Negation**: a match is ignored when one of the 3 tokens before it, inside the same clause, is a negation word (`no`, `not`, `dont`, …). Clause boundaries are `. ? ! , ; :` and newlines, plus the words `but`, `though`, `although`, `however`. Applies to every rule. | "I don't smell gas", "there are no sparks", "no one is in danger" must not fire; "No, there are sparks" must (the comma closes the clause). Safety recall first: the window is short so "no heat and I smell gas" still fires. |
| **PD-6** | **Rule ids** are one stable code per field value, in a fixed order: `R5.gas`, `R5.co`, `R5.sparks_smoke_flames`, `R5.burning_with_breaker`, `R7.burning_unclear`, `R8.danger_words`, `R2.person`, `R24.refund`, `R24.billing_dispute`, `R24.complaint_or_manager`, `R24.legal_or_chargeback`, `R24.commercial`, `OD6.correction`. Pattern `^(R\d+|OD\d+)\.[a-z_]+$`. `rule_ids` order: safety, burning_unclear, danger, person, policy, correction. | Same `R<n>.<name>` style as cases.md §3.4 (`R2.person`, `R24.<reason value>` are the same ids the escalation and handoff paths use, so one person request has one id on every path). AEA-36 takes "the first fired rule id" for the safety case's `rule_id`, so safety must come first. |
| **PD-7** | `policy_trigger` precedence (one value): `legal_or_chargeback` → `refund` → `billing_dispute` → `complaint_or_manager` → `commercial`. | Parked `triggers.py` order; DO-4 keeps legal apart from complaints (SP-1 merged them; DO-4 wins). All are P3. |
| **PD-8** | CO fires on any non-negated mention of a CO device or carbon monoxide, including "do you install co detectors". | Safety recall is a 100% hard gate (M-14); a question about a CO detector getting the safety instruction is the accepted cost (parked and SP-1 behaved the same; SP-1 had 0 hard-gate failures). Recorded in §8. |
| **PD-9** | Imports come from the ticket homes: `from meridian.domain.turn import RuleMatches, SafetyKind` and `from meridian.domain.handoff import HandoffReason`. | AEA-02's plan §4.0 rule 5: consumers import from the home the ticket names; `HandoffReason` (defined in `domain/common.py`) and `SafetyKind` (defined in `domain/common.py`) are re-exported there with `as Name`, so both names are the same object; `domain/__init__.py` stays an empty marker (AEA-02 plan §9). Still "imports only `meridian.domain`" (AC-11). |

### 3.2 Requirement → implementation → verification

| # | Requirement (source) | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 | All 46 opening templates labelled by their `initial` category (ticket AC-1) | Phrase lists §5 step 2 | `tests/unit/gates/test_rules.py::test_issued_templates_labelled` → 46 of 46 |
| AC-2 | Safety recall on the full corpus; every other firing reviewed (ticket AC-2) | Same lists; reviewed list §6.2 | `::test_corpus_firings_reviewed` → 9 of 9 safety calls; 70 reviewed firings printed |
| AC-3 | Labelled synthetic safety variants per kind × dimension (ticket AC-3; HP-2; `synthetic-test-data` rule 4) | Normalisation, token correction, explicit misspelling map | `::test_safety_variants` → 22 cases pass; 5 × 4 table printed |
| AC-4 | Burning paths (R-7) | `_BURNING`, `_BREAKER_TRIPPED`, `_BREAKER_UNSURE`, PD-3 | `::test_burning_paths` → 3 passes |
| AC-5 | Comfort reports fire nothing (HP-2, R-8, M-17) | Narrow lists; no urgent-comfort rule exists | `::test_comfort_reports_do_not_fire` → 6 pass |
| AC-6 | SP-1's narrow danger phrases set `danger_words` (R-8 rule half) | `_DANGER` | `::test_explicit_danger_phrases` → 11 pass |
| AC-7 | Person in words (R-2); manager → `complaint_or_manager` and (PD-1) `person` | `_PERSON`, `_MANAGER` | `::test_person_requests` |
| AC-8 | Corrections set `correction` only (GRC-13) | `_CORRECTION` | `::test_correction_phrases` → 6 pass |
| AC-9 | Plain replies are not corrections | Specific correction phrases only | `::test_plain_replies_are_not_corrections` |
| AC-10 | `RuleMatches` carries no text; ids match one pattern | Only enums, bools and fixed ids are passed to `RuleMatches` | `::test_rule_matches_hold_no_text` |
| AC-11 | Pure; imports only stdlib and `meridian.domain`; defines no `RuleMatches`/`SafetyKind` | PD-9 | `tests/unit/test_import_direction.py::test_rules_imports` |
| AC-12 | [journey] none yet; record at `mock-tested`, blocked by AEA-57, names J-5 and J-7 | Record file §5 step 6 | Read the record's Level / Blocked by / journey fields |
| AC-13 | Context in the same change | §5 step 7 | `git diff --name-only main...HEAD` lists the three context files |
| R-5 "mid-chat and with typos" (PRD) | in-ticket (AC-3) | Phrase anywhere in a long message; PD-4 | AC-3 `mid-chat` and `typo` rows |
| WP-5 / HP-2 shorthand (worked pair) | in-ticket | `_CO` | **`::test_wp5_co_alarm_is_co`** (the ticket's WP-N worked-pair test) |
| WP-6 (worked pair) | in-ticket | PD-3 | `::test_wp6_burning_smell_asks` |
| WP-7 (worked pair) | in-ticket | `_REFUND` | `::test_wp7_refund_request` |
| BILL-DUP is billing information, not a dispute (PRD §3.2 driver B) | in-ticket (AC-1) | `_DISPUTE` has no "charged twice" phrase | AC-1 row BILL-DUP; plan-added `::test_policy_triggers` |
| Membership cancel is not a word rule (cases.md §3.4 row 4) | in-ticket (scope) | No pattern for it | **added**: `::test_policy_triggers` case "I want to cancel my comfort club membership" → nothing |
| Legal kept apart from complaints (DO-4 §3, §7) | in-ticket (What to build) | PD-7 | **added**: `::test_policy_triggers` |
| Negated mentions do not fire (M-17 false alarms; PD-5) | **added** | `_negated` | **added**: `::test_negated_mentions_do_not_fire` |
| Token correction never turns an ordinary word into a keyword ("spoke", "turning", "layer", "manage") | **added** | `_KEEP_AS_IS`, first-two-letters rule | **added**: `::test_typo_correction_does_not_overreach` |
| Empty text and AEA-12's STORE placeholders fire nothing (`text_store` is what `decide_gate` passes, AEA-12) | **added** | Normalisation | **added**: `::test_empty_and_placeholder_text_fire_nothing` |
| Rule-id order fixed, safety first (AEA-36 reads the first id; PD-6) | **added** | `match_rules` step order | **added**: `::test_rule_id_order` |
| Gate order, `decide_gate`, burning answer, intake parsing | other-ticket: AEA-12 | — | AEA-12 |
| Raise-only danger classifier | other-ticket: AEA-37 | — | AEA-37 |
| Counting corrections (`FailureCounters.corrections`) | other-ticket: AEA-38 (graph-core §8) | — | AEA-38 |
| Gate `check_event` built from `rule_ids` | other-ticket: AEA-36 (graph-nodes §1) | — | AEA-36 |
| CAP-2 capture (`gate_result = safety`, no model span before the instruction) | other-ticket: AEA-51 | — | AEA-51 |
| Safety reply text | other-ticket: AEA-03 | — | AEA-03 |
| Metric values M-14…M-17 | other-ticket: E-5 runs (AEA-24 harness) | — | never from these tests |

### 3.3 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (a pure library function; WF-1 calls it through AEA-12 and AEA-36) | — | — | — |

---

## 4. Shared code to use

Copied from DO-4 §3 and §7 as amended by stage7/graph-core.md §8 (AEA-02 writes these; do **not** redefine them):

```python
# src/meridian/domain/turn.py (AEA-02)
class SafetyKind(StrEnum): GAS = "gas"; CO = "co"; SPARKS_SMOKE_FLAMES = "sparks_smoke_flames"; BURNING_WITH_BREAKER = "burning_with_breaker"

class RuleMatches(MeridianModel):                     # frozen, extra="forbid" (MeridianModel, DO-4 §0)
    safety: SafetyKind | None
    burning_unclear: bool                             # burning words, breaker state not stated (R-7)
    danger_words: bool                                # narrow explicit danger only (R-8 rule half)
    person: bool                                      # R-2
    policy_trigger: HandoffReason | None              # refund, billing_dispute, complaint_or_manager, legal_or_chargeback, commercial
    rule_ids: tuple[str, ...]                         # which rules fired → check_event
    correction: bool                                  # graph-core §8 (GRC-13)

# src/meridian/domain/handoff.py (AEA-02; defined in domain/common.py, re-exported here). 16 values (DO-4 §7 + D-14);
# this module returns only the five on the second line.
class HandoffReason(StrEnum):
    SAFETY = "safety"; DANGER = "danger"; BURNING_UNCLEAR = "burning_unclear"; CUSTOMER_REQUESTED_PERSON = "customer_requested_person"
    REFUND = "refund"; BILLING_DISPUTE = "billing_dispute"; COMPLAINT_OR_MANAGER = "complaint_or_manager"; LEGAL_OR_CHARGEBACK = "legal_or_chargeback"; COMMERCIAL = "commercial"
    LATE_TECHNICIAN = "late_technician"; FEE_BEARING_CHANGE = "fee_bearing_change"; MEMBERSHIP_CANCEL = "membership_cancel"
    UNSUPPORTED_ACTION = "unsupported_action"; IDENTITY_UNVERIFIED = "identity_unverified"; AI_FAILURE = "ai_failure"; BURNING_RULED_OUT = "burning_ruled_out"
```

The exact imports in `rules.py` (PD-9), and nothing else from `meridian`:

```python
from meridian.domain.handoff import HandoffReason
from meridian.domain.turn import RuleMatches, SafetyKind
```

**Always construct `RuleMatches` with all seven keyword arguments** (no field has a default; the pydantic mypy plugin
runs with `init_typed = true` and `init_forbid_extra = true`, so a missing, extra or mistyped argument is a type error).

**Typing notes** (mypy strict + `pydantic.mypy`, over `src/meridian` **and** `tests`; checked on a scratch copy):

- Module constants: `Final` with the type written where it is not a plain literal: `Final[dict[SafetyKind, str]]`,
  `Final[frozenset[str]]`, compiled patterns `Final[re.Pattern[str]]`.
- `_TARGETS_BY_PREFIX` is built by a small typed helper, not a comprehension over a mutable global:
  ```python
  def _index_targets(targets: frozenset[str]) -> dict[str, tuple[str, ...]]:
      grouped: dict[str, list[str]] = {}
      for word in sorted(targets):
          grouped.setdefault(word[:2], []).append(word)
      return {prefix: tuple(words) for prefix, words in grouped.items()}

  _TARGETS_BY_PREFIX: Final[dict[str, tuple[str, ...]]] = _index_targets(_FUZZY_TARGETS)
  ```
- In `match_rules`, annotate the accumulators: `ids: list[str] = []`, `safety: SafetyKind | None`,
  `policy: HandoffReason | None`.
- In tests, the label tuple has a named alias (bare `tuple` fails strict):
  `Labels = tuple[SafetyKind | None, bool, bool, bool, HandoffReason | None, bool]`.
- A name another module imports but does not re-export is read as `vars(rules_mod)["RuleMatches"]` in the test
  (attribute access `rules_mod.RuleMatches` fails mypy strict's no-implicit-re-export check; `getattr` with a constant
  fails ruff B009).

The public surface this ticket adds (consumers: AEA-12 `decide_gate` calls `match_rules(intake.text_store)`;
AEA-36 reads `rules.rule_ids`; AEA-37 sees the verdict; AEA-38 reads `rules.correction`):

```python
def match_rules(text: str) -> RuleMatches: ...       # pure; never raises on any str (empty included)
ALL_RULE_IDS: Final[frozenset[str]]                  # the 13 ids of PD-6 (tests and AEA-36 may read it)
```

---

## 5. Steps

The slice implements one function on the pure-core side of DO-3 §2.1: `gates/` → `domain/` only. It adds no seam,
no Protocol, no class. Order:

### Step 1. Preconditions (stop if any fails)

1. `cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-05 && export UV_LINK_MODE=hardlink && uv sync` (never copy a venv; no `node_modules`).
2. `uv run python -c "from meridian.domain.turn import RuleMatches, SafetyKind; from meridian.domain.handoff import HandoffReason; print(sorted(RuleMatches.model_fields))"` must print the seven field names of §4 (`burning_unclear, correction, danger_words, person, policy_trigger, rule_ids, safety`). If the import fails, AEA-02 is not on the base: **stop and report `blocked-on AEA-02`** (no workaround, no local copy of the types).
3. `ls src/meridian/gates/__init__.py tests/unit/gates/__init__.py tests/unit/test_import_direction.py` must all exist (AEA-01; present on `16ca639`). If not: **stop, report `blocked-on AEA-01`**. Create no `__init__.py`.
4. Facts from `pyproject.toml` on `16ca639` (no need to re-derive): ruff `line-length = 110`, lint rules `E W F I B UP S RUF` with `E501` ignored (tests also ignore `S101`); **mypy** `strict = true`, `plugins = ["pydantic.mypy"]`, `files = ["src/meridian", "tests", "eval"]`, tests may leave defs untyped; pytest `addopts = "--strict-markers --strict-config -ra"`, `pythonpath = ["."]`, markers `journey` and `live` only (use neither).

### Step 2. `src/meridian/gates/rules.py`

Module docstring: one paragraph saying what it does (the *Goal* lines) and that it is pure (no I/O, no logging, no clock).
Imports: `from __future__ import annotations`, `import re`, `import unicodedata`, `from typing import Final`, plus the two
`meridian.domain` lines of §4. **Nothing else.** No `print`, `open`, logging, globals mutated at call time.

**2a. Rule ids (PD-6)**, module constants:

```python
_SAFETY_IDS: Final[dict[SafetyKind, str]] = {
    SafetyKind.GAS: "R5.gas", SafetyKind.CO: "R5.co",
    SafetyKind.SPARKS_SMOKE_FLAMES: "R5.sparks_smoke_flames", SafetyKind.BURNING_WITH_BREAKER: "R5.burning_with_breaker",
}
_POLICY_IDS: Final[dict[HandoffReason, str]] = {
    HandoffReason.REFUND: "R24.refund", HandoffReason.BILLING_DISPUTE: "R24.billing_dispute",
    HandoffReason.COMPLAINT_OR_MANAGER: "R24.complaint_or_manager",
    HandoffReason.LEGAL_OR_CHARGEBACK: "R24.legal_or_chargeback", HandoffReason.COMMERCIAL: "R24.commercial",
}
RULE_ID_BURNING_UNCLEAR: Final = "R7.burning_unclear"
RULE_ID_DANGER_WORDS: Final = "R8.danger_words"
RULE_ID_PERSON: Final = "R2.person"
RULE_ID_CORRECTION: Final = "OD6.correction"
ALL_RULE_IDS: Final[frozenset[str]] = frozenset(
    {*_SAFETY_IDS.values(), *_POLICY_IDS.values(), RULE_ID_BURNING_UNCLEAR, RULE_ID_DANGER_WORDS, RULE_ID_PERSON, RULE_ID_CORRECTION}
)
```

**2b. Word sets for typo tolerance (PD-4, PD-5)**, exactly these members:

```python
_NEGATIONS: Final = frozenset({"no", "not", "dont", "doesnt", "didnt", "isnt", "arent", "wasnt", "werent",
                               "hasnt", "havent", "never", "without", "nobody", "cant", "cannot"})
_WINDOW_STOPS: Final = frozenset({"|", "but", "though", "although", "however"})
# Keywords a near-miss token is corrected TO (all 6+ letters):
_FUZZY_TARGETS: Final = frozenset("""
carbon monoxide detector detectors alarming sparks sparking sparked smoking flames flaming burning scorched scorching
breaker breakers tripped tripping rotten breathe breathing unconscious fainted heatstroke emergency person somebody
someone representative operator supervisor manager refund refunded reimburse reimbursed reimbursement lawyer lawyers
attorney lawsuit chargeback dispute disputing overcharged overcharge complaint complain unprofessional commercial
warehouse rooftop misunderstood incorrect""".split())
# Tokens never corrected: short exact keywords, and real words one edit away from a target:
_KEEP_AS_IS: Final = frozenset("""
flame spark smoke alarm burnt burned carton manage managed manages layer layers trapped spares flakes flares burying
burping""".split())
# Explicit misspellings and shorthand for short words (looked up before anything else):
_TYPOS: Final[dict[str, str]] = {
    "c0": "co", "gass": "gas", "smel": "smell", "smeel": "smell", "smelt": "smell", "egs": "eggs", "eggz": "eggs",
    "alrm": "alarm", "alram": "alarm", "alarn": "alarm", "smoek": "smoke", "smok": "smoke", "smkoe": "smoke",
    "fier": "fire", "waht": "what", "wat": "what", "aksed": "asked", "askd": "asked", "asekd": "asked",
    "siad": "said", "wrnog": "wrong", "worng": "wrong", "wrogn": "wrong", "thta": "that", "taht": "that",
    "tahts": "thats", "nto": "not", "humna": "human", "hunam": "human", "speek": "speak", "spek": "speak",
    "tlak": "talk", "breker": "breaker",
}
# Index for speed: first two letters -> targets (built by _index_targets, §4 Typing notes).
_TARGETS_BY_PREFIX: Final[dict[str, tuple[str, ...]]] = _index_targets(_FUZZY_TARGETS)
```

**2c. Helpers** (private, pure):

1. `_within_one_edit(a: str, b: str) -> bool`: True when `a == b`, or the lengths are equal and they differ in exactly
   one position, or they differ in exactly two **adjacent** positions that are swapped (`a[i] == b[i+1]` and
   `a[i+1] == b[i]`), or the lengths differ by one and deleting one character from the longer gives the shorter.
   *Invariant: distance ≤ 1 (optimal string alignment); never more.*
2. `_canonical(token: str) -> str`, in this order:
   1. `token in _TYPOS` → `_TYPOS[token]`;
   2. `token in _FUZZY_TARGETS or token in _KEEP_AS_IS or len(token) < 5` → `token` unchanged;
   3. `hits = [k for k in _TARGETS_BY_PREFIX.get(token[:2], ()) if _within_one_edit(token, k)]`;
      exactly one hit → that keyword; zero or several → `token` unchanged.
   *Invariant: only a token within one edit of exactly one keyword sharing its first two letters is changed
   ("turning" never becomes "burning"; "spoke" never becomes "smoke").*
3. `_normalise(text: str) -> str`, steps in this exact order:
   1. `unicodedata.normalize("NFKC", text)`;
   2. `.translate(_APOSTROPHES)` with `_APOSTROPHES: Final = str.maketrans({"\u2018": "'", "\u2019": "'", "\u02bc": "'", "`": "'"})`
      (write the escapes, not the characters); `.lower()`; then **delete** every `'` ("that's" → "thats", "can't" → "cant");
   3. dotted initials: `re.sub(r"\b([a-z])\.([a-z])\.?(?![a-z])", r"\1\2", t)` ("c.o." → "co");
   4. slash pairs: `re.sub(r"\b([a-z])/([a-z])\b", r"\1\2", t)` ("a/c" → "ac");
   5. clause marks: `re.sub(r"[.?!,;:\n\r]+", " | ", t)`;
   6. everything else not `[a-z0-9| ]` → space: `re.sub(r"[^a-z0-9| ]+", " ", t)`;
   7. letter runs of 3+ → 2: `re.sub(r"([a-z])\1{2,}", r"\1\1", t)` ("smelllll" → "smell");
   8. `" ".join(tok if tok == "|" else _canonical(tok) for tok in t.split())`.
   Result: lower-case tokens separated by single spaces, clause boundaries as the token `|`.
   Example: `"I smel gas, near my furnce!"` → `"i smell gas | near my furnce |"`.
4. `_negated(t: str, start: int) -> bool`: `toks = t[:start].split()`; walk back from the end to the last token in
   `_WINDOW_STOPS` (exclusive); of the tokens after it, take the last 3; return `any(w in _NEGATIONS for w in those)`.
   *Invariant: a negation never reaches across a clause mark or "but".*
5. `_fires(pattern: re.Pattern[str], t: str) -> bool`: `any(not _negated(t, m.start()) for m in pattern.finditer(t))`.

**2d. Patterns** (declare each string as `_GAS: Final = r"…"` and so on; compile each once at import as
`_GAS_RX: Final[re.Pattern[str]] = re.compile(_GAS)`, giving the 15 names `_GAS_RX`, `_CO_RX`, `_FIRE_RX`, `_BURNING_RX`,
`_BREAKER_TRIPPED_RX`, `_BREAKER_UNSURE_RX`, `_DANGER_RX`, `_PERSON_RX`, `_MANAGER_RX`, `_LEGAL_RX`, `_REFUND_RX`,
`_DISPUTE_RX`, `_COMPLAINT_RX`, `_COMMERCIAL_RX`, `_CORRECTION_RX`; copy the strings exactly; `E501` is ignored, so a
long literal may stay on one line, or be wrapped with implicit string concatenation without changing its content):

```python
_GAS = r"\b(smell|smells|smelling|smelled|whiff|odor|odour)\b(?: [a-z0-9]+){0,3}? gas\b|\bgas (smell|smells|odor|odour|leak|leaks|leaking)\b|\bgas is leaking\b|\bleak(ing|s)? gas\b|\brotten eggs?\b|\b(sulfur|sulphur)\b"
_CO = r"\bcarbon monoxide\b|\bmonoxide\b|\bco2? (alarm|alarms|alarming|detector|detectors|monitor|monitors|sensor)\b|\bco is (going off|beeping|alarming)\b"
_FIRE = r"\b(spark|sparks|sparking|sparked|smoke|smoking|smoked|flames|flaming|on fire|caught fire|catching fire)\b|\bflame\b(?! (sensor|rod|rectifier))|\bfire\b(?! (up|ups|place|places|wood|works|department))"
_BURNING = r"\b(burning|burnt|burned|scorch|scorched|scorching|melting)\b(?! (out|up|hot))"
_BREAKER_TRIPPED = r"\bbreakers? (has |have |keeps |keep |was |were |is |just |had )?(tripped|tripping|trips|trip|flipped|popped|blew|blown)\b|\b(tripped|tripping|trip|flipped|popped|blew) (the |a |my |our |a few |two |some )?(circuit )?breakers?\b|\b(tripped|blown) (circuit )?breakers?\b"
_BREAKER_UNSURE = r"\b(if|whether|maybe|might have|may have)( the| a| my| our| any)?( circuit)? breakers?\b"
_DANGER = r"\b(in danger|cant breathe|cannot breathe|can not breathe|trouble breathing|not breathing|passed out|unconscious|fainted|heatstroke|heat stroke|medical emergency)\b"
_PERSON = r"\b(talk|speak|chat) (to|with) (a |an |the |some )?(someone|somebody|real|actual|live|human|humans|person|people|agent|representative|rep|staff|employee|operator)\b|\b(connect|transfer|put) me (to|with|through)\b|\btransfer me\b|\b(real|actual|live) (person|human|agent|representative|rep|people)\b|\b(want|need|get|like|request|prefer)\b(?: [a-z]+){0,2} (a |an )?(human|representative|operator)\b|\b(can|could|will|would|please|have) (someone|somebody|a person|a human|a rep|a representative) (call|phone|text) me\b|\b(want|need|like) (someone|somebody|a person) to (call|phone) me\b|^(operator|agent|representative|rep|human|person|a human|a person)( please)?( \|)?$"
_MANAGER = r"\b(talk|speak|chat|complain|escalate this|escalate it) (to|with) (a |an |the |your |some )?(manager|supervisor|boss|owner)\b|\b(want|need|get|like|request|see|demand)\b(?: [a-z]+){0,2} (manager|supervisor)\b|(?<!im )(?<!am )(?<!was )(?<!as )\b(your|a) (manager|supervisor)\b|\b(someone|somebody|person|anyone) in charge\b|^(manager|supervisor)( please)?( \|)?$"
_LEGAL = r"\b(lawyer|lawyers|attorney|attorneys|lawsuit|legal action|chargeback|charge back|small claims|better business bureau|bbb|suing|sued)\b|\b(going to|gonna|will|ill|could|can|might|want to|plan to|about to) sue\b|\bsue (you|meridian|your company|the company|them|your business)\b"
_REFUND = r"\b(refund|refunds|refunded|money back|reimburse|reimbursed|reimbursement)\b"
_DISPUTE = r"\bnot what i agreed\b|\bovercharg\w*|\bcharged (me )?(wrong|too much|for something|for work|for parts)\b|\bwrong (amount|charge|price|total)\b|\b(dispute|disputing)\b|\bdont (owe|agree)\b|\btake (that|it|the fee|the charge) off\b|\bshouldnt have to pay\b|\b(bill|invoice|charge|fee|price|total) (is|was|looks|seems) (wrong|too high)\b"
_COMPLAINT = r"\b(rude|tracked mud|unprofessional|disrespectful|ripped off|scam|second opinion|shoddy|sloppy work|poor workmanship|bad workmanship)\b|\bcalled (two|three|four|five|2|3|4|5|several|multiple|many) times\b|\b(nobody|no one|noone)( has| have| ever| even)* (called|call|got|gotten) (me )?back\b|\bnever (called|call|got|gotten) (me )?back\b|\b(file|make|lodge|register) a complaint\b|\bwant to complain\b|\bcomplain about\b"
_COMMERCIAL = r"\b(commercial|strip (center|mall|plaza)|shopping (center|mall|plaza)|rooftop units?|rtus?|office (building|park|space)|warehouse|retail (space|store|building))\b"
_CORRECTION = r"\bthats not what i (asked|said|meant|wanted|was asking)\b|\bnot what i (asked|meant)\b|\b(no|nope|but|again)( \|)? i (said|meant|asked)\b|\b(thats|that is|that was|this is|you are|youre|your) (wrong|incorrect|not right|not correct)\b|\byou (misunderstood|misheard|got it wrong|got that wrong|have it wrong|are not listening|arent listening|re not listening)\b|\bi (didnt|did not) (ask|say|mean) (that|this|for that|about that)\b|\b(wrong answer|not my question|you didnt answer my question)\b"
```

Where these come from: `_GAS`, `_CO`, `_FIRE`, `_BURNING`, `_BREAKER_TRIPPED`, `_PERSON`, `_REFUND`, `_DISPUTE`,
`_COMPLAINT`, `_LEGAL`, `_COMMERCIAL` start from the parked `triggers.py`; `_CO` widens as SP-1 build §4.5 says;
`_DANGER` is SP-1 build §5 step 1's narrow list. Changes from the parked file (each a decision of this plan): bare
"natural gas", "human", "representative", "tenants", "my business" and a bare "sue" removed (they fired on ordinary
sentences or names); legal kept apart (DO-4); `_MANAGER` split out of `_PERSON` (PD-1); flame-sensor / fire-up /
burned-out exclusions added (HVAC vocabulary, M-17); the `_URGENT` comfort pattern **not** carried over (R-8 narrowed:
no word rule for no-heat/no-cooling/leaks).

**2e. `match_rules(text: str) -> RuleMatches`**, numbered steps:

1. `t = _normalise(text)`.
2. `burning = _fires(_BURNING_RX, t)`; `tripped = _fires(_BREAKER_TRIPPED_RX, t) and _BREAKER_UNSURE_RX.search(t) is None`.
   (Every "`_X` → …" below means `_fires(_X_RX, t)`.)
   *(`_BREAKER_UNSURE` is a plain search, not negation-guarded: any uncertainty about the breaker means "not stated".)*
3. Safety, first match wins: `_GAS` → `GAS`; elif `_CO` → `CO`; elif `_FIRE` → `SPARKS_SMOKE_FLAMES`;
   elif `burning and tripped` → `BURNING_WITH_BREAKER`; else `None`.
4. `burning_unclear = burning and safety is None` (PD-3).
5. `danger_words = _fires(_DANGER_RX, t)`.
6. `manager = _fires(_MANAGER_RX, t)`; `person = manager or _fires(_PERSON_RX, t)` (PD-1).
7. `policy_trigger` (PD-7): `_LEGAL` → `LEGAL_OR_CHARGEBACK`; elif `_REFUND` → `REFUND`; elif `_DISPUTE` →
   `BILLING_DISPUTE`; elif `manager or _fires(_COMPLAINT_RX, t)` → `COMPLAINT_OR_MANAGER`; elif `_COMMERCIAL` →
   `COMMERCIAL`; else `None`.
8. `correction = _fires(_CORRECTION_RX, t)`.
9. `rule_ids`, appended in this order only when set: `_SAFETY_IDS[safety]`, `RULE_ID_BURNING_UNCLEAR`,
   `RULE_ID_DANGER_WORDS`, `RULE_ID_PERSON`, `_POLICY_IDS[policy_trigger]`, `RULE_ID_CORRECTION` → `tuple(...)`.
10. `return RuleMatches(safety=..., burning_unclear=..., danger_words=..., person=..., policy_trigger=...,
    rule_ids=..., correction=...)`.
*Invariant: nothing derived from `text` reaches `RuleMatches` except enum members, booleans and ids from `ALL_RULE_IDS`
(AC-10).* Measured on the scratch prototype: under 1 ms for a 2,000-character message.

### Step 3. `tests/unit/gates/data/corpus_firings_reviewed.csv`

Copy §6.2 **verbatim** (header + 70 rows, `\n` line endings, no trailing blank line issues). It holds call IDs, line
numbers, rule ids and reasons only; **no transcript text**.

### Step 4. Tests

Write `tests/unit/gates/test_rules.py` (§7.1) and append the `test_rules_imports` block to
`tests/unit/test_import_direction.py` (§7.2). Iterate with the commands in §7.3 until green. If a case in §7.1 fails,
fix `rules.py` toward the plan; **do not change an expected value in this plan or in the CSV**. If the plan's
expectation looks wrong, stop and send it back to the planner.

### Step 5. Commit 1 (code and tests)

`git add src/meridian/gates/rules.py tests/unit/gates/test_rules.py tests/unit/gates/data/corpus_firings_reviewed.csv tests/unit/test_import_direction.py`.
Message:

```
gates: typo-tolerant word rules (AEA-05)

match_rules(text) -> RuleMatches for safety, burning, danger, person,
policy and correction words; reviewed corpus firings; import check.
Refs #5

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```

Note the short SHA of this commit (`git rev-parse --short HEAD`); step 6 and 7 cite it.

### Step 6. Journey record `docs/testing/journeys/<YYYY-MM-DD>-AEA-05.md` (AC-12)

Create the folder if missing. Content (fields of `integrated-journeys.md` §4; fill `<…>`):

```markdown
# Journey record: AEA-05 gates word rules

| Field | Value |
|---|---|
| Claim | `match_rules` labels safety, burning, danger, person, policy and correction words (AEA-05). No journey runs it yet. |
| Level | `mock-tested` |
| Tested revision | `<commit-1 short SHA>` |
| Environment | VPS worktree `inno-aea-callcenter-wt/AEA-05`; Python 3.12 via `uv run`; unit tests only; no server, no database, no model |
| Command | `uv run pytest tests/unit/gates/test_rules.py tests/unit/test_import_direction.py::test_rules_imports -q` |
| Result | <N passed> |
| Evidence location | Implementer report for AEA-05; reviewed corpus list `tests/unit/gates/data/corpus_firings_reviewed.csv` |
| Remaining limitations | Unit level only: the gate decision (AEA-12), the gates node and its `check_event` (AEA-36), and the safety reply through the real server are not exercised; danger without explicit words is the classifier's (AEA-37) |
| Blocked by | AEA-57 (journey harness, wave 2) |
| Journeys that will exercise this code | **J-5** (safety words: CO alarm and danger path, WP-5 / DANGER / NODANGER) once AEA-51 lands; **J-7** ("talk to a person" words) once AEA-52 lands |
```

No secrets, phone numbers or transcript text in it.

### Step 7. Context (AC-13)

Read each line first; AEA-02 merges just before this ticket and may have edited the same lines. Keep its text and add
AEA-05's part.

1. `.claude/reference/area-map.md`, A1 row (on `16ca639`:
   `| 1 | **A1 Gates** | Decide the turns that never reach a model | `gates/{rules,gate}.py` | AEA-05, 12 | planned |`):
   change **only the last cell** (`planned`) to `` `rules.py` actual (AEA-05, `<commit-1 SHA>`); `gate.py` planned ``.
   AEA-12's plan (step I-7.1) expects exactly this text.
2. `.claude/state/icm-progress.md`: on `16ca639` there are two *Routes verified against code and tests* rows (AEA-04's,
   then AEA-03's). In the **AEA-03 row** (its evidence starts `2026-10-21: area map A0 → `policy/texts.py``) replace
   only the evidence cell with
   `2026-10-21: area map A0 → `policy/texts.py` (AEA-03, `2689582`; 14 pass) and A1 → `gates/rules.py` (AEA-05, `<commit-1 SHA>`; <N> pass in `tests/unit/gates/test_rules.py`)`.
   Keep its status (`provisional`) and its next-check cell; leave AEA-04's row alone; row ≤ 400 characters
   (`context-maintenance` rule 6: replace the evidence link, keep the row count). If AEA-02 changed this row first, keep
   its text and add the `A1 → gates/rules.py …` clause.
3. `docs/design/code-design.md` §3: the line `**Built:** `policy/texts.py` (AEA-03, `2689582`).` (two lines under
   `Owner area and wave in the right-hand columns (§8). …`) becomes
   `**Built:** `policy/texts.py` (AEA-03, `2689582`), `gates/rules.py` (AEA-05, `<commit-1 SHA>`).` If other entries
   were added before you, append `, `gates/rules.py` (AEA-05, `<commit-1 SHA>`)` before the final full stop. Touch
   nothing else in DO-3.
4. Commit 2: `git add docs/testing/journeys/<YYYY-MM-DD>-AEA-05.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`, message
   `docs: AEA-05 journey record and context rows` + blank line + `Refs #5` + blank line +
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
5. `git diff --name-only main...HEAD` must list exactly the owned files of §2 (AC-13 evidence).

### What the implementer must NOT do

- Define `RuleMatches`, `SafetyKind` or `HandoffReason` anywhere, or import anything from `meridian` other than the two
  lines in §4. No import of `docs/parked/**` (copy, never import), `gates/gate.py`, `policy/*`, `privacy/*`.
- Add a broad danger word list ("hot", "cold", "no heat", "elderly", "88", "baby"), an urgent-comfort rule, a
  membership-cancel rule, or any reply text, priority or gate order.
- Put transcript text, names, account numbers or phone numbers into the CSV, assertion messages, test ids or prints
  (print call IDs, line numbers and rule ids only).
- Edit `pyproject.toml`/`uv.lock` (no new dependency is needed), `tests/conftest.py`, another ticket's test file or
  another ticket's function in `tests/unit/test_import_direction.py`, the issued data, the call map, `apps/web/**`,
  `docs/ux/**`, the OpenAPI file. Add no module-level import to `tests/unit/test_import_direction.py` (ruff E402/I001).
- Change a PD-6 id or the behaviour of any §7.1 phrase: AEA-12, AEA-14 and AEA-36 are planned against them.
- Run the full suite (not required: no shared fixture, setting or dependency changes; nothing imports `rules.py` yet),
  use `pytest -n` above 2, `git add -A`, push, or force-push.

---

## 6. Data and fixtures

### 6.1 Inputs the tests read (read-only, never copied)

- `docs/data/handoff-inventory-call-map.csv` (derived; columns `call_id`, `initial`, `template`, …): AC-1 groups the
  distinct `(initial, template)` pairs → **46**.
- `docs/data/issued/meridian_dataset/call_transcripts/*.txt` (issued): AC-2 reads every line starting with
  `Customer:` (strip that prefix and surrounding whitespace) → **2,256** lines; line numbers are 1-based over
  `splitlines()`.
- Locate the repository root from the test file: `REPO = Path(__file__).resolve().parents[3]` in
  `tests/unit/gates/test_rules.py`.
- Synthetic cases (AC-3…AC-10, plan-added) are written inline in the test file, each with its source (clean issued
  line or worked pair) and, for AC-3, its varied dimension (`synthetic-test-data` rule 4). No seeds needed: the cases
  are fixed strings. Every case was checked against the plan's prototype (scratch only, not committed), and re-checked
at the refresh against `16ca639` (§0).

### 6.2 `tests/unit/gates/data/corpus_firings_reviewed.csv` (copy verbatim)

Reviewed by the planner on 2026-10-21: all 70 firings are the call's opening request (line 8, or line 10 when a
line-noise turn comes first), each with the label its call-map category implies; no other customer line in any of the
420 calls fires. The 9 safety calls are included.

```csv
call_id,line_no,rule_ids,reason
CALL-20260706-0101,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260706-0182,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260709-0082,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260710-0028,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260710-0136,8,R24.refund,BILL-REFUND opening request; refund request (KB Supervisor escalation; R-24)
CALL-20260710-0335,8,R2.person+R24.complaint_or_manager,COMPLAINT-OPINION opening request; asks for someone in charge about workmanship (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260712-0046,8,R5.gas,SAF-GAS opening request; gas smell (KB Immediate safety escalation; R-5)
CALL-20260713-0075,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260714-0234,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260714-0246,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260715-0100,8,R24.refund,BILL-REFUND opening request; refund request (KB Supervisor escalation; R-24)
CALL-20260715-0289,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260717-0180,8,R5.sparks_smoke_flames,SAF-SPARK opening request; visible sparks (KB Immediate safety escalation; R-5)
CALL-20260718-0062,8,R2.person+R24.complaint_or_manager,COMPLAINT-CONDUCT opening request; asks for a manager about technician conduct (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260718-0111,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260721-0093,8,R5.co,SAF-CO opening request; CO detector alarming (KB Immediate safety escalation; R-5)
CALL-20260722-0198,10,R2.person+R24.complaint_or_manager,COMPLAINT-CONDUCT opening request; asks for a manager about technician conduct (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260724-0391,8,R24.complaint_or_manager,COMPLAINT-REPEAT opening request; repeated unanswered calls (KB Supervisor escalation; R-24)
CALL-20260725-0329,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260726-0189,8,R2.person+R24.complaint_or_manager,COMPLAINT-OPINION opening request; asks for someone in charge about workmanship (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260728-0089,8,R24.commercial,COMMERCIAL opening request; commercial project (KB Department redirects; R-24)
CALL-20260728-0264,8,R5.gas,SAF-GAS opening request; gas smell (KB Immediate safety escalation; R-5)
CALL-20260729-0041,8,R2.person+R24.complaint_or_manager,COMPLAINT-CONDUCT opening request; asks for a manager about technician conduct (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260729-0260,10,R2.person+R24.complaint_or_manager,COMPLAINT-CONDUCT opening request; asks for a manager about technician conduct (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260729-0278,10,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260730-0222,8,R2.person+R24.complaint_or_manager,COMPLAINT-CONDUCT opening request; asks for a manager about technician conduct (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260730-0223,8,R24.complaint_or_manager,COMPLAINT-REPEAT opening request; repeated unanswered calls (KB Supervisor escalation; R-24)
CALL-20260730-0306,8,R24.complaint_or_manager,COMPLAINT-REPEAT opening request; repeated unanswered calls (KB Supervisor escalation; R-24)
CALL-20260730-0396,8,R24.commercial,COMMERCIAL opening request; commercial project (KB Department redirects; R-24)
CALL-20260802-0079,8,R2.person+R24.complaint_or_manager,COMPLAINT-CONDUCT opening request; asks for a manager about technician conduct (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260805-0214,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260805-0290,8,R5.co,SAF-CO opening request; CO detector alarming (KB Immediate safety escalation; R-5)
CALL-20260806-0377,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260810-0078,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260810-0162,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260810-0239,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260811-0299,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260812-0169,8,R24.refund,BILL-REFUND opening request; refund request (KB Supervisor escalation; R-24)
CALL-20260815-0345,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260816-0038,8,R5.co,SAF-CO opening request; CO detector alarming (KB Immediate safety escalation; R-5)
CALL-20260816-0191,8,R24.refund,BILL-REFUND opening request; refund request (KB Supervisor escalation; R-24)
CALL-20260816-0224,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260817-0241,10,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260818-0092,8,R24.refund,BILL-REFUND opening request; refund request (KB Supervisor escalation; R-24)
CALL-20260819-0177,8,R24.complaint_or_manager,COMPLAINT-REPEAT opening request; repeated unanswered calls (KB Supervisor escalation; R-24)
CALL-20260819-0228,8,R24.commercial,COMMERCIAL opening request; commercial project (KB Department redirects; R-24)
CALL-20260820-0013,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260821-0353,10,R24.refund,BILL-REFUND opening request; refund request (KB Supervisor escalation; R-24)
CALL-20260822-0185,8,R5.gas,SAF-GAS opening request; gas smell (KB Immediate safety escalation; R-5)
CALL-20260822-0341,8,R5.co,SAF-CO opening request; CO detector alarming (KB Immediate safety escalation; R-5)
CALL-20260823-0068,8,R24.refund,BILL-REFUND opening request; refund request (KB Supervisor escalation; R-24)
CALL-20260827-0065,8,R24.refund,BILL-REFUND opening request; refund request (KB Supervisor escalation; R-24)
CALL-20260828-0267,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260830-0286,8,R2.person+R24.complaint_or_manager,COMPLAINT-OPINION opening request; asks for someone in charge about workmanship (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260831-0051,8,R24.complaint_or_manager,COMPLAINT-REPEAT opening request; repeated unanswered calls (KB Supervisor escalation; R-24)
CALL-20260831-0339,8,R2.person+R24.complaint_or_manager,COMPLAINT-OPINION opening request; asks for someone in charge about workmanship (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260901-0127,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260902-0168,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260904-0418,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260905-0318,8,R5.co,SAF-CO opening request; CO detector alarming (KB Immediate safety escalation; R-5)
CALL-20260906-0032,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260906-0283,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260906-0411,8,R2.person+R24.complaint_or_manager,COMPLAINT-OPINION opening request; asks for someone in charge about workmanship (KB Supervisor escalation; R-2; R-24; plan decision PD-1)
CALL-20260908-0029,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260909-0119,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260910-0387,8,R24.billing_dispute,BILL-DISPUTE opening request; customer disagrees with the invoice amount (KB Supervisor escalation; R-24)
CALL-20260915-0133,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260916-0311,8,R7.burning_unclear,SCH-BURNING opening request; burning smell with no breaker state (R-7; D2)
CALL-20260916-0403,8,R24.commercial,COMMERCIAL opening request; commercial project (KB Department redirects; R-24)
CALL-20260917-0187,8,R24.commercial,COMMERCIAL opening request; commercial project (KB Department redirects; R-24)
```

Totals: 70 = BILL-DISPUTE 16, SCH-BURNING 16, BILL-REFUND 8, COMPLAINT-CONDUCT 6, COMPLAINT-OPINION 5,
COMPLAINT-REPEAT 5, COMMERCIAL 5, SAF-CO 5, SAF-GAS 3, SAF-SPARK 1 (one per call of each category).

---

## 7. Checks

### 7.1 `tests/unit/gates/test_rules.py`: the tests to write with the code

Imports: `csv`, `uuid`, `re`, `collections.Counter`, `pathlib.Path`, `pytest`; `from meridian.gates.rules import
ALL_RULE_IDS, match_rules`; `from meridian.domain.turn import RuleMatches, SafetyKind`; `from meridian.domain.handoff
import HandoffReason`. A type alias `Labels = tuple[SafetyKind | None, bool, bool, bool, HandoffReason | None, bool]`, a
helper `def _labels(m: RuleMatches) -> Labels:` returning
`(m.safety, m.burning_unclear, m.danger_words, m.person, m.policy_trigger, m.correction)` and a constant
`NOTHING: Labels = (None, False, False, False, None, False)`. A module constant
`_SAFETY_ID = {SafetyKind.GAS: "R5.gas", SafetyKind.CO: "R5.co", SafetyKind.SPARKS_SMOKE_FLAMES: "R5.sparks_smoke_flames", SafetyKind.BURNING_WITH_BREAKER: "R5.burning_with_breaker"}`
(literal in the test, not imported from `rules.py`). Use `pytest.mark.parametrize` with readable `ids=` (case ids like
`"co-typo"`, never the text). Assertion messages name the case id or call id, never message text.

| Test | Cases and expected result |
|---|---|
| `test_wp5_co_alarm_is_co` (**WP-5 worked pair**) | `"My carbon monoxide detector is going off."` and HP-2's `"co alarm keeps going off"` → `safety is SafetyKind.CO`, `burning_unclear is False`, `rule_ids == ("R5.co",)`, all other labels empty |
| `test_wp6_burning_smell_asks` (WP-6) | `"I need to schedule a service call. I smell something burning from the vents."` → `safety is None`, `burning_unclear is True`, `rule_ids == ("R7.burning_unclear",)` |
| `test_wp7_refund_request` (WP-7) | `"I want a full refund on the repair. It didn't fix anything and I had to call another company."` → `policy_trigger is HandoffReason.REFUND`, `person is False`, `rule_ids == ("R24.refund",)` |
| `test_issued_templates_labelled` (AC-1) | Read the call map, distinct `(initial, template)`; assert `len == 46`. Expected by category (a dict in the test, each entry with a comment citing its source): `SAF-CO` → `(CO, F, F, F, None, F)` (KB *Immediate safety escalation*); `SAF-GAS` → `(GAS, …)`; `SAF-SPARK` → `(SPARKS_SMOKE_FLAMES, …)`; `SCH-BURNING` → `(None, True, F, F, None, F)` (R-7, D2); `BILL-REFUND` → `(None, F, F, F, REFUND, F)`; `BILL-DISPUTE` → `(…, BILLING_DISPUTE, F)`; `COMPLAINT-CONDUCT`, `COMPLAINT-OPINION` → `(None, F, F, True, COMPLAINT_OR_MANAGER, F)` (KB *Supervisor escalation*, R-2, PD-1); `COMPLAINT-REPEAT` → `(None, F, F, F, COMPLAINT_OR_MANAGER, F)`; `COMMERCIAL` → `(…, COMMERCIAL, F)` (KB *Department redirects*); **every other category** (incl. `BILL-DUP`, PRD §3.2 driver B; `MEM-CANCEL`, cases.md §3.4 row 4; `SCH-LATE`) → `NOTHING`. Assert `_labels(match_rules(template)) == expected` for all 46; print `"templates labelled: 46/46"` |
| `test_corpus_firings_reviewed` (AC-2) | Load the CSV (§6.2) into `{(call_id, line_no): (rule_ids_tuple, reason)}`; assert every `reason` non-empty. Run `match_rules` on all customer lines; `actual = {(call_id, line_no): rule_ids}` for lines with any id. Assert `actual.keys() == expected.keys()` (on failure print the **keys** only of the two differences) and each `rule_ids` equal. Assert the 9 safety calls (`SAFETY_CALLS = {"CALL-20260712-0046": GAS, "CALL-20260728-0264": GAS, "CALL-20260822-0185": GAS, "CALL-20260721-0093": CO, "CALL-20260805-0290": CO, "CALL-20260816-0038": CO, "CALL-20260822-0341": CO, "CALL-20260905-0318": CO, "CALL-20260717-0180": SPARKS_SMOKE_FLAMES}`) each have a line whose `match_rules(...).safety` is that kind. Assert `len(customer_lines) == 2256`. Print `"customer lines: 2256; safety calls: 9/9; reviewed firings: 70"` and the `Counter` of rule-id tuples |
| `test_safety_variants` (AC-3) | 22 cases `(case_id, text, kind, dimension, source)`; `source` is the clean issued line it varies (`SAF-GAS` "I smell gas near my furnace.", `SAF-CO` "My carbon monoxide detector is going off.", `SAF-SPARK` "There are sparks coming from the outdoor unit.", synthetic clean `"I smell something burning and the breaker tripped."` for burning-with-breaker). **gas:** typo `"i smel gas near my furnce"`; mid-chat `"Thanks for booking that. Also, I smell gas near my furnace now."`; paraphrase `"there is a gas leak in the basement"`; paraphrase (HP-2) `"smells like rotten eggs"`; case `"I SMELL GAS NEAR MY FURNACE"`; shorthand `"gas smell by furnace"`. **co:** typo `"my carbon monoxde detecter is going off"`; mid-chat `"ok the 2pm works. wait, my carbon monoxide detector just started going off"`; paraphrase `"our monoxide alarm is sounding"`; case `"MY CARBON MONOXIDE DETECTOR IS GOING OFF"`; shorthand (HP-2) `"co alarm keeps going off"`; shorthand `"C.O. detector beeping"`. **sparks_smoke_flames:** typo `"there are sprks coming from the outdoor unit"`; mid-chat `"Before you look up my account, I just saw sparks coming out of the outdoor unit"`; paraphrase `"flames are coming out of the furnace"`; case `"THERE ARE SPARKS COMING FROM THE OUTDOOR UNIT"`; shorthand `"outdoor unit sparking"`. **burning_with_breaker:** typo `"i smell somthing burnign and the breker tripped"`; mid-chat `"Thursday is fine. Also there is a burning smell now and the breaker just tripped."`; paraphrase `"there is an electrical burning odor and the circuit breaker keeps tripping"`; case `"I SMELL SOMETHING BURNING AND THE BREAKER TRIPPED"`; shorthand `"burnt smell, breaker popped"`. Each → `safety is kind`, `burning_unclear is False`, `rule_ids[0] == _SAFETY_ID[kind]`. Also assert every (kind, dimension) of the 4 × 5 grid has ≥ 1 case; print the grid of counts |
| `test_burning_paths` (AC-4) | `"I smell something burning and the breaker tripped."` → `BURNING_WITH_BREAKER`, `burning_unclear False`; `"I smell something burning and I see smoke."` → `SPARKS_SMOKE_FLAMES`, `burning_unclear False`; WP-6's sentence → `safety None`, `burning_unclear True` |
| `test_burning_breaker_unknown_or_denied_still_asks` (plan-added, PD-3) | `"I don't know if the breaker tripped, but something smells burnt."` and `"I smell something burning but the breaker has not tripped."` → `safety None`, `burning_unclear True` |
| `test_comfort_reports_do_not_fire` (AC-5) | `"My AC isn't cooling."` (WP-3 / NODANGER), `"the furnace wont kick on"`, `"the ac runs but the air is warm"`, `"my thermostat is blank"`, `"the water heater pilot light keeps going out"`, DANGER's `"my mother is 88 and it's 95 degrees in here"` → `_labels(...) == NOTHING` and `rule_ids == ()` (so `danger_words` is False for DANGER) |
| `test_explicit_danger_phrases` (AC-6) | One sentence per SP-1 phrase: `"Someone in the house is in danger"`, `"My son can't breathe"`, `"She cannot breathe"`, `"He is having trouble breathing"`, `"My father is not breathing"`, `"My mom passed out"`, `"My husband is unconscious"`, `"Grandpa fainted"`, `"I think she has heat stroke"`, `"heatstroke"`, `"This is a medical emergency"` → `danger_words True`, `safety None`, `rule_ids == ("R8.danger_words",)` |
| `test_person_requests` (AC-7) | person, no policy: `"can I talk to a person"`, `"I want to speak to a human"`, `"connect me to a live agent"`, `"representative please"`, `"agent"`, `"transfer me"`, `"can someone call me back"`, `"is this a real person?"` (PD-2) → `person True`, `policy_trigger None`, `rule_ids == ("R2.person",)`. Manager (PD-1): `"I want to talk to a manager"`, `"can I speak to your supervisor"`, `"let me talk to someone in charge"`, `"is your manager around"` → `person True` **and** `policy_trigger is COMPLAINT_OR_MANAGER`, `rule_ids == ("R2.person", "R24.complaint_or_manager")`. Not a request: `"I spoke to a representative yesterday"`, `"I need a person to come out and fix my AC"`, `"I'm a manager at a bank"`, `"don't need a human, just book me"` → `person False`; `"i manage a 12 unit strip center"` → `person False`, `policy_trigger is COMMERCIAL` |
| `test_correction_phrases` (AC-8) | `"that's not what I asked"`, typo `"thats not waht i asked"`, `"that's wrong"`, typo `"thats wrnog"`, `"no, I said Thursday"`, typo `"no, i siad thursday"` → `correction True`, every other label empty, `rule_ids == ("OD6.correction",)` |
| `test_plain_replies_are_not_corrections` (AC-9) | `"no"`, `"No."`, `"no thanks"`, `"not sure"`, `"yes"`, `"Yes please"`, `"nope"` → `correction False` and `rule_ids == ()` |
| `test_rule_matches_hold_no_text` (AC-10) | `sentinel = "zq" + uuid.uuid4().hex[:12]`; text `f"I smell gas near my furnace {sentinel} and I want a refund"` → assert it fired (`rule_ids` non-empty); `sentinel not in m.model_dump_json()`, `not in repr(m)`, `not in` any id; every id matches `re.fullmatch(r"(R\d+|OD\d+)\.[a-z_]+", rid)` and is in `ALL_RULE_IDS`; `len(ALL_RULE_IDS) == 13` |
| `test_policy_triggers` (plan-added) | `"I'm going to call my lawyer"` → `LEGAL_OR_CHARGEBACK`; `"I want to file a chargeback"` → `LEGAL_OR_CHARGEBACK`; `"I want a refund or I'll call my lawyer"` → `LEGAL_OR_CHARGEBACK` (PD-7); `"The tech quoted me $252 and the invoice says $312. That's not what I agreed to."` → `BILLING_DISPUTE`, `correction False`; `"I think I got charged twice"` → `None` (driver B); `"the tech was rude"` → `COMPLAINT_OR_MANAGER`, `person False`; `"do you guys do commercial work?"` → `COMMERCIAL`; `"I want to cancel my comfort club membership"` → `NOTHING`; `"This is Sue Miller"` → `NOTHING` |
| `test_negated_mentions_do_not_fire` (plan-added, PD-5) | `"I don't smell gas"`, `"there are no sparks"`, `"no one is in danger"`, `"no burning smell"`, `"I don't want a refund"`, `"I don't need to talk to a person"` → `NOTHING`; and the comma case `"No, there are sparks"` → `SPARKS_SMOKE_FLAMES` |
| `test_typo_correction_does_not_overreach` (plan-added, PD-4) | `"the fan keeps turning"`, `"the burst pipe is leaking"`, `"I spoke to the tech"`, `"the top layer of insulation"`, `"the tech dripped water"`, `"the flame sensor needs cleaning"`, `"the furnace won't fire up"`, `"the motor burned out"`, `"it's burning up in here"` → `NOTHING` |
| `test_empty_and_placeholder_text_fire_nothing` (plan-added) | `""`, `"   "`, AEA-04's STORE placeholders `"[card number removed]"` and `"[code]"`, AEA-12's `"[code entered]"`, `"[details submitted]"` → `NOTHING`, `rule_ids == ()` |
| `test_rule_id_order` (plan-added, PD-6) | `"I smell gas and my dad can't breathe, let me talk to a manager, that's wrong"` → `rule_ids == ("R5.gas", "R8.danger_words", "R2.person", "R24.complaint_or_manager", "OD6.correction")` |

### 7.2 `tests/unit/test_import_direction.py::test_rules_imports` (AC-11)

The file already imports `ast`, `dataclasses`, `sys`, `Path` and `meridian.policy.limits` at the top and defines
`SRC = Path(__file__).resolve().parents[2] / "src" / "meridian"`. Append at the **end** of the file one block headed by
the comment `# --- AEA-05: gates/rules.py ---`, using `SRC`, `ast`, `sys` and `Path` as they are, **adding no
module-level import** and not calling or editing the other tickets' helpers:

1. A private helper `def _aea05_imported_modules(tree: ast.Module) -> list[str]:` walking **all** nodes: for
   `ast.Import` collect each `alias.name`; for `ast.ImportFrom` `assert node.level == 0, "relative import in gates/rules.py"`
   and collect `node.module or ""`. Return the sorted list.
2. `def test_rules_imports() -> None:` with a one-line docstring reading
   `AEA-05 AC-11: gates/rules.py imports only the standard library and meridian.domain; no own types; no I/O.`
   `tree = ast.parse((SRC / "gates" / "rules.py").read_text(encoding="utf-8"))`; `seen = _aea05_imported_modules(tree)`;
   `print("gates/rules.py imports:", seen)`.
3. Every name is stdlib (`name.split(".")[0] in sys.stdlib_module_names or name == "__future__"`) **or** is
   `meridian.domain` / starts with `meridian.domain.`; collect the rest into `outside` and `assert not outside, outside`.
4. `defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}`;
   `assert not defined & {"RuleMatches", "SafetyKind", "HandoffReason"}`.
5. `io_builtins = {"open", "print", "input", "exec", "eval", "compile", "__import__", "breakpoint"}`; the set of
   `n.func.id` for every `ast.Call` whose `func` is an `ast.Name` must be disjoint from it (same check as AEA-04's).
6. Identity, with the imports **inside the function**:
   `import meridian.gates.rules as rules_mod` and `from meridian.domain.turn import RuleMatches, SafetyKind`;
   `assert vars(rules_mod)["RuleMatches"] is RuleMatches` and `assert vars(rules_mod)["SafetyKind"] is SafetyKind`.

### 7.3 Commands (cheapest first; stop at the first red)

Run from the worktree root with `export UV_LINK_MODE=hardlink`:

| # | Check | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check src/meridian/gates/rules.py tests/unit/gates tests/unit/test_import_direction.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check src/meridian/gates/rules.py tests/unit/gates tests/unit/test_import_direction.py` | `… files already formatted` (run without `--check` to fix, then re-run) |
| 3 | Type check (mypy strict, pydantic plugin) | `uv run mypy src/meridian/gates/rules.py tests/unit/gates/test_rules.py tests/unit/test_import_direction.py` | `Success: no issues found in 3 source files` |
| 4 | Affected tests (while iterating and before the final commit) | `uv run pytest tests/unit/gates/test_rules.py tests/unit/test_import_direction.py -q` | all pass; no skips |
| 5 | Evidence prints | `uv run pytest tests/unit/gates/test_rules.py -q -s -k "templates or corpus or variants"` and `uv run pytest tests/unit/test_import_direction.py::test_rules_imports -q -s` | the 46/46, 2256 / 9/9 / 70 lines, the 4 × 5 grid, the import list |
| 6 | Affected scope proof | `grep -rln "gates.rules\|match_rules" tests/ src/` | only `src/meridian/gates/rules.py`, `tests/unit/gates/test_rules.py`, `tests/unit/test_import_direction.py` |
| 7 | Affected journeys | `uv run python -m tests.journeys.affected --base main` and `uv run pytest -m journey --collect-only -q` | `0 journeys affected` (no `tests/journeys/j*/test_*.py` exists yet); collect-only exits 0 with no tests (AEA-01's `conftest.py` hook). Record "no journey gate yet (AEA-57)" in the report |
| 8 | Diff scope | `git diff --name-only main...HEAD` | exactly the owned files of §2 |

No pytest-xdist is needed (the whole file runs in about a second; the corpus pass is 2,256 lines at under 1 ms each). If
used at all, `-n 2` at most. **Full suite: not run** (build-loop rule: no `conftest.py`, setting, dependency or
widely-imported module changes here). No test calls a model, a network or a database.

### 7.4 Evidence the implementer reports, per criterion

AC-1 `46/46` line; AC-2 `9/9` and `70` lines with the Counter; AC-3 grid; AC-4…AC-10 pass lines; AC-11 import list;
AC-12 the record path and its Level / Blocked-by lines; AC-13 the `git diff --name-only` output; plus the four gate
outputs (lint, format, type, tests) and the journey line, each with the command run. Verification level for every claim:
`mock-tested`.

---

## 8. Risks and requests

**Collisions with other slices**

- `tests/unit/test_import_direction.py` already holds AEA-01, 03 and 04 functions on `16ca639`; **AEA-02** appends its
  own too. The collision map (slice plan §3) does not list the file. Each ticket appends a self-contained block, so a
  textual conflict at the end of the file is likely when AEA-02 and AEA-05 merge. **Request to the orchestrator /
  merge agent:** keep every block (independent functions, private helpers). Merge order 04 → 02 → 05 puts AEA-05's
  block last.
- `.claude/state/icm-progress.md` (*Routes verified…* rows) and DO-3 §3's `**Built:**` line may also be touched by
  AEA-02's context criterion. Resolve by keeping both texts and joining the lists (§5 step 7). The area-map A1 row is
  AEA-05's and later AEA-12's only.
- `tests/unit/gates/`: AEA-05 owns `test_rules.py` and `data/corpus_firings_reviewed.csv`; AEA-12 (wave 1) owns
  `test_gate.py`. No shared file.
- **Siblings planned against this plan:** AEA-12 §4.4 (phrases and what they fire), AEA-36 PA-4 (`rule_ids[0]` is the
  safety id, then danger), AEA-14 (`R2.person`, `R24.<reason>`). Verified unchanged on the scratch prototype at the
  refresh. A change to PD-6 or a §7.1 phrase would break them, so the implementer may not make one (§5 *must NOT*).

**Shared primitives needed:** none new. `RuleMatches` with `correction`, `SafetyKind`, `HandoffReason` must exist as
§4 copies them (AEA-02). AEA-01 must provide `pyproject.toml`, `src/meridian/gates/__init__.py`, the lint/type/pytest
config and `tests/unit/test_import_direction.py`.

**Known, accepted behaviour (recorded so reviewers do not read it as a bug)**

- PD-8: "do you install co detectors" and "my smoke alarm is going off" fire safety; recall first (M-14 hard gate).
- PD-2: "is this a real person?" fires `person` (one extra P3 handoff at worst).
- "I want to dispute this charge with my bank" gives `billing_dispute`, not `legal_or_chargeback`: "dispute" fires and
  "chargeback" is absent; both are P3 supervisor escalations.
- "my brotherinlaw is a lawyer" fires `legal_or_chargeback` (any mention of a lawyer); rare and P3.
- A free-text reply "yes, the breaker tripped" to the burning card has no burning word, so `safety` stays `None`; AEA-12's
  step 7 then gives `BURNING_ANSWER` "unsure" (conditional instruction, P1) rather than P0. **Note for AEA-12's
  planner:** if P0 is wanted there, AEA-12 must read breaker words itself; `RuleMatches` has no field for a bare
  breaker trip and DO-4 fixes its fields.

**Spec gaps, none blocking**

- DO-4 gives no format for `rule_ids`; PD-6 fixes it in the cases.md §3.4 style. AEA-36 consumes them as opaque
  stable codes.
- The parked `triggers.py` and SP-1 merged legal into complaints and put membership cancel in the rules; DO-4 and
  cases.md §3.4 win (legal apart; membership cancel is the planner's).

**Contract problems:** none. No signed contract (OpenAPI, `UI_CONTRACTS.md`) is touched; no decision D-4…D-15 is
answered differently.

**Gates:** none (no human, external, paid or live gate).

---

## 9. Readiness

**READY**, with one merge-order prerequisite: **blocked-on AEA-02** for the import of `RuleMatches`, `SafetyKind`
(`meridian.domain.turn`) and `HandoffReason` (`meridian.domain.handoff`), which every line of `rules.py`'s logic
returns. AEA-01 (the scaffold) is on `main` since `07924f5`. Start the implementer when AEA-02 is on `main` (wave-0
order AEA-04 → AEA-02 → AEA-05, R-G-18; AEA-04 merged at `ef03e05`); step 1.2 stops it cleanly otherwise, with no
local copy of the types. No `NEEDS-DECISION`: the only open choice the ticket left to the
plan (AC-7, manager → person) is decided as PD-1, inside the ticket's stated latitude.

**Reference:** the reviewed corpus-firing list for AC-2 is §6.2 of this plan, committed as
`tests/unit/gates/data/corpus_firings_reviewed.csv` (AC-13).
