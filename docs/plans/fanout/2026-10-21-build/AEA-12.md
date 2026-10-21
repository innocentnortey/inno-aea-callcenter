# Plan — [AEA-12] gates: intake parsing and the gate decision

**Status:** planned. **READY** once AEA-02 and AEA-05 are merged to `main` (AEA-01 and AEA-04 already are); see §9.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/12 (spec copy:
`docs/plans/tickets/AEA-12.md`) · **Base revision:** `16ca639` (main when refreshed; holds AEA-01 `893b825`, AEA-03
`2689582`, AEA-04 `9145044`, AEA-08 `c0621de`; first planned at `9c3e7e7`)
**Lane / risk / wave:** `lane::build-loop` · **`risk::security`** · wave 1
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 (refreshed the same day against `16ca639`) · **Builders:**
`test-writer-agent` (frozen tests first, §7.1), then `fanout-implementer` (Sonnet) · **Slug / branch:**
`gate-intake-decision` → branch `aea-12-gate-intake`, worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-12`
(the orchestrator creates it, from a `main` that already holds AEA-02 and AEA-05)

This plan is written for builders who have not read the design. Every name, value, path and command below is decided.
If something here turns out wrong when you run it, **stop and report back**. Do not improvise, and do not edit a
frozen test.

---

## 1. Goal and sources

### Goal (from the issue, *What to build*)

> **US-3 · Get the safety instruction first.** "As a homeowner who smells gas, hears a CO alarm or sees sparks, smoke or
> flames, I need the safety instruction before anything else, so that I leave the home before I'm asked for a name or an
> account." Also served: US-2 (a person on the first ask), US-4 (burning smell: asked, not told to check), US-5 (danger
> words), US-8 (the code is entered in chat and never shown).

`src/meridian/gates/gate.py` is the pure code that decides which turns never reach a model. It exposes exactly five
public functions, one public type alias, one public order constant and two public text constants:

| Name | What it does |
|---|---|
| `parse_intake(payload: TurnPayload) -> Intake` | Turns a CON-2 payload into an `Intake` **before anything stores the text**: STORE-redacts every client string it keeps, keeps the code and the form phone as `SecretStr`. |
| `decide_gate(intake: Intake, flags: GateFlags) -> GateDecision` | Runs `match_rules(intake.text_store)` and returns one `GateKind` by graph-core §3's 11-step table. |
| `flags_from_state(state: ConversationState) -> GateFlags` | Reads the four flags out of the conversation state. |
| `card_target(card_id: str) -> CardTarget` | Parses an untrusted card id into `(kind, task_id)`. |
| `burning_card_id(turn_id: TurnId) -> str` | `"burn-<turn_id>"`. |
| `CardTarget` | `tuple[Literal["burning", "code", "locate", "task", "unknown"], str \| None]` |
| `GATE_ORDER_HEAD` | `(GateKind.SAFETY, GateKind.AI_PAUSED)`: steps 1 and 2 as **one tuple** (GRC-3, decided option A by D-14). |
| `CODE_ENTERED`, `DETAILS_SUBMITTED` | `"[code entered]"`, `"[details submitted]"`: the stored text of a code turn and of a submitted form. |

**Concrete example (the ticket's worked pairs).**

- Input (WP-5): a text payload `"My carbon monoxide detector is going off."`. `parse_intake` → `Intake(kind="text",
  text_store="My carbon monoxide detector is going off.", …)`. `decide_gate(intake, no flags)` →
  `GateDecision(kind=GateKind.SAFETY, rules.safety=SafetyKind.CO)`; `gate_result()` = `"safety"`. No model is called;
  the gates node (AEA-36) then sends the KB instruction first. HP-2's typo form `"co alarm keeps going off"` gives the
  same decision.
- Input (WP-6): `"I need to schedule a service call. I smell something burning from the vents."` → `BURNING_ASK`,
  `gate_result()` = `"burning_unclear"`. On the next turn the customer taps "Not sure" on card `burn-<turn_id>`: a choice
  payload `{"kind": "choice", "card_id": "burn-<turn_id>", "option": "not_sure"}` → `BURNING_ANSWER`,
  `burning_answer="unsure"`, `gate_result()` = `"burning_unclear"` (R-7: "If unclear → a conditional safety
  instruction").
- Input (a code turn): `{"kind": "code", "card_id": "code-<turn_id>", "code": <6 digits>}` → `Intake(kind="code",
  text_store="[code entered]", code_digits=SecretStr(…), card_id="code-<turn_id>")` → `CODE_ENTRY`. The digits exist
  only inside the `SecretStr`; `repr`, `model_dump_json` and the stored text never show them.

### Context

Wave 1 of the Stage 8 build. Wave 0 lands the types (`domain/turn.py`, `domain/state.py`: AEA-02), the redaction
function (`privacy/redact.py`: AEA-04, **on main**), the word rules (`gates/rules.py`: AEA-05) and the scaffold
(AEA-01, **on main**). This ticket is the decision code between them. It is `risk::security` because a bug here could
store a verification code, a card-like number or a phone in `text_store`, state or a log, or let an untrusted `card_id`
route a turn into another task. GRC-3 (safety before or after "AI paused") was decided as option A on 2026-10-21
(stage7-signoff D-14: "the DAT/CAS/GRC items stay on their recommended options"), so the ticket's "Awaiting Innocent:
GRC-3" line is settled.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-12.md` (= issue #12) | AC-1…AC-15; worked pairs WP-5, WP-6 |
| Requirements | PRD `docs/prd/inno-aea-callcenter-prd.md` R-2, R-5, R-7, R-8, R-13, R-15, R-31, R-47; US-2…US-5, US-8; HP-2 | Safety first; person on first ask; burning asks; card numbers never stored; code never shown; AI pauses under a person |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §1 (`Controller`, `IdentityState`, `OpenTask`), §3 (`RuleMatches`, `FormValues`, `Intake`, `GateKind`, `GateDecision`, `decide_gate`), §4 (`join_plan` takes the gate's policy word), §14 (`RunTurn.payload`, `TurnService` step 4) | Exact field names; §3's order comment is **superseded** by graph-core §3 |
| Stage 7 addenda (win over DO-4, §16) | `stage7/graph-core.md` §1 (type homes), §2 (`CardChoice`, payload union, `Intake.card_id`, rules 1–4 "never in state"), §3 (`GateFlags`, `flags_from_state`, `card_target`, `CardTarget`, `burning_card_id`, card prefixes, the 11-step table, the `gate_result()` table) | The whole algorithm of §5 below. Re-read at `16ca639`: unchanged since first planning (AEA-08's `c0621de` touched wording only) |
| Stage 7 addenda | `stage7/data.md` §1 (`redact`, `RedactionProfile.STORE`, `Redacted.replaced`, `RedactionKind.CARD`, tokens `[card number removed]`, `[code]`; STORE keeps phones, emails, addresses, names, city and ZIP) | What STORE removes and what it keeps; confirmed in the merged `privacy/redact.py` (§4.3) |
| Stage 7 addenda | `stage7/web.md` §9 (`run_turn` step 4 runs `parse_intake` once, writes the message row) | `parse_intake` runs before any flags exist, so it decides `text_store` from the payload alone |
| Decision ledgers | `docs/plans/7b-decisions/graph-core.md` GRC-3, GRC-4, GRC-5, GRC-10; `residuals-graph.md` R-G-10, R-G-20; `residuals-web.md` R-W-15; `docs/plans/stage7-signoff.md` D-14 | Order tuple = option A; payload union in `domain/turn.py`; `gate_result()` is AEA-02's |
| OpenAPI (signed, read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` `TurnPayload`, `TextPayload` (text 1–2000), `ChoicePayload` (`card_id`, `option`: strings, no limits), `CodePayload` (`code` `^[0-9]{6}$`, "Never reaches the model, logs or traces"), `FormPayload` (`values` all optional; phone "DATA CLASS: PII"), `BurningCheckBlock` | `card_id` and `option` are client-supplied and unbounded: treat as untrusted |
| Code design | DO-3 `docs/design/code-design.md` (revision 3) §2.1 (pure core imports no I/O), §3 (tree line `gate.py`, l.212), §4.1 row `gates/gate.py` ("depends on: rules, domain, redact"), §5.4 (gate edges), §9 (unit tests mirror `src/`), §10 C-6 | Module home; allowed imports; test home `tests/unit/gates/` |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` E-1 (WP-5, WP-6), E-5 (safety and danger slice, rule half), E-3 (person request) | This module is exercised by those E-runs; numbers come from runs at Stage 9, not from these unit tests |
| Observability contract | DO-6 `docs/design/observability-contract.md` *Content and redaction* step 1 (intake masks); `turn.gate_result` status values; WF-1 | The intake masks happen here, before any store, model or trace; this module logs and writes nothing |
| Key-metrics registry | DO-7 M-14, M-15, M-16, M-17 | Stay computable from `turn.gate_result` (AC-2, AC-5, AC-6); targets measured at Stage 9 |
| Sibling plans | `docs/plans/fanout/2026-10-21-build/AEA-02.md` §4.0 (type homes and `as Name` re-exports), §4.1, §4.4, §4.8, §4.10; `AEA-05.md` §4, §7.1 (rule phrases, `rule_ids`, PD-6, PD-9) | Exact import paths; the phrases the tests below rely on |
| Merged code | `src/meridian/privacy/redact.py` (AEA-04, `9145044`); `tests/journeys/affected.py`, `pyproject.toml`, `tests/conftest.py` (AEA-01, `893b825`); precedent context edits `22023f2` (AEA-04), `90757d3` (AEA-01) | `redact` as built; commands; the format of the AC-15 context edits |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md` rule 6 | Frozen tests first; affected tests only; journey record at level `mock-tested`; context rows in the same change |

---

## 2. Boundary

### Owned files: the only files the builders may create or edit

| Path | Who | Create / modify | What |
|---|---|---|---|
| `tests/unit/gates/test_gate.py` | **test-writer** (frozen after) | create | Every test of §7.1. The implementer **never edits it** (tamper check) |
| `src/meridian/gates/gate.py` | implementer | create | §4–§5 |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-12.md` | implementer | create | AC-14 record (§5 step I-6) |
| `.claude/reference/area-map.md` | implementer | modify **the A1 row's Status cell only** | AC-15 (step I-7.1) |
| `.claude/state/icm-progress.md` | implementer | modify **one Evidence cell** | *Routes verified against code and tests* (AC-15, step I-7.2) |
| `docs/design/code-design.md` | implementer | modify **one tree line** in §3 (the `gate.py` line) | AC-15 (step I-7.3) |

`tests/unit/gates/__init__.py` already exists on main (AEA-01); neither builder touches it.

### Shared surfaces: read, never edit

- `src/meridian/domain/*.py`, `src/meridian/ports/*.py`, `src/meridian/config.py` (AEA-02).
- `src/meridian/gates/rules.py` (AEA-05). `src/meridian/privacy/redact.py` (AEA-04). `src/meridian/policy/*` (AEA-01,
  AEA-03).
- `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/journeys/**`, `tests/unit/test_import_direction.py`
  (AEA-01 and the wave-0 tickets append there; this ticket does **not**: its purity check lives in `test_gate.py`).
- `docs/design/**` other than the one line above, `docs/plans/**`, `docs/ux/**`, `apps/web/**`,
  `docs/ux/03-structure/ui-contracts.openapi.yaml`, `docs/ux/03-structure/UI_CONTRACTS.md`, the briefing,
  `docs/data/issued/**`, `docs/archive/**`, `docs/parked/**`. Never read `.env`.

### Owned by other tickets: do not create or touch

- `agent/nodes/front.py` (the gates node that writes `burning_card_id`, AEA-36); `agent/nodes/compose.py` (mints card
  ids, AEA-21); `services/turn.py` (calls `parse_intake`, AEA-40); `policy/escalation.py` (AEA-14); `agent/nodes/plan.py`
  (`join_plan`, AEA-37); `tests/unit/gates/test_rules.py` (AEA-05). This ticket adds no safety text, creates no case,
  verifies no identity, writes no state and calls no model.

### Interfaces this slice produces (others build against them; keep the names exactly)

- `meridian.gates.gate`: `parse_intake`, `decide_gate`, `flags_from_state`, `card_target`, `burning_card_id`,
  `CardTarget`, `GATE_ORDER_HEAD`, `CODE_ENTERED`, `DETAILS_SUBMITTED`.
- Consumers: AEA-40 (`parse_intake`), AEA-36 (`decide_gate`, `flags_from_state`, `burning_card_id`), AEA-21
  (`burning_card_id`), AEA-37 / AEA-14 (read the `GateDecision`). This ticket consumes no sibling of its own or a later
  wave, so it needs no injected double.

---

## 3. Requirements table

Every acceptance criterion of the issue (verbatim IDs), then the obligations the sources add. "Test" means a function
in `tests/unit/gates/test_gate.py` unless a path is given. Run with
`uv run pytest tests/unit/gates/test_gate.py -q -rA`.

### 3.1 Acceptance criteria → frozen tests (the test-writer's manifest)

| AC | Tag | Requirement (short; full text in the ticket) | How it is implemented | Frozen test(s) |
|---|---|---|---|---|
| AC-1 | invariant | Gate order = graph-core §3 table; steps 1–2 one tuple. Option A: CO + `ai_paused` → `SAFETY`; option B → `AI_PAUSED`. Earliest step wins: safety + person → `SAFETY`; burning + person → `BURNING_ASK`; person words in a code turn → `PERSON` | `GATE_ORDER_HEAD` read at call time; §5 algorithm D-1…D-12 | `test_order_first_match_wins` (parametrised over both tuples × 7 combinations, §7.1) |
| AC-2 | invariant | **WP-5** and `"co alarm keeps going off"` → `SAFETY`, `rules.safety = co`, `gate_result()` = `safety` | D-2 | `test_wp5_co_alarm_is_safety` |
| AC-3 | invariant | **WP-6** → `BURNING_ASK`, `gate_result()` = `burning_unclear` | D-5 | `test_wp6_burning_smell_asks` |
| AC-4 | invariant | Burning answers: `yes`/`no`/`not_sure` → `yes`/`no`/`unsure`; stale `burn-` card still counts; text while `burning_card_id` set → `unsure`; same text with person words → `PERSON`; `gate_result()` yes → `safety`, unsure → `burning_unclear`, no → `clear` | D-4, D-8 | `test_burning_answers` |
| AC-5 | invariant | Person words → `PERSON`, `gate_result()` = `person_requested`, on turn 1 | D-7 | `test_person_words_first_ask` |
| AC-6 | invariant | Danger words → `DANGER_RULE`, `gate_result()` = `danger` | D-6 | `test_danger_words` |
| AC-7 | invariant | `ai_paused` + free text, no safety → `AI_PAUSED`, `gate_result()` = `ai_paused` | D-2 | `test_human_controller_pauses_ai` |
| AC-8 | invariant | Code payload → kind `code`, `"[code entered]"`, `SecretStr`, `card_id` kept, `CODE_ENTRY`; `new_code` choice on open code card → `CODE_ENTRY`; locate form → `"[details submitted]"`, phone `SecretStr`, `LOCATE`; where form on open task → ZIP/city, `CARD_CHOICE` + `resume_task_id`; slot choice on open task → `CARD_CHOICE` + `resume_task_id` | P-3…P-5, D-9…D-11 | `test_code_cards_and_forms` |
| AC-9 | failure/refusal | Unknown prefix, task not in `open_task_ids`, `code-` choice with no code card open → `FREE_TEXT`; stale choice's `text_store` = option; stale form's = `"[details submitted]"`, values discarded | C-1…C-6, P-5, D-12 | `test_untrusted_and_stale_cards_are_free_text` |
| AC-10 | invariant | `card_target`, `burning_card_id`, `flags_from_state` exact | C-1…C-6, F-1…F-4 | `test_card_target_burning_card_id_and_flags` |
| AC-11 | invariant | Card-like number → `[card number removed]`, `card_number_seen` True; standalone six digits → `[code]` | P-2 | `test_card_and_code_removed_at_intake` |
| AC-12 | negative | Code, card-like number and full phone, generated in the test, absent from `text_store`, `repr`/`model_dump_json` of `Intake` and `GateDecision`, `rule_ids`, a validation error message, captured logs | P-1…P-5; no logging in `gate.py` | `test_secrets_absent_from_intake_decision_errors_logs` |
| AC-13 | invariant | Pure: same input → same decision; imports no I/O and nothing from `agent/`, `services/`, `web/`, `adapters/` | Import allowlist §4.1 | `test_gate_module_is_pure` |
| AC-14 | journey | No journey yet (wave 1 is before AEA-57). Record at level `mock-tested`, *Blocked by* AEA-57, naming **J-3** (code and form intake), **J-5** (the gate decision), **J-7** (the person request); the affected-journey command prints "0 journeys affected" | Step I-6 | the record + `uv run python -m tests.journeys.affected --base main` |
| AC-15 | regression/context | Area map A1 row, ICM *Routes verified* row, DO-3 §3 status updated in the same change | Step I-7 | `git diff --name-only main...HEAD` lists the three files |

**Level of AC-14: `mock-tested`** (unit level: no server, no database, no model). Nothing integrated is claimed. This is
the ticket's single `[journey]` criterion.

### 3.2 Obligations the sources add (plan-added; frozen with the rest)

| # | Obligation | Source | Disposition | Frozen test |
|---|---|---|---|---|
| PA-1 | Every client string `parse_intake` keeps is STORE-redacted: the choice `option` (into `text_store` and `choice.option`) and a `card_id` that `card_target` classes `unknown` | graph-core §2 (`card_id` "untrusted"), DO-6 step 1 ("card-like numbers in any message") | added (P-1, P-3) | `test_untrusted_choice_strings_are_store_redacted` |
| PA-2 | Form `text_store` rules: locate → `"[details submitted]"`; where form (only `zip_or_city`) on a task card → the STORE-redacted ZIP or city; any other form → `"[details submitted]"`; a form on a card that is not `locate` or `task` keeps no `FormValues` | DO-4 §3 `Intake.text_store` comment; graph-core §3 step 11 | added (P-5) | `test_form_text_store_rules` |
| PA-3 | `AI_PAUSED` comes before every card step (a code, a burn choice and a locate form while a person controls the chat) | graph-core §3 steps 2–10 | added (D-2) | `test_ai_paused_precedes_every_card_step` |
| PA-4 | A code payload is `CODE_ENTRY` whether or not a code card is open (step 8 "kind `code`" has no condition) | graph-core §3 step 8 | added (D-9) | `test_code_payload_is_always_code_entry` |
| PA-5 | A policy word gets no kind of its own: it rides on `rules.policy_trigger` of the decision | DO-4 §4; ticket *What to build* | added (D-12) | `test_policy_word_rides_on_free_text` |
| PA-6 | An unrecognised option on a `burn-` card (e.g. `"maybe"`) is `unsure`: fail toward the conditional safety instruction | R-7 "If unclear → a conditional safety instruction" | added (D-4) | inside `test_burning_answers` |
| — | `gate_result()` itself (every kind) | R-G-10 | other-ticket: AEA-02 (`domain/turn.py` §4.8) implements it; this ticket asserts it for AC-2…AC-7 and the three burning answers | — |
| — | The gates node writes `burning_card_id`; compose mints `code-`/`locate-`/task card ids | GRC-4, GRC-5 | other-ticket: AEA-36, AEA-21 | — |
| — | Code digits and form phone in no checkpoint, row, log, span or model request | graph-core §2 rule 4 | other-ticket: AEA-51 (sentinel test), AEA-40 AC-8 | — |
| — | WF-1 capture (CAP-1, CAP-2) | DO-6 | other-ticket: AEA-51 | — |
| — | E-1 / E-5 measured numbers | DO-5 | n/a here: Stage 9 runs | — |

**Entry-point registration:** None. `gate.py` adds no route, command or job (ticket: "Entry points added or changed:
None").

---

## 4. Shared code to use (copied from the contracts and the merged code; verify in pre-flight step 0)

### 4.1 The exact imports of `gate.py`, and nothing else

```python
from __future__ import annotations

import re
from typing import Final, Literal

from meridian.domain.common import TurnId
from meridian.domain.state import ConversationState
from meridian.domain.turn import (
    CardChoice,
    ChoicePayload,
    CodePayload,
    FormPayload,
    FormValues,
    GateDecision,
    GateFlags,
    GateKind,
    Intake,
    TextPayload,
    TurnPayload,
)
from meridian.gates.rules import match_rules
from meridian.privacy.redact import Redacted, RedactionKind, RedactionProfile, redact
```

(`RuleMatches` is not imported: `gate.py` only reads `match_rules`' return value. If ruff's `F401` would flag an import
above as unused in your final code, drop that one import; never add one outside the allowlist.)

**Why these paths work under mypy strict:** AEA-02 (§4.0 of its plan) *defines* `FormValues` in `domain/identity.py`
and `SafetyKind` in `domain/common.py`, and re-exports both from `domain/turn.py` as `from meridian.domain.X import
Name as Name`, which mypy strict accepts. Import them from `meridian.domain.turn`, never from `identity` or `common`.

**Allowlist (AC-13 asserts it):** `__future__`, `re`, `typing`, `meridian.domain.common`, `meridian.domain.state`,
`meridian.domain.turn`, `meridian.gates.rules`, `meridian.privacy.redact`. No `logging`, `datetime`, `time`, `os`,
`random`, `sqlite3`, `httpx`, any SDK, and nothing under `meridian.agent`, `meridian.services`, `meridian.web`,
`meridian.adapters`, `meridian.ports`, `meridian.policy`. If, on the base, a type is not importable from the module
§4.1 names, **stop and report** (`blocked-on AEA-02`); the frozen allowlist would need the same file, and neither
builder edits around it.

### 4.2 Types consumed (AEA-02; DO-4 §3 + graph-core §2–§3, as AEA-02's plan §4.1, §4.4, §4.8, §4.10 writes them)

```python
# domain/common.py
class MeridianModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)
class TurnId(_PatternId): PATTERN = _UUID4_PATTERN        # str subclass; lower-case UUID4; TurnId("…") constructs unvalidated

# domain/turn.py (SafetyKind defined in common, FormValues in identity; both re-exported here)
class SafetyKind(StrEnum): GAS = "gas"; CO = "co"; SPARKS_SMOKE_FLAMES = "sparks_smoke_flames"; BURNING_WITH_BREAKER = "burning_with_breaker"

class FormValues(MeridianModel):
    name: str | None = None
    phone: SecretStr | None = None
    customer_id: CustomerId | None = None             # ^MHC-[0-9]{5}$
    invoice_number: InvoiceId | None = None           # ^INV-[0-9]{6}$
    zip_or_city: str | None = None

class CardChoice(MeridianModel):     card_id: str; option: str          # client-supplied, untrusted
class TextPayload(MeridianModel):    kind: Literal["text"] = "text"; text: str = Field(min_length=1, max_length=2000)
class ChoicePayload(CardChoice):     kind: Literal["choice"] = "choice"
class CodePayload(MeridianModel):    kind: Literal["code"] = "code"; card_id: str; code: SecretStr
    # field_validator("code"): exactly six digits, else PydanticCustomError("invalid_format", "expected exactly six digits")
class FormPayload(MeridianModel):    kind: Literal["form"] = "form"; card_id: str; values: FormValues
TurnPayload = Annotated[TextPayload | ChoicePayload | CodePayload | FormPayload, Field(discriminator="kind")]

class Intake(MeridianModel):
    kind: Literal["text", "choice", "code", "form"]
    text_store: str
    code_digits: SecretStr | None
    form: FormValues | None
    card_number_seen: bool
    choice: CardChoice | None
    card_id: str | None = None

class RuleMatches(MeridianModel):
    safety: SafetyKind | None
    burning_unclear: bool
    danger_words: bool
    person: bool
    policy_trigger: HandoffReason | None
    rule_ids: tuple[str, ...]
    correction: bool                                  # graph-core §8; gate.py does not read it

class GateKind(StrEnum):
    AI_PAUSED = "ai_paused"; SAFETY = "safety"; BURNING_ASK = "burning_ask"; BURNING_ANSWER = "burning_answer"
    DANGER_RULE = "danger_rule"; PERSON = "person"; CODE_ENTRY = "code_entry"; LOCATE = "locate"
    CARD_CHOICE = "card_choice"; FREE_TEXT = "free_text"

class GateFlags(MeridianModel):
    ai_paused: bool
    burning_card_id: str | None
    code_card_open: bool
    open_task_ids: tuple[str, ...]

class GateDecision(MeridianModel):
    kind: GateKind
    rules: RuleMatches
    burning_answer: Literal["yes", "no", "unsure"] | None = None
    resume_task_id: str | None = None
    def gate_result(self) -> GateResult: ...          # GateResult = Literal["clear", "safety", "burning_unclear", "danger", "person_requested", "ai_paused"]
```

`MeridianModel` makes every model immutable, rejects unknown fields, strips string whitespace (so `"   "` becomes `""`),
and keeps the input out of validation errors.

`domain/state.py` (`IdentityState` defined in `identity`, re-exported here):

```python
class Controller(MeridianModel):  kind: Literal["ai", "human"]; representative_name: str | None = None; case_ref: CaseRef | None = None
class IdentityState(MeridianModel): status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]; …
class OpenTask(MeridianModel):    task_id: str; specialist: …; intent: …; opened_turn: TurnId; details: …; status: Literal["open", "waiting_identity", "done"]
class ConversationState(MeridianModel):
    thread_id: ThreadId                               # required
    controller: Controller = Controller(kind="ai")    # default_factory
    identity: IdentityState                           # default_factory: status "not_checked"
    open_tasks: list[OpenTask] = []                   # default_factory
    burning_card_id: str | None = None                # GRC-4; writer: the gates node only
    turn_input: TurnInput                             # required
    …                                                 # other keys not read here
```

`domain/handoff.py`: `HandoffReason` (defined in `common`, re-exported here; tests only, for PA-5:
`HandoffReason.REFUND`).

### 4.3 Functions consumed

```python
# meridian.gates.rules (AEA-05, plan §4)
def match_rules(text: str) -> RuleMatches: ...       # pure; never raises on any str; "" → nothing fires

# meridian.privacy.redact (AEA-04, ON MAIN at 9145044; stdlib dataclass, not pydantic) — copied from the file
class RedactionKind(StrEnum):
    CARD = "card"; CODE = "code"; PHONE = "phone"; EMAIL = "email"; ADDRESS = "address"; NAME = "name"
    CUSTOMER_ID = "customer_id"; INVOICE_ID = "invoice_id"; FREE_TEXT = "free_text"
class RedactionProfile(StrEnum): STORE = "store"; SONNET = "sonnet"; JEV = "jev"; TRACE = "trace"; LOG = "log"
@dataclass(frozen=True)
class Redacted:
    text: str                                         # the redacted text; LOG: ""
    replaced: Mapping[RedactionKind, int]             # a MappingProxyType; only kinds with a count > 0 appear
    length: int
    def __repr__(self) -> str: ...                    # counts only, never text
class UnknownRedactionProfile(ValueError): ...
def redact(text: str, profile: RedactionProfile) -> Redacted: ...   # pure, idempotent
```

**What STORE does (data.md §1; `_RULES_BY_PROFILE[STORE] = (_CARD_RULE, _CODE_RULE)` in that order):** it replaces
card-like numbers (13–19 digits, single spaces or dashes between digits, not glued to other digits) with
`[card number removed]`, then standalone six-digit numbers (not after `INV-`, `$`, or a digit plus `.`/`,`) with
`[code]`. It **keeps** phones, emails, street addresses, names, city and the 5-digit ZIP. So a phone typed into free
text stays in `text_store` by design (the SONNET, JEV and TRACE profiles mask it later). AC-12's phone is therefore the
**form** phone, which is a `SecretStr` and never enters `text_store`.

### 4.4 Rule phrases the tests rely on (from AEA-05's plan §7.1; these fire exactly as noted)

| Phrase | Fires |
|---|---|
| `"My carbon monoxide detector is going off."`, `"co alarm keeps going off"` | `safety = CO` (`R5.co`) |
| `"I need to schedule a service call. I smell something burning from the vents."` | `burning_unclear` |
| `"I smell something burning"` | `burning_unclear` |
| `"can I talk to a person"` | `person` (`R2.person`) |
| `"My son can't breathe"` | `danger_words` |
| `"I want a refund"` | `policy_trigger = REFUND` only |
| `"not sure"`, `"When will the technician arrive?"`, `"yes"`, `"56"`, `"new_code"`, `"Austin"`, `"78704"`, `"[code entered]"`, `"[details submitted]"`, `"[card number removed]"` | nothing |

If AEA-05 as merged does not fire a phrase as listed, the test-writer stops and reports (it is AEA-05's behaviour, not
this ticket's).

---

## 5. Steps

### 5.0 Order of work

1. **Test-writer** (steps 0, T-1…T-4): writes `tests/unit/gates/test_gate.py` exactly as §7.1, proves every test is
   red for the right reason (`ModuleNotFoundError: meridian.gates.gate`), commits. The orchestrator records the hash in
   the frozen-test manifest.
2. **Implementer** (steps 0, I-1…I-8): writes `gate.py` until the frozen tests pass, then the record and context rows.

Module boundary (rule `code-design-solid-modularity`): `gate.py` sits in the pure core (DO-3 §2.1). It depends on
`domain` (types), `gates.rules` (word rules) and `privacy.redact` (masking), all lower or same-area modules; nothing
depends on it yet. It defines no new interface or abstraction.

### Step 0 (both roles). Pre-flight: the wave-0 imports exist on the base

Run in the worktree, with `export UV_LINK_MODE=hardlink` in every shell:

```bash
uv sync
uv run python -c "from meridian.domain.turn import CardChoice, ChoicePayload, CodePayload, FormPayload, FormValues, GateDecision, GateFlags, GateKind, Intake, RuleMatches, SafetyKind, TextPayload, TurnPayload; from meridian.domain.state import ConversationState, Controller, IdentityState, OpenTask; from meridian.domain.common import TurnId; from meridian.domain.handoff import HandoffReason; print('domain ok')"
uv run python -c "from meridian.gates.rules import match_rules; from meridian.privacy.redact import Redacted, RedactionKind, RedactionProfile, redact; print('rules+redact ok')"
uv run python -c "from meridian.domain.state import ConversationState; from meridian.domain.turn import GateFlags; print('burning_card_id' in ConversationState.model_fields, sorted(GateFlags.model_fields))"
ls src/meridian/gates/__init__.py tests/unit/gates/__init__.py
```

Expected: `domain ok`, `rules+redact ok`, `True ['ai_paused', 'burning_card_id', 'code_card_open', 'open_task_ids']`,
both files listed. If a domain import fails: **stop, report `blocked-on AEA-02`**. If `match_rules` fails:
`blocked-on AEA-05`. (`redact` and both `__init__.py` files are on main since `9145044` / `893b825`.) Never write a
local copy of a missing type.

### Steps T-1…T-4 (test-writer)

- **T-1.** Create `tests/unit/gates/test_gate.py` with the module header, helpers and fixtures of §7.1 (a).
- **T-2.** Write every test of §7.1 (b), with the names exactly as listed (the reviewer and the record cite them).
- **T-3.** Run `uv run pytest tests/unit/gates/test_gate.py -q`. Every test must fail with
  `ModuleNotFoundError: No module named 'meridian.gates.gate'` (raised inside the `g` fixture), and nothing else.
  Then `uv run pytest --collect-only -q` must exit 0 (the file collects because the module is imported by the
  fixture, not at the top). Then `uv run ruff check tests/unit/gates/test_gate.py`,
  `uv run ruff format --check tests/unit/gates/test_gate.py`, `uv run mypy tests/unit/gates/test_gate.py` must pass.
- **T-4.** Commit: `git add tests/unit/gates/test_gate.py`, message
  `test(gates): frozen tests for intake parsing and the gate decision (AEA-12)` + blank line + `Refs #12` + blank
  line + `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` as the **last** line.

### Step I-1. `card_target` and `burning_card_id` (algorithm C)

Module-level private constants (no other module-level state):

```python
_MAX_CARD_ID_CHARS: Final = 128
_CARD_ID_CHARS: Final = re.compile(r"[A-Za-z0-9._-]+")
_TASK_CARD: Final = re.compile(r"(?P<task>.+)\.(?P<n>[0-9]+)")
_PREFIXES: Final[tuple[tuple[str, Literal["burning", "code", "locate"]], ...]] = (
    ("burn-", "burning"), ("code-", "code"), ("locate-", "locate"),
)
CardTarget = tuple[Literal["burning", "code", "locate", "task", "unknown"], str | None]
```

`card_target(card_id: str) -> CardTarget`, numbered steps:

- **C-1.** If `len(card_id) > _MAX_CARD_ID_CHARS` or `_CARD_ID_CHARS.fullmatch(card_id) is None` → `("unknown", None)`.
  *Invariant: an id with spaces, brackets, unicode or over 128 characters routes nowhere (empty string included).*
- **C-2.** For each `(prefix, kind)` in `_PREFIXES`, in order: if `card_id.startswith(prefix)` → return `(kind, None)`
  when `len(card_id) > len(prefix)`, else `("unknown", None)`. *Invariant: the three code-minted prefixes win over the
  task pattern ("burn-x.1" is a burning card); a bare prefix is unknown.*
- **C-3.** `m = _TASK_CARD.fullmatch(card_id)`; if `m` → `("task", m.group("task"))`. The regex splits at the **last**
  dot because `.+` is greedy: `"t.1.3"` → task `"t.1"`. *Invariant: a task card always names a non-empty task id and
  a numeric suffix.*
- **C-4.** Otherwise → `("unknown", None)`.
- **C-5.** Matching is case-sensitive: `"BURN-…"` is unknown.
- **C-6.** `card_target` never raises and never trusts the id: it only classifies. Whether a task is open is
  `decide_gate`'s question (D-11).

`burning_card_id(turn_id: TurnId) -> str`: `return f"burn-{turn_id}"`.

### Step I-2. `flags_from_state` (algorithm F)

- **F-1.** `ai_paused = state.controller.kind == "human"`.
- **F-2.** `burning_card_id = state.burning_card_id`.
- **F-3.** `code_card_open = state.identity.status == "code_sent"`.
- **F-4.** `open_task_ids = tuple(t.task_id for t in state.open_tasks if t.status != "done")`, in list order.
- Return `GateFlags(ai_paused=…, burning_card_id=…, code_card_open=…, open_task_ids=…)`. Read nothing else.

### Step I-3. `parse_intake` (algorithm P)

Public constants: `CODE_ENTERED: Final = "[code entered]"`, `DETAILS_SUBMITTED: Final = "[details submitted]"`.

Private helpers:

```python
def _card_seen(r: Redacted) -> bool:
    return r.replaced.get(RedactionKind.CARD, 0) > 0

def _store_card_id(card_id: str) -> tuple[str, bool]:
    """Known-shape ids are kept verbatim (a STORE pass could mangle a UUID with a long digit run);
    an unknown id routes nowhere, so it is STORE-redacted before it can reach state."""
    if card_target(card_id)[0] != "unknown":
        return card_id, False
    r = redact(card_id, RedactionProfile.STORE)
    return r.text, _card_seen(r)

def _is_where_form(v: FormValues) -> bool:
    return bool(v.zip_or_city) and v.name is None and v.phone is None and v.customer_id is None and v.invoice_number is None
```

`parse_intake(payload: TurnPayload) -> Intake`, numbered steps (pass **every** `Intake` field explicitly):

- **P-1 Text.** `if isinstance(payload, TextPayload)`: `r = redact(payload.text, RedactionProfile.STORE)` →
  `Intake(kind="text", text_store=r.text, code_digits=None, form=None, card_number_seen=_card_seen(r), choice=None,
  card_id=None)`. *Invariant: no free text reaches `text_store` unredacted (R-13, DO-6 step 1).*
- **P-2** (what P-1 guarantees, AC-11): a card-like number → `[card number removed]` with `card_number_seen=True`; a
  standalone six-digit number → `[code]`.
- For every other kind: `card_id, id_card_seen = _store_card_id(payload.card_id)`;
  `target_kind = card_target(card_id)[0]`.
- **P-3 Choice.** `if isinstance(payload, ChoicePayload)`: `r = redact(payload.option, RedactionProfile.STORE)` →
  `Intake(kind="choice", text_store=r.text, code_digits=None, form=None, card_number_seen=id_card_seen or
  _card_seen(r), choice=CardChoice(card_id=card_id, option=r.text), card_id=card_id)`. Build a **new** `CardChoice`;
  never store the `ChoicePayload` instance itself in `choice` (it is a `CardChoice` subclass with a `kind` field).
  *Invariant: the stored text of a choice is its option string (graph-core §3 step 11; AEA-40 reads it), and an
  untrusted option cannot smuggle a card number into state.*
- **P-4 Code.** `if isinstance(payload, CodePayload)` → `Intake(kind="code", text_store=CODE_ENTERED,
  code_digits=payload.code, form=None, card_number_seen=id_card_seen, choice=None, card_id=card_id)`. Reuse the
  `SecretStr` object; never call `get_secret_value()` in `gate.py`. *Invariant: the digits exist only inside the
  `SecretStr` (R-15, US-8).*
- **P-5 Form.** `if not isinstance(payload, FormPayload): raise TypeError(f"parse_intake: unsupported payload type
  {type(payload).__name__}")` (the message names the type only, never a value). Then, with `v = payload.values`:
  - `target_kind == "locate"` → `text_store=DETAILS_SUBMITTED`, `form=v`, `seen=id_card_seen`;
  - `target_kind == "task"` and `_is_where_form(v)` → `r = redact(v.zip_or_city, RedactionProfile.STORE)`;
    `text_store = r.text or DETAILS_SUBMITTED`, `form=v`, `seen = id_card_seen or _card_seen(r)`;
  - `target_kind == "task"`, not a where form → `text_store=DETAILS_SUBMITTED`, `form=v`, `seen=id_card_seen`;
  - any other `target_kind` (`unknown`, `burning`, `code`) → `text_store=DETAILS_SUBMITTED`, **`form=None`** (the values
    are discarded at intake: no node could ever route them), `seen=id_card_seen`.
  - Return `Intake(kind="form", text_store=…, code_digits=None, form=…, card_number_seen=seen, choice=None,
    card_id=card_id)`.
  *Invariant: a form's name, phone, customer id and invoice number never reach `text_store`; only a where form's ZIP
  or city does (DO-4 §3), and STORE keeps the ZIP and the city.*

(mypy note: `v.zip_or_city` is `str | None`; inside the where-form branch narrow it with a local
`zc = v.zip_or_city` and `assert zc is not None` is **not** allowed in `src/` by ruff `S101`; instead compute
`zc = v.zip_or_city or ""` and redact `zc`.)

No `try`/`except`, no logging, no `print`.

### Step I-4. `decide_gate` (algorithm D, graph-core §3's table)

Public constant, with a comment citing GRC-3 and D-14:

```python
GATE_ORDER_HEAD: tuple[GateKind, GateKind] = (GateKind.SAFETY, GateKind.AI_PAUSED)
```

`decide_gate` must read `GATE_ORDER_HEAD` **from the module global at call time** (the frozen AC-1 test flips it with
`monkeypatch.setattr`). Do not bind it as a default argument, copy it into a closure or mark it `Final`.

Private helper `_burning_answer(option: str) -> Literal["yes", "no", "unsure"]`: `match option: case "yes": return
"yes"; case "no": return "no"; case _: return "unsure"` (covers `"not_sure"` and anything unrecognised: PA-6).

`decide_gate(intake: Intake, flags: GateFlags) -> GateDecision`, numbered steps; the first that applies returns:

- **D-1.** `rules = match_rules(intake.text_store)`. `target_kind, task_id = card_target(intake.card_id) if
  intake.card_id is not None else ("unknown", None)`. Every returned decision carries `rules=rules`.
- **D-2 (steps 1–2, the tuple).** `for head in GATE_ORDER_HEAD:` if `head is GateKind.SAFETY and rules.safety is not
  None` → `SAFETY`; if `head is GateKind.AI_PAUSED and flags.ai_paused` → `AI_PAUSED`. *Invariant: under option A a
  safety phrase gets the safety instruction even while a person controls the chat; every other step waits behind a
  paused AI.*
(Numbering: D-2 covers table steps 1–2; from D-4 on, D-n is table step n − 1. There is no D-3.)
- **D-4 (step 3).** `intake.kind == "choice"` and `intake.choice is not None` and `target_kind == "burning"` →
  `BURNING_ANSWER` with `burning_answer=_burning_answer(intake.choice.option)`. Any `burn-` card counts, current or
  stale. *Invariant: a "yes" is never ignored.*
- **D-5 (step 4).** `rules.burning_unclear` → `BURNING_ASK`.
- **D-6 (step 5).** `rules.danger_words` → `DANGER_RULE`.
- **D-7 (step 6).** `rules.person` → `PERSON`.
- **D-8 (step 7).** `intake.kind == "text"` and `flags.burning_card_id is not None` → `BURNING_ANSWER`,
  `burning_answer="unsure"`.
- **D-9 (step 8).** `intake.kind == "code"` → `CODE_ENTRY` (no condition on `code_card_open`: the identity node
  answers a code with no code sent). Or `intake.kind == "choice"` and `target_kind == "code"` and
  `flags.code_card_open` → `CODE_ENTRY`. `resume_task_id` stays `None`.
- **D-10 (step 9).** `intake.kind == "form"` and `target_kind == "locate"` → `LOCATE`.
- **D-11 (step 10).** `intake.kind in ("choice", "form")` and `target_kind == "task"` and `task_id in
  flags.open_task_ids` → `CARD_CHOICE`, `resume_task_id=task_id`. *Invariant: an untrusted card can only resume a task
  the conversation actually has open.*
- **D-12 (step 11).** Otherwise → `FREE_TEXT` (text; a stale or unknown card; a `code-` choice with no code card
  open; a form on a closed task). The policy word, if any, rides on `rules.policy_trigger` (PA-5).

Construct each decision as `GateDecision(kind=…, rules=rules)` plus `burning_answer=` / `resume_task_id=` only where
named above.

### Step I-5. Iterate to green

`uv run pytest tests/unit/gates/test_gate.py -q -rA` until every test passes. Then the fast gates of §7.2. If a
frozen test fails and you believe the test is wrong, **stop and report** the test name, the input and the two values;
do not edit the test and do not bend `gate.py` away from §5 to satisfy it. Commit 1:
`git add src/meridian/gates/gate.py`, message `feat(gates): intake parsing and the gate decision (AEA-12)` + blank
line + one paragraph (what the five functions do; GRC-3 option A as one tuple) + blank line + `Refs #12` + blank line
+ `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` as the **last** line. Note the short SHA
(`git rev-parse --short=7 HEAD`) as `<sha7>`, and the pass count of `uv run pytest tests/unit/gates -q` as `<N>`.

### Step I-6. Journey record (AC-14)

Date: `TZ=America/Chicago date +%F`. Create `docs/testing/journeys/<date>-AEA-12.md` (the folder exists on main), in
the format of `2026-10-21-AEA-04.md` plus the field list of `integrated-journeys.md` §4:

```markdown
# Journey record: AEA-12 gates/gate.py

| Field | Value |
|---|---|
| Claim | AEA-12 `gates/gate.py`: `parse_intake`, `decide_gate`, `flags_from_state`, `card_target` and `burning_card_id` behave as stage7/graph-core.md §3 says (AC-1…AC-13). No journey run. |
| Level | `mock-tested` |
| Tested revision | `<sha7>` |
| Environment | VPS worktree `inno-aea-callcenter-wt/AEA-12`, Python 3.12 via `uv`; no server, no database, no model; unit tests only |
| Command | `uv run pytest tests/unit/gates -q -rA`; `uv run python -m tests.journeys.affected --base main` |
| Result | `<N> passed`; affected command: `0 journeys affected` |
| Evidence location | GitLab issue #12 comment; implementer report; this file |
| Remaining limitations | Unit level only: the gates node (AEA-36), the turn service's intake step (AEA-40) and the real entry point (AEA-51) are not exercised; spec gaps G-1…G-5 in the plan §8 |
| Blocked by | AEA-57 (journey harness, wave 2) |
| Journeys that will exercise this code | J-3 (code and form intake) and J-5 (the gate decision: CO alarm and danger path) once AEA-57 and AEA-51 land; J-7 (the person request) once AEA-52 lands |
```

No code, card number, phone number or demo credential in it.

### Step I-7. Context rows (AC-15)

The collision map (slice plan §3) says each ticket changes **only its own row** of these three files. Read each line
first; AEA-05 (wave 0) may have edited the A1 row before you. Use `<sha7>` from step I-5.

1. **`.claude/reference/area-map.md`, the A1 row** (`| 1 | **A1 Gates** | Decide the turns that never reach a model |
   `gates/{rules,gate}.py` | AEA-05, 12 | <Status> |`). Change **only the last (Status) cell**; leave the Owns and
   Tickets cells as they are. Follow the A0 row's wording ("`<path>` actual (AEA-NN, `<sha>`)"):
   - If the Status cell already names `gates/rules.py` as actual (AEA-05's edit, e.g. ``partly built: `gates/rules.py`
     actual (AEA-05, `abc1234`); `gates/gate.py` planned``), the area is now complete: write
     ``built: `gates/rules.py` actual (AEA-05, `<its sha, unchanged>`); `gates/gate.py` actual (AEA-12, `<sha7>`)``.
   - If it still reads `planned`, write ``partly built: `gates/gate.py` actual (AEA-12, `<sha7>`); `gates/rules.py`
     planned`` and tell the orchestrator (AEA-05 should already be merged).
2. **`.claude/state/icm-progress.md`, the *Routes verified against code and tests* row.** Main has **two** rows with
   that title (lines 17–18 at `16ca639`, left by parallel merges). Edit **only the last** of them (at `16ca639` its
   Evidence begins `2026-10-21: area map A0 → `policy/texts.py``; if AEA-05 changed it, it is still the last row with
   that title). Keep its Status (`provisional`) and its last cell; **replace only the Evidence cell** with:
   ``<date>: area map A1 → `gates/gate.py` checked against `tests/unit/gates/test_gate.py` (AEA-12, `<sha7>`; <N> pass)``.
   The row stays ≤ 400 characters (context-maintenance rule 6). Do not delete or merge the duplicate row (not this
   ticket's row; reported in §8).
3. **`docs/design/code-design.md` §3, the tree line** (l.212 at `16ca639`):
   `│   └── gate.py                                  parse_intake (text, choice, code, form) + decide_gate       A1    1`.
   Append three spaces and `built AEA-12 <sha7>` to the end of that line, exactly as AEA-04 did for
   `privacy/redact.py` (`… A0    0   built AEA-04 9145044`). Touch nothing else in DO-3.
4. Commit 2: `git add docs/testing/journeys/<date>-AEA-12.md .claude/reference/area-map.md
   .claude/state/icm-progress.md docs/design/code-design.md`, message
   `docs(AEA-12): journey record and context for gates/gate.py` + blank line + `Refs #12` + blank line +
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` as the **last** line.

### Step I-8. Final evidence

`git diff --name-only main...HEAD` must list exactly six files: `src/meridian/gates/gate.py`,
`tests/unit/gates/test_gate.py` (the test-writer's commit), `docs/testing/journeys/<date>-AEA-12.md`,
`.claude/reference/area-map.md`, `.claude/state/icm-progress.md`, `docs/design/code-design.md`. Report every command of
§7.2 with its result line, and the tamper check: `git diff <frozen-test-commit> HEAD -- tests/unit/gates/test_gate.py`
prints nothing.

### What the builders must NOT do

- Edit `tests/unit/gates/test_gate.py` after the test-writer commits (implementer), or `src/` (test-writer).
- Define or copy any type of §4.2, or import anything outside the §4.1 allowlist. No `logging`, no clock, no I/O.
- Add a word rule or read words in `gate.py` (a missing rule goes to AEA-05); add safety text (AEA-03/AEA-36); write
  state, create a case, verify identity or call a model; read `rules.correction` (it is AEA-38's).
- Call `get_secret_value()` anywhere in `gate.py`; put a value in an exception message.
- Trust a `card_id`: never compare it to anything but the three prefixes, the task pattern and `flags.open_task_ids`.
- Put a literal six-digit code, card-like number or full phone number in code, tests, test ids, comments, commit
  messages or docs. Tests build them at run time with `secrets.randbelow`.
- Edit `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/unit/test_import_direction.py`, anything under
  `domain/`, `gates/rules.py`, `privacy/redact.py`, the OpenAPI, `UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`.
- `git add -A`, force-push, push `main`, run more than `-n 2` workers, bind ports 4019 or 5184, copy a venv, or put
  `node_modules` in the worktree.

---

## 6. Data and fixtures

All synthetic, built inside the test file; no fixture files.

| Value | Built how | Source of the sample |
|---|---|---|
| WP-5, WP-6 sentences, HP-2 typo | literal strings (§4.4) | `docs/data/worked-pairs.md` WP-5, WP-6; `docs/design/hard-problems.md` HP-2 |
| Rule phrases | literal strings (§4.4) | AEA-05 plan §7.1 |
| Six-digit code | `_code()` = `"".join(str(secrets.randbelow(10)) for _ in range(6))` | synthetic |
| Card-like number | `_card()` = `"4" + "".join(str(secrets.randbelow(10)) for _ in range(15))`, then grouped as four blocks of four joined by `" "` | synthetic; AEA-04 STORE card pattern (13–19 digits, single spaces allowed) |
| Full phone | `_phone()` = `f"512-555-01{secrets.randbelow(100):02d}"` | synthetic; the 555-01xx fictional range |
| Turn ids | `_turn_id()` = `TurnId(str(uuid.uuid4()))` | synthetic |
| Task ids | `"t1"`, `"t2"`, `"t3"`, `"t9"`, `"t.1"` | synthetic |
| ZIP / city | `"78704"`, `"Austin"` | Meridian's fictional Austin service area |

`secrets.randbelow` is used instead of `random` so ruff's `S311` stays quiet (it is also ignored under `tests/**`).
Parametrize ids are readable words, never a generated value.

---

## 7. Checks

### 7.1 The frozen test file: `tests/unit/gates/test_gate.py` (test-writer)

**(a) Header, helpers, fixtures.**

```python
from __future__ import annotations

import ast
import importlib
import logging
import secrets
import uuid
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from pydantic import SecretStr, ValidationError

from meridian.domain.common import TurnId
from meridian.domain.handoff import HandoffReason
from meridian.domain.state import Controller, ConversationState, IdentityState, OpenTask
from meridian.domain.turn import (
    ChoicePayload, CodePayload, FormPayload, FormValues, GateDecision, GateFlags, GateKind, Intake, SafetyKind,
    TextPayload,
)
```

(Format the import block with `ruff format`; the one-line grouping above is for reading only.)

- Fixture `g() -> ModuleType`: `return importlib.import_module("meridian.gates.gate")`. Every test takes `g` and calls
  `g.parse_intake`, `g.decide_gate`, etc. (So the file collects before `gate.py` exists and each test is red with
  `ModuleNotFoundError`.)
- `_flags(*, paused=False, burning=None, code_open=False, tasks=()) -> GateFlags` →
  `GateFlags(ai_paused=paused, burning_card_id=burning, code_card_open=code_open, open_task_ids=tuple(tasks))`.
- `_text(t) -> TextPayload` = `TextPayload(text=t)`; `_choice(card_id, option)` = `ChoicePayload(card_id=card_id,
  option=option)`; `_code_payload(card_id, digits)` = `CodePayload(card_id=card_id, code=SecretStr(digits))`;
  `_form(card_id, **values)` = `FormPayload(card_id=card_id, values=FormValues(**values))` (pass `phone=SecretStr(p)`
  where a phone is used).
- `_decide(g, payload, flags=None) -> tuple[Intake, GateDecision]`: `i = g.parse_intake(payload)`;
  `return i, g.decide_gate(i, flags or _flags())`.
- `_state(*, controller_kind="ai", burning=None, identity_status="not_checked", tasks=()) -> ConversationState`:
  partial construction without validation (`ConversationState` requires `thread_id` and `turn_input`, which the gate
  never reads), typed through `Any` so strict mypy accepts it: `construct_state: Any =
  ConversationState.model_construct`; `construct_identity: Any = IdentityState.model_construct`; `construct_task: Any
  = OpenTask.model_construct`; return `construct_state(controller=Controller(kind=controller_kind),
  identity=construct_identity(status=identity_status), open_tasks=[construct_task(task_id=tid, status=st) for tid, st
  in tasks], burning_card_id=burning)`.
- `_code()`, `_card()`, `_phone()`, `_turn_id()` as §6.

**(b) Tests.** Each docstring starts with its tag (`invariant:`, `failure/refusal:`, `negative:`) and the AC id.

| Test | Cases and exact assertions |
|---|---|
| `test_order_first_match_wins` (AC-1) | Parametrise `order` over `[pytest.param((GateKind.SAFETY, GateKind.AI_PAUSED), id="option_a"), pytest.param((GateKind.AI_PAUSED, GateKind.SAFETY), id="option_b")]`; `monkeypatch.setattr(g, "GATE_ORDER_HEAD", order)`. Combinations (input, flags → kind under A / under B): (1) `"My carbon monoxide detector is going off."`, `paused=True` → `SAFETY` / `AI_PAUSED`; (2) `"co alarm keeps going off, can I talk to a person"`, no flags → `SAFETY` / `SAFETY`; (3) `"I smell something burning, can I talk to a person"`, no flags → `BURNING_ASK` / `BURNING_ASK`; (4) `"My son can't breathe, can I talk to a person"`, no flags → `DANGER_RULE` / `DANGER_RULE`; (5) person words in a code turn: `"can I talk to a person"`, `code_open=True` → `PERSON` / `PERSON`; (6) `"can I talk to a person"`, `paused=True` → `AI_PAUSED` / `AI_PAUSED`; (7) `"I smell something burning"`, `paused=True` → `AI_PAUSED` / `AI_PAUSED`. Also assert `g.GATE_ORDER_HEAD` (unpatched, in a separate assertion before patching) `== (GateKind.SAFETY, GateKind.AI_PAUSED)` and is a `tuple`. Print one line per combination: `f"{order_id} case{n}: {kind.value}"` |
| `test_wp5_co_alarm_is_safety` (AC-2, **WP-5**) | Both `"My carbon monoxide detector is going off."` and `"co alarm keeps going off"`: `d.kind is GateKind.SAFETY`, `d.rules.safety is SafetyKind.CO`, `d.gate_result() == "safety"`; print both |
| `test_wp6_burning_smell_asks` (AC-3, **WP-6**) | `"I need to schedule a service call. I smell something burning from the vents."` → `d.kind is GateKind.BURNING_ASK`, `d.gate_result() == "burning_unclear"`, `d.burning_answer is None` |
| `test_burning_answers` (AC-4, PA-6) | `burn = g.burning_card_id(_turn_id())`; flags `burning=burn`. Choices on `burn` with option `"yes"`, `"no"`, `"not_sure"`, `"maybe"` → `BURNING_ANSWER` with `"yes"`, `"no"`, `"unsure"`, `"unsure"`. Stale: a choice `"yes"` on `g.burning_card_id(_turn_id())` (a different turn) with `_flags()` (no burning id) → `BURNING_ANSWER`, `"yes"`. Free text `"not sure"` with `burning=burn` → `BURNING_ANSWER`, `"unsure"`. `"not sure, can I talk to a person"` with `burning=burn` → `PERSON`. `gate_result()`: yes → `"safety"`, unsure → `"burning_unclear"`, no → `"clear"`. Print each case's kind and answer |
| `test_person_words_first_ask` (AC-5) | `"can I talk to a person"`, `_flags()` (turn 1: nothing set) → `PERSON`, `gate_result() == "person_requested"` |
| `test_danger_words` (AC-6) | `"My son can't breathe"` → `DANGER_RULE`, `gate_result() == "danger"` |
| `test_human_controller_pauses_ai` (AC-7) | `"When will the technician arrive?"`, `paused=True` → `AI_PAUSED`, `gate_result() == "ai_paused"`; and `g.flags_from_state(_state(controller_kind="human")).ai_paused is True` |
| `test_code_cards_and_forms` (AC-8) | (a) `code = _code()`; `cid = f"code-{_turn_id()}"`; code payload → `i.kind == "code"`, `i.text_store == "[code entered]"`, `isinstance(i.code_digits, SecretStr)`, `i.code_digits.get_secret_value() == code`, `i.card_id == cid`, `d.kind is GateKind.CODE_ENTRY`, `d.resume_task_id is None`. (b) choice `"new_code"` on `cid`, `code_open=True` → `CODE_ENTRY`. (c) locate form on `f"locate-{_turn_id()}"` with `name="Omar Patel"`, `phone=SecretStr(_phone())` → `i.text_store == "[details submitted]"`, `isinstance(i.form.phone, SecretStr)`, `d.kind is GateKind.LOCATE`. (d) where form on `"t1.2"` with `zip_or_city="78704"`, `tasks=("t1",)` → `i.text_store == "78704"`, `i.form.zip_or_city == "78704"`, `d.kind is GateKind.CARD_CHOICE`, `d.resume_task_id == "t1"`; same with `"Austin"` → `text_store == "Austin"`. (e) slot choice `"56"` on `"t1.1"`, `tasks=("t1",)` → `CARD_CHOICE`, `resume_task_id == "t1"`, `i.choice.option == "56"`, `i.choice.card_id == "t1.1"`. All five: `gate_result() == "clear"`. Print intake kind, text_store, decision kind, resume id per case (never the code) |
| `test_untrusted_and_stale_cards_are_free_text` (AC-9) | Choices, each → `FREE_TEXT`, `resume_task_id is None`, `text_store` = the option: unknown prefix `"slot-56"` option `"56"`; task not open `"t9.1"` option `"56"` with `tasks=("t1",)`; `code-` choice `"new_code"` with `code_open=False`. Forms, each → `FREE_TEXT`, `text_store == "[details submitted]"`, `resume_task_id is None`: on `"slot-56"` with `name` + `phone` (→ `i.form is None`); on `f"code-{_turn_id()}"` with `name` + `phone` (→ `i.form is None`); on `g.burning_card_id(_turn_id())` with `zip_or_city="78704"` (→ `i.form is None`); a locate-style form (`name` + `phone`) on `"t9.1"` with `tasks=("t1",)`. For every case: `set(GateDecision.model_fields) == {"kind", "rules", "burning_answer", "resume_task_id"}` and the phone string (where used) is absent from `d.model_dump_json()`. Print case → kind, text_store |
| `test_card_target_burning_card_id_and_flags` (AC-10) | `t = _turn_id()`: `card_target(f"burn-{t}") == ("burning", None)`, `code-` → `("code", None)`, `locate-` → `("locate", None)`, `"t7.2"` → `("task", "t7")`, `"t.1.3"` → `("task", "t.1")`, `"burn-x.1"` → `("burning", None)`. Unknown (each `("unknown", None)`): `""`, `"burn-"`, `"code-"`, `"locate-"`, `"slot-56"`, `"t7"`, `"t7."`, `".3"`, `"t7.x"`, `"burn-a b"`, `"BURN-abc"`, `"a" * 127 + ".1"` (129 characters). Length edge: `"a" * 124 + ".1"` (126 characters) → `("task", "a" * 124)`. `burning_card_id(t) == f"burn-{t}"`. `flags_from_state(_state(controller_kind="human", burning="burn-x", identity_status="code_sent", tasks=[("t1", "open"), ("t2", "waiting_identity"), ("t3", "done")])) == GateFlags(ai_paused=True, burning_card_id="burn-x", code_card_open=True, open_task_ids=("t1", "t2"))`; and `_state()` defaults → `GateFlags(ai_paused=False, burning_card_id=None, code_card_open=False, open_task_ids=())`; `identity_status="verified"` → `code_card_open is False` |
| `test_card_and_code_removed_at_intake` (AC-11) | `card = _card()`: text `f"Can you take my card {card} now?"` → `card not in i.text_store`, `"[card number removed]" in i.text_store`, `i.card_number_seen is True`. `code = _code()`: text `f"the code was {code} I think"` → `code not in i.text_store`, `"[code]" in i.text_store`, `i.card_number_seen is False`. Print both stored texts |
| `test_secrets_absent_from_intake_decision_errors_logs` (AC-12) | `caplog.set_level(logging.DEBUG)`. `code, card, phone = _code(), _card(), _phone()`. Drive four turns through `_decide`: a code payload with `code`; a text with `card` and `code` in it; a locate form with `phone=SecretStr(phone)`; a choice on `"t1.1"` whose option contains `card`. For each `(i, d)` and each secret `s` in `(code, card, phone)`: `s not in i.text_store`, `s not in repr(i)`, `s not in i.model_dump_json()`, `s not in repr(d)`, `s not in d.model_dump_json()`, `all(s not in rid for rid in d.rules.rule_ids)`. Validation errors (`pytest.raises(ValidationError)`), each `str(err)` free of all three secrets: `TextPayload.model_validate({"kind": "text", "text": "x" * 1990 + card})` (too long); `CodePayload.model_validate({"kind": "code", "card_id": "code-x", "code": code, "note": code})` (extra field); `FormPayload.model_validate({"kind": "form", "card_id": "locate-x", "values": {"phone": phone, "customer_id": "MHC-1"}})` (bad customer id). Finally every secret absent from `caplog.text` and from each `record.getMessage()` |
| `test_gate_module_is_pure` (AC-13) | Parse `Path(g.__file__).read_text(encoding="utf-8")` with `ast`; collect every `Import` alias name and every `ImportFrom` module (assert `level == 0`). Assert the set ⊆ `{"__future__", "re", "typing", "meridian.domain.common", "meridian.domain.state", "meridian.domain.turn", "meridian.gates.rules", "meridian.privacy.redact"}` and disjoint from `{"sqlite3", "httpx", "anthropic", "openai", "langfuse", "fastembed", "requests", "socket", "time", "datetime", "random", "logging", "os"}`; no name starts with `meridian.agent`, `meridian.services`, `meridian.web`, `meridian.adapters`, `meridian.ports`. Print the sorted import list. Determinism: for WP-5's text, a code payload, and a burn choice, `parse_intake` twice → equal `Intake`s; `decide_gate` twice on the same intake and flags → equal decisions |
| `test_untrusted_choice_strings_are_store_redacted` (PA-1) | `card = _card()`: choice on `"t1.1"` with option `f"pay with {card}"`, `tasks=("t1",)` → `card not in i.text_store`, `card not in i.choice.option`, `i.card_number_seen is True`, `i.card_id == "t1.1"`. A choice whose `card_id` is `card.replace(" ", "")` (16 digits, unknown shape) option `"yes"` → `card.replace(" ", "") not in (i.card_id or "")`, `card not in repr(i)`, `i.card_number_seen is True`, `d.kind is GateKind.FREE_TEXT`. A code payload whose `card_id` is `_code()` (six digits, unknown) → that string not in `repr(i)`, `d.kind is GateKind.CODE_ENTRY`. A minted id is kept verbatim: `cid = f"code-{_turn_id()}"` → `i.card_id == cid` |
| `test_form_text_store_rules` (PA-2) | On `"t1.2"`, `tasks=("t1",)`: where form `zip_or_city="Austin"` → `"Austin"`; where form `zip_or_city="   "` → `"[details submitted]"`; task form with `zip_or_city="78704"` **and** `phone` → `"[details submitted]"`, `i.form is not None`, `CARD_CHOICE`. A stale where form (`"t9.2"`, only `zip_or_city="78704"`) → `FREE_TEXT`, `resume_task_id is None`, `text_store == "78704"` (graph-core §2 order: intake runs before flags exist; see §8 gap G-1) |
| `test_ai_paused_precedes_every_card_step` (PA-3) | `paused=True`: a code payload → `AI_PAUSED`; a `"yes"` choice on a burn card → `AI_PAUSED`; a locate form → `AI_PAUSED`; a slot choice on an open task → `AI_PAUSED` |
| `test_code_payload_is_always_code_entry` (PA-4) | Code payload on `f"code-{_turn_id()}"` with `code_open=False` → `CODE_ENTRY`; on `"slot-56"` → `CODE_ENTRY` |
| `test_policy_word_rides_on_free_text` (PA-5) | `"I want a refund"` → `FREE_TEXT`, `d.rules.policy_trigger is HandoffReason.REFUND`, `gate_result() == "clear"` |

### 7.2 Commands (implementer, worktree root; `export UV_LINK_MODE=hardlink`)

While iterating: `uv run pytest tests/unit/gates/test_gate.py -q -rA`.

Once before the final commit, cheapest first; stop at the first red:

| # | Command | Passing looks like |
|---|---|---|
| G-1 | `uv run ruff check` | `All checks passed!` |
| G-2 | `uv run ruff format --check` | `N files already formatted` |
| G-3 | `uv run mypy` | `Success: no issues found in N source files` (mypy's `files` = `src/meridian`, `tests`, `eval`) |
| G-4 | `uv run pytest tests/unit/gates tests/unit/test_import_direction.py -q -rA` | all passed. **Affected tests:** `tests/unit/gates/` mirrors the changed package (it also holds AEA-05's `test_rules.py`, which imports `gates.rules`, a neighbour); `test_import_direction.py` is the static import scan of `src/meridian`. `grep -rl "meridian.gates.gate" tests/` lists only `test_gate.py` |
| G-5 | `uv run python -m tests.journeys.affected --base main` | `changed files: <k> (base main)` then `0 journeys affected`, exit 0 (AC-14; no `tests/journeys/j*/test_*.py` exists before AEA-57) |
| G-6 | `git diff --name-only main...HEAD` | exactly the six files of step I-8 (AC-15) |

No full suite: this ticket changes no `conftest.py`, setting, dependency or lockfile, and nothing imports `gate.py`
yet (rule `build-loop-test-scope`). Never more than `-n 2` if you parallelise.

### 7.3 Review and merge (for the orchestrator)

`code-review-agent` re-runs G-1…G-5. `security-privacy-agent` reads this ticket's diff at the **wave-1 merge** (the
wave contains `risk::security` tickets), focusing on P-1…P-5, D-11 and gaps G-2 and G-4. The merge gate runs the
affected tests (`tests/unit/gates`, `tests/unit/test_import_direction.py`) and the affected journeys (none yet).

---

## 8. Risks and requests

**Collisions with other slices**

- `.claude/reference/area-map.md` A1 row: AEA-05 (wave 0) and this ticket only. AEA-05 merges first; step I-7.1
  rewrites only the Status cell and keeps AEA-05's text.
- `.claude/state/icm-progress.md` *Routes verified* row: every ticket's context criterion touches it, and main already
  carries **two** rows with that title (a merge left both). This ticket edits only the last one and leaves the
  duplicate alone; the orchestrator (or the wave-1 seam audit) should fold the duplicates into one row in a
  `lane::direct` cleanup. At merge, keep the higher status and the newest evidence.
- `docs/design/code-design.md` §3: this ticket touches only the `gate.py` tree line; AEA-05 touches only the
  `rules.py` line above it. No shared line.
- `tests/unit/gates/`: AEA-05 owns `test_rules.py`; this ticket owns `test_gate.py`. No shared file.
- AEA-21 and AEA-36 import `gates.gate.burning_card_id` (and AEA-36 `decide_gate`, `flags_from_state`). Their names and
  signatures are fixed above; they test against doubles until this merges.

**Shared primitives needed:** none new. Everything comes from AEA-02, AEA-04, AEA-05 and AEA-01 as §4 copies it.

**Spec gaps (engineering calls made here, none blocking; for reconciliation)**

- **G-1 Stale where form.** graph-core §3 step 11 says a stale form's `text_store` is `"[details submitted]"`. But
  `parse_intake` runs at `TurnService` step 4, before the gates node builds flags (graph-core §2 rule 1, web.md §9),
  so it cannot know a task is closed. Decision: a form that carries only `zip_or_city` on a task-shaped card stores
  the ZIP or city (DO-4 §3 "a where form → the ZIP or city"), even if the task turns out closed; the gate still
  returns `FREE_TEXT` with no `resume_task_id`, so nothing routes it. Every form that carries a name, phone, customer
  id or invoice number stores `"[details submitted]"`, and forms on cards that are not `locate` or `task` keep no
  `FormValues` at all. ZIP and city are not private (STORE keeps them, data.md §1). The step-11 sentence holds for
  every form with private values. Proposed wording for graph-core §3 step 11: "a stale form's `text_store` is what
  `parse_intake` stored (`"[details submitted]"`, or the ZIP or city of a where form); its values route nowhere".
  This is inside the addenda's engineering latitude (graph-core §3 is "[Decided §7, engineering]"); it touches no
  signed contract.
- **G-2 Unbounded `card_id` and `option`.** The signed OpenAPI gives neither a length limit. `card_target` treats ids
  over 128 characters or outside `[A-Za-z0-9._-]` as unknown, and `parse_intake` STORE-redacts unknown ids and every
  option. A long option string can still be stored as a long `text_store`. Request (not a blocker): AEA-40 bounds
  `option` and `card_id` at its own validation step; changing the OpenAPI is Innocent's, so it is only reported here.
- **G-3 Task id shape.** Task card ids are `<task_id>.<n>`; `task_id` has no defined format. This plan requires task
  ids to use only `[A-Za-z0-9._-]`, to be ≤ 120 characters, and **not** to start with `burn-`, `code-` or `locate-`.
  Request to AEA-37 (which mints `OpenTask.task_id`): confirm. A task id that violates it makes its cards `unknown` or
  misclassified, so they fall to `FREE_TEXT` (safe, but the slot pick would not resume).
- **G-4 Known-shape id with a card number inside** (e.g. `"<16 digits>.1"`). It is task-shaped, so it is kept verbatim
  and could reach `TurnInput.card_id`. It routes nowhere (the task is not open). Redacting known-shape ids was
  rejected because AEA-04's card pattern (`\d(?:[ -]?\d){12,18}`, dashes allowed) can match a long digit run inside a
  minted UUID and would corrupt real ids. Residual, noted for the wave-1 security review.
- **G-5 Burning reply in words.** A free-text "yes, the breaker tripped" after the burning card has no burning word,
  so step 7 gives `unsure` (conditional instruction, P1), not P0. This follows the table; AEA-05's plan records the
  same note. A P0 here would need a `RuleMatches` field DO-4 does not have.

**Contract problems:** none. No signed contract (OpenAPI, `UI_CONTRACTS.md`) changes; no decision D-4…D-15 is
answered differently (GRC-3 is built as decided by D-14, option A).

**Gates:** none (no human, external, paid or live gate).

---

## 9. Readiness

**READY**, with two real import prerequisites from wave 0 that are **not yet on main** at `16ca639`:

- **AEA-02**: every type of §4.2 (`meridian.domain.turn`, `.state`, `.common`, `.handoff`), including `GateFlags`,
  `CardChoice`, the `TurnPayload` union, `Intake.card_id`, `ConversationState.burning_card_id` and
  `GateDecision.gate_result()`. `src/meridian/domain/` holds only `__init__.py` today.
- **AEA-05**: `match_rules` with the phrases of §4.4. `src/meridian/gates/rules.py` does not exist today.

Already on main: **AEA-04** (`redact`, `RedactionProfile.STORE`, `Redacted.replaced`, `RedactionKind.CARD`; `9145044`)
and **AEA-01** (package skeleton, `pyproject.toml` with ruff/mypy strict/pytest markers, the affected-journeys command;
`893b825`).

Both builders' step 0 stops cleanly if AEA-02 or AEA-05 is missing. No `NEEDS-DECISION`: GRC-3 was decided (D-14,
option A), and the gaps in §8 are engineering calls inside the addenda's latitude, reported for reconciliation.
