# Plan — [AEA-03] foundation: every fixed customer sentence

**Status:** planned (READY)
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/3 (identical to
`docs/plans/tickets/AEA-03.md`) · **Base revision:** `9c3e7e7` (main) · **Wave:** 0 · **Lane:** build-loop · **Risk:** none
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21 · **Implementer:** fanout-implementer (Sonnet)
**Branch / worktree:** `aea-03-fixed-customer-texts` in `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-03`

---

## 1. Goal and sources

### Goal

From the issue's *What to build*: one module, `src/meridian/policy/texts.py`, that holds **every fixed sentence the
backend sends to a customer, word for word**, behind
`render(text_id: TextId, /, **values: str) -> str`, plus the one money formatter `format_usd(cents: int) -> str`.
Standard library only. Worked pair WP-5: for "My carbon monoxide detector is going off." the reply's first text is
built from this module: "Leave the home immediately and call 911 or your gas utility from outside." then "Don't flip
switches, open windows near the furnace, or restart equipment." then "Once you're outside and safe, you can leave a
number here if you'd like." No follow-up time anywhere (R-6, R-26).

**Concretely, what the implementer delivers:**
input `render(TextId.CODE_WRONG, n="2")` → output `"That code doesn't match. 2 tries left."`;
input `render(TextId.CODE_WRONG)` → raises `TextRenderError` with `text_id == "identity.code_wrong"`,
`placeholder == "n"`; input `format_usd(125000)` → `"$1,250"`.

### Context

Wave 0 foundation ticket, built in parallel with AEA-01 (scaffold), AEA-02 (domain), AEA-04 (redaction), AEA-05
(rules), AEA-06 (eval cases). Nothing in `src/` exists on main yet (`src/` is empty; the parked tree in
`docs/parked/2026-10-21-first-attempt/` is reference only and holds no texts module worth copying). After wave 0 this file
is **frozen**: a missing sentence later is a small follow-up ticket merged before its dependants (slice plan §3). Eleven
later tickets import it (AEA-13, 14, 21, 27, 29, 30, 31, 36, 38, 40, 43, 45, 46); AEA-06 quotes the same SCREEN_SPECS
words into `must_say`; AEA-50 hashes this file into `agent_version`.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-03.md` | AC-1…AC-12; the ten groups; named ids; `amount`, `format_usd`; report unplaceable sentences |
| Component contract (addendum, wins over DO-4) | `docs/design/contracts/stage7/data.md` §2 | `TextId(StrEnum)` values `"<group>.<name>"`; `TextRenderError(KeyError)` with `text_id: str`, `placeholder: str \| None`; `render(text_id: TextId, /, **values: str) -> str`; placeholders exactly `case_ref, due_label, window, digits, rep_name, n, amount`; `format_usd(cents: int) -> str`; `PERSON_REQUEST_LABEL`; `live` lines with `rep_name`; `booking.urgent_note`; `INBOX_CODE_BODY` / `INBOX_CODE_GONE` |
| Code design (DO-3) | `docs/design/code-design.md` §2.4 (line 163), §3 (line 192), §4.1 (line 306), §10 C-13 (line 668) | `policy/texts.py` depends on **none**; interface "constants, `render(text_id, **values)`"; TURN_TIMEOUT uses the UX sentence, not DO-1's "I'm sorry, …"; safety text uses the KB's "immediately" |
| DO-4 | `docs/design/contracts/internal-components.md` §11 (lines 747–760) | TURN_TIMEOUT, BUSY, SPEND_CAP_REACHED, RATE_LIMITED, AI_PAUSED customer texts come from this module |
| Cases addendum | `stage7/cases.md` §2 (`FeeNote.line`, lines 279–311), §3.2 (`PROMISE_TABLE`, lines 344–371), A-11 (line 875) | promise strings imported word for word by AEA-14; `R26.safety_none` = `""`; fee line = `render(<fee text>, amount=format_usd(cents))`; A-11 list (OD4 line, can't-guarantee, phone-support, banner, "Demo: recorded, not sent", CON-17/CON-19 decision lines) |
| Graph addenda | `stage7/graph-nodes.md` §6 (line 228), §8 (line 260); `stage7/graph-tools.md` §5 (lines 365–366), C-5 (line 500) | `booking.urgent_note`; quick-checks `offer_text` from this module; inbox bodies, placeholder `digits` |
| Web / staff addenda | `stage7/web.md` §9 (line 366), §14 (lines 561, 612–613); `stage7/staff.md` §5 (line 361) | notices from this module; greeting via `render`; `render(TextId.PERSON_REQUEST_LABEL)`; event `line` sentences from here |
| Decisions | `docs/plans/7b-decisions/data.md` DAT-6 (line 120), DAT-29 (line 143); `residuals-web.md` R-W-6, R-W-7 (lines 60–61); `residuals-graph.md` R-G-7 (line 26); `stage7-signoff.md` D-4…D-15 | SCREEN_SPECS wording wins (DAT-6); the DAT-29 additions; `amount` + `format_usd`. None of D-4…D-15 touches this module |
| UX copy (read only) | `docs/ux/03-structure/SCREEN_SPECS.md` lines 19–31, 76–157, 179; `UI_CONTRACTS.md` lines 67–100, 166; `ui-contracts.openapi.yaml` (examples cited per row in §5) | the word sources, cited per text below |
| KB (issued, read only) | `docs/data/issued/meridian_dataset/knowledge_base/policies/escalation_and_safety.md` | safety words "leave the home immediately and call 911 or their gas utility from outside" ("their" → "your") |
| Requirements | PRD R-1, R-5…R-8, R-13, R-15, R-16, R-21, R-26, R-27, R-34; US-1, US-3, US-25 | as mapped in §3 |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` line 83 (`must_say`) | E-1/E-5/E-6 `must_say` are exact-string checks against these sentences; AEA-06 owns the cases |
| Observability (DO-6) | — | N/A: no entry point, no record, no span (ticket *Observability*) |
| Metrics (DO-7) | `docs/design/key-metrics-registry.md` lines 62, 66 | M-10 compares `promise.text` with the table sentence held here; M-14 needs the KB instruction held here; both stay exact string equality |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §4, `context-maintenance.md`; workspace `code-design-solid-modularity.md` | affected tests only; journey record at level `mock-tested`; context rows updated in the same change; pure module, no seam invented |

---

## 2. Boundary

### Owned files (the only files the implementer may create or edit)

| File | Action | Notes |
|---|---|---|
| `src/meridian/policy/texts.py` | **create** | the module |
| `tests/unit/policy/test_texts.py` | **create** | 13 tests, §7 |
| `tests/unit/policy/texts_source_fixture.json` | **create** | the word-source fixture, §6 |
| `tests/unit/test_import_direction.py` | **create, or append if it already exists** | add **only** `test_texts_imports_stdlib_only` and its private helper `_aea03_imported_modules`. This file is shared with AEA-01, 02, 04, 05 (see §8 R-1); never edit another ticket's function |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-03.md` | **create** | the AC-11 record (`<YYYY-MM-DD>` = the day of the commit, `date +%F`) |
| `.claude/reference/area-map.md` | **modify, two spots only** | line 8 sentence and the A0 row's *Status* cell (step 9) |
| `docs/design/code-design.md` | **modify, one line only** | a "Built:" line under §3's first paragraph (step 9) |
| `.claude/state/icm-progress.md` | **modify, one row only** | row *Routes verified against code and tests* (step 9) |

### Shared surfaces: read only

`docs/ux/03-structure/SCREEN_SPECS.md`, `UI_CONTRACTS.md`, `ui-contracts.openapi.yaml`; the KB file above; every
`docs/design/**` contract; `docs/plans/**` (except this plan); the parked tree.

### Not this ticket's, never touch

`pyproject.toml`, `uv.lock`, every `__init__.py` (package markers are AEA-01's skeleton), `tests/conftest.py` (AEA-01),
`src/meridian/policy/limits.py` (AEA-01), `policy/booking.py` (AEA-13), `policy/handoff.py` (AEA-14), `domain/*`,
`ports/*`, `config.py` (AEA-02), `privacy/redact.py` (AEA-04), `gates/rules.py` (AEA-05), `eval/**` (AEA-06),
`tests/journeys/**` (AEA-01 skeleton, AEA-57), `docs/ux/**`, `apps/web/**`, the OpenAPI and `UI_CONTRACTS.md`, the briefing,
`docs/data/issued/**`, `docs/archive/**`, `docs/parked/**`, `.claude/state/resume.md`, `.claude/state/build-ledger.md`,
`PROJECT-CHECKLIST.md`, `docs/plans/**`.

**No `__init__.py` is needed to build or test this ticket**: with `PYTHONPATH=src`, `meridian` and `meridian.policy`
import as namespace packages until AEA-01's markers land; after they land nothing changes.

---

## 3. Requirements table

### 3a. Acceptance criteria (verbatim from the issue) and how each is met

| AC | Criterion (verbatim) | Implemented by | Verified by |
|---|---|---|---|
| AC-1 [invariant] | Every sentence in `policy/texts.py` equals its entry in a fixture copied from its word source (each entry cites its SCREEN_SPECS line, OpenAPI example or "proposal"), and every fixture entry has a `TextId` — evidence: one-to-one, no unmatched entry either side (UXR-18). | step 3 (texts), step 5 (fixture) | `tests/unit/policy/test_texts.py::test_every_sentence_matches_its_source_fixture`; support: `::test_fixture_quotes_its_source_files` (plan-added) |
| AC-2 [invariant] | Every `TextId` value is `"<group>.<name>"` with a group from data.md §2's ten, and the ids other contracts name exist with their exact spelling (`identity.inbox_code_body`, `identity.inbox_code_gone`, `booking.urgent_note`, the four `live` lines, and `live.person_request_label` rendering "Talk to a person", R-W-6) — evidence: passes; the group → count table printed. | step 2 | `::test_text_id_shape_and_named_ids` (run with `-s`; prints the table) |
| AC-3 [invariant] | The R-26 promise sentences and the `OD4.danger_review` line are present word for word, and no other sentence in the module promises a time — evidence: the promise variants and the fee-bearing can't-guarantee line render exactly; a scan finds no other "within" / "by {time}" sentence. | step 3 (promise, fee_change rows) | `::test_promise_texts_word_for_word` |
| AC-4 [invariant] | The safety lines use the KB's "immediately" and "your", and the conditional and emergency-line cards carry (512) 555-0199 marked as a demo number — evidence: passes. | step 3 (safety rows) | `::test_safety_lines` (reads the KB file) |
| AC-5 [invariant] | TURN_TIMEOUT and BUSY are the UX sentences (C-13, UXR-26) — evidence: both equal the fixture; DO-1's "I'm sorry, …" variant is absent. | step 3 (limits rows) | `::test_timeout_and_busy_sentences` |
| AC-6 [negative] | Forbidden phrases appear in no sentence: "charged" in any form (including "No fee has been charged"), "shortly", "an agent will be with you", a wait time or a queue position, and "sent" for a follow-up — evidence: scan over every text id finds none. | step 3 | `::test_forbidden_phrases_absent` |
| AC-7 [failure/refusal] | `render` with an unknown text id, a missing placeholder or an extra placeholder raises `TextRenderError` — evidence: all three raise; `text_id` and `placeholder` attributes set. | step 4 | `::test_render_refuses_unknown_missing_and_extra` |
| AC-8 [negative] | A `TextRenderError` names the text id and the placeholder name only, never a supplied value: a distinctive reference value and a distinctive six-digit value (assembled at run time) passed in are absent from the error's message and attributes — evidence: neither sentinel found. | step 4 | `::test_render_error_holds_no_values` |
| AC-9 [invariant] | `policy/texts.py` imports nothing beyond the standard library (DO-3 §4.1) — evidence: passes; the scan lists every import it saw. | step 3 (imports) | `tests/unit/test_import_direction.py::test_texts_imports_stdlib_only` |
| AC-10 [invariant] | One money formatter and an `amount` placeholder (data.md §2, R-W-7): `format_usd(8900) == "$89"`, `format_usd(1250) == "$12.50"`, `format_usd(125000) == "$1,250"`, a negative amount raises `ValueError`; `render(<booking fee text>, amount="$89")` gives "Standard diagnostic fee: $89" (OpenAPI `ConfirmationBlock` `fee_line` example), with the dollar figure coming only from `amount` — evidence: passes; the rendered fee line printed. | step 4 | `::test_format_usd_and_fee_line_amount` |
| AC-11 [journey] | Runs no journey yet … record `docs/testing/journeys/YYYY-MM-DD-AEA-03.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1, J-5, J-6, J-9 … | step 8 | the record's Level, Blocked-by and Claim fields |
| AC-12 [regression/context] | Context updated in the same change … area-map A0 row notes `policy/texts.py` planned → actual with the commit; DO-3 §3 status line notes it built; the ICM row *Routes verified against code and tests* names this ticket's tests once they pass; any sentence that could not be placed … is listed in the plan as a report to the UX session, not written or edited. | step 9; the report is §8b of this plan | `git diff` of the three files; §8b |

**Plan-added tests** (each closes a reconciliation gap in 3b; the issue gets a comment proposing them):
`::test_fixture_quotes_its_source_files` (the fixture really is a copy of its sources),
`::test_wp5_carbon_monoxide_lines` (the WP-5 worked pair at module level),
`::test_templates_use_known_placeholders_only` (no placeholder outside data.md §2's seven),
`::test_greeting_says_automated` (R-1 / US-1).

### 3b. Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| `TextId(StrEnum)`, values `"<group>.<name>"`, ten groups | data.md §2 | AC-2 | in-ticket | step 2 |
| `TextRenderError(KeyError)` with `text_id: str`, `placeholder: str \| None`, names only | data.md §2 | AC-7, AC-8 | in-ticket | step 4 |
| `render(text_id: TextId, /, **values: str) -> str`, closed placeholder set | data.md §2 | AC-7 | in-ticket | step 4 |
| `render` never formats numbers: a non-`str` value is refused | data.md §2 ("render itself never formats numbers") | partly (AC-10) | **added**: a non-`str` value raises `TextRenderError` | step 4; asserted in AC-10 test |
| `format_usd` rules incl. `ValueError` on negative | data.md §2, R-W-7 | AC-10 | in-ticket | step 4 |
| No dollar amount typed into any sentence | data.md §2, cases.md §2 | AC-10 (fee line only) | **added**: every `$<digit>` is a placeholder; scan over all texts | step 3 (`fee_change.fee_applies`, `demo.monitor_spend_cap` use `{amount}`); AC-10 test |
| Greeting says automated, not a person | R-1, US-1, web.md §14 | groups list | **added** test | `::test_greeting_says_automated` |
| WP-5 worked pair | ticket *Example pair*; rule build-loop-test-scope | example only | **added** test | `::test_wp5_carbon_monoxide_lines` |
| Placeholders only from the seven | data.md §2 | implied | **added** test + import-time check | step 3, step 4 |
| `PROMISE_TABLE` strings imported from here, incl. `R26.safety_none` = `""` | cases.md §3.2 | promise group | in-ticket; `promise.safety_none` = `""` added so AEA-14 types no literal | step 3 |
| Promise mapping (reason → row), due rule | cases.md §3.2 | out of scope | other-ticket | AEA-14 |
| Building `FeeNote.line` from `SCHEDULE_FEES` | cases.md §2 | out of scope | other-ticket | AEA-13 (fee texts for tune-up / waived / estimate: see §8b U-1) |
| `must_say` items quoting the same words | DAT-6 | Evaluation | other-ticket | AEA-06 |
| Hash of this file into `agent_version` | data.md §7 | handoff | other-ticket | AEA-50 |
| Observability | DO-6 | N/A | n/a: a constants module has no entry point, record or span | — |
| A sentence with no word source | ticket scope boundary | AC-12 | reported, not written | §8b |

### 3c. Scope rule used to decide what is a "fixed sentence" (decided here)

In scope, and written: every sentence the ticket's ten groups name, plus any **full sentence** that a CON-1…CON-6,
CON-17 or CON-19 response field carries, that code (never a model) builds, and that has a word source (SCREEN_SPECS,
an OpenAPI example, or a marked proposal). **Out of scope, reported in §8b:** short labels and option or button labels
("Yes", "Skip and book", "Call 911 (from outside)", "Send a new code", "Nobody online", timeline labels) — except the one
label a contract names (`PERSON_REQUEST_LABEL`) and `booking.urgent_note`, both required by AC-2; example sentences
SCREEN_SPECS gives as model text ("e.g."); and sentences with no word source.

---

## Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — |

---

## 4. Shared code to use

**Nothing from another ticket.** The module imports only these standard-library names (DO-3 §4.1 "depends on: none"):

```text
from __future__ import annotations
import re
import string                       # string.Formatter().parse(...) to read placeholder names
from collections.abc import Mapping
from enum import StrEnum            # Python 3.12 (the parked pyproject pins >=3.12,<3.13)
from types import MappingProxyType
from typing import Final
```

**Public names the module exports, exactly** (`__all__` in this order):
`["PLACEHOLDERS", "TEXTS", "TextId", "TextRenderError", "format_usd", "render"]`.

```text
PLACEHOLDERS: Final[frozenset[str]] = frozenset({"case_ref", "due_label", "window", "digits", "rep_name", "n", "amount"})

class TextId(StrEnum): ...                      # 71 members, §5 step 2 table; value "<group>.<name>"

class TextRenderError(KeyError):
    text_id: str                                # a name only (see step 4 for unknown ids)
    placeholder: str | None                     # a placeholder NAME only; None for an unknown id
    def __init__(self, text_id: str, placeholder: str | None, problem: str) -> None: ...
    def __str__(self) -> str: ...               # returns self.args[0] (KeyError would quote a repr)

TEXTS: Final[Mapping[TextId, str]]              # MappingProxyType over the private dict; read-only

def render(text_id: TextId, /, **values: str) -> str: ...
def format_usd(cents: int) -> str: ...
```

`TEXTS` is an addition data.md §2 does not list: a read-only view the fixture test, AEA-14 (to build
`PROMISE_TABLE` from templates) and AEA-06 can read. It adds no behaviour; `render` stays the way callers get text.

**How consumers will call it (for the record; they build against this after wave 0):**

| Consumer | Call |
|---|---|
| AEA-14 `PROMISE_TABLE` | `"R26.unstaffed" → TEXTS[TextId.PROMISE_UNSTAFFED]` (a template with `{due_label}`, `{case_ref}`), `"R26.refund" → TEXTS[TextId.PROMISE_REFUND]`, `"R26.staffed" → TEXTS[TextId.PROMISE_STAFFED]`, `"R26.safety_none" → TEXTS[TextId.PROMISE_SAFETY_NONE]` (`""`), `"OD4.danger_review" → TEXTS[TextId.PROMISE_DANGER_REVIEW]`; extra lines `PROMISE_REFUND_NO_OUTCOME`, `FEE_CANT_GUARANTEE` (`window`), `FEE_PHONE_SUPPORT_OPEN` |
| AEA-13 `FeeNote.line` | `render(TextId.FEE_STANDARD_DIAGNOSTIC, amount=format_usd(8900))` → "Standard diagnostic fee: $89" |
| AEA-28 / AEA-39 change request | `render(TextId.FEE_APPLIES, amount=format_usd(<late-change fee cents>))` → "The $49 fee applies under current policy." |
| AEA-40 greeting / history | `render(TextId.GREETING)`; `render(TextId.PERSON_REQUEST_LABEL)` |
| AEA-43 inbox | `render(TextId.INBOX_CODE_BODY, digits=<code>)`; `render(TextId.INBOX_CODE_GONE)` |
| AEA-46 events | `render(TextId.REP_JOINED, rep_name="Riley")` etc. |
| AEA-53 monitoring | `render(TextId.MONITOR_SPEND_CAP, amount=format_usd(round(limits.spend.daily_cap_usd * 100)))` |

---

## 5. Steps

Build order; each step is checkable on its own. The module is a pure leaf in DO-3's layering (pure core, no
dependencies); it implements no Protocol and invents no seam.

### Step 1 — worktree and environment

1. Work in `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-03` on branch `aea-03-fixed-customer-texts` (the
   orchestrator creates it from `main`). `export UV_LINK_MODE=hardlink`. Do not run `uv sync`, do not create a `.venv`
   and do not create `pyproject.toml`; every command in §7 uses `uv run --no-project` with Python 3.12, which is
   installed on this VPS.
2. Create the directories `src/meridian/policy/`, `tests/unit/policy/` and `docs/testing/journeys/` if missing, with
   **no** `__init__.py` files.

### Step 2 — `TextId`: the 71 members (exact member names and values)

Define `class TextId(StrEnum)` with exactly these members, in this order (grouped by the ten groups of data.md §2).
Member names are UPPER_SNAKE without a group prefix, matching the contract-fixed names `INBOX_CODE_BODY`,
`INBOX_CODE_GONE`, `PERSON_REQUEST_LABEL`.

| # | Member | Value |
|---|---|---|
| 1 | `GREETING` | `greeting.opening` |
| 2 | `ARE_YOU_A_PERSON` | `greeting.are_you_a_person` |
| 3 | `SAFETY_LEAVE_NOW` | `safety.leave_now` |
| 4 | `SAFETY_DONT_TOUCH` | `safety.dont_touch` |
| 5 | `SAFETY_CONTACT_LINE` | `safety.contact_line` |
| 6 | `BURNING_QUESTION` | `safety.burning_question` |
| 7 | `WARNING_TEXT` | `safety.warning_text` |
| 8 | `EMERGENCY_NUMBER_LINE` | `safety.emergency_number_line` |
| 9 | `EMERGENCY_LINE_LEAD` | `safety.emergency_line_lead` |
| 10 | `URGENCY_HOT_COLD` | `safety.urgency_hot_cold` |
| 11 | `URGENCY_WATER` | `safety.urgency_water` |
| 12 | `URGENCY_AT_RISK` | `safety.urgency_at_risk` |
| 13 | `REGULAR_BOOKING_NOTE` | `safety.regular_booking_note` |
| 14 | `CODE_PROMPT` | `identity.code_prompt` |
| 15 | `VERIFIED` | `identity.verified` |
| 16 | `CODE_WRONG` | `identity.code_wrong` |
| 17 | `CODE_EXPIRED` | `identity.code_expired` |
| 18 | `NOT_VERIFIED` | `identity.not_verified` |
| 19 | `INBOX_CODE_BODY` | `identity.inbox_code_body` |
| 20 | `INBOX_CODE_GONE` | `identity.inbox_code_gone` |
| 21 | `PROMISE_UNSTAFFED` | `promise.unstaffed` |
| 22 | `PROMISE_REFUND` | `promise.refund` |
| 23 | `PROMISE_REFUND_NO_OUTCOME` | `promise.refund_no_outcome` |
| 24 | `PROMISE_STAFFED` | `promise.staffed` |
| 25 | `PROMISE_DANGER_REVIEW` | `promise.danger_review` |
| 26 | `PROMISE_SAFETY_NONE` | `promise.safety_none` |
| 27 | `REFERENCE_LINE` | `promise.reference_line` |
| 28 | `FEE_APPLIES` | `fee_change.fee_applies` |
| 29 | `FEE_ORIGINAL_STAYS` | `fee_change.original_stays` |
| 30 | `FEE_CANT_GUARANTEE` | `fee_change.cant_guarantee` |
| 31 | `FEE_PHONE_SUPPORT_OPEN` | `fee_change.phone_support_open` |
| 32 | `FOLLOWUP_LEGEND` | `followup.legend` |
| 33 | `FOLLOWUP_SAVED_PHONE` | `followup.saved_phone` |
| 34 | `RECORDED_NOT_SENT` | `followup.recorded_not_sent` |
| 35 | `BOOKED` | `booking.booked` |
| 36 | `SLOT_TAKEN` | `booking.slot_taken` |
| 37 | `OUT_OF_AREA` | `booking.out_of_area` |
| 38 | `NO_WINDOW_FITS` | `booking.no_window_fits` |
| 39 | `IDENTITY_NEEDED` | `booking.identity_needed` |
| 40 | `CANCELLED_NO_FEE` | `booking.cancelled_no_fee` |
| 41 | `FEE_STANDARD_DIAGNOSTIC` | `booking.fee_standard_diagnostic` |
| 42 | `SLOTS_NOT_HELD` | `booking.slots_not_held` |
| 43 | `MEMBERS_NOTE` | `booking.members_note` |
| 44 | `FREE_CHANGE_NOTE` | `booking.free_change_note` |
| 45 | `URGENT_NOTE` | `booking.urgent_note` |
| 46 | `QUICK_CHECKS_OFFER` | `booking.quick_checks_offer` |
| 47 | `TURN_TIMEOUT` | `limits.turn_timeout` |
| 48 | `BUSY` | `limits.busy` |
| 49 | `RATE_LIMITED` | `limits.rate_limited` |
| 50 | `BOOKING_CAP` | `limits.booking_cap` |
| 51 | `SPEND_CAP_REACHED` | `limits.spend_cap_reached` |
| 52 | `NO_INFORMATION` | `limits.no_information` |
| 53 | `FAILURE_OFFER` | `limits.failure_offer` |
| 54 | `REP_JOINED` | `live.rep_joined` |
| 55 | `AI_PAUSED` | `live.ai_paused` |
| 56 | `AI_RESUMED` | `live.ai_resumed` |
| 57 | `CHAT_CLOSED` | `live.chat_closed` |
| 58 | `AI_PAUSED_NOTICE` | `live.ai_paused_notice` |
| 59 | `PERSON_REQUEST_LABEL` | `live.person_request_label` |
| 60 | `SHIFT_ENDED` | `demo.shift_ended` |
| 61 | `STAFFING_CHANGED_ON_SHIFT` | `demo.staffing_changed_on_shift` |
| 62 | `STAFFING_BANNER` | `demo.staffing_banner` |
| 63 | `DEMO_RESET` | `demo.reset` |
| 64 | `OVERSIGHT_OVERDUE` | `demo.oversight_overdue` |
| 65 | `OVERSIGHT_SHIFT_ENDED_ONE_WAITING` | `demo.oversight_shift_ended_one_waiting` |
| 66 | `MONITOR_SPEND_CAP` | `demo.monitor_spend_cap` |
| 67 | `MONITOR_LATENCY` | `demo.monitor_latency` |
| 68 | `MONITOR_RESTART` | `demo.monitor_restart` |
| 69 | `MONITOR_ZERO_TRAFFIC` | `demo.monitor_zero_traffic` |
| 70 | `MONITOR_FAILURE_RATE` | `demo.monitor_failure_rate` |
| 71 | `MONITOR_TRACE_EXPORT` | `demo.monitor_trace_export` |

Group counts (the AC-2 table must print exactly this): greeting 2 · safety 11 · identity 7 · promise 7 · fee_change 4 ·
followup 3 · booking 12 · limits 7 · live 6 · demo 12 · **total 71**.

Give the class a one-line docstring per group as a comment block (`# --- safety (R-5…R-8) ---`), nothing more.

### Step 3 — the texts, word for word

Write a private `_TEXTS: Final[dict[TextId, str]]` with one entry per member, then
`TEXTS: Final[Mapping[TextId, str]] = MappingProxyType(_TEXTS)`.

**Copy each template exactly as below.** Apostrophes are the plain ASCII `'` (the sources contain no curly quotes).
Every template is ASCII. Where a line would pass 100 characters, split the Python string with **implicit
concatenation inside parentheses**, breaking only right after a space so the space stays at the end of the first piece
(the fixture test catches any slip). Placeholders are `{name}` with no format spec and no conversion.

`Src` gives the word source the fixture cites (`SS` = `docs/ux/03-structure/SCREEN_SPECS.md`, `OA` =
`docs/ux/03-structure/ui-contracts.openapi.yaml`, `GT` = `docs/design/contracts/stage7/graph-tools.md`), with the line
number checked on 2026-10-21 at `9c3e7e7`. `Ex` = the example values the fixture renders with (only rows with
placeholders).

| Member | Template (exact) | Src | Ex |
|---|---|---|---|
| `GREETING` | `Hi, I'm Meridian Home Comfort's automated assistant, not a person. I can answer questions about our services, book a visit, and look up your account once you've confirmed it's you. If you'd like a person at any point, tap Talk to a person.` | SS:142 | |
| `ARE_YOU_A_PERSON` | `No. I'm Meridian's automated assistant. If you'd like a person, tap Talk to a person.` | SS:143 (**proposal**) | |
| `SAFETY_LEAVE_NOW` | `Leave the home immediately and call 911 or your gas utility from outside.` | SS:144 | |
| `SAFETY_DONT_TOUCH` | `Don't flip switches, open windows near the furnace, or restart equipment.` | SS:144 | |
| `SAFETY_CONTACT_LINE` | `Once you're outside and safe, you can leave a number here if you'd like.` | SS:144 | |
| `BURNING_QUESTION` | `Do you already know whether a breaker has tripped? Please don't go to the panel to check. Do you see any smoke, sparks or flames?` | SS:145 | |
| `WARNING_TEXT` | `A burning smell can be serious. If you smell gas, see smoke, sparks or flames, or a breaker has tripped, leave the home immediately and call 911 from outside.` | SS:146 | |
| `EMERGENCY_NUMBER_LINE` | `Meridian's 24/7 emergency number is (512) 555-0199 (demo number).` | SS:146 | |
| `EMERGENCY_LINE_LEAD` | `Because someone may be in danger, please call Meridian's 24/7 emergency number now: (512) 555-0199 (demo number). I've also logged this for our team as an emergency-priority request.` | SS:147 | |
| `URGENCY_HOT_COLD` | `Is it very hot or very cold in your home right now?` | SS:148 | |
| `URGENCY_WATER` | `Is water still running?` | SS:148 | |
| `URGENCY_AT_RISK` | `Is anyone at higher risk, like an older person, a baby or someone unwell?` | SS:148 | |
| `REGULAR_BOOKING_NOTE` | `This is a regular booking, not emergency service.` | SS:98 | |
| `CODE_PROMPT` | `I've sent a 6-digit code to the phone number on your account, ending in {digits}. Please type it here.` | SS:150 | digits=`02` |
| `VERIFIED` | `Thanks, you're verified for this chat.` | SS:108 | |
| `CODE_WRONG` | `That code doesn't match. {n} tries left.` | SS:104 | n=`2` |
| `CODE_EXPIRED` | `That code has expired. Codes last 10 minutes.` | SS:105 | |
| `NOT_VERIFIED` | `I can't confirm your account here. A representative will help.` | SS:151 | |
| `INBOX_CODE_BODY` | `Your Meridian Home Comfort verification code is {digits}. It expires in 10 minutes.` | SS:179 | **none** (would be a code; AC-8 test renders it with run-time digits) |
| `INBOX_CODE_GONE` | `This code is no longer shown. Ask the chat for a new code if you need one.` | GT:500 (**proposal**) | |
| `PROMISE_UNSTAFFED` | `No representative is online right now. A representative will get back to you within 1 business day, by {due_label}. Your reference is {case_ref}.` | SS:152 | due_label=`Monday, October 19, 7:00 pm`, case_ref=`MHC-C-0007` |
| `PROMISE_REFUND` | `A representative will get to your refund request within 2 business days.` | SS:152 | |
| `PROMISE_REFUND_NO_OUTCOME` | `I can't promise an outcome.` | SS:152 | |
| `PROMISE_STAFFED` | `A representative will join this chat when available. You can keep chatting with me while you wait, if you like.` | SS:152 | |
| `PROMISE_DANGER_REVIEW` | `No representative is online right now, so someone will review this online request within 1 business day. That is not the wait for emergency help; for that, please use the emergency line.` | SS:147 | |
| `PROMISE_SAFETY_NONE` | `` (empty string) | SS:144 ("No follow-up time anywhere on or under the card (R-6, R-26)"; cases.md §3.2 `R26.safety_none`) | |
| `REFERENCE_LINE` | `Your reference is {case_ref}.` | OA:1423 (`HandoffBlock.extra_lines`) | case_ref=`MHC-C-0007` |
| `FEE_APPLIES` | `The {amount} fee applies under current policy.` | SS:153 (also SS:28) | amount=`$49` |
| `FEE_ORIGINAL_STAYS` | `Your original appointment stays until a representative confirms.` | SS:153 | |
| `FEE_CANT_GUARANTEE` | `I can't promise anyone will confirm a change before your appointment starts; until a representative confirms, please plan on the technician arriving {window}.` | SS:153 | window=`12:00 pm – 4:00 pm` (en dash U+2013) |
| `FEE_PHONE_SUPPORT_OPEN` | `Phone support is open until 7:00 pm today if you'd like to call.` | SS:153 | |
| `FOLLOWUP_LEGEND` | `We'll follow up by email unless you'd prefer a phone call.` | SS:154 | |
| `FOLLOWUP_SAVED_PHONE` | `Follow-up saved: phone call, the number ending in {digits}, {window}.` | SS:154 | digits=`02`, window=`mornings` |
| `RECORDED_NOT_SENT` | `Demo: recorded, not sent` | SS:29 (also OA `const` at 10766) | |
| `BOOKED` | `You're booked. Here are the details.` | SS:112 | |
| `SLOT_TAKEN` | `Sorry, that window just went. Here are the next open ones.` | SS:111 | |
| `OUT_OF_AREA` | `Sorry, that address is outside Meridian's service area, so I can't book a visit there.` | SS:100 | |
| `NO_WINDOW_FITS` | `That's the earliest I can book. I can't add you to a waitlist from here.` | SS:101 | |
| `IDENTITY_NEEDED` | `Booking changes your account, so I need to confirm it's you before I write it.` | SS:102 | |
| `CANCELLED_NO_FEE` | `There's no fee.` | SS:114 (also OA:1282 `CancelledBlock.fee_line`) | |
| `FEE_STANDARD_DIAGNOSTIC` | `Standard diagnostic fee: {amount}` (no final period, as the OpenAPI example) | OA:1170 (`ConfirmationBlock.fee_line`) | amount=`$89` |
| `SLOTS_NOT_HELD` | `Windows are shown, not held.` | SS:149 | |
| `MEMBERS_NOTE` | `Members' fees and member-only windows appear after the code.` | SS:149 | |
| `FREE_CHANGE_NOTE` | `You can change this visit free of charge until 24 hours before the window.` | OA:1175 (`ConfirmationBlock.free_change_note`) | |
| `URGENT_NOTE` | `Urgent` | SS:97 (slot card marked "Urgent") | |
| `QUICK_CHECKS_OFFER` | `Before I book, there are a few quick things you can try. They're optional.` | OA:596 (`QuickChecksBlock.offer_text`) | |
| `TURN_TIMEOUT` | `This is taking longer than it should.` | SS:76 (also SS:83) | |
| `BUSY` | `A lot of people are chatting right now, so I can't take this message. A person can pick it up.` | OA:2243 (UXR-26; UI_CONTRACTS line 84) | |
| `RATE_LIMITED` | `I can't take more messages in this chat right now.` | SS:124 | |
| `BOOKING_CAP` | `I can't make more bookings in this chat.` | SS:124 | |
| `SPEND_CAP_REACHED` | `I can't answer more questions right now. A person can pick this up.` | SS:125 | |
| `NO_INFORMATION` | `I don't have that information.` | SS:126 | |
| `FAILURE_OFFER` | `It sounds like I'm not getting this right. Would you like a person?` | SS:127 | |
| `REP_JOINED` | `{rep_name} (demo representative) has joined.` | SS:120 (OA `EvRepresentativeJoined`) | rep_name=`Riley` |
| `AI_PAUSED` | `The assistant is paused while {rep_name} is here.` | SS:120 (OA `EvAiPaused`) | rep_name=`Riley` |
| `AI_RESUMED` | `{rep_name} handed the chat back to the automated assistant.` | SS:121 (OA `EvAiResumed`) | rep_name=`Riley` |
| `CHAT_CLOSED` | `{rep_name} closed this chat.` | SS:122 (OA `EvChatClosed`) | rep_name=`Riley` |
| `AI_PAUSED_NOTICE` | `{rep_name} is in this chat, so the assistant is paused. Your message went to {rep_name}.` | OA:2281 (CON-2 `AI_PAUSED` notice) | rep_name=`Riley` |
| `PERSON_REQUEST_LABEL` | `Talk to a person` | SS:142 (the greeting quotes the button) | |
| `SHIFT_ENDED` | `The simulated shift ended before a representative joined.` | SS:123 | |
| `STAFFING_CHANGED_ON_SHIFT` | `Staffing changed: simulated staff on shift (demo).` | SS:130 | |
| `STAFFING_BANNER` | `Simulated staffing (demo). No Meridian employee is online.` | SS:30 | |
| `DEMO_RESET` | `The demo was reset, so this chat has ended. Nothing from it was kept.` | SS:128 | |
| `OVERSIGHT_OVERDUE` | `{case_ref} is past its due time. Assign it or pick it up.` | OA:6496 (CON-17 alert line) | case_ref=`MHC-C-0006` |
| `OVERSIGHT_SHIFT_ENDED_ONE_WAITING` | `Simulated shift ended with 1 customer waiting. Their case now has the 1-business-day promise.` | OA:6600 (CON-17; one waiting customer only, see §8b U-8) | |
| `MONITOR_SPEND_CAP` | `Spend reached the {amount} daily cap: new chats hand off and no model calls run until tomorrow.` | OA:7025 (CON-19 `decision_line`) | amount=`$30` |
| `MONITOR_LATENCY` | `p95 latency is over 12.5 s per turn: check the model route.` | OA:7029 | |
| `MONITOR_RESTART` | `The health check restarted the service: check the logs.` | OA:7033 | |
| `MONITOR_ZERO_TRAFFIC` | `No new live chat for 4 hours: check the public URL and the health check.` | OA:7037 | |
| `MONITOR_FAILURE_RATE` | `More than 2% of turns failed: check the model route and the logs.` | OA:7041 | |
| `MONITOR_TRACE_EXPORT` | `Trace export is failing and traces are being dropped: check the Langfuse server on the VPS.` | OA:7045 | |

Decisions made here (do not revisit):
- `FEE_APPLIES` and `MONITOR_SPEND_CAP` take the dollar figure through `{amount}` (R-W-7's rule "no amount is typed into
  a sentence"; the $49 is a `SCHEDULE_FEES` row and the $30 is `Limits.spend.daily_cap_usd`, MC-22 "one literal"). The
  rendered text equals the source sentence exactly.
- `CODE_EXPIRED` follows SCREEN_SPECS line 105 and UI_CONTRACTS' named-error table, not the OpenAPI example's longer
  "… I can send a new code." (wrong at the resend cap; reported, §8b U-4).
- `AI_PAUSED_NOTICE` follows the OpenAPI notice text (it is the response field); UI_CONTRACTS quotes only its first
  sentence (reported, U-5).
- `URGENT_NOTE` is `Urgent`, the only wording any source gives for the urgent mark (SCREEN_SPECS line 97).
- `FOLLOWUP_SAVED_PHONE` uses `window` for the callback window ("mornings"); the KB calls it "the customer's preferred
  callback window".
- `PROMISE_SAFETY_NONE` is `""` so AEA-14 imports every `PROMISE_TABLE` value from here and types none.
- The demo emergency number "(512) 555-0199" appears in texts and tests because SCREEN_SPECS line 5 defines it as the
  fictional demo number the copy must show; it is not a person's phone number.

**Import-time check (fail loud):** after `_TEXTS` is built, the module computes
`_FIELDS: Final[Mapping[TextId, frozenset[str]]]` by parsing each template with `string.Formatter().parse`, and raises
`RuntimeError("policy/texts.py: …")` at import if (a) any `TextId` member has no entry or an entry has no member,
(b) a field name is not in `PLACEHOLDERS`, or (c) a field has a format spec, a conversion, or an empty/positional name.
The message names the text id and the field name only. This protects the invariant "every render either returns a
complete sentence or raises a named error".

### Step 4 — `TextRenderError`, `render`, `format_usd`

**`TextRenderError(KeyError)`**
1. `__init__(self, text_id: str, placeholder: str | None, problem: str)`: set `self.text_id = text_id`,
   `self.placeholder = placeholder`, then `super().__init__(f"{problem}: text_id={text_id!r}, placeholder={placeholder!r}")`.
   `problem` is always one of four fixed phrases: `"unknown text id"`, `"missing placeholder"`, `"unexpected placeholder"`,
   `"placeholder value must be a str"`. *Invariant: the message and attributes are built only from names, never from a
   value a caller passed.*
2. `__str__` returns `str(self.args[0])` (KeyError's default would wrap it in quotes).

**`render(text_id: TextId, /, **values: str) -> str`**, in this order (first failure wins):
1. If `text_id` is not an instance of `TextId`: raise `TextRenderError(name, None, "unknown text id")` where
   `name = text_id` if `isinstance(text_id, str)` and it matches `^[a-z_]+\.[a-z0-9_]+$`, else `"<not a text id>"`.
   *Invariant: an id shaped like a value (digits, spaces, a reference) never reaches the message.* A plain `str`
   equal to a valid value (e.g. `"greeting.opening"`) is refused too: callers use the enum.
2. `required = _FIELDS[text_id]`; `supplied = set(values)`.
3. Missing: if `required - supplied` is non-empty → raise with `placeholder = sorted(required - supplied)[0]`,
   `"missing placeholder"`.
4. Extra: if `supplied - required` is non-empty → raise with `placeholder = sorted(supplied - required)[0]`,
   `"unexpected placeholder"`. (A name outside `PLACEHOLDERS` is also "unexpected".)
5. Type: for each name in `sorted(required)`, if `not isinstance(values[name], str)` → raise with that name,
   `"placeholder value must be a str"`. *Invariant: `render` never formats a number; money comes only from
   `format_usd`.*
6. Return `_TEXTS[text_id].format(**values)`. (Values containing `{` are safe: `format` parses only the template.)
   Raise from steps 1–5 with `from None` so no chained exception carries a value.

**`format_usd(cents: int) -> str`**
1. If `isinstance(cents, bool)` or not `isinstance(cents, int)`: `raise TypeError("format_usd: cents must be an int")`.
2. If `cents < 0`: `raise ValueError("format_usd: amount must not be negative")` (no value in the message).
3. `dollars, rem = divmod(cents, 100)`; return `f"${dollars:,}"` when `rem == 0`, else `f"${dollars:,}.{rem:02d}"`.
   Expected: 8900 → `$89`, 12900 → `$129`, 1250 → `$12.50`, 125000 → `$1,250`, 123456 → `$1,234.56`, 5 → `$0.05`,
   0 → `$0`.

Module docstring (3–5 lines): what it holds, that UX owns the words (UXR-18, DAT-6), that a missing sentence is a
follow-up ticket (frozen after wave 0), and that it imports only the standard library.

### Step 5 — the fixture `tests/unit/policy/texts_source_fixture.json`

UTF-8 JSON, `ensure_ascii` false (the en dash stays a real `–`), 2-space indent. Shape:

```json
{
  "schema": "aea-03 texts source fixture v1",
  "copied_at": "9c3e7e7",
  "entries": [
    {
      "id": "greeting.opening",
      "template": "Hi, I'm Meridian Home Comfort's automated assistant, …",
      "source": {"kind": "screen_specs", "file": "docs/ux/03-structure/SCREEN_SPECS.md", "line": 142,
                 "where": "SCR-1 copy notes, Greeting (R-1)"},
      "example": null
    },
    {
      "id": "identity.code_wrong",
      "template": "That code doesn't match. {n} tries left.",
      "source": {"kind": "screen_specs", "file": "docs/ux/03-structure/SCREEN_SPECS.md", "line": 104,
                 "where": "SCR-1 flow states, Code wrong (R-15)"},
      "example": {"values": {"n": "2"}, "rendered": "That code doesn't match. 2 tries left."}
    }
  ]
}
```

Rules: one entry per row of the step 3 table, same order; `template` is the step 3 template (copy it from the
**source document**, not from `texts.py`, so the comparison means something); `source.kind` is `"screen_specs"`,
`"openapi"` or `"proposal"`; `source.file` is the repo-relative path (`SS`/`OA`/`GT` above; for proposals the file the
proposal is written in: SS for `ARE_YOU_A_PERSON`, GT for `INBOX_CODE_GONE`); `source.line` is the step 3 line;
`example` is present exactly for the rows with an `Ex` value (`values` as given, `rendered` = the exact sentence as the
source prints it) and `null` otherwise. `INBOX_CODE_BODY` has `example: null`.

### Step 6 — `tests/unit/policy/test_texts.py`

Imports: `json`, `re`, `string`, `pathlib.Path`, `typing.Any`, `typing.cast`, `pytest`, and
`from meridian.policy.texts import PLACEHOLDERS, TEXTS, TextId, TextRenderError, format_usd, render`.
`REPO = Path(__file__).resolve().parents[3]`; `FIXTURE = json.loads(Path(__file__).with_name("texts_source_fixture.json").read_text("utf-8"))`.
No markers, no network, no model, no DB.

Every call that deliberately passes a non-`str` value goes through a variable typed `dict[str, Any]` (e.g.
`bad: dict[str, Any] = {"n": 2}` then `render(TextId.CODE_WRONG, **bad)`), so `mypy --strict` passes on the test file.

Tests, each named exactly:

1. **`test_every_sentence_matches_its_source_fixture`** (AC-1): `{e["id"] for e in entries} == {t.value for t in TextId}`
   and the list has no duplicate id; for every entry `TEXTS[TextId(e["id"])] == e["template"]`; every
   `e["source"]["kind"]` in `{"screen_specs", "openapi", "proposal"}` and `file`, `line`, `where` present; for every
   entry with an `example`, `render(TextId(e["id"]), **e["example"]["values"]) == e["example"]["rendered"]`. On failure
   the assertion names the id. Print `f"{len(entries)} fixture entries, {len(TextId)} text ids, unmatched: 0"`.
2. **`test_fixture_quotes_its_source_files`** (plan-added): for each entry, read `REPO / e["source"]["file"]` once
   (cache in a dict), collapse whitespace (`re.sub(r"\s+", " ", text)`); split the template into its literal chunks with
   `string.Formatter().parse` and assert each non-empty chunk is a substring of that text; if `example` is not null,
   also assert `example["rendered"]` is a substring. Skip the empty `promise.safety_none` template's chunk check (it has
   none). This proves each fixture entry was copied from its cited document.
3. **`test_text_id_shape_and_named_ids`** (AC-2): every value matches
   `^(greeting|safety|identity|promise|fee_change|followup|booking|limits|live|demo)\.[a-z][a-z0-9_]*$`; each of the ten
   groups has ≥ 1 id; `TextId.INBOX_CODE_BODY.value == "identity.inbox_code_body"`,
   `TextId.INBOX_CODE_GONE.value == "identity.inbox_code_gone"`, `TextId("booking.urgent_note") is TextId.URGENT_NOTE`,
   `TextId.PERSON_REQUEST_LABEL.value == "live.person_request_label"` and `render(TextId.PERSON_REQUEST_LABEL) == "Talk to a person"`;
   with `rep_name="Riley"`: `REP_JOINED` → "Riley (demo representative) has joined.", `AI_PAUSED` → "The assistant is
   paused while Riley is here.", `AI_RESUMED` → "Riley handed the chat back to the automated assistant.",
   `CHAT_CLOSED` → "Riley closed this chat.". Print the group → count table (expected values in step 2) and assert it.
4. **`test_promise_texts_word_for_word`** (AC-3): assert exact strings (typed in the test, independent of the fixture):
   `render(PROMISE_UNSTAFFED, due_label="Monday, October 19, 7:00 pm", case_ref="MHC-C-0007")` == SS:152's sentence;
   `PROMISE_REFUND`, `PROMISE_REFUND_NO_OUTCOME`, `PROMISE_STAFFED`, `PROMISE_DANGER_REVIEW` equal their step 3 texts;
   `TEXTS[PROMISE_SAFETY_NONE] == ""`; `render(FEE_CANT_GUARANTEE, window="12:00 pm – 4:00 pm")` equals SS:153's
   sentence. Then the scan: `TIME_PROMISE = re.compile(r"\bwithin\b|\bby \{|\bby \d|\bby (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I)`;
   for every id **not** in `{PROMISE_UNSTAFFED, PROMISE_REFUND, PROMISE_STAFFED, PROMISE_DANGER_REVIEW, PROMISE_SAFETY_NONE}`,
   `TIME_PROMISE.search(TEXTS[id])` is None; also assert it *does* match `PROMISE_UNSTAFFED`, `PROMISE_REFUND` and
   `PROMISE_DANGER_REVIEW` (the scan is live).
5. **`test_safety_lines`** (AC-4): read the KB file
   `REPO / "docs/data/issued/meridian_dataset/knowledge_base/policies/escalation_and_safety.md"`; `kb_phrase =
   "leave the home immediately and call 911 or their gas utility from outside"` is in it; `your_phrase = kb_phrase.replace("their", "your")` and
   `TEXTS[SAFETY_LEAVE_NOW] == your_phrase[0].upper() + your_phrase[1:] + "."`; the KB contains `"flip switches, open windows near the
   furnace, or restart equipment"` and `TEXTS[SAFETY_DONT_TOUCH]` contains it too; `"immediately"` is in
   `SAFETY_LEAVE_NOW` and `WARNING_TEXT`; no `safety` group text contains the word `their` (`\btheir\b`);
   `"(512) 555-0199 (demo number)"` is in `EMERGENCY_NUMBER_LINE` and in `EMERGENCY_LINE_LEAD`.
6. **`test_wp5_carbon_monoxide_lines`** (plan-added; the WP-5 worked pair): the three lines a CO alarm reply starts with,
   `[render(SAFETY_LEAVE_NOW), render(SAFETY_DONT_TOUCH), render(SAFETY_CONTACT_LINE)]`, equal
   `["Leave the home immediately and call 911 or your gas utility from outside.", "Don't flip switches, open windows near the furnace, or restart equipment.", "Once you're outside and safe, you can leave a number here if you'd like."]`;
   none of them matches `r"\bwithin\b|business day|\d{1,2}:\d{2}|\bby \w+day\b"` (no follow-up time, R-6, R-26);
   `render(PROMISE_SAFETY_NONE) == ""`.
7. **`test_timeout_and_busy_sentences`** (AC-5): `render(TURN_TIMEOUT) == "This is taking longer than it should."`;
   `render(BUSY) == "A lot of people are chatting right now, so I can't take this message. A person can pick it up."`;
   both equal their fixture templates; no text contains `"I'm sorry"`.
8. **`test_forbidden_phrases_absent`** (AC-6): scan every template **and** every fixture `example.rendered`,
   case-insensitive, with: `charged` → `r"\bcharged\b"`; `shortly` → `r"\bshortly\b"`; agent →
   `r"\ban agent will be with you\b"`; wait time → `r"\bwait(ing)? time\b|\b\d+\s*(minute|min|hour)s?\s+(wait|away)\b"`;
   queue position → `r"\bqueue position\b|\bposition in (the )?(queue|line)\b|\b(you are|you're) (next|number \d+|#\s*\d+)\b|\bin line\b"`.
   For `followup` group ids only, `r"(?<!not )\bsent\b"` must not match (so "Demo: recorded, not sent" passes). Collect
   all hits and assert the list is empty (so one run shows every offender). Note in a comment: "charged in any form"
   is read as any sentence using "charged" (SCREEN_SPECS line 28's example is a negation); "free of charge" is not a
   charge claim (reported to UX, §8b U-10).
9. **`test_render_refuses_unknown_missing_and_extra`** (AC-7): (a) `render(cast(TextId, "greeting.not_a_text"))` raises
   `TextRenderError` with `text_id == "greeting.not_a_text"`, `placeholder is None`; (b) `render(TextId.CODE_WRONG)` →
   `text_id == "identity.code_wrong"`, `placeholder == "n"`; (c) `render(TextId.VERIFIED, n="2")` →
   `text_id == "identity.verified"`, `placeholder == "n"`; (d) `render(cast(TextId, "greeting.opening"))` (a plain str)
   raises with `text_id == "greeting.opening"`; (e) with `bad: dict[str, Any] = {"n": 2}`, `render(TextId.CODE_WRONG, **bad)`
   raises with `placeholder == "n"`. Each error `isinstance(err, KeyError)`.
10. **`test_render_error_holds_no_values`** (AC-8): build sentinels at run time:
    `ref = "MHC-C-" + "".join(str(d) for d in (9, 4, 7, 1))` and `six = "".join(str(d) for d in (7, 0, 3, 9, 1, 5))`.
    Trigger: missing (`render(PROMISE_UNSTAFFED, case_ref=ref)`), extra (`render(VERIFIED, digits=six, case_ref=ref)`),
    extra on the code body (`render(INBOX_CODE_BODY, digits=six, n=ref)`), non-str (`render(CODE_WRONG, **{"n": int(six)})`),
    and unknown id built from a value (`render(cast(TextId, six))` → `text_id == "<not a text id>"`). For each error,
    neither sentinel (nor `str(int(six))`) appears in `str(err)`, `repr(err)`, `err.args`, `err.text_id`,
    `err.placeholder`, or `err.__cause__`/`err.__context__` (both None). Separately, `render(INBOX_CODE_BODY, digits=six)`
    equals `f"Your Meridian Home Comfort verification code is {six}. It expires in 10 minutes."` (proves the body works
    without a code in the fixture).
11. **`test_format_usd_and_fee_line_amount`** (AC-10): `format_usd(8900) == "$89"`, `(12900) == "$129"`,
    `(1250) == "$12.50"`, `(125000) == "$1,250"`, `(123456) == "$1,234.56"`, `(5) == "$0.05"`, `(0) == "$0"`;
    `pytest.raises(ValueError)` for `-1`; `pytest.raises(TypeError)` for `True` and for `cast(int, 89.0)`;
    `line = render(TextId.FEE_STANDARD_DIAGNOSTIC, amount=format_usd(8900))`, `print(line)`, `line == "Standard diagnostic fee: $89"`;
    `render(FEE_STANDARD_DIAGNOSTIC, amount="$129").endswith("$129")`; `"$" not in TEXTS[FEE_STANDARD_DIAGNOSTIC]`;
    no template anywhere matches `r"\$\d"` (no typed amount); `render(FEE_STANDARD_DIAGNOSTIC, **{"amount": 8900})`
    raises `TextRenderError` (render never formats numbers); `render(FEE_APPLIES, amount=format_usd(4900)) == "The $49 fee applies under current policy."`.
12. **`test_templates_use_known_placeholders_only`** (plan-added): `PLACEHOLDERS == {"case_ref", "due_label", "window", "digits", "rep_name", "n", "amount"}`;
    for every template, every parsed field name is in `PLACEHOLDERS`, with empty format spec and no conversion.
13. **`test_greeting_says_automated`** (plan-added; R-1, US-1): `"automated assistant"` and `"not a person"` are in
    `render(GREETING)`; `"Talk to a person"` is in `GREETING` and `ARE_YOU_A_PERSON`.

### Step 7 — `tests/unit/test_import_direction.py::test_texts_imports_stdlib_only` (AC-9)

If the file does not exist, create it with a module docstring `"""Static import-direction checks (one function per
owning ticket; AEA-01, 02, 03, 04, 05)."""`, `from __future__ import annotations`, `import ast`, `import sys`,
`from pathlib import Path`. If it exists (another wave-0 ticket landed first), **append** only the block below and add
any of those three imports that are missing at the top; change nothing else.

Block (self-contained so a merge with the other tickets' blocks is a plain union):
1. `def _aea03_imported_modules(path: Path) -> list[str]:` parse with `ast.parse(path.read_text("utf-8"))`; walk all
   nodes; for `ast.Import` add each `alias.name`; for `ast.ImportFrom` add `"." * node.level + (node.module or "")`;
   return the sorted unique list.
2. `def test_texts_imports_stdlib_only() -> None:` `path = Path(__file__).resolve().parents[2] / "src/meridian/policy/texts.py"`;
   `seen = _aea03_imported_modules(path)`; `print("policy/texts.py imports:", seen)`; assert no entry starts with `"."`
   (no relative import); assert every `name.split(".")[0] in sys.stdlib_module_names` (this includes `__future__`);
   the assertion message lists the offenders.

### Step 8 — the journey record `docs/testing/journeys/<YYYY-MM-DD>-AEA-03.md` (AC-11)

A short Markdown file: title `# Journey record — AEA-03 (policy/texts.py)`, then the `integrated-journeys.md` §4 field
table with these values:

| Field | Value |
|---|---|
| Claim | AEA-03: every fixed customer sentence in `src/meridian/policy/texts.py` equals its word-source fixture; `render` refuses unknown ids and wrong placeholders without leaking values; `format_usd` formats customer money. No journey runs: wave 0 precedes AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1). Journeys that will exercise this code: **J-1** (the greeting), **J-5** (the safety instruction), **J-6** (the promise text), **J-9** (the notice texts) |
| Level | `mock-tested` |
| Tested revision | the code commit's SHA (step 10) |
| Environment | VPS worktree `inno-aea-callcenter-wt/AEA-03`; Python 3.12 via `uv run --no-project`; no server, no DB, no model |
| Command | the two pytest commands of §7 |
| Result | pass/fail counts from the final run |
| Evidence location | the implementer's report on issue #3 (pytest output, group table, import list) |
| Remaining limitations | No integrated path ran; consumers (AEA-14, 21, 40, 43, 46 …) are not built; sentences reported to the UX session (plan §8b) are not in the module |
| Blocked by | AEA-57 (journey harness); the turn steps of J-5, J-6, J-9 also wait on AEA-51, J-6's staff side on AEA-52 |

### Step 9 — context rows (AC-12), after the tests pass

Use the code commit's short SHA (step 10) as `<sha>`.
1. `.claude/reference/area-map.md`:
   - line 8: if it still reads `**Every code path below is planned.**`, change that sentence to
     `**Every code path below is planned unless its row marks it actual.**` (leave the rest of the paragraph). If another
     ticket already changed it, leave it.
   - A0 row (the row starting `| 0 | **A0 Foundation** |`), last cell `planned`: replace with
     ``planned; `policy/texts.py` actual (AEA-03, `<sha>`)``. If the cell already carries another ticket's "actual" note,
     append ``; `policy/texts.py` actual (AEA-03, `<sha>`)`` instead. Change no other cell.
2. `docs/design/code-design.md` §3: directly under the line `Owner area and wave in the right-hand columns (§8). Sizes
   follow `code-structure.md`.` add a blank line and ``**Built:** `policy/texts.py` (AEA-03, `<sha>`).`` If a
   `**Built:**` line already exists there, append ``; `policy/texts.py` (AEA-03, `<sha>`)`` before its final period.
   Touch nothing else in DO-3.
3. `.claude/state/icm-progress.md`, row `| Routes verified against code and tests | pending | — | First implemented slice with tests (§8) |`:
   replace with
   ``| Routes verified against code and tests | provisional | 2026-10-21: area map A0 → `policy/texts.py` checked against `tests/unit/policy/test_texts.py` (AEA-03, `<sha>`; 13 pass) | Each slice adds its route; verified when every area-map row is actual |``
   If the row was already changed by another ticket, append ``; `policy/texts.py` ↔ `tests/unit/policy/test_texts.py` (AEA-03, `<sha>`)``
   to its evidence cell, keeping the row under 400 characters. Use the real pass count.
4. Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` from the worktree root; fix any FAIL that your
   three edits caused (and only those).

### Step 10 — commits (factory mode; never push, never force)

1. Commit 1 (code): `git add src/meridian/policy/texts.py tests/unit/policy/test_texts.py tests/unit/policy/texts_source_fixture.json tests/unit/test_import_direction.py`
   then commit `feat(policy): every fixed customer sentence in policy/texts.py (AEA-03)` with a body listing the 71
   ids by group count, `render`/`format_usd`, and `Closes #3` **not** written (the orchestrator closes the issue after
   merge). Last line: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
2. Commit 2 (record and context): `git add docs/testing/journeys/<YYYY-MM-DD>-AEA-03.md .claude/reference/area-map.md docs/design/code-design.md .claude/state/icm-progress.md`
   then commit `docs(context): AEA-03 texts built; journey record mock-tested` with the same last line. Never
   `git add -A` or `git add .`.
3. Before each commit run `git diff --cached --name-only` and confirm only owned files are staged.

### File map

| File | Current | Change |
|---|---|---|
| `src/meridian/policy/texts.py` | absent | create (steps 2–4) |
| `tests/unit/policy/texts_source_fixture.json` | absent | create (step 5) |
| `tests/unit/policy/test_texts.py` | absent | create (step 6) |
| `tests/unit/test_import_direction.py` | absent on `9c3e7e7` (shared) | create or append one block (step 7) |
| `docs/testing/journeys/<date>-AEA-03.md` | absent | create (step 8) |
| `.claude/reference/area-map.md` | exists | two spots (step 9.1) |
| `docs/design/code-design.md` | exists | one line (step 9.2) |
| `.claude/state/icm-progress.md` | exists | one row (step 9.3) |

### What the implementer must NOT do

- Reword, shorten, "fix" or add any sentence. A sentence that looks wrong (U-items in §8b) stays as listed or stays out.
- Add a placeholder outside the seven, a parameter to `render`, a public function, or any import outside the standard
  library. Add no `__init__.py`, `conftest.py`, `pyproject.toml` or lock file.
- Put a verification code, a card-like number or a customer phone number in the fixture or tests (the six digits in
  AC-8 are assembled at run time; the only phone number is the spec'd demo emergency number).
- Edit `docs/ux/**`, the OpenAPI, `UI_CONTRACTS.md`, the KB, `apps/web/**`, any other ticket's file, or another
  ticket's function in `tests/unit/test_import_direction.py`.
- Run the full suite, start a server, bind ports 4019 or 5184, call a model, or push.

---

## 6. Data and fixtures

All synthetic or quoted from the signed UX copy and the issued KB (read only):
- `tests/unit/policy/texts_source_fixture.json` (step 5): 71 entries copied from SCREEN_SPECS / OpenAPI examples /
  proposals at `9c3e7e7`. Example values come from those same sources: case refs `MHC-C-0007` / `MHC-C-0006` (seeded
  synthetic case refs), "Riley" (the demo representative), "02" (masked last two digits), "$89" / "$49" / "$30"
  (fee schedule and the daily cap), "Monday, October 19, 7:00 pm", "12:00 pm – 4:00 pm", "mornings".
- AC-8 sentinels are built at run time from digit tuples; nothing six-digit is stored in a file.
- The KB file is read in `test_safety_lines`; nothing is written to `docs/`.

---

## 7. Checks

Run everything from the worktree root with `export UV_LINK_MODE=hardlink`. These commands work whether or not AEA-01's
`pyproject.toml` has landed (ruff and mypy pick up its config when present; `-o addopts=""` neutralises any pytest
addopts so no plugin is needed).

**While iterating (affected tests = the two new test targets; nothing else imports `policy/texts.py` yet):**

```bash
PYTHONPATH=src uv run --no-project --python 3.12 --with pytest \
  python -m pytest -o addopts="" -p no:cacheprovider -q -s \
  tests/unit/policy/test_texts.py \
  "tests/unit/test_import_direction.py::test_texts_imports_stdlib_only"
```

Passing looks like: `14 passed`, the AC-2 group table (greeting 2 … demo 12, total 71), the import list
(`['__future__', 'collections.abc', 'enum', 're', 'string', 'types', 'typing']`), and the printed fee line
`Standard diagnostic fee: $89`. If another ticket's function in `test_import_direction.py` exists, do not run it (its
module may not exist on this branch).

**Once before the final commit, cheapest first, stop at the first red:**

```bash
F="src/meridian/policy/texts.py tests/unit/policy/test_texts.py tests/unit/test_import_direction.py"
uv run --no-project --python 3.12 --with ruff ruff format --check $F
uv run --no-project --python 3.12 --with ruff ruff check $F
MYPYPATH=src uv run --no-project --python 3.12 --with mypy --with pytest \
  mypy --strict --explicit-package-bases $F
# then the pytest command above
```

- Type checker: if AEA-01's `pyproject.toml` is present and configures **pyright** instead of mypy, run
  `uv run --no-project --python 3.12 --with pyright --with pytest pyright $F` instead; otherwise mypy `--strict` as
  above. If mypy reports "Source file found twice", run it once on `src/meridian/policy/texts.py` alone and once on the
  two test files.
- Ruff: if `ruff format` would change files, run `ruff format $F` and re-check; if `ruff check` flags E501 on a text,
  split the string per step 3, never `# noqa` a sentence.
- **Affected journeys:** none exist (AEA-57 has not landed); AC-11's record states it. `uv run pytest -m journey` is not
  run by this ticket.
- **Full suite:** not run (this change reaches no shared fixture, setting, dependency or cross-codebase import yet;
  rule `build-loop-test-scope`).
- **Context check:** `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` shows no FAIL caused by step 9.

**Report back (on issue #3 through the orchestrator):** each AC with its command and result; the group table; the
import list; the fee line; `git diff --stat main...HEAD`; and §8b's list as "reported, not written".

### Checks and evidence (template form)

| Check | Command | Evidence |
|---|---|---|
| Capture verification | n/a: no workflow, entry point or record (DO-6 N/A) | — |
| Evaluation check | n/a here: E-1/E-5/E-6 `must_say` use these words; AEA-06/AEA-24 run them | — |
| Unit + fixture | pytest command above | `14 passed`, printed tables |
| Lint / format / types | the three gate commands | three clean outputs |
| Journey record | `docs/testing/journeys/<date>-AEA-03.md` | Level `mock-tested`, Blocked by AEA-57 |

---

## 8. Risks and requests

### 8a. Risks and collisions (for the orchestrator)

- **R-1 `tests/unit/test_import_direction.py` is named by five wave-0 tickets** (AEA-01 AC-5/AC-7, AEA-02 AC-18,
  AEA-03 AC-9, AEA-04 AC-10, AEA-05 AC-11), all built in parallel. Each branch will create the file, so the second merge
  hits an add/add conflict. This plan keeps AEA-03's part self-contained (one test, one `_aea03_` helper, stdlib
  imports only), so the merge resolution is a plain union of blocks plus de-duplicated imports. **Request:** the merge
  step resolves this file by union (or the other planners adopt the same "one prefixed block per ticket" shape).
- **R-2 Context files shared by every wave-0 ticket**: the area-map A0 row and line 8, DO-3 §3's "Built:" line and the
  ICM row are edited by AEA-01, 02, 03, 04 (and AEA-08 reconciles the area map in wave 0). Step 9 tells the implementer
  to append, not overwrite, but concurrent branches will still conflict textually; resolve by keeping every ticket's
  note.
- **R-3 The fixture-to-source test reads `docs/ux/**` and the OpenAPI.** If the UX session edits a sentence (or the
  pending D-5 `last_event_id` OpenAPI edit moves lines), `test_fixture_quotes_its_source_files` checks substrings, not
  line numbers, so line shifts do not break it; a **wording** change will turn it red on purpose: that is the signal that
  a texts follow-up ticket is due (UX owns copy). It runs only when this module's tests run (affected tests) and in the
  pre-deploy full suite.
- **R-4 HandoffBlock wording seam (AEA-21 / AEA-29, not this ticket):** the OpenAPI HANDOFF and CHANGE_REQUEST examples
  carry `promise_text` as the R-26 sentence cut before ", by …" ("No representative is online right now. A
  representative will get back to you within 1 business day"), `due_label` as "by Monday, October 19, 7:00 pm" and
  the reference in `extra_lines` ("Your reference is MHC-C-0007."), which the screen joins (UI_CONTRACTS line 166,
  UXR-19). This module holds the full SCREEN_SPECS sentence (`PROMISE_UNSTAFFED`, for `promise.text` and M-10) and
  `REFERENCE_LINE`; it does **not** hold the cut head. Whoever builds `HandoffBlock` (AEA-21 compose with AEA-29's
  `HandoffResult`) must decide how the block's three fields are produced; if they need the head as its own text, that is
  a small follow-up on this file merged before them.
- **R-5 Literal thresholds in CON-19 lines:** `MONITOR_LATENCY` ("12.5 s"), `MONITOR_FAILURE_RATE` ("2%") and
  `MONITOR_ZERO_TRAFFIC` ("4 hours") keep the OpenAPI's typed numbers (no placeholder fits them); if AEA-32/AEA-53's
  alert settings change a threshold, the sentence needs a follow-up. The spend line takes `{amount}`.
- **R-6 Redaction of the demo emergency number:** AEA-04's SONNET/TRACE/JEV profiles replace phone numbers, so
  "(512) 555-0199" in assistant text sent to a model or trace becomes "[phone ending 99]" / "[phone]". Customer-facing
  text is unaffected (STORE leaves phones). Note for AEA-04/AEA-19/AEA-51 reviewers, not a defect here.
- **R-7 Sibling sentinel:** AEA-21 AC-7 uses `"512-555-0199"` (dashes) as a form-phone sentinel that must not appear in
  checkpoints; this module's demo number is `"(512) 555-0199"` (parentheses, space), so a substring search for the
  dashed form never matches a fixed text. Keep the formats distinct.
- **R-8 `FEE_APPLIES` now needs `amount`:** AEA-28/AEA-39 must call `render(TextId.FEE_APPLIES, amount=format_usd(4900))`
  (from the fee schedule's late-change row); a bare `render(TextId.FEE_APPLIES)` raises `TextRenderError`. Stated in §4.

**Shared primitive requests:** none. **Spec gaps:** §8b. **Contract problems:** none requiring a signed-contract change.

### 8b. Report to the UX session: sentences not placed (AC-12; reported, not written, not edited)

Each item names who needs it. A follow-up on `policy/texts.py` lands only after the UX session words it.

| # | Sentence or gap | Why not written | Needed by |
|---|---|---|---|
| U-1 | Fee lines for **tune-up** ($129 non-member / "Included" for members), the **waived** diagnostic line for members (cases.md §2: "a waived row renders the waived text with the scheduled amount"), and the **free estimate** line | No wording in SCREEN_SPECS or OpenAPI; only "Standard diagnostic fee: $89" exists | **AEA-13** AC-13 (wave 1) — the most urgent follow-up |
| U-2 | "Your visit on [date] is cancelled." (SCREEN_SPECS line 114, before "There's no fee.") | Needs a date placeholder; data.md §2's seven have none (`CANCELLED_NO_FEE` = "There's no fee." is written) | AEA-21 / AEA-28 |
| U-3 | The card-not-taken reply (R-13: "never asks for or accepts card numbers") | No word source anywhere | AEA-21 / AEA-38 |
| U-4 | CODE_EXPIRED: OpenAPI example (line 1745) adds "I can send a new code." to SCREEN_SPECS' "That code has expired. Codes last 10 minutes." | Sources disagree; SCREEN_SPECS + UI_CONTRACTS followed (the extra sentence is false at the resend cap) | UX to align the OpenAPI example |
| U-5 | AI_PAUSED: UI_CONTRACTS line 85 quotes "Riley is in this chat, so the assistant is paused."; the OpenAPI notice text (line 2281) adds "Your message went to Riley." | OpenAPI response text followed | UX to confirm |
| U-6 | CODE_WRONG with one try left reads "1 tries left." | SCREEN_SPECS words only "2 tries left."; the ticket fixes `{n} tries left.` | UX: a singular variant |
| U-7 | Phone-support line on **Saturday**: phone hours end 4:00 pm (cases.md §3.1 `PHONE_HOURS`), but the only wording says "until 7:00 pm today" | No time placeholder; written literally | AEA-14 (suppress on Saturday, or a UX-worded variant) |
| U-8 | CON-17 alert lines: P0/P1 created ("P0 safety case MHC-C-0008 created at 2:16 pm, unowned. Assign it." needs a time placeholder), unowned, due soon, stuck waiting, and the plural shift-ended line (only "1 customer waiting" is worded) | No wording, or a placeholder outside the seven | AEA-30 / AEA-48 / AEA-53 |
| U-9 | "Staffing changed:" line when the simulation is switched **off** | Only the "on" variant is worded (SCREEN_SPECS line 130) | AEA-30 |
| U-10 | "You can change this visit free of charge until 24 hours before the window." (OpenAPI 1175) contains "charge" | Written (it is not a charge claim); UX to confirm against the "charged in any form" rule | UX |
| U-11 | Saved follow-up line for **email** ("Follow-up saved: email, …") | Only the phone variant is worded | AEA-29 / AEA-45 |
| U-12 | History texts "Code entered" and "Details sent" (AEA-40 AC-19) | Not in any UX document yet; AEA-40 already records them as an AEA-03 follow-up after UX agreement | AEA-40 |
| U-13 | Labels the API carries but this module does not hold: option and button labels ("Yes", "No", "Not sure", "Skip", "Skip and book", "Show the checks", "Send a new code", "Show windows", "Call 911 (from outside)", "Start a new chat", "Email · the address on your account", "Phone call · the number ending in 02", "Mornings", "Afternoons", "Any time"), staffing labels ("Nobody online", "Simulated staff on shift (demo)"), confirmation timeline labels, the masked hints ("the phone ending in 02"), the `settled` summaries ("Verified for this chat") | Out of scope by §3c (labels, not sentences); the consumer types them from SCREEN_SPECS. If UX wants them centralised, that is a follow-up | AEA-21, 27, 28, 30 |
| U-14 | Dispute / unsupported-action lines ("I can't change or remove charges, but a person can review this with you."; "I can't switch off auto-renewal from this chat.") | SCREEN_SPECS line 110 gives them as examples ("e.g."): model text, not fixed | AEA-38 (responder) |

---

## Gates

None (wave 0; no human, paid, live or external gate). The fee-amount gate was resolved by R-W-7.

---

## 9. Readiness

**READY.** Every decision is made above; no signed contract changes; no decision D-4…D-15 is answered differently.
**Blocked on:** nothing. AEA-03 imports nothing from another ticket and builds without AEA-01's scaffold (namespace
packages with `PYTHONPATH=src`). Merge note only: `tests/unit/test_import_direction.py` and the three context files are
shared with other wave-0 tickets (§8a R-1, R-2).

## Deviations

- `uv sync` was not run: the worktree has no `pyproject.toml` (AEA-01's); checks used `uv run --no-project` as step 1 says.
- Code commit is `2689582`; context commit follows it. The test file has 14 passing targets (13 in test_texts.py plus the import test), as the plan's check section expects.
- Ruff in this environment applies stricter rules (FURB): `sorted(x)[0]` became `min(x)` and `re.I` became `re.IGNORECASE`; behaviour identical.
