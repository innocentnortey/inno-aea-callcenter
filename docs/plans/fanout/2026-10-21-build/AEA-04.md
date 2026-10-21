# Plan — [AEA-04] privacy: one redaction function, five profiles

**Status:** planned (READY)
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #4 (spec copy: `docs/plans/tickets/AEA-04.md`) · **Base revision:** `main` @ `9c3e7e7`
**Lane / risk / wave:** `lane::build-loop` · `risk::security` · wave 0, merges first in the wave-0 order **AEA-04 → AEA-02 → AEA-05** (R-G-18)
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21. **Builders:** `test-writer-agent` (frozen tests first), then `fanout-implementer` (Sonnet).

---

## 1. Goal and sources

### Goal (quoted from the issue, *What to build*)

> As a **homeowner** asking about my bill, I need to receive a one-time code at the phone or email on my account and
> type it in the chat, so that nobody else can read my account by guessing my name. (US-8; R-15, R-16)

Build `src/meridian/privacy/redact.py` exactly as `docs/design/contracts/stage7/data.md` §1 signs it: one pure,
idempotent, standard-library-only function `redact(text, profile) -> Redacted` with five profiles (STORE, SONNET, JEV,
TRACE, LOG), the types `RedactionKind`, `RedactionProfile`, `Redacted`, `UnknownRedactionProfile`, and the alias
`Redactor`. Every later outbound path (intake storage, model calls, trace export, log formatter) calls it.

**In practice (WP-2):** the customer types *"Hi, my name is Omar Patel, account MHC-10002, phone ‹phone ending 02›"* and
later a message with a card-like number.
- JEV (to the planner model) sees `my name is [name], account [customer id], phone [phone]` and `[card number removed]`.
- SONNET (to Anthropic) sees the name and `INV-204411` but `[phone ending 02]` and `[card number removed]`.
- TRACE (to Langfuse) sees `[name]`, `[phone ending 02]`, and the invoice amounts and due date unchanged.
- STORE (to the database) only loses the card number and any six-digit code.
- LOG keeps nothing but the length.

### Context

Wave 0 of Stage 8. `src/`, `tests/` and `pyproject.toml` do not exist on `main` yet: AEA-01 builds the scaffold in
parallel and owns `pyproject.toml`, the package markers (`__init__.py`) and lint/type configuration. AEA-02 imports
`RedactionProfile` from this file for `RoleSpec.redaction`, so this ticket merges first and its public names are
frozen after wave 0. DAT-1 (how names are found) was decided by Innocent on 2026-10-21 as option A (stage7-signoff D-14:
"the DAT/CAS/GRC items stay on their recommended options"), so the ticket's "Awaiting Innocent: DAT-1" line is settled.

### Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-04.md` | Types, profile matrix, placeholders, AC-1…AC-12 |
| Signed addendum (wins over DO-4) | `docs/design/contracts/stage7/data.md` §1 | Exact class/enum names and values, `redact` signature, `Redactor` alias, placeholder table, profile matrix |
| Component contracts | `docs/design/contracts/internal-components.md` (DO-4) §3 `Intake.text_store` (line 131), §3 `PlannerInput.latest_message` JEV (line 229), §5 `customer_text` SONNET (line 302, stale comment, AEA-08 fixes it), §12 `RoleSpec.redaction` (line 840), `ModelGateway(…, redact: Redactor, …)` (line 855) | Consumers bind to the names above; do not edit DO-4 |
| Consumers' addenda | `stage7/models.md` §4 line 283 (`LangfuseTraceSink(settings, redact: Redactor, on_alert)`), line 338 (gateway applies `redact(text, spec.redaction)`); `stage7/staff.md` §5 line 325 (`redact_store: Callable[[str], str]` bound by the container); `stage7/graph-core.md` §12 line 563 (R-G-18) | `Redactor` must be `Callable[[str, RedactionProfile], Redacted]`; the one-profile binding is the container's, not here |
| Decision ledgers | `docs/plans/7b-decisions/data.md` DAT-1 (A, decided via D-14), DAT-5 (SONNET masks contact, by source), DAT-28 (tokens); `merge-clashes.md` MC-23 (`Redactor` defined here); `residuals-graph.md` R-G-18 (merge order) | As written in §3 and §4 below |
| Code design | `docs/design/code-design.md` (DO-3) §3 line 197, §4.1 line 308 (depends on: none), §2.1 (pure core imports no I/O), §8 note (stays in A0), §9 (`tests/unit/privacy/test_redact.py`) | Location, stdlib only, test path |
| Requirements | PRD R-13 (never accept card numbers), R-15 (no code in chat, logs, traces), R-16, R-36 (redacted traces and logs) | Card and code masked by every text-keeping profile; LOG keeps no text |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` | **n/a**: no E-1…E-8 suite scores masking (ticket *Evaluation*) |
| Observability contract | DO-6 `docs/design/observability-contract.md` *Content and redaction* (lines 187–216): the table, "Where redaction happens, in order", "What leaves the environment"; CAP-1 | This file is the masker behind every row; CAP-1 is AEA-51's; AC-12 adds the DAT-1 limit line |
| Key-metrics registry | DO-7 | **n/a**: no redaction metric (ticket *Metrics*) |
| System design | DO-1 §3.2 (what Anthropic and Jev see), §10 *Redaction (R-36)* and *What each vendor sees* | Basis for SONNET's contact row (DAT-5) |
| Project rules | `safe-validation-errors.md` rules 1, 2, 5; `verification-evals-observability.md` rule 19; workspace `context-management-multi-turn.md` rule 5; `integrated-journeys.md` §3–§4; `build-loop-test-scope.md` (+ AEA addition) | Errors never echo input; a negative seeded-value test; stable tokens; journey record at `mock-tested` |
| Spike precedent | branch `archive/spike/SP-1-build`, `spikes/sp1/app/gates.py` `extract_name` | Introduction-pattern shape (read only; never imported) |
| Issued data (read only, shapes only) | `docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite` | Phones are `999-999-9999`; street lines are `NNN(N) Word (Word) Suffix` with suffixes Dr, Ct, Ave, Blvd, Ln, Terrace, St, Rd, Pass, Way; IDs `MHC-99999`, `INV-999999`; case refs `MHC-C-9999` |

---

## 2. Boundary

### Owned files (the only files the test-writer and implementer may create or edit)

| File | Current | Who writes it | Change |
|---|---|---|---|
| `src/meridian/privacy/redact.py` | absent | implementer | **create**: the whole module |
| `tests/unit/privacy/test_redact.py` | absent | test-writer (frozen) | **create** |
| `tests/unit/privacy/test_redactor_alias.py` | absent | test-writer (frozen) | **create** |
| `tests/unit/test_import_direction.py` | absent (shared with AEA-01, 02, 03, 05) | test-writer (frozen) | **create the file if absent, else append**; this ticket owns only the function `test_redact_imports_stdlib_only` |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-04.md` | absent (folder absent) | implementer | **create** (AC-11) |
| `.claude/reference/area-map.md` | exists | implementer | line 25 (A0 row): the token `` `privacy/redact.py` `` only (AC-12) |
| `docs/design/code-design.md` | exists | implementer | line 197 (§3 tree line for `privacy/redact.py`) only (AC-12) |
| `.claude/state/icm-progress.md` | exists | implementer | row *Routes verified against code and tests* only (AC-12) |
| `docs/design/observability-contract.md` | exists | implementer | one new paragraph in *Content and redaction* (AC-12) |

### Read only (never edit)

DO-4 `internal-components.md`, every `stage7/*.md` addendum, `slice-plan.md`, ticket files, the briefing, issued data,
`docs/archive/`, `docs/parked/` (reference only, never imported), `docs/ux/**`, `apps/web/**`,
`ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, `.claude/README.md`, `CLAUDE.md`, `.env*` (never read).

### Owned by other tickets (must not touch)

- AEA-01: `pyproject.toml`, `uv.lock`, **every `__init__.py`** (package markers under `src/meridian/` and `tests/`),
  `tests/conftest.py`, ruff/type-check config, `policy/limits.py`, `web/container.py`, `tests/journeys/`.
  **This ticket creates no `__init__.py` anywhere** (Python 3.12 implicit namespace packages make
  `meridian.privacy.redact` importable with `PYTHONPATH=src` until AEA-01's markers land).
- AEA-02: `config.py`, `domain/*`, `ports/*`, `adapters/sqlite/repos_*.py`.
- AEA-03: `policy/texts.py`. AEA-05: `gates/rules.py`. AEA-08: DO-3 header/status line, DO-4 comments.
- Every consumer (AEA-12, 19, 20, 22, 23, 27, 40, 44/46, 51): none of their files; no `register_*` hunk (the
  `redact_store` binding is the container's, done by its owner).

---

## 3. Requirements table

### 3a. Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| `RedactionKind` with exactly 9 values `card, code, phone, email, address, name, customer_id, invoice_id, free_text` | data.md §1 | What to build | in-ticket (AC-2…6) + plan-added test `test_enum_values_are_the_contract` | Step I-1 |
| `RedactionProfile` with exactly `store, sonnet, jev, trace, log` | data.md §1; DO-4 §12 | What to build | in-ticket + plan-added `test_enum_values_are_the_contract` | Step I-1 |
| `Redacted` frozen; `replaced` counts only; `__repr__` counts and length only | data.md §1 | AC-5 | in-ticket + plan-added `test_redacted_repr_and_immutability` | Step I-2 |
| `UnknownRedactionProfile(ValueError)`, message never holds the text | data.md §1; safe-validation-errors 1–2 | AC-9 | in-ticket + plan-added `test_unknown_profile_swapped_args_not_echoed` | Step I-3 |
| `redact` pure and idempotent | data.md §1; DO-1 §10 "applied again at export" | AC-8 | in-ticket | Steps I-4…I-6 |
| `Redactor = Callable[[str, RedactionProfile], Redacted]` | data.md §1; MC-23 | AC-10 | in-ticket | Step I-2 |
| Standard library only, no I/O | DO-3 §4.1, §2.1 | AC-10 | in-ticket | Step I-1 |
| Profile matrix (which kinds each profile replaces) | data.md §1 table | AC-1…AC-6 | in-ticket | Step I-5 |
| Placeholder tokens, one per kind, stable across calls | data.md §1; DAT-28; workspace `context-management-multi-turn` 5 | AC-2 | in-ticket | Step I-4 |
| SONNET masks phone (last two kept), email, street line; keeps names and IDs | DAT-5; DO-1 §3.2, §10 | AC-3 | in-ticket | Step I-5 |
| TRACE keeps account facts and customer/invoice IDs | data.md §1; DO-6 table row *Account facts* and *IDs* | AC-4 | in-ticket | Step I-5 |
| LOG: text `""`, length only | DO-6 "Logs: Never: length only" | AC-5 | in-ticket | Step I-6 |
| Non-private values not masked | ticket | AC-7 | in-ticket + plan-added `test_brand_greeting_not_a_name` | Step I-4 |
| Untrusted input cannot stall the masker (every pattern runs in bounded time on 100 000 characters) | DO-1 §3.3 rule 1 (browser is untrusted); redaction runs on every message and every exported span | not in ticket | **added**: `test_patterns_run_in_bounded_time` | Step I-4 (bounded quantifiers) |
| Wrong-type `text` refused without echo | safe-validation-errors 1–2 | not in ticket | **added**: `test_non_str_text_refused_without_echo` | Step I-3 |
| Empty input handled per profile | data.md §1 (`length` = `len(input)`) | not in ticket | **added**: `test_empty_text_every_profile` | Step I-6 |
| WP-2 worked pair as a test | `build-loop-test-scope.md` (the ticket's WP-N pair is one of the named tests) | Example pair | **added**: `test_wp2_worked_pair[<profile>]` | Data §6 |
| A plain string equal to a profile value is accepted (`"jev"` behaves as `RedactionProfile.JEV`) | `StrEnum` semantics; `RoleSpec.redaction` may arrive as text before pydantic coerces it | not in ticket | **added** (engineering decision): `test_plain_string_profile_value_accepted` | Step I-3 |
| Journey record at level `mock-tested`, *Blocked by* AEA-57, names J-1 and J-3 | `integrated-journeys.md` §3 rule 1, §4 | AC-11 | in-ticket | Step I-9 |
| Context: area map, DO-3, ICM, DO-6 DAT-1 line | `context-maintenance.md` | AC-12 | in-ticket | Step I-10 |
| CAP-1 (seeded values absent through the real entry point) | DO-6 CAP-1 | Observability | other-ticket: AEA-51 (AC-18) | — |
| Wiring per consumer (`STORE` at intake, `TRACE` in `mask_otel_spans`, `JEV`/`SONNET` in the gateway, `LOG` in the formatter) | DO-6 "Where redaction happens" | Observability | other-ticket: AEA-12, 19, 20, 22, 23, 27, 40 | — |
| Fix DO-4 §5's stale SONNET comment | data.md §1; DAT-5 | What to build | other-ticket: AEA-08 | — |
| Names beyond introduction patterns; a `known:` argument | DAT-1 options B/C | Agent handoff | n/a: DAT-1 decided A (D-14). Nothing added to the signature | — |

### 3b. Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (a pure function; it emits no record and adds no entry point) | — | — | — |

### 3c. Acceptance criteria (verbatim) and plan-added criteria, with the test that proves each

The test-writer freezes **every row** below before the implementer starts. All tests live in
`tests/unit/privacy/test_redact.py` unless the row says otherwise.

| AC | Criterion (issue text, abridged only where marked …) | Test (exact node id) | What passing shows |
|---|---|---|---|
| AC-1 [invariant] | `STORE` replaces every card-like number (13, 16 and 19 digits; plain, spaced, dashed) with `[card number removed]` and every standalone six-digit code with `[code]`, and keeps names, phones, emails and addresses unchanged | `::test_store_masks_cards_and_codes_keeps_contact[<n>-<sep>]` (9 cases: n ∈ 13, 16, 19 × sep ∈ plain, space, dash) | passes for each format |
| AC-2 [invariant] | `JEV` replaces introduced names, phones, emails, street addresses, `MHC-\d{5}`, `INV-\d{6}`, six-digit codes and card-like numbers with data.md §1's tokens, and the same kind maps to the same token across two separate calls | `::test_jev_masks_every_identifier`, `::test_placeholders_stable_across_calls` | pass; name cases are introductions only (DAT-1) |
| AC-3 [invariant] | `SONNET` masks cards, codes, emails and the street line, turns a phone into `[phone ending NN]`, and keeps names, `MHC-`/`INV-` IDs and account facts (DAT-5) | `::test_sonnet_masks_contact_keeps_ids` | passes |
| AC-4 [invariant] | `TRACE` keeps a phone's last two digits only, masks introduced names, emails and the street line, and leaves account facts untouched (amounts such as $478.00, dates such as 2026-11-01, windows such as 8:00 am – 12:00 pm, tier words, `MHC-C-` case references, customer and invoice IDs) | `::test_trace_profile` | passes |
| AC-5 [invariant] | `LOG` returns `text == ""`, `length == len(input)` and `replaced == {free_text: 1}` for non-empty input | `::test_log_profile_is_length_only` | passes; no input substring longer than one character appears in the result or its repr |
| AC-6 [negative] | For every profile, seeded distinctive values (card, code, phone, email, customer ID, invoice ID, street address, introduced name), assembled at run time, are absent from the output text, from `repr(Redacted)` and from any exception text, wherever the matrix marks that kind replaced | `::test_seeded_values_absent[store]`, `[sonnet]`, `[jev]`, `[trace]`, `[log]` | one pass per profile; the kind × profile matrix printed (`-rP`) |
| AC-7 [negative] | ZIP (78620), a city name, dollar amounts, ISO dates, slot numbers and 12-hour times survive `TRACE`, `SONNET` and `STORE`; a ten-digit phone is never treated as a card | `::test_non_private_values_survive` | passes |
| AC-8 [invariant] | `redact(redact(x, p).text, p).text == redact(x, p).text` and the second call's `replaced` counts are all zero, every profile, over the AC-6 inputs | `::test_idempotent[store]` … `[log]` | passes |
| AC-9 [failure/refusal] | Unknown profile raises `UnknownRedactionProfile`; message holds the profile value only, no part of the input text | `::test_unknown_profile_refused_without_echo` | raises; sentinel text absent |
| AC-10 [invariant] | No I/O, stdlib only, `redact` satisfies `Redactor` in the type check | `tests/unit/test_import_direction.py::test_redact_imports_stdlib_only`; type check over `tests/unit/privacy/test_redactor_alias.py` (+ runtime `tests/unit/privacy/test_redactor_alias.py::test_redact_satisfies_redactor_alias`) | passes; the import list printed; type check clean |
| AC-11 [journey] | Runs no journey yet (wave 0 precedes AEA-57); record states level `mock-tested`, *Blocked by* AEA-57, names J-1 and J-3 | the record `docs/testing/journeys/<date>-AEA-04.md` | Level, Blocked-by, journey fields present |
| AC-12 [regression/context] | Area-map A0 row, DO-3 §3, ICM row, DO-6 DAT-1 line | `git diff main -- <the four files>` | the four edits in §5 step I-10 |
| WP-2 (plan-added) | The worked pair WP-2 per profile, as the issue's *Example pair* | `::test_wp2_worked_pair[store]` … `[log]` | exact expected text per profile |
| plan-added | Enum values are the contract's | `::test_enum_values_are_the_contract` | passes |
| plan-added | `Redacted` repr shows counts and length only; it and its `replaced` are immutable | `::test_redacted_repr_and_immutability` | passes |
| plan-added | Swapped arguments (`redact(profile, text)`) never echo the text | `::test_unknown_profile_swapped_args_not_echoed` | passes |
| plan-added | Non-`str` text refused with a type-name-only message | `::test_non_str_text_refused_without_echo` | passes |
| plan-added | `"jev"` (plain `str`) behaves as `RedactionProfile.JEV` | `::test_plain_string_profile_value_accepted` | passes |
| plan-added | Empty text: every profile returns `text ""`, `replaced {}`, `length 0` | `::test_empty_text_every_profile` | passes |
| plan-added | The assistant's own greeting "This is Meridian Home Comfort" is not a name | `::test_brand_greeting_not_a_name` | passes |
| plan-added | Pathological 100 000-character inputs finish in under 2 s for all five profiles together | `::test_patterns_run_in_bounded_time` | passes |

---

## 4. Shared code to use

This module imports **nothing** from the project and nothing outside this list:
`re`, `collections.abc` (`Callable`, `Mapping`), `dataclasses` (`dataclass`), `enum` (`StrEnum`), `types`
(`MappingProxyType`), `typing` (`TypeAlias`). No `__future__` import is needed (Python 3.12).

### 4a. The signed surface (copy exactly; data.md §1)

```python
class RedactionKind(StrEnum):
    CARD = "card"; CODE = "code"; PHONE = "phone"; EMAIL = "email"; ADDRESS = "address"; NAME = "name"
    CUSTOMER_ID = "customer_id"; INVOICE_ID = "invoice_id"; FREE_TEXT = "free_text"   # FREE_TEXT: LOG only

class RedactionProfile(StrEnum):
    STORE = "store"; SONNET = "sonnet"; JEV = "jev"; TRACE = "trace"; LOG = "log"

@dataclass(frozen=True)
class Redacted:
    text: str                                         # the redacted text; LOG: ""
    replaced: Mapping[RedactionKind, int]             # how many values of each kind were replaced; never a value
    length: int                                       # len(input); the only thing LOG keeps
    def __repr__(self) -> str: ...                    # counts and length only

class UnknownRedactionProfile(ValueError): ...        # message names the profile value only, never the text

def redact(text: str, profile: RedactionProfile) -> Redacted: ...

Redactor = Callable[[str, RedactionProfile], Redacted]   # the type of redact (MC-23)
```

Write one member per line (ruff/format style), not the `;`-joined form above. Write the alias as
`Redactor: TypeAlias = Callable[[str, RedactionProfile], Redacted]` with `Callable` from **`collections.abc`** (the
runtime test compares it to `collections.abc.Callable[[str, RedactionProfile], Redacted]`). Do not use the 3.12
`type Redactor = …` statement (it makes a `TypeAliasType`, which consumers cannot use the same way). Export
`__all__ = ["RedactionKind", "RedactionProfile", "Redacted", "UnknownRedactionProfile", "Redactor", "redact"]`.
No other public name: patterns, tokens and tables are private (`_`-prefixed); data.md §0 says a builder may add a
private helper, never a field another ticket reads.

### 4b. Placeholder tokens (data.md §1, DAT-28; exact strings)

| Kind | Token |
|---|---|
| CARD | `[card number removed]` |
| CODE | `[code]` |
| PHONE, JEV | `[phone]` |
| PHONE, SONNET and TRACE | `[phone ending NN]`, where NN is the last two digits of the matched phone (e.g. `[phone ending 02]`) |
| EMAIL | `[email]` |
| ADDRESS | `[address]` (the street line only; city, state and ZIP stay) |
| NAME | `[name]` (the introduction words stay: `my name is [name]`) |
| CUSTOMER_ID | `[customer id]` |
| INVOICE_ID | `[invoice id]` |

### 4c. Profile matrix and the fixed rule order

Rules always run in this order; a profile runs only its own rules, in that order.

| Order | Kind | STORE | SONNET | JEV | TRACE | Why this position (the invariant it protects) |
|---|---|---|---|---|---|---|
| 1 | CARD | ✓ | ✓ | ✓ | ✓ | First, so a card's digit groups are never half-taken as a phone or a code |
| 2 | EMAIL | · | ✓ | ✓ | ✓ | Before PHONE/ADDRESS/NAME, so an address like `omar.patel42@…` goes whole |
| 3 | PHONE | · | ✓ hint | ✓ `[phone]` | ✓ hint | Before ADDRESS, so a phone's last group never starts a street line |
| 4 | ADDRESS | · | ✓ | ✓ | ✓ | Before CODE, so a six-digit house number becomes `[address]`, not `[code] Oak St` |
| 5 | CODE | ✓ | ✓ | ✓ | ✓ | Skips `INV-` digits, so IDs survive where they are kept |
| 6 | CUSTOMER_ID | · | · | ✓ | · | — |
| 7 | INVOICE_ID | · | · | ✓ | · | After CODE (CODE never touches `INV-`) |
| 8 | NAME | · | · | ✓ | ✓ | Last: it keys on words only |
| — | FREE_TEXT | LOG only: no rules run; the text is dropped | | | | |

### 4d. The patterns (exact; prototyped by the planner in a scratch copy against the cases in §6, all idempotent)

Compile each once at module level with `re.compile(...)`, no flags argument (case-insensitive parts use scoped
`(?i:…)` groups, which Python 3.12 supports).

```python
_CARD = r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)"
_EMAIL = r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63}){0,8}\.[A-Za-z]{2,24}(?![A-Za-z0-9-])"
_PHONE = r"(?<![\d+])(?:\+?1[ .-]?)?(?:\(\d{3}\)[ ]?|\d{3}[ .-]?)\d{3}[ .-]?\d{4}(?!\d)"
_STREET_ABBR = r"(?i:st|ave|rd|dr|ln|blvd|ct|cir|trl|pkwy|hwy|ter|cv|pl)"
_STREET_FULL = (
    r"(?:Street|Avenue|Road|Drive|Lane|Boulevard|Court|Circle|Trail|Parkway|Highway|Terrace|Cove|Place|Way|Pass"
    r"|Loop|Run|Path|Bend|Point|Row|Square|Crossing)"
)
_STREET_WORD = r"(?:\d{1,3}(?:st|nd|rd|th)|[A-Za-z][A-Za-z'’-]*)"
_ADDRESS = (
    r"(?<![\w$.,:/#-])\d{1,6}[ \t]+"
    r"(?:(?:[NSEW]|North|South|East|West)\.?[ \t]+)?"
    r"(?:" + _STREET_WORD + r"[ \t]+){1,3}"
    r"(?:" + _STREET_ABBR + r"|" + _STREET_FULL + r")(?![A-Za-z])\.?"
    r"(?:,?[ \t]+(?i:apt|apartment|unit|suite|ste)\.?[ \t]*#?[A-Za-z0-9-]+|,?[ \t]*#[ \t]*[A-Za-z0-9-]+)?"
)
_CODE = r"(?<!\d)(?<![Ii][Nn][Vv]-)(?<!\$)(?<!\d[.,])\d{6}(?!\d|[.,-]\d)"
_CUSTOMER_ID = r"\b(?i:MHC)-\d{5}\b"
_INVOICE_ID = r"\b(?i:INV)-\d{6}\b"
_NAME_WORD = r"[A-Z](?:[a-z]+(?:[A-Z][a-z]+)?|['’][A-Z][a-z]+)(?:-[A-Z][a-z]+)?"
_NAME = (
    r"(?P<intro>\b(?i:my[ \t]+name[ \t]+is|my[ \t]+name['’]s|name[ \t]+is|this[ \t]+is|i[ \t]+am|i['’]m)[ \t]+)"
    r"(?!Meridian\b)"
    r"(?P<name>" + _NAME_WORD + r"(?:[ \t]+" + _NAME_WORD + r"){0,2})(?![A-Za-z'’-])"
)
```

What each rule decides, in plain words (keep these as one-line comments above each pattern):
- **CARD:** 13–19 digits, single spaces or dashes allowed between any two digits, no checksum (DO-6), not glued to
  other digits. It deliberately also catches two numbers that touch with one separator (a phone directly followed by a
  ZIP with one space): masking too much is the safe failure for a card.
- **EMAIL:** local part ≤ 64 characters and bounded domain labels, so a long run of letters without `@` cannot make
  the scan quadratic (the planner measured 7.5 s on 100 000 characters with an unbounded `+`; 0.01 s bounded).
- **PHONE:** US 10-digit forms `ddd-ddd-dddd`, `ddd.ddd.dddd`, `ddd ddd dddd`, `(ddd) ddd-dddd`, `dddddddddd`, with an
  optional `+1`/`1` prefix. Seven-digit local numbers are not phones (limit, §8).
- **ADDRESS:** a house number (not after `$ . , : / # -` or a word character, so `$89`, `8:00` and `MHC-10002` are never
  house numbers), an optional direction, one to three street-name words, a suffix, an optional unit. Abbreviated
  suffixes match in any case (`dr`, `Dr`); full-word suffixes only when capitalised (`Drive`, `Way`, `Pass`), so
  "a 2 hour drive" and "2 techs on the way" are not addresses. City, state and ZIP after the street line stay.
- **CODE:** exactly six digits not touching another digit, not after `INV-` (any case), `$`, or a digit plus `.`/`,`,
  and not followed by `.`/`,`/`-` plus a digit. Letters may touch it (`code123456` and `code:123456` are masked).
- **CUSTOMER_ID / INVOICE_ID:** any case; `MHC-C-0007` case references never match (a letter follows `MHC-`).
- **NAME:** an introduction (`my name is`, `my name's`, `name is`, `this is`, `I am`, `I'm`/`I’m`, any case) then one to
  three capitalised name words (`Omar`, `McDonald`, `O'Neil`, `Smith-Jones`); all-caps words (`AC`) and single letters
  are not names. The introduction stays; only the name words become `[name]`. The brand ("This is Meridian …") is not
  a name.

Replacement callables (private):
- PHONE hint: `lambda m: f"[phone ending {re.sub(r'\D', '', m.group(0))[-2:]}]"` written as a named `def
  _phone_hint(match: re.Match[str]) -> str` (ruff E731 forbids assigning a lambda).
- NAME: `def _name_token(match: re.Match[str]) -> str: return match.group("intro") + "[name]"`.
- Every other kind: the fixed token string from §4b (none contains a backslash, so `re.subn` treats it literally).

### 4e. Consumers (for awareness only; none is called or edited here)

```python
# DO-4 §12 (internal-components.md line 840, 855)
class RoleSpec(MeridianModel):
    ...
    redaction: RedactionProfile                       # JEV for planner/classifier; SONNET for the rest
class ModelGateway:
    def __init__(self, *, choice: ..., structured: ..., tools: ...,
                 ledger: LedgerService, trace: TraceSink, redact: Redactor, limits: Limits) -> None: ...
# stage7/models.md §4 line 283
def __init__(self, settings: LangfuseExportSettings, redact: Redactor, on_alert: TraceAlert) -> None: ...
# stage7/staff.md §5 line 325 (the container binds the one-profile form, not this ticket)
def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock, redact_store: Callable[[str], str]) -> None: ...
#   redact_store = lambda t: redact(t, RedactionProfile.STORE).text
```

---

## 5. Steps

The build follows DO-3's dependency direction: `privacy/` is pure core, imports nothing from `meridian`, and is
imported by A1, A2, A8 and A10a. No new seam or abstraction is introduced (the profile table is private data).

### Phase T — test-writer (`risk::security`: frozen failing tests first)

T-1. Create `tests/unit/privacy/test_redact.py` with every `test_redact.py` row of §3c, designed exactly as §6. The
     module under test is reached through a module-scoped fixture so the file **collects** before `redact.py` exists:
     ```python
     @pytest.fixture(scope="module")
     def rd() -> ModuleType:
         return importlib.import_module("meridian.privacy.redact")
     ```
     Parametrise by the profile **value strings** `("store", "sonnet", "jev", "trace", "log")` (ids = the value) and
     convert inside the test with `rd.RedactionProfile(value)`. Never import `meridian` at module top level here.
T-2. Create `tests/unit/privacy/test_redactor_alias.py` exactly as §6.4 (the `TYPE_CHECKING` block is what the type
     check reads; the runtime test imports inside the function).
T-3. Create or append `tests/unit/test_import_direction.py` with `test_redact_imports_stdlib_only` exactly as §6.5. If
     the file already exists in the branch base (another wave-0 ticket merged first), append the function at the end
     and add only the imports it needs (`ast`, `sys`, `pathlib.Path`) to the existing import block. All helpers stay
     inside the function (no module-level helper another ticket might also define).
T-4. Lint-clean and formatted at line length 110 (§7 fallback commands). Every test function annotated `-> None`.
T-5. Run red: `PYTHONPATH=src uv run --no-project --python 3.12 --with pytest pytest -q -p no:cacheprovider
     tests/unit/privacy tests/unit/test_import_direction.py::test_redact_imports_stdlib_only` → every test fails with
     `ModuleNotFoundError: No module named 'meridian'` (or `FileNotFoundError` for the import scan): red for the right
     reason. Then `… pytest --collect-only -q tests/unit` exits 0.
T-6. Commit only these three test files (`git add <the three paths>`), message `test(privacy): frozen failing tests
     for AEA-04`, last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Record the frozen-test
     manifest as the workflow requires.

### Phase I — implementer

I-0. **Before you start:** read this plan, `docs/design/contracts/stage7/data.md` §1 and the frozen tests. Do not edit
     any frozen test file (tamper check). If a frozen test contradicts this plan or data.md §1, stop and report the
     exact assertion; do not "fix" the test.

I-1. **Create `src/meridian/privacy/redact.py`** with a module docstring (one paragraph: what it masks, that it is
     pure, that DAT-1 limits names to introductions), the six stdlib imports of §4, `__all__`, then `RedactionKind`
     and `RedactionProfile` exactly as §4a (one member per line). *Invariant: the enum values are the contract AEA-02
     and every consumer type against.*

I-2. **`Redacted`, `UnknownRedactionProfile`, `Redactor`.**
     - `@dataclass(frozen=True)` with fields `text: str`, `replaced: Mapping[RedactionKind, int]`, `length: int` in that
       order. Define `__repr__` in the class body (the dataclass keeps a `__repr__` the class defines):
       `Redacted(length=<length>, replaced={<kind>: <n>, ...})` with kinds in the order `replaced` holds them, written
       as `f"{kind}: {count}"`. Never include `text`. *Invariant: a stray `logger.info(result)` or f-string cannot leak
       text.*
     - `class UnknownRedactionProfile(ValueError)` with a docstring; no extra fields.
     - `Redactor: TypeAlias = Callable[[str, RedactionProfile], Redacted]` placed after `Redacted`.

I-3. **Argument checks, in this order, at the top of `redact`:**
     1. Resolve the profile without try/except (so no exception context can carry a value):
        `_PROFILE_BY_VALUE: Mapping[str, RedactionProfile] = MappingProxyType({p.value: p for p in RedactionProfile})`;
        `resolved = _PROFILE_BY_VALUE.get(profile) if isinstance(profile, str) else None`. A `RedactionProfile`
        member and the plain string `"jev"` both resolve (StrEnum hashes and compares as its value).
     2. If `resolved is None`: `raise UnknownRedactionProfile(_describe_profile(profile))`, where
        `_describe_profile` returns
        `f"profile: unknown_redaction_profile (expected one of {expected}; got {shown})"`, `expected` =
        `", ".join(p.value for p in RedactionProfile)`, and `shown` = `repr(str(profile))` **only if** `profile` is a
        `str` that fully matches `[a-z_]{1,16}` (a mistyped profile name such as `"jevv"`), otherwise
        `f"<{type(profile).__name__}>"`. *Invariant: a swapped call `redact(RedactionProfile.JEV, "my name is …")`
        names no customer text, because free text never fits `[a-z_]{1,16}` (safe-validation-errors rule 1).*
     3. If `not isinstance(text, str)`: `raise TypeError(f"text: invalid_type (expected str, got {type(text).__name__})")`.
        *Invariant: bytes or objects holding private data are never echoed.*

I-4. **The rules table.** A private frozen dataclass
     `_Rule(kind: RedactionKind, pattern: re.Pattern[str], replace: str | Callable[[re.Match[str]], str])`, one
     instance per row of §4c using the §4d patterns and §4b tokens: `_CARD_RULE`, `_EMAIL_RULE`, `_PHONE_FULL_RULE`
     (`[phone]`), `_PHONE_HINT_RULE` (`_phone_hint`), `_ADDRESS_RULE`, `_CODE_RULE`, `_CUSTOMER_ID_RULE`,
     `_INVOICE_ID_RULE`, `_NAME_RULE` (`_name_token`). *Invariant: no token contains a digit run of 3+, an `@`, a
     capitalised word after an introduction or an ID prefix, so no rule can match a token again (idempotence, AC-8).*

I-5. **The profile table** (private, `MappingProxyType`), exactly the §4c order:
     ```
     STORE:  (CARD, CODE)
     SONNET: (CARD, EMAIL, PHONE_HINT, ADDRESS, CODE)
     JEV:    (CARD, EMAIL, PHONE_FULL, ADDRESS, CODE, CUSTOMER_ID, INVOICE_ID, NAME)
     TRACE:  (CARD, EMAIL, PHONE_HINT, ADDRESS, CODE, NAME)
     ```
     LOG has no entry (handled in I-6). *Invariant: the matrix is data in one place; a reviewer compares it to
     data.md §1 line by line.*

I-6. **The body of `redact`** after I-3:
     1. If `resolved is RedactionProfile.LOG`: return
        `Redacted(text="", replaced=MappingProxyType({RedactionKind.FREE_TEXT: 1} if text else {}), length=len(text))`.
     2. Otherwise `out = text`, `counts: dict[RedactionKind, int] = {}`; for each rule of the profile, in order:
        `out, n = rule.pattern.subn(rule.replace, out)`; if `n`: `counts[rule.kind] = counts.get(rule.kind, 0) + n`.
     3. Return `Redacted(text=out, replaced=MappingProxyType(counts), length=len(text))`. Only kinds with a count above
        zero appear (AC-5 compares `replaced == {free_text: 1}` exactly).
     No logging, no printing, no global state, no caching. *Invariant: pure; same input, same output, every call.*

I-7. **Iterate** with the affected tests (§7 "while iterating") until all §3c tests pass. Then the fast gates (§7
     "before the final commit"), cheapest first: lint, format check, type check, tests.

I-8. **Commit 1** (code): `git add src/meridian/privacy/redact.py` only. Message
     `feat(privacy): one redaction function, five profiles (AEA-04)`, a body listing the profiles and the AC-1…AC-10
     test result line, last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Note its short SHA
     (`git rev-parse --short HEAD`) for I-9 and I-10.

I-9. **Journey record** `docs/testing/journeys/<YYYY-MM-DD>-AEA-04.md` (today's date, `TZ=America/Chicago date +%F`).
     Fields, exactly these headings as a two-column table (`integrated-journeys.md` §4):
     | Field | Value |
     |---|---|
     | Claim | AEA-04 `privacy/redact.py`: the five redaction profiles behave as stage7/data.md §1 (AC-1…AC-10). No journey run. |
     | Level | `mock-tested` |
     | Tested revision | `<sha from I-8>` |
     | Environment | VPS, Python 3.12, no server; unit tests only (`PYTHONPATH=src`, or `uv run` once AEA-01's `pyproject.toml` is on the branch) |
     | Command | the exact test command you ran in I-7 |
     | Result | `<N passed>` (paste the pytest summary line) |
     | Evidence location | GitLab issue #4 comment; this file |
     | Remaining limitations | Names only by introduction patterns (DAT-1 A); seven-digit local phones and lowercase full-word street suffixes are not caught; no consumer wiring tested here (CAP-1 is AEA-51) |
     | Blocked by | AEA-57 (journey harness, wave 2) |
     | Journeys that will exercise this code | J-1 (the stored "[code entered]") and J-3 (the stored "[details submitted]"), once AEA-57 and AEA-51 land |

I-10. **Context edits (AC-12)**, each touching only the named line or paragraph:
     1. `.claude/reference/area-map.md` line 25 (A0 row): replace the token `` `privacy/redact.py` `` with
        `` `privacy/redact.py` (**actual**, AEA-04 `<sha>`) ``. Leave the row's status cell `planned` (the rest of A0 is
        still planned).
     2. `docs/design/code-design.md` line 197: append `   built AEA-04 <sha>` after the final `0` of the
        `├── privacy/redact.py …` tree line. Do not edit the document's header status line (AEA-08 owns it).
     3. `.claude/state/icm-progress.md`: replace the whole row *Routes verified against code and tests* with exactly
        (fill `<date>`, `<sha>`, `<N>`; keep it under 400 characters):
        ```
        | Routes verified against code and tests | provisional | <date>: first backend slice AEA-04 `privacy/redact.py` (<sha>): `tests/unit/privacy/` and `tests/unit/test_import_direction.py::test_redact_imports_stdlib_only` pass (<N> passed) | Each later slice adds its tests; verified at the wave-0 seam audit |
        ```
     4. `docs/design/observability-contract.md`, *Content and redaction*: insert one paragraph after item 4 of
        "Where redaction happens, in order." (after the line ending `dev-split failure examples only, redacted.`)
        and before `**What leaves the environment.**`, separated by blank lines:
        > **Name-masking limit (DAT-1, Innocent 2026-10-21: option A).** `privacy/redact.py` finds names only by
        > introduction patterns ("my name is …", "this is …", "I'm …" followed by capitalised words) and street lines
        > only by a number, street-name and suffix pattern. Loose names in free chat ("Omar here", "my mother Jane")
        > may therefore reach Jev, under `data_collection: deny`, and the project's own Langfuse. Codes, card-like
        > numbers, phones, emails and customer and invoice IDs have fixed shapes and are always replaced for their
        > profiles.
     Then run `python3 ~/.claude/skills/icm-project/scripts/check_context.py /home/linuxuser/workspaces/inno-aea-callcenter`
     and fix any FAIL your edits caused (report pre-existing ones, do not fix them).

I-11. **Commit 2** (record and context): `git add docs/testing/journeys/<date>-AEA-04.md .claude/reference/area-map.md
     docs/design/code-design.md .claude/state/icm-progress.md docs/design/observability-contract.md`. Message
     `docs(AEA-04): journey record and context for privacy/redact.py`, last line
     `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Never `git add -A`; never push.

I-12. **Report** AC by AC: the command, its result line, verified or not. Include the printed kind × profile matrix
     (AC-6) and import list (AC-10) from `-rP`.

### What the implementer must NOT do

- Edit, rename, reformat or delete a frozen test file; add tests elsewhere instead of fixing code.
- Create any `__init__.py`, `pyproject.toml`, `uv.lock`, `conftest.py`, or ruff/mypy config (AEA-01's).
- Add a dependency, a third-party import, logging, printing, file or network access, a module-level mutable, or any
  public name beyond the six in `__all__`; add a `known:` parameter (DAT-1 B is not chosen).
- Echo `text` or a non-matching `profile` in any exception, repr or str; use `try/except` around `RedactionProfile(…)`
  (its `ValueError` message repeats the value, and exception chaining would carry it).
- Put a literal card-like number, six-digit code or full phone number in code, comments, commit messages or docs.
- Edit DO-4, any stage7 addendum, AEA-08's DO-3 header line, the router, `CLAUDE.md`, or any consumer's file.
- Bind ports, start servers, call a model, read `.env`.

---

## 6. Data and fixtures (synthetic only)

All values are generated **at run time** from `random.Random(seed)` with fixed seeds (the ticket's conventions forbid
literal card-like numbers, codes and full phone numbers in tests). Only the issued, fictional WP-2 identifiers
(`Omar Patel`, `MHC-10002`, `INV-204411`, the invoice amounts and dates) appear as literals; their source is
`docs/data/worked-pairs.md` WP-2 and the issued DB. Nothing reads the issued files at test time.

### 6.1 Helpers (private to `test_redact.py`)

```python
def _digits(rng: random.Random, n: int) -> str:            # n random digits
def _card(rng: random.Random, n: int, sep: str) -> str:    # n digits in groups of 4 joined by sep ("" | " " | "-"); last group shorter
def _phone(rng: random.Random, last_two: str) -> str:      # f"{rng.randint(200, 989)}-{rng.randint(200, 989)}-{_digits(rng, 2)}{last_two}"
def _code(rng: random.Random) -> str:                       # str(rng.randint(100000, 999999))
def _word(rng: random.Random) -> str:                       # rng.choice(["Vel", "Tor", "Quin", "Zar", "Bel"]) + rng.choice(["ana", "ric", "ella", "ton", "ivo"])
def _seeded(seed: int) -> dict[str, str]:
    # keys: card (_card(rng, 16, " ")), code, phone (_phone(rng, "02")), email (f"{first.lower()}.{last.lower()}{rng.randint(10, 99)}@example.test"),
    # customer_id (f"MHC-{rng.randint(10000, 99999)}"), invoice_id (f"INV-{rng.randint(200000, 299999)}"),
    # address (f"{rng.randint(100, 9999)} {_word(rng)} Dr"), name (f"{first} {last}") with first, last = _word(rng), _word(rng)
```

Seeds: `_seeded(11)` and `_seeded(12)` (two customers); `random.Random(4)` for AC-1's per-format cards.

### 6.2 The message template (AC-2, AC-3, AC-4, AC-6, AC-8)

```python
TEMPLATE = ("Hi, my name is {name}. Phone {phone}, email {email}. I live at {address}, Kyle, TX 78640. "
            "Account {customer_id}, invoice {invoice_id}. My code is {code}. Card {card}.")
FACTS = ("Invoice {invoice_id}: Diagnostic visit $89, Contactor replacement $245, After-hours dispatch $144, "
         "total $478.00, due 2026-11-01. Window 8:00 am – 12:00 pm, Plus tier, case MHC-C-0007.")
```

Expected outputs are built with `TEMPLATE.format(...)` from the tokens, so every assertion is an exact string compare:

| Profile | name | phone | email | address | customer_id | invoice_id | code | card | FACTS |
|---|---|---|---|---|---|---|---|---|---|
| STORE | kept | kept | kept | kept | kept | kept | `[code]` | `[card number removed]` | unchanged |
| SONNET | kept | `[phone ending 02]` | `[email]` | `[address]` | kept | kept | `[code]` | `[card number removed]` | unchanged |
| JEV | `[name]` | `[phone]` | `[email]` | `[address]` | `[customer id]` | `[invoice id]` | `[code]` | `[card number removed]` | `{invoice_id}` → `[invoice id]`, rest unchanged |
| TRACE | `[name]` | `[phone ending 02]` | `[email]` | `[address]` | kept | kept | `[code]` | `[card number removed]` | unchanged |

`replaced` for the TEMPLATE message is exactly one per replaced kind (e.g. JEV: all eight kinds `== 1`).

### 6.3 Per-test design

- **AC-1** `test_store_masks_cards_and_codes_keeps_contact[n-sep]`: text = `f"My card is {card} and my code is {code}.
  I'm {name}, {phone}, {email}, {address}."` → exact expected with only card and code tokens; `replaced ==
  {card: 1, code: 1}`; the card's digits (`re.sub(r"\D", "", card)`) absent from the output's digits.
- **AC-2** `test_jev_masks_every_identifier`: TEMPLATE with `_seeded(11)` → exact JEV expected; plus each introduction
  form masks the name: `"this is {name}"`, `"I'm {name}"`, `"I’m {name}"` (U+2019), `"My name is {name}"`,
  `"I am {name}"` → `"<intro> [name]"`. `test_placeholders_stable_across_calls`: TEMPLATE with `_seeded(11)` and with
  `_seeded(12)` give the **same** JEV output string (different values, same tokens); calling twice on the same text
  gives equal results.
- **AC-3** `test_sonnet_masks_contact_keeps_ids`: TEMPLATE + " " + FACTS → exact SONNET expected.
- **AC-4** `test_trace_profile`: TEMPLATE + " " + FACTS → exact TRACE expected; assert `"$478.00"`, `"2026-11-01"`,
  `"8:00 am – 12:00 pm"`, `"Plus"`, `"MHC-C-0007"`, the customer ID and invoice ID all present.
- **AC-5** `test_log_profile_is_length_only`: (a) TEMPLATE message → `text == ""`, `length == len(msg)`,
  `replaced == {RedactionKind.FREE_TEXT: 1}`; no seeded value in `repr`. (b) `msg2` = 64 characters drawn by
  `random.Random(5)` from the alphabet `"QWXZJKVBNM#!?%&*"` (no character of this alphabet can appear in a repr); for
  every 2-character window `w` of `msg2`: `w not in result.text` and `w not in repr(result)`.
- **AC-6** `test_seeded_values_absent[p]`: TEMPLATE with `_seeded(11)`. `REPLACED` = the §4c matrix as a dict of sets
  (LOG = all eight). For each kind in `REPLACED[p]`: the value is not in `result.text`, `repr(result)`, `str(result)`;
  for `phone` also its first eight digits are not in `re.sub(r"\D", "", result.text)`; for `card` its 16 digits are not
  in the output digits; for `name` neither name word appears. For each kept kind: the value **is** in `result.text`.
  Exception text: `pytest.raises(rd.UnknownRedactionProfile)` around `rd.redact(msg, "no_such_profile")`; build
  `exc_text = str(e) + repr(e) + "".join(traceback.format_exception(e))`; no seeded value in it. Print one line
  `f"{p}: " + ", ".join(f"{k}={'replaced' if k in REPLACED[p] else 'kept'}" for k in KINDS)`.
- **AC-7** `test_non_private_values_survive`: text = `"Austin, TX 78620. Kyle 78640. Total $478.00, $89, $1,245.50.
  Due 2026-11-01, issued 2026-10-02, between 2026-11-01 to 2026-11-05. Slot 37, slot 4. Window 8:00 am – 12:00 pm,
  1:00 pm – 5:00 pm. Case MHC-C-0007. Plus tier. A 2 hour drive, 2 techs on the way."` → unchanged and
  `replaced == {}` for STORE, SONNET and TRACE. Phone-not-card: a phone in each of `ddd-ddd-dddd`, `(ddd) ddd-dddd`,
  `dddddddddd` (built from `_phone`) → STORE output unchanged with `replaced == {}`; SONNET output is
  `[phone ending NN]`, never `[card number removed]`.
- **AC-8** `test_idempotent[p]`: inputs = TEMPLATE (`_seeded(11)`, `_seeded(12)`), TEMPLATE + FACTS, the AC-7 text,
  the WP-2 turns; `first = redact(x, p)`, `second = redact(first.text, p)`: `second.text == first.text` and
  `all(n == 0 for n in second.replaced.values())`.
- **AC-9** `test_unknown_profile_refused_without_echo`: sentinel message = TEMPLATE with `_seeded(12)`;
  `redact(sentinel, "no_such_profile")` raises `UnknownRedactionProfile` (also `isinstance(e, ValueError)`);
  `"no_such_profile" in str(e)`; no seeded value and no 12-character slice of the sentinel in `exc_text`.
- **WP-2** `test_wp2_worked_pair[p]`: `turn1 = f"Hi, my name is Omar Patel, account MHC-10002, phone {_phone(rng, '02')}."`,
  `turn2 = f"What is INV-204411 for? I can pay now, card {_card(rng, 16, ' ')}."`, `facts` = FACTS with `INV-204411`.
  Expected: JEV `"Hi, my name is [name], account [customer id], phone [phone]."` / `"What is [invoice id] for? I can
  pay now, card [card number removed]."`; SONNET `"Hi, my name is Omar Patel, account MHC-10002, phone [phone ending 02]."`
  / `"What is INV-204411 for? I can pay now, card [card number removed]."`; TRACE `"Hi, my name is [name], account
  MHC-10002, phone [phone ending 02]."` / card removed / `facts` unchanged; STORE: turn1 unchanged, turn2 card removed;
  LOG: `text == ""` and `length == len(turn)` for each.
- `test_enum_values_are_the_contract`: `[k.value for k in rd.RedactionKind] == ["card", "code", "phone", "email",
  "address", "name", "customer_id", "invoice_id", "free_text"]`; profiles `== ["store", "sonnet", "jev", "trace",
  "log"]`; `issubclass(rd.UnknownRedactionProfile, ValueError)`.
- `test_redacted_repr_and_immutability`: JEV on TEMPLATE; `re.fullmatch(r"Redacted\(length=\d+, replaced=\{[a-z_: 0-9,]*\}\)",
  repr(r))`; `"[" not in repr(r)`; `str(r) == repr(r)`; assigning `r.text` raises `dataclasses.FrozenInstanceError`;
  `r.replaced[rd.RedactionKind.CARD] = 5` raises `TypeError`.
- `test_unknown_profile_swapped_args_not_echoed`: `rd.redact(rd.RedactionProfile.JEV, sentinel)` raises
  `UnknownRedactionProfile`; no seeded value and no 12-character slice of the sentinel in `exc_text`.
- `test_non_str_text_refused_without_echo`: `rd.redact(sentinel.encode(), rd.RedactionProfile.STORE)` and
  `rd.redact(None, …)` raise `TypeError`; message contains `"bytes"` / `"NoneType"`; no seeded value in `exc_text`.
- `test_plain_string_profile_value_accepted`: for each value string, `rd.redact(msg, value) == rd.redact(msg,
  rd.RedactionProfile(value))`.
- `test_empty_text_every_profile`: each profile → `text == ""`, `dict(replaced) == {}`, `length == 0`.
- `test_brand_greeting_not_a_name`: TRACE and JEV on `"This is Meridian Home Comfort, how can I help?"` → unchanged.
- `test_patterns_run_in_bounded_time`: inputs `"1 " * 50_000`, `"1-" * 50_000`, `"a" * 100_000 + "@"`,
  `"my name is " + "Ab " * 33_000`, `"1234 " + "Oak " * 25_000`; run all five profiles over all five inputs; total
  `time.perf_counter()` delta `< 2.0` s (the planner measured ~0.5 s for the pattern set above).

### 6.4 `tests/unit/privacy/test_redactor_alias.py` (exact shape)

```python
"""AEA-04 AC-10: `redact` satisfies `Redactor` (read by the type checker) and the alias has the documented shape."""

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meridian.privacy.redact import RedactionProfile, Redactor, redact

    _AS_REDACTOR: Redactor = redact

    def _one_arg(text: str) -> str:
        return text

    _WRONG_SHAPE: Redactor = _one_arg  # type: ignore[assignment]

    def _bind_store(fn: Redactor) -> Callable[[str], str]:
        return lambda t: fn(t, RedactionProfile.STORE).text


def test_redact_satisfies_redactor_alias() -> None:
    rd = importlib.import_module("meridian.privacy.redact")
    assert rd.Redactor == Callable[[str, rd.RedactionProfile], rd.Redacted]
    assert isinstance(rd.redact("x", rd.RedactionProfile.STORE), rd.Redacted)
```

Under `mypy --strict` (which enables `warn_unused_ignores`) the `_WRONG_SHAPE` line proves the alias **rejects** a
one-argument callable: if it did not, the ignore would be unused and mypy would fail. Verified by the planner on a
scratch copy: clean with a correct module, and an error inside `redact.py` is reported.

### 6.5 `tests/unit/test_import_direction.py::test_redact_imports_stdlib_only` (exact shape)

```python
def test_redact_imports_stdlib_only() -> None:
    """AEA-04 AC-10: privacy/redact.py imports only these stdlib modules and calls no I/O builtin."""
    path = Path(__file__).resolve().parents[2] / "src" / "meridian" / "privacy" / "redact.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import in privacy/redact.py"
            found.add(node.module or "")
    print("privacy/redact.py imports:", sorted(found))
    allowed = {"__future__", "collections.abc", "dataclasses", "enum", "re", "types", "typing"}
    assert found <= allowed, sorted(found - allowed)
    assert all(name.split(".")[0] in sys.stdlib_module_names for name in found)
    io_builtins = {"open", "print", "input", "exec", "eval", "compile", "__import__", "breakpoint"}
    called = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not called & io_builtins, sorted(called & io_builtins)
```

(`re.compile` is an attribute call, so it is not caught by the `compile` builtin check.)

---

## 7. Checks

`export UV_LINK_MODE=hardlink`. Run from the worktree root. Never copy a venv; pytest workers `-n 2` at most (this set
needs none). Cheapest first; stop at the first red.

**Which command set.** If the branch has no `pyproject.toml` (AEA-01 not merged yet), use the **fallback** set. If
`main` gains AEA-01's `pyproject.toml` before your final gate, run `git merge --no-edit main` into your branch (never
rebase a branch holding frozen tests, never push) and use the **project** set.

| Check | Fallback command (no `pyproject.toml`) | Project command (after AEA-01) | Passing looks like |
|---|---|---|---|
| Lint | `uv run --no-project --with ruff ruff check --line-length 110 src/meridian/privacy tests/unit/privacy tests/unit/test_import_direction.py` | `uv run ruff check src/meridian/privacy tests/unit/privacy tests/unit/test_import_direction.py` | `All checks passed!` |
| Format | `uv run --no-project --with ruff ruff format --check --line-length 110 <same paths>` | `uv run ruff format --check <same paths>` | `N files already formatted` |
| Type check | `MYPYPATH=src uv run --no-project --python 3.12 --with mypy mypy --strict --explicit-package-bases src/meridian/privacy/redact.py tests/unit/privacy/test_redactor_alias.py` | the checker AEA-01 configured, over the same two files (mypy: `uv run mypy src/meridian/privacy/redact.py tests/unit/privacy/test_redactor_alias.py`; pyright: `uv run pyright <same>`) | `Success: no issues found in 2 source files` (or 0 errors) |
| Affected tests (while iterating and final) | `PYTHONPATH=src uv run --no-project --python 3.12 --with pytest pytest -q -rP -p no:cacheprovider tests/unit/privacy tests/unit/test_import_direction.py::test_redact_imports_stdlib_only` | `uv run pytest -q -rP tests/unit/privacy tests/unit/test_import_direction.py::test_redact_imports_stdlib_only` | all pass; `-rP` shows the AC-6 matrix and the AC-10 import list |
| Who else is affected | `grep -rl "meridian.privacy" tests/ src/ \| grep -v "privacy/redact.py\|tests/unit/privacy"` | same | at wave 0: nothing else (AEA-02's `config.py` tests join the affected set at their merge) |
| Journeys | none: no harness before AEA-57 (`build-loop-test-scope` AEA addition) | if AEA-01's affected-journey command exists, run it on this diff | `0 journeys affected` |
| Context check | `python3 ~/.claude/skills/icm-project/scripts/check_context.py /home/linuxuser/workspaces/inno-aea-callcenter` | same | no new FAIL |
| Capture verification | n/a here: CAP-1 is AEA-51's (AC-18) | — | — |
| Evaluation check | n/a (ticket *Evaluation*: N/A) | — | — |

**Full suite:** not required. This change adds one leaf module and its own tests; it touches no shared fixture,
settings, dependency or widely imported module yet (rule `build-loop-test-scope`).

**Existing tests that must stay green:** none exist on `main` today. If the branch has merged `main` with other wave-0
tests in `tests/unit/test_import_direction.py`, the whole file must pass.

---

## 8. Risks and requests

**Requests to the orchestrator (no product decision; none blocks the build):**
1. **`tests/unit/test_import_direction.py` is shared by five wave-0 tickets** (AEA-01 AC-5/AC-7, AEA-02 AC-18,
   AEA-03 AC-9, AEA-04 AC-10, AEA-05 AC-11) and is not in the slice plan's collision map. Each adds one
   self-contained function; whichever merges second gets an add/add or end-of-file conflict. Resolve by **keeping
   every function from both sides** (a union; no function is edited), then run the whole file. Simplest: tell AEA-01's
   planner to create this file, and merge AEA-01 before AEA-04 if both are ready (R-G-18 does not order AEA-01).
2. **Package markers and tool config are AEA-01's.** This ticket relies on implicit namespace packages and the
   fallback commands until AEA-01 lands. If AEA-01's ruff settings (line length, rule set) differ from line length 110
   and the default rules, the frozen tests may need a **format- or lint-only** change after AEA-01 merges; please
   allow that diff through the tamper check (no assertion changes), or have AEA-01 adopt `line-length = 110` (the
   parked `pyproject.toml`'s value).
3. **Same-line doc edits:** the area-map A0 row (line 25) is edited by AEA-01, 02, 03 and 04; the ICM row *Routes
   verified…* may be edited by several wave-0 tickets. The merge step resolves these by applying each ticket's token
   change on the one line. AEA-04 avoids DO-3's header status line (AEA-08's) and edits only its own §3 tree line.
4. **Issue comment:** post the plan-added criteria (§3c rows marked plan-added) on issue #4 at merge, as the template
   asks.
5. **Router line** `.claude/README.md` "No backend code exists yet" becomes stale once any backend file merges; it is
   not in this ticket's owned files (AEA-01 or the wave-end context pass should update it).

**Known limits (accepted; written into DO-6 by step I-10 for names):**
- Names: introduction patterns only (DAT-1 A). "Omar here", "my mother Jane", lowercase names and a first name after
  "I'm" that is followed by a capitalised non-name ("I'm Locked out" → `I'm [name] out`) are mis-handled; over-masking
  in JEV/TRACE is the accepted direction.
- Street lines with a lowercase full-word suffix ("1234 oak hollow drive") are not caught; abbreviated suffixes in any
  case are.
- Seven-digit local phone numbers and phones with extensions are not phones.
- A six-digit number typed without its `INV-` prefix ("invoice 204411") is masked as `[code]` in every text-keeping
  profile; the code rule wins (DO-6: codes never raw in any record).
- Two digit groups touching with one separator and totalling 13–19 digits (a phone directly followed by a ZIP, two ISO
  dates separated by one space) are masked as a card; "2026-11-01 to 2026-11-05" is not.

**Spec notes (no change needed):**
- DO-1 §10 says traces get "the same set as Jev"; data.md §1 and the DO-6 table keep customer and invoice IDs in
  traces. The signed addendum wins (stage7 addenda win over DO-4/DO-1 sketches); AC-4 tests it.
- DO-4 §5's comment "card-like numbers and codes masked" is stale; AEA-08 fixes it (not this ticket).
- `safe-validation-errors` rule 1 says an error never names the value; data.md §1 says the message names the profile
  value. Step I-3 satisfies both: it names the value only when it has the shape of a profile name (`[a-z_]{1,16}`).

**Merge-order note:** AEA-02 imports `RedactionProfile` from this file, so the five public type names and the enum
values are frozen once this merges. Renaming anything later is a cross-ticket change.

---

## 9. Readiness

**READY.** No product decision is open (DAT-1 decided A via stage7-signoff D-14; DAT-5 settled by source; DAT-28 and
MC-23 engineering, signed in data.md §1). No signed contract changes. No blocker: the module imports nothing from
another ticket.

**Gates:** none human, external, paid or live. `risk::security`: frozen tests first (Phase T) and
`security-privacy-agent` reads this diff at the wave-0 merge.
