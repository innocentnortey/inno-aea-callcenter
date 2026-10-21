# Plan — [AEA-13] policy: booking rules

**Status:** READY (2026-10-21). Innocent chose option A of section 9 ("go with your recommendation"); the four fee sentences are
provisional wording pending the UX session. As an exception to AEA-03's ownership, the implementer for AEA-13 adds them to
`policy/texts.py`, its fixture and `test_texts.py` itself (booking group 16, total 75), so the R-1 follow-up ticket is not needed.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/13 (body = `docs/plans/tickets/AEA-13.md`)
**Base revision:** `main` at `9c3e7e7`, when this was planned. The implementer branches from `main` after the merges above.
**Lane / risk:** `lane::build-loop`, no `risk::security`. This is plan → implement (code and the tests named here) →
affected tests → `code-review-agent`. There is no test-writer and no security pass (`.claude/rules/build-loop-test-scope.md`).
**Worktree / branch:** `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-13`, branch `aea-13-booking-rules`.
**Planned by:** `claude-opus-5-5` (fanout-planner), 2026-10-21.

---

## 1. Goal and sources

**Goal** (from the issue's *What to build*): `src/meridian/policy/booking.py` is the pure rule table that the scheduling
service and its executors (AEA-28) apply. It does four jobs:

1. It maps a city or ZIP to a zone (`zone_for`).
2. It counts hours from the injected demo clock to the start of a window (`hours_before`).
3. It decides whether a change carries the $49 fee (`fee_bearing`).
4. It quotes the visit fee for a service type and membership tier (`fee_note`). It also holds the one table of scheduled
   fee amounts (`SCHEDULE_FEES`, `MEMBER_ALLOWANCE_ROWS`) and the not-served lists (`NOT_SERVED_CITIES`, `LAKEWAY_ZIPS`).

The module does no I/O and reads no clock. It types no customer wording: every sentence comes from `policy/texts.py`.

**Worked pairs this slice must reproduce** (the WP-N pair):

| Pair | Input | Expected |
|---|---|---|
| WP-4 | MHC-57204, Austin, not a member, tune-up today `12:00-16:00`, clock Fri 2026-10-16 10:00 America/Chicago | `zone_for("Austin") == "central"`; `hours_before(...) == 2.0`; `fee_bearing(2.0) is True` (the AI must not move it; R-21) |
| WP-4F | Same customer, visit on 2026-10-22 `08:00-12:00`, same clock | `hours_before(...) == 142.0`; `fee_bearing(142.0) is False` |
| WP-3 | MHC-10001 Linda Foster, Round Rock, `standard` member, `hvac_repair` | `zone_for("Round Rock") == "north"`; `fee_note("hvac_repair", "standard")` is waived: `amount_cents == 0`, `waived is True`. The transcript agent's $89 quote is not repeated |

**Sources checked** (each was opened while planning):

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-13.md` | AC-1…AC-15, scope boundary, blockers 02 and 03 |
| Slice plan | `docs/plans/slice-plan.md` §1 wave-1 row AEA-13; §2 edges `AEA-03 → 13`, `AEA-13 → 27`; §3 collision map | Owns only `policy/booking.py`; `policy/texts.py` and `domain/*` are frozen after wave 0, so a missing sentence is a small follow-up merged first |
| Component contract (wins over DO-4) | `docs/design/contracts/stage7/cases.md` §2 | `Zone`, `FeeNote` (six fields), `LAKEWAY_ZIPS`, `NOT_SERVED_CITIES`, the four function signatures, `fee_bearing` body, the fee row for each service type, and the `line` rule |
| Component contract | `docs/design/contracts/stage7/graph-tools.md` §4 | `SCHEDULE_FEES` literal (three rows) and `MEMBER_ALLOWANCE_ROWS`, copied below |
| Component contract | `docs/design/contracts/stage7/data.md` §2 | `render(text_id, /, **values: str)`, the `amount` placeholder, `format_usd(cents)`. An extra or missing placeholder raises `TextRenderError` |
| Component contract | `docs/design/contracts/internal-components.md` §0 (`MeridianModel`), §5 (`ChangeRequestDraft.hours_before`, `ConfirmationView.fee_note`), §13 (`Clock.now()` is tz-aware America/Chicago) | The demo clock is always aware; this module never reads a clock |
| Code design | `docs/design/code-design.md` §2.1 (the pure core imports nothing that does I/O), §3 (tree row `policy/booking.py`, A5, wave 1), §4.1 row `policy/booking.py`, §6 S-3, §9 (tests mirror `src/`) | Module boundary and dependency direction: `policy/booking.py` → `domain/` and `policy/texts.py` only |
| Decisions | `docs/plans/7b-decisions/cases.md` CAS-6, 7, 8, 34; `residuals-graph.md` R-G-2, R-G-3, R-G-7; `residuals-web.md` R-W-7; `docs/plans/stage7-signoff.md` D-4…D-15 (none touches this module) | As cited per requirement below |
| Requirements | `docs/prd/inno-aea-callcenter-prd.md` R-3, R-14, R-18, R-20, R-21, R-22, R-23 | R-20: "diagnostic $89 waived for members; tune-up $129 or included" |
| Issued data (read only) | `scheduling_db/SCHEMA.md` (zone map, windows); KB `policies/service_area.md`, `membership/comfort_club_overview.md`, `services/service_catalog.md`, `faq/customer_faq.md`, `faq/faq_old_copy.md` (holds the excluded `$79`) | Zone and ZIP lists; fee wording sources for §9 |
| Rules | `.claude/rules/integrated-journeys.md` §3 rule 1, §4; `build-loop-test-scope.md` (with its AEA addition); `context-maintenance.md` | AC-14 record at level `mock-tested`; AC-15 context rows |
| AEA-03 plan | `docs/plans/fanout/2026-10-21-build/AEA-03.md` §8b U-1; branch `aea-03-fixed-customer-texts` (`2689582`) `src/meridian/policy/texts.py` | Only **one** booking fee text exists: `TextId.FEE_STANDARD_DIAGNOSTIC = "booking.fee_standard_diagnostic"` → `"Standard diagnostic fee: {amount}"`. The tune-up, waived and estimate texts were reported to the UX session and are not written. **This is the open decision** |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` E-7, E-1 (WP-3, WP-4, WP-4F) | Measured at Stage 9, not here |
| Observability (DO-6) | n/a | The module has no entry point and writes no record of its own; AEA-28's transaction records the decisions (issue *Observability*) |
| Metrics (DO-7) | M-9, M-21 | They stay computable from AEA-28's rows; nothing to emit here |

---

## 2. Boundary

**Owned files (the only files the implementer creates or edits):**

| File | Create / modify | Change |
|---|---|---|
| `src/meridian/policy/booking.py` | **create** | The whole module (§5 steps 1–6) |
| `tests/unit/policy/test_booking.py` | **create** | The 13 AC tests and 6 plan-added tests in §7 |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-13.md` | **create** | AC-14 record. The date is the run day in America/Chicago |
| `.claude/reference/area-map.md` | modify: **only** the A5 row's *Status* cell | AC-15 |
| `.claude/state/icm-progress.md` | modify: **only** the row *Routes verified against code and tests* | AC-15 |
| `docs/design/code-design.md` | modify: **add one line** under the §3 heading's *Built:* line(s) | AC-15 |

**Shared surfaces, read only. Never edit these:**
- `src/meridian/policy/texts.py`, `tests/unit/policy/test_texts.py`, `tests/unit/policy/texts_source_fixture.json` (AEA-03 and its follow-up).
- `src/meridian/domain/*` (AEA-02).
- `src/meridian/policy/__init__.py`, `tests/unit/policy/__init__.py`, `tests/unit/test_import_direction.py`, `tests/conftest.py`, `pyproject.toml`, `uv.lock`, `tests/journeys/**` (AEA-01).

**Owned by other tickets. Do not touch:**
- `services/scheduling.py`, `agent/tools/scheduling.py`, `adapters/sqlite/repos_booking.py`, `schema/50_booking.sql` (AEA-28 and AEA-10).
- `agent/tools/account.py` (AEA-27).
- `policy/handoff.py` and `policy/escalation.py` (AEA-14).

**Never edit:**
- The briefing, `docs/data/issued/**`, `docs/archive/`, `docs/parked/`.
- `docs/ux/**`, `apps/web/**`, `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`.

**Module boundary and dependency direction** (DO-3 §2.1, rule `code-design-solid-modularity`):
- `policy/booking.py` belongs to the pure core.
- It imports only the standard library, `meridian.domain.*` (the types) and `meridian.policy.texts` (`TextId`, `render`,
  `format_usd`).
- Callers are `services/scheduling.py`, `agent/tools/scheduling.py` (AEA-28) and `agent/tools/account.py` (AEA-27). Calls
  only flow inward to this module.
- No new interface or abstraction is introduced.

**Entry-point registration:** None. These are pure functions with no route, job or command.

---

## 3. Requirements table

Each AC from the issue, word for word in substance, with how this plan builds it and how it is checked. Every test is in
`tests/unit/policy/test_booking.py`.

| ID | Requirement | How implemented (§5 step) | Verified by |
|---|---|---|---|
| AC-1 [invariant] | `zone_for` maps every city in `SCHEMA.md`'s zone map to its zone and returns only the three `Zone` values | Step 2 `_CITY_ZONES` | `::test_city_to_zone_schema_map`: one assertion per city (9), and every result is in `{"north","central","south"}` |
| AC-2 [invariant] | Every ZIP group in `service_area.md` maps to its city's zone, and any 787xx ZIP maps to `central` unless it is in `LAKEWAY_ZIPS` | Step 2 `_SERVICE_AREA_ZIPS`, derived `_ZIP_ZONES`, the `787` rule | `::test_zip_groups_to_zone`: one assertion per listed ZIP (15), plus 78701, 78745, 78799 → central |
| AC-3 [invariant] | Dripping Springs, 78620, Manor and 78653 → `central` (Q-3) | Step 2 | `::test_new_april_2026_areas_central`: four assertions |
| AC-4 [failure/refusal] | San Marcos, Bastrop, Elgin, Lakeway, 78734, 78738, and a city or ZIP in no list → `None` | Step 2 | `::test_not_served_areas`: each returns `None` (also `"Houston"`, `"77002"`, `"78701x"`) |
| AC-5 [invariant] | `hours_before` uses the injected time, never the server clock: WP-4 → 2.0; a window that started an hour ago → −1.0 | Step 3 | `::test_wp4_two_hours_before`: 2.0 and −1.0, with the module's `datetime` and `date` patched to report 2030 and to record any call. Zero calls recorded |
| AC-6 [invariant] | `fee_bearing` is True at 2.0 and at −1.0, False for WP-4F (142.0), and False at exactly 24.0 | Step 4 | `::test_fee_bearing_boundary`: four values, plus 24.0 reached through `hours_before` |
| AC-7 [invariant] | `fee_note` returns cases §2's `FeeNote`. `hvac_repair` and `plumbing` use the `"Diagnostic visit"` row: 8900 for `none`, 0 and waived for `standard` and `plus` (WP-3). The non-member line is "Standard diagnostic fee: $89". `estimate` has `fee_row` None and 0 | Step 5 | `::test_fee_note_by_tier`: all six fields for every service type × tier |
| AC-8 [invariant] | `SCHEDULE_FEES` holds the three rows; `MEMBER_ALLOWANCE_ROWS == frozenset({"Seasonal tune-up"})`; every `FeeNote.amount_cents == SCHEDULE_FEES[fee_row][tier]`; no second 89 or 129 literal | Step 1 | `::test_schedule_fees_single_source`: rows equal; AST scan finds the int `8900` once and `12900` once, and no `89`, `129`, `49`, `79`, `4900`, `7900` |
| AC-9 [negative] | No fee line, for any tier or service, contains "charged", a waived late-change fee, or the old-FAQ $79 | Step 5 (texts only) | `::test_fee_note_never_charged_or_waived`: scan over all 12 combinations |
| AC-10 [negative] | An unknown ZIP or city returns `None`, raises nothing, and is never logged | Step 2 (no logging import at all) | `::test_unknown_location_not_logged`: `None`; the value is absent from `caplog.text` at DEBUG |
| AC-11 [invariant] | The module is pure: no I/O, no clock read, no import of `services/`, `agent/` or adapters; every `line` comes from `render` | Steps 1–5 import list | `::test_booking_module_is_pure`: AST import allow-list; source scan for clock and I/O calls; a spy on `render` is called once per `fee_note` call |
| AC-12 [invariant] | Tune-up: `none` → `"Seasonal tune-up"`, 12900, not waived; `standard`/`plus` → 0 and waived. Estimate → `fee_row=None`, 0, not waived, for every tier | Step 5 | `::test_fee_note_tune_up_and_estimate` |
| AC-13 [invariant] | Every fee line is `render(<fee TextId>, amount=format_usd(amount_cents))`. A waived row renders the waived text with `amount=format_usd(SCHEDULE_FEES[fee_row]["none"])`. No dollar literal in `booking.py` | Step 5 | `::test_fee_line_rendered_with_format_usd`: spies on `render` and `format_usd` (table in §5 step 5); regex `\$[0-9]` over the source finds nothing |
| AC-14 [journey] | Runs no journey yet. The record states level `mock-tested`, *Blocked by* AEA-57, and names J-3 and J-4. The affected-journeys command prints "0 journeys affected" | Step 8 | The record's fields; output of `uv run python -m tests.journeys.affected --base main` |
| AC-15 [regression/context] | The area map A5 row, the ICM row and DO-3 §3 status are updated in the same change | Step 9 | `git diff --name-only main...HEAD` lists the three files |
| WP-3/WP-4/WP-4F (plan-added, the worked pair) | The issue's example pair end to end through the public functions | Steps 2–5 | `::test_worked_pairs_wp3_wp4` |
| S-1 (plan-added) | Input normalisation: case, spacing, a trailing ", TX"/"Texas", ZIP+4. Over-long or non-`str` input → `None` | Step 2 | `::test_zone_for_normalises_input` |
| S-2 (plan-added) | `hours_before` refuses a naive `now` and a malformed window, with no value in the message | Step 3 | `::test_hours_before_rejects_naive_now_and_bad_window` |
| S-3 (plan-added) | Real elapsed hours across time zones and the 2026-11-01 DST change | Step 3 | `::test_hours_before_is_timezone_safe` |
| S-4 (plan-added) | Every issued customer's ZIP and city give the same served zone (data check on `customers.csv`, read only) | Step 2 | `::test_issued_customers_city_and_zip_agree` |
| S-5 (plan-added) | `fee_note` refuses an unknown service type or tier with a `ValueError` that holds no value | Step 5 | `::test_fee_note_rejects_unknown_service_or_tier` |

**Source-contract reconciliation** (anything the issue left implicit):

| Obligation | Source | Disposition |
|---|---|---|
| Fee lines for tune-up (`none`), member waived (diagnostic), member included (tune-up), estimate | cases §2 `line`; AEA-03 §8b U-1 | **needs-decision** (§9). The texts must exist in `policy/texts.py` before the build. Requested as an AEA-03 follow-up (§8 R-1) |
| Estimate line rendered **without** `amount` | data.md §2 (`render` raises on an extra placeholder); cases §2 (estimate has `fee_row=None`, so there is no scheduled amount) | **Decided here, engineering.** `render(TextId.FEE_ESTIMATE_FREE)` takes no kwargs. AC-13's evidence list ($89, $129) covers only the rows that have a fee |
| `"After-hours dispatch"` row has no `ServiceType` | graph-tools §4 (AEA-27 reads it) | In table, never chosen by `fee_note` |
| `hours_before` with a naive `now` | DO-4 §13 `Clock.now()` aware; data.md §8a `FixedClock` rejects naive | **Added:** `ValueError` (S-2) |
| Elapsed (absolute) hours, not wall-clock difference | fee schedule "<24h" | **Added:** aware subtraction (S-3) |
| `window_start` for `ChangeRequestDraft` | DO-4 §5 | other-ticket: AEA-28 computes it. This module keeps a **private** `_window_start` helper (cases.md preamble: private helpers allowed) |
| Slot status, member slots, booking cap, service-type match | issue scope | other-ticket: AEA-28 |

---

## 4. Shared code to use

Copy these names exactly.

**From AEA-02 (`domain/`).**
- `Zone` and `FeeNote` live in `meridian.domain.records` (AEA-02 ticket, file table).
- `ServiceType` and `Window` exist as names, but no contract fixes which module holds them. Find them with step 0.

```python
Zone = Literal["north", "central", "south"]

class FeeNote(MeridianModel):          # extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True
    service_type: ServiceType
    tier: Literal["none", "standard", "plus"]
    fee_row: str | None
    amount_cents: int = Field(ge=0)
    waived: bool
    line: str = Field(min_length=1, max_length=120)

# ServiceType values (SCHEMA.md): "hvac_repair", "hvac_tune_up", "plumbing", "estimate"
# Window values (SCHEMA.md):      "08:00-12:00", "12:00-16:00", "13:00-17:00", "16:00-19:00"
```

**From AEA-03 (`meridian.policy.texts`)**, as built on `aea-03-fixed-customer-texts` (`2689582`):

```python
class TextId(StrEnum): ...             # values "<group>.<name>"
def render(text_id: TextId, /, **values: str) -> str: ...
    # unknown id, missing placeholder, extra placeholder, non-str value → TextRenderError (names only)
def format_usd(cents: int) -> str: ... # 8900 → "$89", 12900 → "$129", 1250 → "$12.50"; negative → ValueError
TextId.FEE_STANDARD_DIAGNOSTIC         # "booking.fee_standard_diagnostic" → "Standard diagnostic fee: {amount}"  (exists)
```

**From the AEA-03 follow-up** (§8 R-1; names fixed here, wording is the §9 decision):

| `TextId` member | Value | Placeholders |
|---|---|---|
| `FEE_DIAGNOSTIC_WAIVED` | `"booking.fee_diagnostic_waived"` | `amount` |
| `FEE_TUNE_UP` | `"booking.fee_tune_up"` | `amount` |
| `FEE_TUNE_UP_INCLUDED` | `"booking.fee_tune_up_included"` | `amount` |
| `FEE_ESTIMATE_FREE` | `"booking.fee_estimate_free"` | none |

The tests never hard-code the new wording. They compare `line` with `render(...)` of the same id. So a later UX rewording
of these four sentences changes nothing in this ticket. The only literal sentence asserted is the signed OpenAPI example
`"Standard diagnostic fee: $89"`.

**This module produces** (public names; consumers AEA-27, AEA-28, AEA-14, AEA-29), copied from cases §2 and graph-tools §4:

```python
LAKEWAY_ZIPS: frozenset[str] = frozenset({"78734", "78738"})
NOT_SERVED_CITIES = frozenset({"San Marcos", "Bastrop", "Elgin", "Lakeway"})
SCHEDULE_FEES: Mapping[str, Mapping[Literal["none", "standard", "plus"], int]]   # literal in §5 step 1
MEMBER_ALLOWANCE_ROWS: frozenset[str] = frozenset({"Seasonal tune-up"})

def zone_for(city_or_zip: str) -> Zone | None: ...
def hours_before(now: datetime, slot_date: date, window: Window) -> float: ...
def fee_bearing(hours: float) -> bool: return hours < 24.0
def fee_note(service_type: ServiceType, tier: Literal["none", "standard", "plus"]) -> FeeNote: ...
```

Set `__all__` to exactly these eight names, sorted:
`["LAKEWAY_ZIPS", "MEMBER_ALLOWANCE_ROWS", "NOT_SERVED_CITIES", "SCHEDULE_FEES", "fee_bearing", "fee_note", "hours_before", "zone_for"]`.

---

## 5. Steps

**Step 0 — Preconditions (check, don't fix).**

On the worktree branch, run:

```bash
grep -n "FEE_DIAGNOSTIC_WAIVED\|FEE_TUNE_UP\b\|FEE_TUNE_UP_INCLUDED\|FEE_ESTIMATE_FREE\|FEE_STANDARD_DIAGNOSTIC" src/meridian/policy/texts.py
grep -n "^Zone\b\|^class FeeNote\|^ServiceType\b\|^Window\b" src/meridian/domain/*.py
test -f pyproject.toml && test -f tests/unit/policy/__init__.py && test -f tests/journeys/affected.py
```

- All five `TextId` members must exist.
- `Zone`, `FeeNote`, `ServiceType` and `Window` must each be found. Import each from the module where grep found it.
- The three files must exist.

If anything is missing, **stop and report `blocked-on`** (AEA-01, AEA-02, AEA-03 or the texts follow-up). Do not create a
stand-in. Run `export UV_LINK_MODE=hardlink` and then `uv sync`. Never copy a venv.

**Step 1 — Module header, imports, fee table.**

Create `src/meridian/policy/booking.py`.

1. Write a docstring. It says the module is pure (DO-3 §2.1), lists its sources (SCHEMA.md, service_area.md, the 2026 fee
   schedule) and its consumers. **No dollar sign followed by a digit and no 8900/12900/14900 in any comment or docstring.**
2. Imports, and only these:
   - `from __future__ import annotations`
   - `import re`
   - `from collections.abc import Mapping`
   - `from datetime import date, datetime, time`
   - `from types import MappingProxyType`
   - `from typing import Final, Literal`
   - `from zoneinfo import ZoneInfo`
   - The domain names from step 0.
   - `from meridian.policy.texts import TextId, format_usd, render`

   Import the names as written: the tests patch `meridian.policy.booking.render`, `.format_usd`, `.datetime` and `.date`.
3. Copy the fee table from graph-tools §4, values unchanged, wrapped read-only:
   ```python
   SCHEDULE_FEES: Final[Mapping[str, Mapping[Literal["none", "standard", "plus"], int]]] = MappingProxyType({
       "Diagnostic visit": MappingProxyType({"none": 8900, "standard": 0, "plus": 0}),
       "After-hours dispatch": MappingProxyType({"none": 14900, "standard": 0, "plus": 0}),
       "Seasonal tune-up": MappingProxyType({"none": 12900, "standard": 0, "plus": 0}),
   })
   MEMBER_ALLOWANCE_ROWS: Final[frozenset[str]] = frozenset({"Seasonal tune-up"})
   ```
   Each of 8900, 12900 and 14900 appears exactly once in the file. *Invariant: one owner for every scheduled amount (C-3, AC-8).*
4. Add private constants:
   - `_CHICAGO: Final = ZoneInfo("America/Chicago")`
   - `_TIERS: Final[frozenset[str]] = frozenset({"none", "standard", "plus"})`

**Step 2 — `zone_for` and its tables.**

1. Constants. Keys are lower-case city names.
   ```python
   _CITY_ZONES: Final[Mapping[str, Zone]] = MappingProxyType({
       # SCHEMA.md "Zone mapping (city → zone)"
       "round rock": "north", "cedar park": "north", "pflugerville": "north",
       "georgetown": "north", "leander": "north", "hutto": "north",
       "austin": "central", "kyle": "south", "buda": "south",
       # Q-3 (Innocent 2026-10-20): newly served April 2026, configured here, never an edit to SCHEMA.md
       "dripping springs": "central", "manor": "central",
   })
   _SERVICE_AREA_ZIPS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
       # KB policies/service_area.md (updated 2026-04-01); each group keyed by a city in _CITY_ZONES
       "round rock": ("78664", "78665", "78681"),
       "cedar park": ("78613", "78641", "78645"),      # "Cedar Park / Leander" (both north)
       "pflugerville": ("78660", "78634"),             # "Pflugerville / Hutto" (both north)
       "georgetown": ("78626", "78628", "78633"),
       "kyle": ("78640", "78610"),                     # "Kyle / Buda" (both south)
       "dripping springs": ("78620",),
       "manor": ("78653",),
   })
   _ZIP_ZONES: Final[Mapping[str, Zone]] = MappingProxyType(
       {z: _CITY_ZONES[city] for city, zips in _SERVICE_AREA_ZIPS.items() for z in zips})
   _AUSTIN_ZIP_PREFIX: Final = "787"                  # service_area.md "Austin: 787xx (all)"
   _NOT_SERVED_KEYS: Final[frozenset[str]] = frozenset(c.casefold() for c in NOT_SERVED_CITIES)
   _ZIP_RE: Final = re.compile(r"(\d{5})(?:-\d{4})?")
   _STATE_SUFFIX_RE: Final = re.compile(r"(.*?)(?:,\s*|\s+)(?:tx|texas)")   # used with fullmatch only
   _MAX_LOCATION_CHARS: Final = 64
   ```
   Define `LAKEWAY_ZIPS` and `NOT_SERVED_CITIES` exactly as in §4, each with its source comment from cases §2 (CAS-8 `[A]`;
   `[Source: KB policies/service_area.md]`).
2. Body of `zone_for(city_or_zip)`, in this order:
   1. If the input is not a `str`, return `None`. *(No exception: AC-10.)*
   2. `text = " ".join(city_or_zip.split())`. If `text == ""` or `len(text) > _MAX_LOCATION_CHARS`, return `None`.
      *(This bounds the work done on untrusted input.)*
   3. `m = _ZIP_RE.fullmatch(text)`. If it matches, let `zip5 = m.group(1)`. Then:
      - if `zip5 in LAKEWAY_ZIPS`, return `None`. *(The specific exclusion wins over 787xx: CAS-8.)*
      - if `zip5 in _ZIP_ZONES`, return its zone;
      - if `zip5.startswith(_AUSTIN_ZIP_PREFIX)`, return `"central"`;
      - otherwise return `None`.
   4. Otherwise it is a city:
      - `key = text.casefold()`;
      - `s = _STATE_SUFFIX_RE.fullmatch(key)`; if it matches, `key = s.group(1)`. Then `key = key.strip(" ,")`;
      - if `key in _NOT_SERVED_KEYS`, return `None`;
      - otherwise return `_CITY_ZONES.get(key)`. That is `None` when the city is in no list.
   5. **Never log, never raise, never put the input into any value or message.** Import no `logging`.

**Step 3 — `hours_before`.**

1. Private constant: `_WINDOW_RE: Final = re.compile(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})")`.
2. Private helper `_window_start(slot_date: date, window: str) -> datetime`:
   - `m = _WINDOW_RE.fullmatch(window)`. If there is no match, `raise ValueError("hours_before: window must look like HH:MM-HH:MM")`.
   - Return `datetime.combine(slot_date, time(int(m.group(1)), int(m.group(2))), tzinfo=_CHICAGO)`.
   - `time()` raises `ValueError` itself for an hour above 23. Let it propagate.
3. Body of `hours_before(now, slot_date, window)`:
   1. If `now.tzinfo is None or now.utcoffset() is None`, `raise ValueError("hours_before: now must be timezone-aware (the demo clock)")`.
      *Invariant: R-3, the demo clock is always aware; a naive value would mean somebody passed a server reading.*
   2. `start = _window_start(slot_date, window)`.
   3. `return (start - now).total_seconds() / 3600.0`. This is negative once the window has started.
      *Aware subtraction gives real elapsed hours across DST.*
4. No call to `datetime.now`, `datetime.today`, `datetime.utcnow`, `date.today` or `time.time` anywhere in the module.

**Step 4 — `fee_bearing`.** The body is exactly `return hours < 24.0`, with the source comment from cases §2 (fee schedule
"Late cancellation (<24h)"; CAS-6: exactly 24.0 → free; started or past → fee-bearing). Add no NaN guard and no other branch.

**Step 5 — `fee_note`.**

1. Private constants:
   ```python
   _FEE_ROW_FOR: Final[Mapping[str, str | None]] = MappingProxyType({
       "hvac_repair": "Diagnostic visit",       # CAS-7 / fee schedule "Diagnostic visit"
       "plumbing": "Diagnostic visit",          # CAS-7: no service restriction on the diagnostic row
       "hvac_tune_up": "Seasonal tune-up",      # R-G-3
       "estimate": None,                        # services/service_catalog.md "Free in-home estimate"
   })
   _PAY_TEXT: Final[Mapping[str, TextId]] = MappingProxyType({
       "Diagnostic visit": TextId.FEE_STANDARD_DIAGNOSTIC,
       "Seasonal tune-up": TextId.FEE_TUNE_UP,
   })
   _WAIVED_TEXT: Final[Mapping[str, TextId]] = MappingProxyType({
       "Diagnostic visit": TextId.FEE_DIAGNOSTIC_WAIVED,
       "Seasonal tune-up": TextId.FEE_TUNE_UP_INCLUDED,
   })
   ```
2. Body of `fee_note(service_type, tier)`:
   1. If `service_type not in _FEE_ROW_FOR`: `raise ValueError("fee_note: unknown service type")`. If `tier not in _TIERS`:
      `raise ValueError("fee_note: unknown tier")`. *Neither message holds the value.*
   2. `fee_row = _FEE_ROW_FOR[service_type]`.
   3. If `fee_row is None`, return `FeeNote(service_type=service_type, tier=tier, fee_row=None, amount_cents=0, waived=False, line=render(TextId.FEE_ESTIMATE_FREE))`.
   4. Otherwise:
      - `amount = SCHEDULE_FEES[fee_row][tier]`;
      - `waived = amount == 0`.
   5. If `waived`: `line = render(_WAIVED_TEXT[fee_row], amount=format_usd(SCHEDULE_FEES[fee_row]["none"]))`.
      Otherwise: `line = render(_PAY_TEXT[fee_row], amount=format_usd(amount))`.
   6. Return `FeeNote(service_type=service_type, tier=tier, fee_row=fee_row, amount_cents=amount, waived=waived, line=line)`.
   7. Invariants:
      - `tier` is the **verified** customer's tier. The caller passes `"none"` when unverified (R-14). This function does not check verification.
      - No waiver or discount of any kind beyond the tier column (D3 = DEC-2).
      - The late-change $49 is never handled here.
3. The expected `render` calls, which `test_fee_line_rendered_with_format_usd` asserts:

   | service_type | tier | `TextId` | `amount` kwarg | `format_usd` called with |
   |---|---|---|---|---|
   | `hvac_repair`, `plumbing` | `none` | `FEE_STANDARD_DIAGNOSTIC` | `"$89"` | `8900` |
   | `hvac_repair`, `plumbing` | `standard`, `plus` | `FEE_DIAGNOSTIC_WAIVED` | `"$89"` | `8900` |
   | `hvac_tune_up` | `none` | `FEE_TUNE_UP` | `"$129"` | `12900` |
   | `hvac_tune_up` | `standard`, `plus` | `FEE_TUNE_UP_INCLUDED` | `"$129"` | `12900` |
   | `estimate` | any | `FEE_ESTIMATE_FREE` | *(no kwargs)* | not called |

**Step 6 — Fast gates on the module alone.** Run:

```bash
uv run ruff format src/meridian/policy/booking.py
uv run ruff check src/meridian/policy/booking.py
uv run mypy src/meridian/policy/booking.py
```

mypy runs in strict mode with the pydantic plugin (AEA-01 `pyproject.toml`).

**Step 7 — Tests.**

Write `tests/unit/policy/test_booking.py` per §7, then run it. Test-file conventions:
- `from meridian.policy import booking` and `from meridian.policy.booking import ...`;
- `from meridian.policy.texts import TextId, render, format_usd`;
- `CHI = ZoneInfo("America/Chicago")`;
- `NOW = datetime(2026, 10, 16, 10, 0, tzinfo=CHI)`. This is the same instant as `WORKED_PAIRS_NOW`. Do **not** import `tests/fakes` (AEA-11 owns it and may not be merged).

**Step 8 — Journey record (AC-14).**

Run `uv run python -m tests.journeys.affected --base main` and copy its output. Create
`docs/testing/journeys/<YYYY-MM-DD>-AEA-13.md` in the format of `2026-10-21-AEA-03.md`: a two-column table with these fields.

| Field | Value |
|---|---|
| Claim | "AEA-13: `policy/booking.py` maps city/ZIP to zone (Q-3, CAS-8), counts hours to a window on the injected clock, applies the 24-hour rule (CAS-6), and quotes the fee by tier from one table. No journey runs: wave 1 precedes AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1). Journeys that will exercise this code once AEA-51 lands: **J-3** (zones and windows; WP-3, WP-4F) and **J-4** (the 24-hour rule and fee; WP-4)" |
| Level | `mock-tested` |
| Tested revision | The feat commit SHA (branch `aea-13-booking-rules`) |
| Environment | VPS worktree `inno-aea-callcenter-wt/AEA-13`; `uv run`; no server, no DB, no model |
| Command | The exact pytest, ruff, mypy and affected-journeys commands from §7 |
| Result | `N passed`; ruff clean; mypy clean; affected command output quoted (`0 journeys affected`) |
| Evidence location | The implementer's report |
| Remaining limitations | No integrated path ran. AEA-28 (the caller) is not built. The four fee sentences from the follow-up carry the wording Innocent approved (§9), and UX-5 may reword them |
| Blocked by | AEA-57 (journey harness); J-3 and J-4 turn steps also wait on AEA-51 |

**Step 9 — Context (AC-15).** Make three edits, each confined to its own row or line.

1. `.claude/reference/area-map.md`, row `| 1 | **A5 Scheduling** | …`: change the last cell from `planned` to
   ``planned; `policy/booking.py` actual (AEA-13, `<feat sha>`)``.
2. `.claude/state/icm-progress.md`, row `Routes verified against code and tests`:
   - set status to `provisional` if it is still `pending`;
   - replace the evidence cell with ``<date>: area map A5 → `policy/booking.py` checked against `tests/unit/policy/test_booking.py` (AEA-13, `<feat sha>`; N pass)``;
   - keep the next-step cell as ``Each slice adds its route; verified when every area-map row is actual``.
   - The row stays at most 400 characters.
3. `docs/design/code-design.md` §3: under the existing `**Built:** …` line or lines (add the first one after the sentence
   "Owner area and wave in the right-hand columns (§8). …" if none exists), add a new line
   ``**Built:** `policy/booking.py` (AEA-13, `<feat sha>`).`` Do not touch the tree block.

**Step 10 — Commits.** Make two commits on `aea-13-booking-rules`. Use explicit `git add <paths>`, never `-A`.

1. `feat(policy): booking rules — zones, 24-hour rule, fee by tier (AEA-13)`, with `src/meridian/policy/booking.py` and
   `tests/unit/policy/test_booking.py`.
2. `docs(context): AEA-13 booking rules built; journey record mock-tested`, with the record and the three context files
   (SHA from commit 1).

The last line of each message is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push and do not merge.

---

## 6. Data and fixtures

- **Values come from issued or synthetic data only.**
  - Customer ids, cities and windows come from `docs/data/worked-pairs.md` (WP-3, WP-4, WP-4F) and issued `SCHEMA.md`.
  - The distinctive unknown location for AC-10 is the synthetic string `"Zyxwvut Hollow QX"`.
  - There are no names, phones, emails, codes or card-like numbers in the test file or its output.
- **`test_issued_customers_city_and_zip_agree`** reads the issued CSV
  `docs/data/issued/meridian_dataset/scheduling_db/customers.csv` **read-only**: `open(path, newline="", encoding="utf-8")`
  with `csv.DictReader`, using only the `city` and `zip` columns.
  - Path: `Path(__file__).resolve().parents[3] / "docs/data/issued/meridian_dataset/scheduling_db/customers.csv"`.
  - Expected today: 154 rows, nine cities, ZIPs 78745, 78610, 78613, 78626, 78634, 78640, 78641, 78660, 78664. Every row
    has `zone_for(zip) == zone_for(city)` and the zone is not `None`.
  - The test prints nothing and puts no row values in assertion messages. Use `assert mismatches == 0`, where
    `mismatches` is a count.
- No new fixture files. No `conftest.py`. Don't use `tests/fakes` or `tests/fixtures`.

---

## 7. Checks

**Tests the implementer writes** (all in `tests/unit/policy/test_booking.py`; the WP-N pair is `test_worked_pairs_wp3_wp4`):

| Test | Asserts |
|---|---|
| `test_city_to_zone_schema_map` | Round Rock, Cedar Park, Pflugerville, Georgetown, Leander, Hutto → `"north"`; Austin → `"central"`; Kyle, Buda → `"south"`; every result ∈ `{"north","central","south"}` |
| `test_zip_groups_to_zone` | 78664, 78665, 78681, 78613, 78641, 78645, 78660, 78634, 78626, 78628, 78633 → north; 78640, 78610 → south; 78701, 78745, 78799 → central |
| `test_new_april_2026_areas_central` | `"Dripping Springs"`, `"78620"`, `"Manor"`, `"78653"` → `"central"` |
| `test_not_served_areas` | `"San Marcos"`, `"Bastrop"`, `"Elgin"`, `"Lakeway"`, `"78734"`, `"78738"`, `"Houston"`, `"77002"` → `None`; also `"78701x"` → `None` |
| `test_wp4_two_hours_before` | Patch `booking.datetime` with a subclass of `datetime` whose `now`, `utcnow` and `today` classmethods append to a `calls` list and return `datetime(2030, 1, 1, tzinfo=CHI)`. Patch `booking.date` likewise with a `date` subclass overriding `today` (use `monkeypatch.setattr`). `hours_before(NOW, date(2026,10,16), "12:00-16:00") == 2.0`; `hours_before(datetime(2026,10,16,13,0,tzinfo=CHI), date(2026,10,16), "12:00-16:00") == -1.0`; `calls == []` |
| `test_fee_bearing_boundary` | `fee_bearing(2.0) is True`; `fee_bearing(-1.0) is True`; `fee_bearing(hours_before(NOW, date(2026,10,22), "08:00-12:00")) is False` (that hours value `== 142.0`); `fee_bearing(24.0) is False`; `hours_before(datetime(2026,10,16,12,0,tzinfo=CHI), date(2026,10,17), "12:00-16:00") == 24.0` |
| `test_fee_note_by_tier` | For `hvac_repair` and `plumbing`: `none` → `FeeNote(service_type=s, tier="none", fee_row="Diagnostic visit", amount_cents=8900, waived=False, line="Standard diagnostic fee: $89")` (compare the whole model); `standard`, `plus` → `fee_row="Diagnostic visit"`, `amount_cents=0`, `waived=True`, `line == render(TextId.FEE_DIAGNOSTIC_WAIVED, amount="$89")`. `estimate` × each tier → `fee_row is None`, `amount_cents == 0`, `waived is False`, `line == render(TextId.FEE_ESTIMATE_FREE)`. `isinstance(result, FeeNote)` |
| `test_schedule_fees_single_source` | `SCHEDULE_FEES == {"Diagnostic visit": {"none": 8900, "standard": 0, "plus": 0}, "After-hours dispatch": {"none": 14900, "standard": 0, "plus": 0}, "Seasonal tune-up": {"none": 12900, "standard": 0, "plus": 0}}` (compare as `{k: dict(v) for k, v in SCHEDULE_FEES.items()}`); `MEMBER_ALLOWANCE_ROWS == frozenset({"Seasonal tune-up"})`; for all 12 (service, tier) with a row, `note.amount_cents == SCHEDULE_FEES[note.fee_row][note.tier]`. AST scan of `booking.py`: `int` constants count `8900` == 1, `12900` == 1, `14900` == 1; none of `{89, 129, 49, 79, 4900, 7900}` present. `SCHEDULE_FEES["Diagnostic visit"]["none"] = 1` raises `TypeError` (read-only) |
| `test_fee_note_never_charged_or_waived` | For all 4 × 3 combinations: `"charg" not in line.casefold()`; `"$79" not in line`; `"$49" not in line`; `not ("late" in cf and "waiv" in cf)` |
| `test_unknown_location_not_logged` | `caplog.set_level(logging.DEBUG)`; `zone_for("Zyxwvut Hollow QX") is None` and `zone_for("99999") is None` with no exception; `"Zyxwvut" not in caplog.text` and `"99999" not in caplog.text` |
| `test_booking_module_is_pure` | Parse `src/meridian/policy/booking.py` with `ast`; collect `Import`/`ImportFrom` module names. Every name is in `{"__future__", "re", "collections.abc", "datetime", "types", "typing", "zoneinfo", "meridian.policy.texts"}` or starts with `"meridian.domain."`. No name starts with `meridian.services`, `meridian.agent`, `meridian.adapters`, `meridian.web`, `meridian.ports`, `meridian.gates`, `meridian.config`. The source contains none of `".now("`, `".today("`, `"utcnow"`, `"time.time"`, `"open("`, `"logging"`. Then monkeypatch `booking.render` with a spy that records and delegates to the real `render`; call `fee_note` for all 12 combinations; the spy recorded 12 calls |
| `test_fee_note_tune_up_and_estimate` | `fee_note("hvac_tune_up","none")`: `fee_row == "Seasonal tune-up"`, `amount_cents == 12900`, `waived is False`, `line == render(TextId.FEE_TUNE_UP, amount="$129")`; `"standard"`, `"plus"`: `amount_cents == 0`, `waived is True`, `line == render(TextId.FEE_TUNE_UP_INCLUDED, amount="$129")`; `fee_note("estimate", t)` for each tier: `fee_row is None`, `0`, `waived is False` |
| `test_fee_line_rendered_with_format_usd` | Spies on `booking.render` and `booking.format_usd` (both delegate to the real ones). For each row of the §5 step 5 table, assert the recorded `(text_id, kwargs)` and the `format_usd` args. Source scan: `re.search(r"\$[0-9]", source) is None` |
| `test_worked_pairs_wp3_wp4` | WP-4: `zone_for("Austin") == "central"`; `h = hours_before(NOW, date(2026,10,16), "12:00-16:00")`; `h == 2.0`; `fee_bearing(h) is True`. WP-4F: `fee_bearing(hours_before(NOW, date(2026,10,22), "08:00-12:00")) is False`. WP-3: `zone_for("Round Rock") == "north"` and `zone_for("78664") == "north"`; `n = fee_note("hvac_repair","standard")`; `n.waived is True`, `n.amount_cents == 0`, `n.line != "Standard diagnostic fee: $89"` |
| `test_zone_for_normalises_input` | `"  austin "`, `"AUSTIN"`, `"Austin, TX"`, `"Austin TX"`, `"austin, texas"` → `"central"`; `"round  rock"` → `"north"`; `"78701-1234"` → `"central"`; `"78734-0001"` → `None`; `"Lakeway, TX"` → `None`; `""`, `"   "`, `"a" * 65` → `None`; `zone_for(78701)` (an int; add `# type: ignore[arg-type]`) → `None` |
| `test_hours_before_rejects_naive_now_and_bad_window` | `pytest.raises(ValueError)` for `hours_before(datetime(2026,10,16,10,0), date(2026,10,16), "12:00-16:00")`; for window `"noon-4pm"` and `"25:00-26:00"` (the latter raised by `time()`). For the window cases, `str(excinfo.value)` does not contain `"noon"` |
| `test_hours_before_is_timezone_safe` | `hours_before(datetime(2026,10,16,15,0,tzinfo=timezone.utc), date(2026,10,16), "12:00-16:00") == 2.0`; `hours_before(datetime(2026,10,31,12,0,tzinfo=CHI), date(2026,11,1), "12:00-16:00") == 25.0` (DST ends 2026-11-01) |
| `test_issued_customers_city_and_zip_agree` | §6 |
| `test_fee_note_rejects_unknown_service_or_tier` | `pytest.raises(ValueError, match="unknown service type")` for `fee_note("duct_cleaning", "none")`; `match="unknown tier"` for `fee_note("hvac_repair", "gold")` (both with `# type: ignore[arg-type]`); neither message contains the bad value |

**Commands. Run them cheapest first and stop at the first red.** Run from the worktree root with `export UV_LINK_MODE=hardlink`.

While iterating:

```bash
uv run pytest tests/unit/policy/test_booking.py -q
```

Before the final commit (record each result in the report):

```bash
uv run ruff format --check src/meridian/policy/booking.py tests/unit/policy/test_booking.py
uv run ruff check src/meridian/policy/booking.py tests/unit/policy/test_booking.py
uv run mypy src/meridian/policy/booking.py tests/unit/policy/test_booking.py
grep -rlE "meridian\.policy\.booking|policy import booking" tests/ eval/     # affected-test discovery
uv run pytest tests/unit/policy/ -q                                         # test_booking.py + test_texts.py + test_limits.py stay green
uv run python -m tests.journeys.affected --base main                        # expect "0 journeys affected", exit 0
```

**Passing looks like this:**
- format and check are clean;
- mypy reports `Success: no issues found`;
- the grep lists only `tests/unit/policy/test_booking.py`;
- pytest shows all 19 tests in `test_booking.py` passed, and `test_texts.py` and `test_limits.py` unchanged and green;
- the affected command prints `0 journeys affected`.

**Tests that must stay green:** `tests/unit/policy/test_texts.py`, `tests/unit/policy/test_limits.py`,
`tests/unit/test_import_direction.py`. This ticket changes none of them, and `test_texts.py`'s fixture check must still
pass after the follow-up.

**Full suite:** not run. This change reaches no shared fixture, settings, dependency or cross-codebase module
(`build-loop-test-scope.md`). Use pytest `-n 2` at most if you parallelise at all. It is not needed here.

**The implementer must not:**
- Edit `policy/texts.py`, its fixture or test, `domain/*`, `pyproject.toml`, `conftest.py`, or any file outside §2's owned list.
- Add a missing `TextId` or type itself, or write a stand-in sentence in `booking.py`. Stop and report `blocked-on` instead.
- Type a dollar figure, `$`+digit, or a second 8900/12900/14900 anywhere in `booking.py`, comments included.
- Read a clock, import `logging`, open a file, or touch SQLite in `booking.py`.
- Echo an input value in any exception message.
- Add a waiver, a discount, or any handling of the $49 late-change fee.
- Check slot status, member slots, service-type match or the booking cap (all AEA-28's).
- Make a public helper other tickets would start reading. Use `_window_start` only privately.
- Use `git add -A`, push, merge or force-push. Do not bind ports 4019 or 5184. Make no paid model call.

---

## 8. Risks and requests

**R-1. Request to the integrator: an AEA-03 follow-up, "booking fee texts (U-1)", merged before AEA-13's implementer starts.**
- Owner files: `src/meridian/policy/texts.py`, `tests/unit/policy/texts_source_fixture.json`, `tests/unit/policy/test_texts.py`.
- It adds four `TextId` members in the `booking` group with the exact names and placeholders in §4. The wording is §9's
  decision.
- Each fixture entry has `source.kind = "proposal"` (AEA-03's convention for `ARE_YOU_A_PERSON` and `INBOX_CODE_GONE`) and
  cites the KB file its words come from.
- The AC-2 group-count table changes to booking 16, total 75.
- It is one small `lane::build-loop` ticket with no security surface.
- This is the edge `AEA-03 → 13` that the slice plan §2 already names ("the booking fee texts"), so no wave moves.

**R-2. Collisions on context files.** `area-map.md`, `icm-progress.md` and `code-design.md` §3 are edited by every wave-1
ticket's AC-15 equivalent. This plan confines AEA-13 to its own row or line, but the ICM row is one shared row. Expect a
trivial merge conflict there; the merge step keeps the newest evidence, as `context-maintenance.md` rule 6 says.

**R-3. Where `ServiceType` and `Window` live** is not fixed by any contract (graph-core GRC "cases A-1" only names them).
Step 0 finds them with grep. If AEA-02 defined them as something other than a `Literal` of the four SCHEMA values each,
stop and report. Do not redefine them locally.

**R-4. `zoneinfo` needs tz data at run time.** The VPS has `/usr/share/zoneinfo`. The deploy image (AEA-50) must too; that
is already required by `FixedClock` and `Clock`. Nothing to do here; noted for AEA-50's reviewer.

**R-5. City aliases.** Only the cities in SCHEMA.md and Q-3 are recognised. A spelling such as "Round Rock TX 78664", or a
neighbourhood name, returns `None`, and AEA-28 answers `outside_service_area` (`OutOfArea.reason` `unknown_location`).
This is fail-closed by design, and AEA-28 prefers the customer record's ZIP (cases §4 `slice_inputs`: "zone_for(zip, else
city)"), which is always clean in the issued data (S-4 proves it). A broader alias table would be a Stage 9 change driven
by transcript replays.

**R-6. Contract problems:** none. No signed contract (OpenAPI, `UI_CONTRACTS.md`) changes. `fee_line` stays a required
non-empty string, and every `FeeNote.line` is one.

**Gates:** none of human, paid or live type. The block is the §9 decision.

---

## 9. Readiness

**NEEDS-DECISION.** It is also blocked on AEA-01, AEA-02, AEA-03 and the R-1 follow-up.

**The story.**
- **Where we were.** AEA-13 is the rule book for bookings: which zone a customer is in, whether a change is inside 24 hours,
  and what fee the confirmation card shows. Zones, the clock arithmetic, the 24-hour rule and the fee amounts are all
  settled by the issued data and Stage 7 decisions, and this plan fixes every one of them.
- **What happened.** The fee *sentence* on the card has to come from `policy/texts.py`, word for word from the UX copy.
  The UX copy has exactly one fee sentence, the OpenAPI example "Standard diagnostic fee: $89". The ticket, R-20 and
  cases.md §2 also need a sentence for four more cases:
  - a member whose diagnostic fee is waived (Linda Foster, WP-3);
  - a non-member's tune-up ($129);
  - a member's tune-up, which is included twice a year;
  - a free in-home estimate.
  
  When AEA-03 was built, its planner reported these four as gap U-1 to the UX session and did not write them. AEA-13 is not
  allowed to type customer words itself.
- **Why it matters.** This is the brief's trap: issued agents quoted the $89 diagnostic for tune-ups in 16 of 16 calls, and
  quoted $89 to a member who pays nothing. Without its own sentences the card would either show a wrong fee or no fee line
  at all, and the OpenAPI makes `fee_line` required. AEA-27 and AEA-28 (wave 2) wait on AEA-13. The wording itself is cheap
  to change later: the code and tests refer only to the sentence ids, so a UX rewording touches `texts.py` alone.

**Option A: approve four proposal sentences now** *(recommended)*. Each sentence quotes the KB's own words. A small AEA-03
follow-up adds them as "proposal" entries, and UX-5 may reword them later without touching AEA-13.
- Diagnostic, member: "Diagnostic fee: waived for Comfort Club members (normally {amount})". Source:
  `comfort_club_overview.md` "Diagnostic fee ($89) waived on all service calls".
- Tune-up, non-member: "Seasonal tune-up fee: {amount} per system". Source: fee schedule "Seasonal tune-up (per system)
  $129".
- Tune-up, member: "Seasonal tune-up: included with Comfort Club, two per year (normally {amount})". Source:
  `service_catalog.md` "Included for Comfort Club members"; `comfort_club_overview.md` "Two seasonal tune-ups per year".
- Estimate: "Free in-home estimate with a Comfort Advisor". Source: `service_catalog.md`, verbatim.

*What happens:* one roughly 30-minute follow-up ticket, then AEA-13 builds from this plan unchanged. No wave moves.
*Tradeoff:* the words are ours until the UX session confirms them.

**Option B: send U-1 to the UX session and wait for its wording.** *What happens:* AEA-13 and, behind it, AEA-27, AEA-28
and the wave-2 scheduling path wait for the UX session's answer. *Tradeoff:* the UX track owns the words from the start,
but the critical scheduling work stalls on another session's timing.

**Option C: reuse "There's no fee." for members and estimates and add only a tune-up price line.** *What happens:* one new
sentence instead of four, but cases.md §2's rule ("a waived row renders the waived text with the scheduled amount") and
AC-13 have to change, which is a Stage 7 contract edit. *Tradeoff:* fewer new words, but a member is told "There's no fee"
for a tune-up even when both yearly visits may already be used, which is a promise the policy does not back.

*Recommended: A.* It fixes the exact trap a grader probes ($89 quoted for a tune-up or to a member), uses only KB wording,
and keeps the wave intact.

**Decision needed:** Should the four missing fee sentences use the proposed KB-based wording now (A), wait for the UX
session's wording (B), or be cut to one new sentence by reusing "There's no fee." (C)?


## Deviations

- **R-1 folded in (2026-10-21).** The four option-A sentences were added by the AEA-13 implementer in branch `aea-13-booking-rules` (commit `5409c06`), not by a separate AEA-03 follow-up ticket. Fixture sources use `kind: proposal`; because `test_fixture_quotes_its_source_files` needs the wording in a readable file, three entries cite `docs/testing/journeys/2026-10-21-AEA-13.md` (lines 20-22, which hold the wording and the rendered forms) and the estimate cites `service_catalog.md` line 27 (verbatim).
- **`hours_before` subtracts in UTC.** Plan step 3 said "aware subtraction gives real elapsed hours across DST". It does not: Python subtracts wall-clock time when both values share one `ZoneInfo`, so S-3 (Oct 31 12:00 to Nov 1 12:00 = 25.0) returned 24.0. The module converts both to UTC first (`from datetime import UTC`).
- **ICM row appended, not replaced.** Every earlier slice appended its own *Routes verified* row, so AEA-13 did the same rather than rewrite one shared row.
- **Journeys ran.** The harness has merged, so the affected-journeys command selected 6 journeys (texts.py changed) instead of printing "0 journeys affected". The record states level `mock-tested` for booking.py itself and quotes the run.
- **mypy** is run as `MYPYPATH=src uv run mypy ...` for the test files; without `MYPYPATH` mypy treats `meridian` as an untyped installed package.
