# Plan — [AEA-16] retrieval: manifest and ingestion of the 17 KB files

**Status:** planned — READY, **blocked-on AEA-02** (wave 0; not merged on `main` at `16ca639`)
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #16 (body = `docs/plans/tickets/AEA-16.md`) · **Base revision:** `main`
`16ca639` (AEA-01 merged at `07924f5`, AEA-03 and AEA-04 merged; AEA-02's worktree exists with no commits yet) plus the
DO-4 / stage7 signatures and AEA-02's plan §4.1, §4.2, §4.13 for the types it will add. The implementer's worktree is cut
from `main` **after** AEA-02 merges. Lane `lane::build-loop`, risk: none (no test-writer, no security agent). Wave 1,
gates: none.
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21; refreshed the same day against `main` `16ca639` (first
version planned against `bc02266`). **Implementer:** `fanout-implementer` on Sonnet.
**Worktree / branch:** `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-16`, branch `aea-16-retrieval-ingest`.

---

## 1. Goal and sources

### 1.1 Goal (from the issue's *What to build*)

> **US-6.** As a homeowner, I need answers about membership, billing fees, warranty, services, hours and the service area
> that come from Meridian's current documents and show where they came from … *(the answer names its source and version
> date … never an archived copy.)*

One command (the WF-14 entry point) reads the issued knowledge base, decides for each of the 17 files whether it may be an
answer source, cuts every answer-source file into chunks that carry file, section and version, embeds them with
`BAAI/bge-small-en-v1.5`, and writes **one index directory** that the rest of the system reads. Staff-only discretion notes
go to a separate file that is never embedded. Three modules: `retrieval/settings.py`, `retrieval/manifest.py`,
`retrieval/ingest.py` (stage7/data.md §3).

**Concrete example (WP-1, stale twin).** Input: the issued KB holds `membership/comfort_club_overview.md` ("Effective
2026-01-01", $189/year) and its near-twin `archive/comfort_club_overview.md` ($149, "cancel at any time"). Process: the
manifest says the first is `current` and the second `excluded`. Output: `manifest.json` row for the archive file has
`status: "excluded"`, a reason and `chunks: 0`; `passages.jsonl` has 7 chunks whose `file` is
`membership/comfort_club_overview.md`, each with `version_label: "Effective 2026-01-01"` and `version_date: "2026-01-01"`,
and **no** line whose `file` starts with `archive/`.

### 1.2 Context

Wave-1 ticket of Stage 8. On `main` `16ca639` only `src/meridian/retrieval/__init__.py` and `tests/unit/retrieval/__init__.py`
exist (AEA-01); `domain/` and `ports/` hold only `__init__.py` until AEA-02 merges. The
parked first attempt (`docs/parked/2026-10-21-first-attempt/src_meridian/kb/{manifest,ingest}.py`) is read for shapes and
data only, never imported. AEA-33 (wave 2) loads this ticket's index; AEA-50 runs the CLI at `docker build`; AEA-29 imports
`StaffGuidance`; AEA-51's container resolves `STAFF_GUIDANCE_FOR` prefixes against `load_staff_guidance()`.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Requirements | PRD `docs/prd/inno-aea-callcenter-prd.md` R-9 (every format; manifest of 17 with status and parse method), R-10 (exclusions, staff-only, stub), R-11 (bge-small, local index, file/section/version citation); §4.3a; US-6, US-7 | AC-1…AC-5 |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §0 (`MeridianModel`, `PassageId` = `<file path>#<chunk n>`, superseded note: ingest mints it), §5 `Passage`, §13 `IndexInfo`, §16 (addenda win) | Exact shapes; §13 gets the layout note (AC-11) |
| Addendum (wins over DO-4) | `docs/design/contracts/stage7/data.md` §3 (every type, constant, file, the CLI), §9 item 4 (staff guidance → AEA-29, CAS-33); `stage7/cases.md` §5 `STAFF_GUIDANCE_FOR` | Signatures copied in §4 below |
| Decision ledger | `docs/plans/7b-decisions/data.md` DAT-11 (chunking [A]), DAT-12 (`ingest_run.json`, no DB row), DAT-13 (`staff_notes.json`, `load_staff_guidance`), DAT-17 (k, floor), DAT-18 (stub never indexed); `merge-clashes.md` MC-26 (`StaffGuidance` in `manifest.py`, no numpy/fastembed import) | Steps 2–4 |
| Code design | DO-3 `docs/design/code-design.md` §3 tree rows `retrieval/{settings,manifest,ingest}.py` (A3, wave 1), §2.4 *kb/* row, §6 S-5 (embedder port deferred → `EmbedFn` is a plain callable), §7 rows R-9/R-10/R-11 | Module boundaries; no new seam |
| Deploy | DO-1 §11 decision 10 (index built at image build, ships in the image), §9 (build cannot write the volume) | Atomic temp-dir write; no DB row |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` (E-2 retrieval; expected-answer authority = PRD §4.3a / R-10) | No eval cases here (AEA-06), no harness (AEA-24); `manifest_hash` lets E-2 name its index |
| Observability contract | DO-6 `docs/design/observability-contract.md` row WF-14 (ingest_run, manifest 17 files with status and parse method, index record); CAP-9; *Content and redaction* (logs: IDs, counts, statuses) | AC-8, AC-9 |
| Key-metrics registry | DO-7 M-6 (hit @3), M-7 (answers citing an excluded file) | No target here; AC-2 keeps M-7's ingestion share at 0 |
| Rules | `.claude/rules/retrieval-and-context.md` 2, 5, 6, 7; `source-authority.md` 2; `build-loop-test-scope.md` (+ AEA addition); `integrated-journeys.md` §3–§5; `context-maintenance.md` 6 | Settings in one file; journey record level `mock-tested` |
| Issued data | `docs/data/issued/meridian_dataset/knowledge_base/` (17 files, read-only); `data/kb_transcriptions/holiday_hours_2026.md` (hand transcription, read-only) | Tests copy into `tmp_path`, never write the originals |
| Sign-off | `docs/plans/stage7-signoff.md` D-4…D-15 | None touches AEA-16 |

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files the implementer may create or edit)

| File | Action |
|---|---|
| `src/meridian/retrieval/settings.py` | create |
| `src/meridian/retrieval/manifest.py` | create |
| `src/meridian/retrieval/ingest.py` | create |
| `tests/unit/retrieval/test_manifest.py` | create |
| `tests/unit/retrieval/test_ingest.py` | create |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-16.md` | create (AC-10; date = the implementer's day, America/Chicago) |
| `.claude/reference/area-map.md` | modify **only the last cell of the A3 row** (AC-11) |
| `.claude/state/icm-progress.md` | **add one row** directly after the last `\| Routes verified against code and tests \|` row (AC-11; precedent: AEA-03 and AEA-04 each have their own row) |
| `docs/design/code-design.md` | add **one line** under §3 (AC-11) |
| `docs/design/contracts/internal-components.md` | add **one blockquote note** at the top of §13 (AC-11) |
| `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<YYYY-MM-DD>-aea-16-retrieval-ingest-claude-01.md` | create (outside this repo; not committed here) |

### 2.2 Shared surfaces read, never edited

`src/meridian/domain/common.py` (`MeridianModel`, `PassageId`), `src/meridian/domain/records.py` (`Passage`),
`src/meridian/ports/runtime.py` (`IndexInfo`), `src/meridian/retrieval/__init__.py` and
`tests/unit/retrieval/__init__.py` (both AEA-01, already present, leave empty), `pyproject.toml` / `uv.lock` (AEA-01;
already list `numpy>=2.0`, `pypdf>=6.21` (locked 6.21.1), `fastembed>=0.9` (locked 0.9.0); ruff ignores `UP040`; mypy
strict with the pydantic plugin, `init_typed = true`), `tests/conftest.py`, `tests/journeys/affected.py`,
`tests/unit/test_import_direction.py` (one function per owning ticket; this ticket adds none — PA-3 lives in
`test_manifest.py`),
the issued KB and `data/kb_transcriptions/holiday_hours_2026.md`.

### 2.3 Owned by other tickets — do not create or edit

`adapters/retrieval_fastembed.py`, `agent/tools/knowledge.py` (AEA-33); `domain/*`, `ports/*`, `config.py` (AEA-02);
`policy/handoff.py` incl. `STAFF_GUIDANCE_FOR` (AEA-14); `services/handoff.py` (AEA-29); `Dockerfile`, `.dockerignore`
(AEA-50); `eval/**` (AEA-06, AEA-24); `tests/fakes/` (AEA-11); `tests/journeys/**` (no journey file for this ticket); anything
under `docs/data/issued/`, `docs/parked/`, `docs/archive/`, `docs/ux/**`, `apps/web/**`, the OpenAPI, `UI_CONTRACTS.md`.
Do not add a `tests/unit/retrieval/conftest.py` (AEA-33 may test near here; keep helpers inside the two test files).

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's, verbatim IDs) → implementation → verification

| AC | Requirement (short; full text in the issue) | Implemented by | Verified by |
|---|---|---|---|
| AC-1 [invariant] | `MANIFEST` lists all 17 issued files exactly once, status, parse method, version label on every current row, reason on every non-current row; an extra file on disk, or a listed file absent, raises `UnlistedFile` and writes nothing | §5 step 2 (`MANIFEST`, validators); step 3.3 (listing check, before any temp dir) | `tests/unit/retrieval/test_manifest.py::test_manifest_covers_all_17_issued_files`; `tests/unit/retrieval/test_ingest.py::test_unlisted_file_fails_build` |
| AC-2 [invariant] | The 4 excluded files, the staff-only file and the stub are never embedded or in `passages.jsonl`; the 11 current files are; non-current `chunks` = 0 | step 3.5 (only `CURRENT` rows parse to passages) | `test_ingest.py::test_only_current_files_indexed` |
| AC-3 [invariant] | Each format parsed by its own method and recorded: MD heading split, TXT and fee PDF paragraph groups, CSV one chunk per data row, PNG via the linked transcription | step 3.4 readers; step 3.5 | `test_ingest.py::test_each_format_parsed` |
| AC-4 [invariant] | A section over `MAX_SECTION_CHARS` is cut at blank-line paragraphs into pieces near `PIECE_CHARS`, no overlap; `section` = heading path | step 3.4 `_cut` | `test_ingest.py::test_heading_split_and_long_section_cut` |
| AC-5 [invariant] | Unique `passage_id` `<file>#<n>`, `file`, `section`, `version_label`, `version_date` only for full dates; `embed_text` = `section + "\n" + text`; vectors rows = lines, norm 1 ± 1e-5 | steps 3.5–3.6 | `test_ingest.py::test_chunk_provenance` |
| AC-6 [failure/refusal] | Missing/unreadable answer source or missing transcription → `MissingSource` naming the file; CLI non-zero printing `MissingSource`; no index directory | steps 3.3, 3.4, 3.8 (temp dir + rename), 3.10 (CLI) | `test_ingest.py::test_missing_source_fails_build`, `::test_cli_exit_codes` |
| AC-7 [invariant] | Staff-only file → `staff_notes.json` as `StaffGuidance` (`internal/agent_discretion_notes.md#<n>`, version label, `text_sha256`); `load_staff_guidance` returns exactly them; never embedded; the "Waive the $49 late-cancellation fee once per customer per year" bullet is in some passage | step 3.4 `_staff_passages`; step 3.9 | `test_ingest.py::test_staff_notes_written_not_indexed` |
| AC-8 [negative] | Through the entry point's `main`: excluded/stub text in no artefact and no output; staff-only text only in `staff_notes.json`; stdout/logs carry IDs, counts, statuses only | steps 3.5, 3.10 | `test_ingest.py::test_excluded_text_absent` |
| AC-9 [capture] | WF-14 entry point writes `manifest.json` (17 rows), `index_record.json` (IndexInfo fields + every settings constant), `ingest_run.json` (completed); a failing run's `IngestRun` is `failed` with the class name; `manifest_hash` stable across runs, changes with one KB byte | steps 3.7–3.10 | `test_ingest.py::test_entry_point_writes_wf14_records` + the implementer's **one real-embedder CLI run** (§7.4), output pasted in the report |
| AC-10 [journey] | Runs no journey yet (before AEA-57). Record `docs/testing/journeys/YYYY-MM-DD-AEA-16.md`: level `mock-tested`, *Blocked by* AEA-57, names **J-2**; the affected-journeys command prints "0 journeys affected" | step 8 | the record's fields; `uv run python -m tests.journeys.affected --base main` output |
| AC-11 [regression/context] | Area map A3 row; ICM row; DO-3 A3 built; DO-4 §13 layout + `manifest_hash` note; dev-log entry | step 8 | `git diff --stat main...HEAD` on those paths |

### 3.2 Plan-added criteria (the orchestrator posts them on issue #16 as a comment)

| ID | Criterion | Verified by |
|---|---|---|
| PA-1 (WP-1 worked pair) | The WP-1 pair as a named test: the current membership file's chunks carry "Effective 2026-01-01" / 2026-01-01; no `archive/` file in `passages.jsonl`; the archive row is `excluded`, reason set, `chunks` 0; the fee-schedule chunk legitimately contains "$149" (WP-2: check by path, not text) | `test_ingest.py::test_wp1_stale_twin_by_path` |
| PA-2 | An existing `out_dir` is refused with `IngestError` and left untouched (a rebuild never half-overwrites a shipped index) | `test_ingest.py::test_existing_out_dir_refused` |
| PA-3 | `manifest.py` and `settings.py` import no numpy, pypdf or fastembed (MC-26: AEA-29 imports `StaffGuidance` without the embedding stack) | `test_manifest.py::test_manifest_and_settings_import_no_heavy_stack` |
| PA-4 | Model validators: a CURRENT spec without a version label, a non-current spec without a reason, a non-current row with `chunks` > 0, and a `StaffGuidance` whose `text_sha256` ≠ SHA-256 of its text are each rejected | `test_manifest.py::test_validators_reject_bad_rows` |
| PA-5 | TXT paragraph groups (the only TXT is excluded, so tested on the helper) | `test_ingest.py::test_plain_text_paragraph_groups` |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| 17 files, status + parse method each | R-9, WF-14 | AC-1, AC-9 | in-ticket | 2, 3.7 |
| Exclusions exactly per R-10 | R-10, DEC-4 | AC-2 | in-ticket | 2, 3.5 |
| Stub never indexed | DAT-18 | AC-2 | in-ticket | 2 |
| All retrieval constants in one file, recorded with the index | retrieval rule 5, data.md §3 | AC-9 | in-ticket | 1, 3.7 |
| One embedding model per index; model name recorded | retrieval rule 6, R-11 | AC-9 | in-ticket | 3.7 (`IndexInfo.embedding_model` is a `Literal`) |
| Readiness check (dimension, 17 files) | retrieval rule 7 | — | other-ticket | AEA-33 `readiness()` reads what this writes |
| `OVERLAP_CHARS` must actually be honoured | retrieval rule 5 | — | added | 3.1 guard: non-zero overlap raises `IngestError` (no silent ignore) |
| Missing listed file: `UnlistedFile` (AC-1) vs missing PDF: `MissingSource` (AC-6) | data.md §3 (both definitions overlap) | AC-1, AC-6 | added (engineering decision, §8 D-1) | 3.3: an absent **CURRENT or STAFF_ONLY** file → `MissingSource`; an absent EXCLUDED/STUB file → `UnlistedFile` |
| Hash and parse the same bytes | data.md §3 `source_sha256` | AC-3, AC-9 | added | 3.4: read each file once; hash and parse that buffer |
| Index record must be readable as `IndexInfo` by AEA-33 | DO-4 §13, AEA-33 `info()` | AC-9, AC-11 | added | 3.7 layout + DO-4 §13 note says how to read it |
| Staff guidance resolvable by "the bullet's opening words" | cases.md §5 `STAFF_GUIDANCE_FOR` | AC-7 (one prefix) | added (§8 D-2) | 3.4 `_staff_passages`: one passage per bullet; test checks all five prefixes `startswith` |
| No DB row for the ingest run | DAT-12 | Observability | in-ticket | 3.8 |
| Logs/stdout: IDs, counts, statuses | DO-6 *Content and redaction* | AC-8 | in-ticket | 3.10 |
| No paid call / no model download in default tests | build prompt, DO-3 S-5 | Agent handoff | in-ticket | stand-in `EmbedFn` in tests; fastembed imported lazily |
| E-2 cases and harness | DO-5 | Evaluation | other-ticket | AEA-06, AEA-24 |
| Attaching guidance to a brief | cases.md §5 | Scope | other-ticket | AEA-29, AEA-51 |
| CAP-9 test in the image | DO-6 CAP-9 | Observability | other-ticket | AEA-50 (`tests/capture/`) |
| data.md §3 cites "AEA-16 AC-5/AC-7/AC-8" with older numbering (now AC-6, AC-9, AC-11) | data.md §3 | — | n/a here | stale cross-refs; report to the orchestrator for AEA-08, do not edit data.md |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| `python -m meridian.retrieval.ingest --kb-dir PATH --transcriptions-dir PATH --out-dir PATH` | WF-14 knowledge-base ingestion and index build | DO-6 registry row WF-14; data.md §3 | EV: E-2; M-6, M-7; capture CAP-9 (AEA-50) |

---

## 4. Shared code to use (exact shapes, copied)

### 4.1 From AEA-02 (not on `main` at `16ca639`; must be merged before you start; verify in step 0)

Copied from DO-4 §0, §5, §13 and AEA-02's plan §4.1 (`domain/common.py`), §4.2 (`domain/records.py`), §4.13
(`ports/runtime.py`, which re-exports `Passage`). `PassageId` validates with `core_schema.str_schema(pattern=...,
strict=True)`: pass a plain `str` such as `f"{path}#{n}"`, never an int or bytes.

```python
# src/meridian/domain/common.py
class MeridianModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)
class PassageId(_PatternId):  PATTERN = r"^[^#\s]+#[0-9]+$"     # "<file path>#<chunk n>"

# src/meridian/domain/records.py   (also re-exported from meridian.ports.runtime)
class Passage(MeridianModel):   # DO-4 §5
    passage_id: PassageId
    file: str
    section: str
    version_label: str
    version_date: dt.date | None
    text: str
    score: float

# src/meridian/ports/runtime.py
class IndexInfo(MeridianModel):
    embedding_model: Literal["BAAI/bge-small-en-v1.5"]
    dimension: int
    chunks: int
    manifest_hash: str
    files: int
```

Imports to write: `from meridian.domain.common import MeridianModel, PassageId`, `from meridian.domain.records import
Passage`, `from meridian.ports.runtime import IndexInfo`. Because `str_strip_whitespace=True`, every `str` field is stripped
on validation: always compute hashes and `embed_text` **from the validated model's fields**, never from the pre-validation
string. Because of mypy `init_typed = true`, build models whose fields are validated id types with
`Model.model_validate({...})` (e.g. `Passage.model_validate({"passage_id": f"{path}#{n}", ..., "score": 0.0})`), not the
constructor.

### 4.2 Module rules (same as AEA-02 §4.0, apply here)

1. First line after the module docstring: `from __future__ import annotations`. Dates: `import datetime as dt`.
2. One statement per line (ruff E702). Absolute imports only.
3. Errors in validators: `pydantic_core.PydanticCustomError("<stable_code>", "<message without any input value>")`.
4. No module-level instances except immutable constants (tuples, strings, `Final` numbers). No settings object, no client.
5. Never `assert` in `src/` (ruff S101). Never `print` chunk text anywhere.

### 4.3 `src/meridian/retrieval/settings.py` (data.md §3, copied; this whole file is these constants)

```python
EMBEDDING_MODEL: Final = "BAAI/bge-small-en-v1.5"     # PRD R-11
SIMILARITY: Final = "cosine"                          # vectors L2-normalised; score = dot product
CHUNKER: Final = "heading-split/1"                    # DAT-11: split at Markdown headings, heading path = section
MAX_SECTION_CHARS: Final = 1100                       # [A] a longer section is cut at blank-line paragraphs …
PIECE_CHARS: Final = 900                              # [A] … into pieces of about this size
OVERLAP_CHARS: Final = 0                              # [A] sections are self-contained in this KB
SEARCH_K: Final = 3                                   # [A] DAT-17; E-2 scores @3
MIN_SCORE: Final = 0.60                               # [A] DAT-17; the relevance floor (cosine)
# Replaced by: the first E-2 run (hit @3 per query and the off-corpus queries' below-floor rate), never by a prompt change.
```

`from typing import Final`. Docstring: "Every retrieval constant in one place (retrieval rule 5); each value is recorded in
index_record.json at build (stage7/data.md §3)." No other names in this module (no helpers, no lowercase module-level
names other than imports), because ingest records `{name: value for name, value in vars(settings).items() if name.isupper()}`.

### 4.4 `src/meridian/retrieval/manifest.py` (data.md §3 + MC-26, copied)

```python
class FileStatus(StrEnum):
    CURRENT = "current"; EXCLUDED = "excluded"; STAFF_ONLY = "staff_only"; STUB = "stub"   # PRD R-10
class ParseMethod(StrEnum):
    MARKDOWN = "markdown"; TEXT = "text"; PDF_TEXT = "pdf_text"; CSV_ROWS = "csv_rows"
    PNG_TRANSCRIPTION = "png_transcription"           # data/kb_transcriptions/holiday_hours_2026.md, linked to the PNG

class ManifestRow(MeridianModel):
    path: str                                         # relative to knowledge_base/, e.g. "membership/comfort_club_overview.md"
    status: FileStatus
    version_label: str | None                         # as the file states it; None only for non-CURRENT rows
    parse_method: ParseMethod
    reason: str | None                                # required when status != CURRENT
    source_sha256: str                                # of the issued file's bytes (and the transcription's, for the PNG)
    chunks: int                                       # 0 for every non-CURRENT row

class ManifestSpec(MeridianModel):                    # the hand-written static part of a row
    path: str; status: FileStatus; version_label: str | None; parse_method: ParseMethod; reason: str | None
MANIFEST: Final[tuple[ManifestSpec, ...]]             # exactly 17

class StaffGuidance(MeridianModel):                   # DAT-13; pydantic only (MC-26)
    passage_id: PassageId                             # "internal/agent_discretion_notes.md#<n>"
    file: Literal["internal/agent_discretion_notes.md"]
    section: str; version_label: str; text: str; text_sha256: str
```

Write one field per line. Allowed imports in this file: standard library, `pydantic`, `pydantic_core`,
`meridian.domain.common`. **Nothing else** (PA-3).

Validators to add (validators, not fields; each `@model_validator(mode="after")` returning `self`):

| Model | Rule | Error code |
|---|---|---|
| `ManifestSpec` and `ManifestRow` | `status == CURRENT` → `version_label` is non-empty and `reason is None` | `manifest_current_row` |
| `ManifestSpec` and `ManifestRow` | `status != CURRENT` → `reason` is non-empty | `manifest_reason_required` |
| `ManifestRow` | `status != CURRENT` → `chunks == 0`; always `chunks >= 0` | `manifest_noncurrent_chunks` |
| `ManifestRow` | `source_sha256` matches `^[0-9a-f]{64}$` (use `Field(pattern=...)`) | pydantic's `string_pattern_mismatch` |
| `StaffGuidance` | `text_sha256 == hashlib.sha256(text.encode("utf-8")).hexdigest()` (on the stripped `text`) | `staff_guidance_hash_mismatch` |

Share the first two rules through one private function `_check_status_fields(status, version_label, reason) -> None` that
both validators call.

**`MANIFEST` data (exact values; the tuple is sorted by `path`).** Parse method follows the extension: `.md` →
`MARKDOWN`, `.txt` → `TEXT`, `.pdf` → `PDF_TEXT`, `.csv` → `CSV_ROWS`, `.png` → `PNG_TRANSCRIPTION`.

| path | status | version_label | reason |
|---|---|---|---|
| `archive/comfort_club_overview.md` | EXCLUDED | `None` | `Superseded membership terms ($149 a year, refunds at any time, transfers to a new address); DEC-4, audit K-6, K-7` |
| `archive/warranty_terms_2023.txt` | EXCLUDED | `"2023"` | `Superseded 2023 warranty (90-day repair labour, 1-year installation); DEC-4, audit K-8, K-9` |
| `faq/customer_faq.md` | CURRENT | `"Last updated 2026-03-02"` | `None` |
| `faq/faq_old_copy.md` | EXCLUDED | `None` | `Undated old copy that contradicts the dated FAQ ($79 diagnostic, $129 after-hours, old hours); DEC-4, audit K-1, K-2, K-4` |
| `faq/troubleshooting_before_you_call.md` | CURRENT | `"undated"` | `None` |
| `internal/agent_discretion_notes.md` | STAFF_ONLY | `"undated"` | `Internal guidance marked "Do not read this document to customers"; staff views only through staff_notes.json, never embedded; audit K-15` |
| `membership/comfort_club_overview.md` | CURRENT | `"Effective 2026-01-01"` | `None` |
| `policies/escalation_and_safety.md` | CURRENT | `"Rev 2026-01"` | `None` |
| `policies/holiday_hours_2026.png` | CURRENT | `"2026 (image)"` | `None` |
| `policies/service_area.md` | CURRENT | `"Updated 2026-04-01"` | `None` |
| `pricing/2026_fee_schedule.pdf` | CURRENT | `"Effective 2026-01-01, supersedes all prior"` | `None` |
| `pricing/repair_price_book_2026.csv` | CURRENT | `"2026"` | `None` |
| `services/duct_cleaning.md` | STUB | `None` | `TODO stub; the service catalog's "Not offered" list answers duct cleaning (referral on request); audit K-14, DAT-18` |
| `services/scheduling_guide.md` | EXCLUDED | `"Rev 2024-11"` | `Rev 2024-11: its 48-hour rule contradicts the current 24-hour rule, and its overflow and waitlist slots are not in the DB; DEC-4, audit K-5` |
| `services/service_catalog.md` | CURRENT | `"Last updated 2026-02-10"` | `None` |
| `services/technician_arrival_and_etas.md` | CURRENT | `"undated"` | `None` |
| `warranty/warranty_policy.md` | CURRENT | `"Effective 2025-06-15"` | `None` |

Version labels are the file's own wording with the colon dropped ("_Effective: 2026-01-01_" → `Effective 2026-01-01`),
matching the ticket's examples. Build each spec as `ManifestSpec(path=..., status=FileStatus.CURRENT, version_label=...,
parse_method=ParseMethod.MARKDOWN, reason=None)` (no validated-id fields, so the constructor is fine).

### 4.5 `src/meridian/retrieval/ingest.py` (data.md §3, copied; numpy typing refined for mypy strict)

```python
class IngestError(Exception): ...                     # named reasons; message holds paths and counts only
class UnlistedFile(IngestError): ...                  # a file on disk not in MANIFEST, or a MANIFEST row with no file
class MissingSource(IngestError): ...                 # unreadable answer source or missing transcription → no output written

EmbedFn: TypeAlias = Callable[[Sequence[str]], npt.NDArray[np.float32]]   # texts → float32 [n, dim]; a stand-in in default tests

class IngestRun(MeridianModel):                       # WF-14 record (DAT-12)
    ingest_run_id: str                                # UUID4
    status: Literal["started", "completed", "failed"]
    started_at: dt.datetime
    finished_at: dt.datetime | None
    manifest_hash: str
    files: int
    chunks: int
    embedding_model: str
    failure: str | None                               # the IngestError class name only

def build_index(kb_dir: Path, out_dir: Path, *, transcriptions_dir: Path, embed: EmbedFn) -> IngestRun: ...
def load_staff_guidance(index_dir: Path) -> tuple[StaffGuidance, ...]: ...   # pure read
def main(argv: Sequence[str] | None = None, *, embed: EmbedFn | None = None) -> int: ...   # the WF-14 CLI
if __name__ == "__main__":
    raise SystemExit(main())
```

- `EmbedFn` is written as `npt.NDArray[np.float32]` instead of the sketch's bare `"np.ndarray"` because mypy strict rejects an
  unparameterised generic; same meaning. Write it as a `TypeAlias` assignment, the project's precedent
  (`privacy/redact.py`: `Redactor: TypeAlias = Callable[...]`; `pyproject.toml` ignores ruff `UP040`), not a PEP 695 `type`
  statement. Imports: `import numpy as np`, `import numpy.typing as npt`, `from collections.abc import Callable, Sequence`,
  `from typing import Final, Literal, TypeAlias`.
- `IngestError.__init__(self, message: str) -> None`: call `super().__init__(message)` and set
  `self.run: IngestRun | None = None`. `build_index` sets `exc.run` to the failed `IngestRun` before re-raising (§5 step 3.8).
  `IngestRun` is defined **above** `IngestError` in the file.
- `main`'s keyword-only `embed` is the test seam (DO-3 S-5): `None` means the real fastembed embedder. Nothing else reads it.
- Allowed imports: standard library, `numpy`, `pypdf` (`from pypdf import PdfReader`, `from pypdf.errors import
  PyPdfError`), `pydantic`, `meridian.domain.common`, `meridian.domain.records`, `meridian.ports.runtime`,
  `meridian.retrieval.settings`, `meridian.retrieval.manifest`. `fastembed` only **inside** `_fastembed_embed` (local
  import, so tests never load onnxruntime).

---

## 5. Steps (build order; each step ends with a check)

The slice stays inside DO-3's A3 boundary: `settings` ← `manifest` ← `ingest`, all depending only on `domain/`,
`ports/runtime.py` (A0) and third-party parsers. It implements no Protocol and consumes none; the embedder is a plain
callable (S-5 deferred). **Do not** add a module, a Protocol or a new public name beyond §4.

### Step 0 — Preflight (no edits)

```bash
cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-16
export UV_LINK_MODE=hardlink
df -h /home                                  # stop and report if under 4 GB free
git log --oneline -40 | grep -i "AEA-02"     # an AEA-02 merge must be listed (AEA-01 merged at 07924f5)
ls src/meridian/domain src/meridian/ports     # common.py, records.py, runtime.py present
grep -n "class Passage\b\|class Passage(" src/meridian/domain/records.py
grep -n "class IndexInfo" src/meridian/ports/runtime.py
grep -n "class PassageId\|class MeridianModel" src/meridian/domain/common.py
uv sync
uv run python -c "import meridian.domain.records, meridian.ports.runtime, numpy, pypdf, fastembed; print('ok')"
```

If any grep finds nothing, or `Passage`/`IndexInfo` fields differ from §4.1, **stop** and report `blocked-on AEA-02` (do
not define them locally).

### Step 1 — `settings.py`

Write §4.3 exactly. Check: `uv run python -c "from meridian.retrieval import settings as s; print(s.SEARCH_K, s.MIN_SCORE)"`
prints `3 0.6`.

### Step 2 — `manifest.py`, then `tests/unit/retrieval/test_manifest.py`

Write §4.4 (enums, models, validators, `MANIFEST` from the table, `StaffGuidance`). Then the tests in §7.1. Check:
`uv run pytest tests/unit/retrieval/test_manifest.py -q` green.

### Step 3 — `ingest.py`

Internal helper type: `@dataclass(frozen=True, slots=True) class _Chunk: section: str; text: str` (one field per line).

**3.1 Guard.** At the start of `build_index`: if `OVERLAP_CHARS != 0`, raise `IngestError("OVERLAP_CHARS other than 0 is not
implemented")`. *Invariant: a setting recorded in `index_record.json` is a setting the chunker actually applied.*

**3.2 Run identity.** `run_id = str(uuid.uuid4())`; `started_at = dt.datetime.now(dt.UTC)`. Everything from 3.3 to 3.8
runs inside one `try:` whose handlers are in 3.8.

**3.3 Output and listing checks (before any directory is created).**
1. If `out_dir.exists()`: raise `IngestError(f"output directory already exists: {out_dir}")`. *Invariant: a shipped index is
   never half-overwritten (PA-2).*
2. If `not kb_dir.is_dir()`: raise `MissingSource(f"knowledge base directory not found: {kb_dir}")`.
3. `on_disk = {p.relative_to(kb_dir).as_posix() for p in kb_dir.rglob("*") if p.is_file()}`;
   `listed = {spec.path for spec in MANIFEST}`.
4. `extra = sorted(on_disk - listed)`: if non-empty, raise `UnlistedFile(f"files not in MANIFEST: {extra}")`.
5. `absent = sorted(listed - on_disk)`; `absent_sources = [p for p in absent if status(p) in {CURRENT, STAFF_ONLY}]`.
   If `absent_sources`: raise `MissingSource(f"answer source missing: {absent_sources}")`. Elif `absent`: raise
   `UnlistedFile(f"MANIFEST rows with no file: {absent}")`. *Invariant: AC-1 and AC-6 both hold (D-1 in §8).*

**3.4 Readers and chunkers (private functions; read each file's bytes once, hash and parse that buffer).**
- `_read(path: Path, label: str) -> bytes`: `path.read_bytes()`; on `OSError` raise `MissingSource(f"{label}: unreadable")`.
  Decode text with `data.decode("utf-8-sig")`; on `UnicodeDecodeError` raise `MissingSource(f"{label}: not UTF-8")`.
- `_version_date(label: str) -> dt.date | None`: `re.search(r"(?<![0-9])([0-9]{4})-([0-9]{2})-([0-9]{2})(?![0-9])", label)`;
  if found, `dt.date(int(y), int(m), int(d))` (on `ValueError` → `None`); else `None`. "Effective 2026-01-01, supersedes
  all prior" → 2026-01-01; "Rev 2026-01", "undated", "2026", "2026 (image)" → `None`.
- `_cut(body: str) -> list[str]` (*invariant: no piece longer than `MAX_SECTION_CHARS`; every paragraph in exactly one piece,
  in order; no overlap*):
  1. If `len(body) <= MAX_SECTION_CHARS`: return `[body]`.
  2. `paras = [p.strip() for p in re.split(r"\n[ \t]*\n", body) if p.strip()]`.
  3. Units: each paragraph `<= MAX_SECTION_CHARS` is one unit; a longer paragraph is split at `"\n"` into lines and the lines
     greedily re-joined with `"\n"` while the joined length stays `<= PIECE_CHARS`; a single line longer than
     `MAX_SECTION_CHARS` is cut into consecutive slices of `PIECE_CHARS` characters.
  4. Greedy pack: `cur = ""`; for each unit `u`: `cand = u if not cur else cur + "\n\n" + u`; if `cur` and
     `len(cand) > PIECE_CHARS`: append `cur` to pieces, `cur = u`; else `cur = cand`. Append the last `cur`.
- `_chunk_markdown(text: str, *, file_name: str) -> list[_Chunk]` (DAT-11 heading split):
  1. Remove HTML comments: `re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)`.
  2. Walk `text.splitlines()`. A heading line matches `^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$`. On a heading: flush the buffer,
     then `heads = heads[: level - 1] + [title.strip()]` (level = number of `#`).
  3. Flush: `body = "\n".join(buf).strip()`. Skip it if empty, or if it is a single italic metadata line
     (`re.fullmatch(r"_[^\n]*_", body)`, e.g. `_Last updated: 2026-03-02_`). Otherwise `section = " > ".join(heads)` (or
     `file_name` when no heading has been seen yet) and emit one `_Chunk(section, piece)` per piece of `_cut(body)`.
  4. Flush once more at the end.
  Expected on the issued KB (planner's scratch run): `faq/customer_faq.md` 5 chunks with sections
  `Meridian Home Comfort — Customer FAQ > Hours & Contact` …; `membership/comfort_club_overview.md` 7 chunks incl.
  `Comfort Club Maintenance Plan > Plans > Comfort Club (Standard)`; no section is over 1,100 characters, so nothing is cut.
- `_pdf_text(data: bytes) -> str`: `PdfReader(io.BytesIO(data))`; for each page
  `page.extract_text(extraction_mode="layout")`; for each line: `line.strip()`, then `re.sub(r" {2,}", " | ", line)` (layout
  mode keeps table rows on one line; this turns column gaps into ` | `). Join lines with `"\n"`, pages with `"\n\n"`.
  Wrap `PdfReader` and extraction in `try/except PyPdfError` → `MissingSource(f"{label}: unreadable PDF")`.
  Planner's scratch run (pypdf 6.21.1, re-run at `16ca639`): layout mode puts a blank line between table rows, so each row is
  its own paragraph. First paragraph `Meridian Home Comfort — 2026 Residential Fee` / `Schedule` (the title → `section`), then
  `Effective January 1, 2026. Supersedes all prior fee schedules.`, the header row `Fee | Non-member | Comfort Club | Comfort
  Club Plus`, 13 rows such as `Diagnostic visit | $89 | Waived | Waived` and `After-hours emergency dispatch | $149 | Waived |
  Waived`, then the `Notes:` paragraph. Whole text 912 characters; body under 1,100 → **one chunk**.
- `_chunk_plain_text(text: str, *, file_name: str) -> list[_Chunk]` (TXT and the PDF's text; paragraph groups):
  1. Paragraphs = runs of non-blank lines (`line.strip()` non-empty), each joined with `"\n"`.
  2. If there are at least 2 paragraphs: `section = " ".join(paragraphs[0].split("\n"))` (the title, e.g.
     `Meridian Home Comfort — 2026 Residential Fee Schedule`) and the body is `paragraphs[1:]`; else `section = file_name`
     and the body is all paragraphs.
  3. `body = "\n\n".join(body_paragraphs)`; one `_Chunk(section, piece)` per piece of `_cut(body)`.
- `_chunk_csv(text: str, *, file_name: str) -> list[_Chunk]` (one chunk per data row):
  `reader = csv.DictReader(io.StringIO(text))`; `fields = reader.fieldnames or []`; for each row (1-based index `i`):
  `text = "; ".join(f"{f}: {row[f].strip()}" for f in fields if row.get(f) and row[f].strip())`; skip a row whose text is
  empty; `section = f"{row['category'].strip()} > {row['description'].strip()}"` when both columns exist and are non-empty,
  else `f"{file_name} > row {i}"`. Wrap in `try/except csv.Error` → `MissingSource`. Example:
  `HVAC repair > Run capacitor replacement` / `sku: HV-CAP-01; description: Run capacitor replacement; category: HVAC repair;
  low_price: 180; high_price: 260; member_discount_eligible: Y`. No invented sentence is added to any row.
- PNG: transcription path = `transcriptions_dir / (Path(spec.path).stem + ".md")`; missing or unreadable →
  `MissingSource(f"transcription missing for {spec.path}: {transcription_path.name}")`. Chunk the transcription with
  `_chunk_markdown(..., file_name=Path(spec.path).name)`; the chunks' `file` is the PNG's path. `source_sha256` =
  `hashlib.sha256(png_bytes + transcription_bytes).hexdigest()` (image bytes first, then transcription bytes).
- `_staff_passages(text: str) -> list[_Chunk]` (staff-only file; one passage per bullet, D-2 in §8):
  1. Remove HTML comments. Track `heads` exactly as in `_chunk_markdown`; on a heading also reset `lead_in = None`.
  2. A line matching `^\s*[-*+]\s+(.+)$` is a bullet: emit `_Chunk(section, bullet_text.strip())`, where `section` =
     `" > ".join(heads)` plus `" > " + lead_in` when `lead_in` is set.
  3. Any other non-blank line: if it ends with `":"`, set `lead_in = line.strip().rstrip(":").strip()`; else emit
     `_Chunk(" > ".join(heads), line.strip())` and set `lead_in = None`. Blank lines change nothing.
  On the issued file this gives 8 passages, e.g. `#0` section `Agent Discretion Guidelines (Internal Only) > Agents may,
  without supervisor approval`, text `Waive the $49 late-cancellation fee once per customer per year for a documented reason
  (illness, emergency).`; `#3` section `… > Agents may NOT`, text `Issue refunds of any kind.`; `#7` section
  `Agent Discretion Guidelines (Internal Only)`, text `Do not read this document to customers.`

**3.5 Per-file loop** (iterate `MANIFEST` in its sorted order):
1. `data = _read(kb_dir / spec.path, spec.path)`; `sha = hashlib.sha256(data).hexdigest()` (PNG: see 3.4).
2. `CURRENT`: chunk by `spec.parse_method` (`MARKDOWN` → `_chunk_markdown`, `TEXT` → `_chunk_plain_text`, `PDF_TEXT` →
   `_chunk_plain_text(_pdf_text(data))`, `CSV_ROWS` → `_chunk_csv`, `PNG_TRANSCRIPTION` → transcription). If a current file
   yields 0 chunks: raise `MissingSource(f"{spec.path}: no text extracted")`. For chunk index `n` from 0:
   `Passage.model_validate({"passage_id": f"{spec.path}#{n}", "file": spec.path, "section": c.section, "version_label":
   spec.version_label, "version_date": _version_date(spec.version_label), "text": c.text, "score": 0.0})`.
   `chunks = n_chunks`.
3. `STAFF_ONLY`: decode, `_staff_passages`, and for index `n` from 0 build
   `StaffGuidance.model_validate({"passage_id": f"{spec.path}#{n}", "file": spec.path, "section": c.section,
   "version_label": spec.version_label or "undated", "text": c.text, "text_sha256": sha256(c.text.strip())})`.
   `chunks = 0`.
4. `EXCLUDED`, `STUB`: nothing beyond the hash; `chunks = 0`. *Invariant (AC-2, AC-8): their bytes are hashed, never decoded
   into any artefact.*
5. Build `ManifestRow(path, status, version_label, parse_method, reason, source_sha256=sha, chunks=chunks)` with
   `ManifestRow.model_validate({...})`.

**3.6 Embed.** `texts = [p.section + "\n" + p.text for p in passages]` (from the validated `Passage`s). If `texts` is empty:
raise `IngestError("no passages to embed")`. `vecs = np.asarray(embed(texts), dtype=np.float32)`. Raise `IngestError` (message
with shapes only) unless `vecs.ndim == 2`, `vecs.shape[0] == len(texts)`, `vecs.shape[1] > 0`, `np.isfinite(vecs).all()`.
`norms = np.linalg.norm(vecs, axis=1)`; if any norm is 0, raise `IngestError`. `vecs = (vecs / norms[:, None]).astype(np.float32)`.
*Invariant: `vectors.npy` row i is passage line i, unit length (score = dot product).*

**3.7 Records.**
- `rows = sorted(rows, key=lambda r: r.path)` (17).
- `manifest_hash = hashlib.sha256(json.dumps([r.model_dump(mode="json") for r in rows], sort_keys=True,
  separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()`.
- `info = IndexInfo(embedding_model=EMBEDDING_MODEL, dimension=int(vecs.shape[1]), chunks=len(passages),
  manifest_hash=manifest_hash, files=len(rows))`.
- `index_record = {**info.model_dump(mode="json"), "settings": {name: value for name, value in vars(settings).items() if
  name.isupper()}}` (import the module as `from meridian.retrieval import settings`). Top level = the five `IndexInfo` fields
  plus one key `settings` holding `EMBEDDING_MODEL`, `SIMILARITY`, `CHUNKER`, `MAX_SECTION_CHARS`, `PIECE_CHARS`,
  `OVERLAP_CHARS`, `SEARCH_K`, `MIN_SCORE` by their Python names.

**3.8 Atomic write** (*invariant: `out_dir` either does not exist or holds a complete index*):
1. `out_dir.parent.mkdir(parents=True, exist_ok=True)`;
   `tmp = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.tmp-", dir=out_dir.parent))` (same filesystem, so the rename is
   atomic). Create it **after** step 3.3 and **before** step 3.5; write `ingest_run.json` with `status="started"` into it.
2. After 3.7, write into `tmp` (all text UTF-8, JSON with `indent=2, sort_keys=True, ensure_ascii=False` + trailing `"\n"`):
   `manifest.json` (list of the 17 rows' `model_dump(mode="json")`), `passages.jsonl` (one
   `json.dumps({**p.model_dump(mode="json", exclude={"score"}), "embed_text": p.section + "\n" + p.text}, sort_keys=True,
   ensure_ascii=False)` per line, `"\n"`-terminated, in passage order), `vectors.npy` (`np.save(tmp / "vectors.npy", vecs,
   allow_pickle=False)`), `index_record.json`, `staff_notes.json` (list of `StaffGuidance.model_dump(mode="json")`),
   `ingest_run.json` (status `completed`, `finished_at` now, `manifest_hash`, `files` 17, `chunks`, `embedding_model`
   `EMBEDDING_MODEL`, `failure` None).
3. `tmp.rename(out_dir)`; return the completed `IngestRun`.
4. Handlers: `except IngestError as exc:` set `exc.run = IngestRun(ingest_run_id=run_id, status="failed",
   started_at=started_at, finished_at=now, manifest_hash=<the hash if computed, else "">, files=<rows built so far or 0>,
   chunks=<passages so far or 0>, embedding_model=EMBEDDING_MODEL, failure=type(exc).__name__)` and re-raise. A
   `finally:` removes `tmp` with `shutil.rmtree(tmp, ignore_errors=True)` if it was created and not renamed (any exception
   type). Nothing is logged.

**3.9 `load_staff_guidance(index_dir)`.** Read `index_dir / "staff_notes.json"` (UTF-8), `json.loads`, return
`tuple(StaffGuidance.model_validate(item) for item in data)`. No other reads, no writes, no caching. A missing file raises
`FileNotFoundError` (the container fails start-up; that is the intended loud failure).

**3.10 CLI `main`.**
1. `argparse.ArgumentParser(prog="python -m meridian.retrieval.ingest", description="Build the KB index (WF-14).")` with
   `--kb-dir`, `--transcriptions-dir`, `--out-dir`, each `type=Path, required=True`. `args = parser.parse_args(argv)`
   (a missing argument exits 2 through argparse).
2. `embed_fn = embed if embed is not None else _fastembed_embed`, where
   `def _fastembed_embed(texts: Sequence[str]) -> npt.NDArray[np.float32]:` does `from fastembed import TextEmbedding`,
   `model = TextEmbedding(EMBEDDING_MODEL)` (cache directory from fastembed's own `FASTEMBED_CACHE_PATH` environment variable;
   no new flag), returns `np.asarray(list(model.embed(list(texts))), dtype=np.float32)`.
3. `try: run = build_index(args.kb_dir, args.out_dir, transcriptions_dir=args.transcriptions_dir, embed=embed_fn)`.
   `except IngestError as exc:` print to stdout
   `f"ingest_run_id={exc.run.ingest_run_id if exc.run else '-'} status=failed failure={type(exc).__name__}"`, print to stderr
   `f"{type(exc).__name__}: {exc}"`, return `1`.
4. On success read back `out_dir / "manifest.json"` and `out_dir / "index_record.json"`; print one line per row
   `f"{row['path']} status={row['status']} parse={row['parse_method']} chunks={row['chunks']}"`, then
   `f"ingest_run_id={run.ingest_run_id} status={run.status} files={run.files} chunks={run.chunks} dimension={record['dimension']} manifest_hash={run.manifest_hash}"`;
   return `0`. *Invariant (AC-8): stdout carries paths, IDs, counts, statuses and hashes; never chunk text.*

Check: `uv run python -c "import meridian.retrieval.ingest"`.

### Step 4 — `tests/unit/retrieval/test_ingest.py`

Write the tests in §7.1. Check: `uv run pytest tests/unit/retrieval -q` green.

### Step 5 — Fast gates (cheapest first; stop at the first red) — §7.3.

### Step 6 — The real-embedder run (AC-9 evidence) — §7.4.

### Step 7 — Commit 1 (code and tests)

```bash
git add src/meridian/retrieval/settings.py src/meridian/retrieval/manifest.py src/meridian/retrieval/ingest.py \
        tests/unit/retrieval/test_manifest.py tests/unit/retrieval/test_ingest.py
git commit -m "feat(retrieval): KB manifest and ingestion to the index directory (AEA-16)" \
  -m "WF-14 entry point: python -m meridian.retrieval.ingest. 17-file manifest, heading-split chunking, staff notes kept out of the index." \
  -m "Refs #16" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

### Step 8 — Journey record, context rows, dev log (AC-10, AC-11). Read each target line first; wave-1 siblings may have edited nearby.

1. Run `uv run python -m tests.journeys.affected --base main` and keep its output (expect `0 journeys affected`, exit 0).
2. Create `docs/testing/journeys/<YYYY-MM-DD>-AEA-16.md`:

   ```markdown
   # Journey record — AEA-16 (retrieval/{settings,manifest,ingest}.py)

   | Field | Value |
   |---|---|
   | Claim | AEA-16 AC-10: no journey runs yet. This code will be exercised by J-2 (membership, billing and warranty answers from the ingested KB; stale twins excluded) once AEA-51 lands the graph on AEA-57's harness |
   | Level | `mock-tested` |
   | Tested revision | `<commit-1 sha>` |
   | Environment | VPS worktree `inno-aea-callcenter-wt/AEA-16`; `uv run`, Python 3.12; no server, no database; stand-in `EmbedFn` in tests; one real fastembed `BAAI/bge-small-en-v1.5` CLI run |
   | Command | `uv run pytest tests/unit/retrieval -q`; `uv run python -m tests.journeys.affected --base main`; the real CLI command from the report |
   | Result | <pytest summary line>; affected: `<changed files line>` then `0 journeys affected`, exit 0; real run: files=17, chunks=<n>, dimension=<d> |
   | Evidence location | this record; the implementer's report on issue #16 |
   | Remaining limitations | No retrieval search (AEA-33), no E-2 run (AEA-24), no image build (AEA-50); chunking constants are [A] until the first E-2 run |
   | Blocked by | AEA-57 (journey harness); J-2's answer steps also wait on AEA-33 and AEA-51 |
   ```
3. `.claude/reference/area-map.md`, row `| 1 | **A3 Retrieval** | …` (currently ends `| AEA-16, 33 | planned |`): change
   **only the last cell** from `planned` to (the A0 row's wording is the precedent)
   ``partly built: `retrieval/{settings,manifest,ingest}.py` actual (AEA-16, `<commit-1 sha>`); `adapters/retrieval_fastembed.py`, `agent/tools/knowledge.py` planned (AEA-33)``.
4. `.claude/state/icm-progress.md`: directly after the **last** row that starts `| Routes verified against code and tests |`
   (today the AEA-03 row), add one row in the same shape (precedent: the AEA-03 and AEA-04 rows):
   ``| Routes verified against code and tests | provisional | <date>: area map A3 → `retrieval/{settings,manifest,ingest}.py` checked against `tests/unit/retrieval/` (AEA-16, `<commit-1 sha>`; <n> pass) | Each slice adds its route; verified when every area-map row is actual |``
   Row ≤ 400 characters. Do not edit the other rows or the *Last reconciled* line.
5. `docs/design/code-design.md` §3: directly after the **last** line in §3 that starts `**Built:**` (today
   ``**Built:** `policy/texts.py` (AEA-03, `2689582`).``), add one line:
   ``**Built:** `retrieval/{settings,manifest,ingest}.py` (AEA-16, `<commit-1 sha>`).`` Touch nothing else (the tree
   already lists `settings.py`; the line-7 *Built so far* note belongs to AEA-01).
6. `docs/design/contracts/internal-components.md` §13: directly after the last `> Superseded at Stage 7: …` note and before
   the ```` ```python ```` block, add one blank line and this note:

   > Built (AEA-16, `<commit-1 sha>`): the index directory `retrieval/ingest.py` writes. `manifest.json` (17 `ManifestRow`s
   > sorted by `path`); `passages.jsonl` (one `Passage` per line without `score`, plus `embed_text` = `section + "\n" + text`;
   > row order = vector order); `vectors.npy` (float32 `[chunks, dimension]`, L2-normalised); `index_record.json` (the five
   > `IndexInfo` fields at the top level plus `settings`, every `retrieval/settings.py` constant by its Python name; read it as
   > `IndexInfo.model_validate({k: record[k] for k in IndexInfo.model_fields})`); `ingest_run.json` (`IngestRun`);
   > `staff_notes.json` (`StaffGuidance` list, one per bullet, never embedded). `manifest_hash` = SHA-256 of the canonical
   > JSON (sorted keys, separators `(",", ":")`, UTF-8) of the 17 rows' `model_dump(mode="json")` in `path` order, including
   > `source_sha256` (for the PNG: the image bytes followed by the transcription bytes) and `chunks`. Shapes:
   > [stage7/data.md](stage7/data.md) §3.
7. Dev log: create `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<YYYY-MM-DD>-aea-16-retrieval-ingest-claude-01.md`
   per `.claude/reference/dev-log.md` (header: project, date and timezone America/Chicago, topic, writer "Claude Sonnet
   (fanout-implementer)", host VPS, branch `aea-16-retrieval-ingest`, base SHA; one entry with **Changed / Why / Checked /
   Remaining**, 50–100 words; the real run's `files`, `chunks`, `dimension` as measured). It lives outside this repo: do not
   `git add` it here.

### Step 9 — Commit 2 (record and context)

```bash
git add docs/testing/journeys/<YYYY-MM-DD>-AEA-16.md .claude/reference/area-map.md .claude/state/icm-progress.md \
        docs/design/code-design.md docs/design/contracts/internal-components.md
git commit -m "docs(context): AEA-16 retrieval build recorded; journey record mock-tested" -m "Refs #16" \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
git diff --name-only main...HEAD     # must list exactly the 5 code/test files and these 5 docs
```

### Step 10 — Report

Each AC (and PA-1…PA-5) verified or not, with the command and the result line; the real CLI output (AC-9); the gates'
output; the two commit SHAs; anything this plan got wrong.

### What the implementer must not do

- Edit any file outside §2.1, including `retrieval/__init__.py`, `pyproject.toml`, `uv.lock`, `domain/*`, `ports/*`.
- Write into `docs/data/issued/` or `data/kb_transcriptions/` (tests copy them into `tmp_path`).
- Import anything from `docs/parked/`, or copy its invented CSV sentence ("Exact pricing is confirmed by the technician on
  site.") or its `P000` ids or keyword boost.
- Add a search, relevance floor, readiness check, keyword/hybrid search, DB row, eval case, Dockerfile line or register hunk.
- Add a CLI flag, a public name, a field, or an exception class beyond §4.
- Print, log or put in an exception message any chunk text; use `assert` in `src/`; load fastembed at module import.
- Run the real embedder inside a default test, or mark a test `live` to get around that.
- `git add -A`, push, force-push, or bind ports 4019 / 5184.

---

## 6. Data and fixtures

All inputs are issued (read-only) or synthetic; no personal data, no codes, no card-like or phone numbers.

| Fixture | Source | Used by |
|---|---|---|
| `ISSUED_KB = ROOT / "docs/data/issued/meridian_dataset/knowledge_base"`, `TRANSCRIPTIONS = ROOT / "data/kb_transcriptions"`, `ROOT = Path(__file__).resolve().parents[3]` | issued KB (S-102…S-105) and the hand transcription (verified 2026-10-20) | all tests; read in place only when nothing is modified |
| `kb_copy(tmp_path) -> Path`: `shutil.copytree(ISSUED_KB, tmp_path / "kb")`; same for `tr_copy` (`tmp_path / "tr"`) | copies of the above | every test that edits, adds or removes a file |
| `_fake_embed(texts) -> npt.NDArray[np.float32]`: for each text, `np.frombuffer(hashlib.sha256(t.encode("utf-8")).digest()[:8], dtype=np.uint8).astype(np.float32) + 1.0`; `np.stack(rows)` (dimension 8, never zero, deliberately not normalised) | synthetic, deterministic | every `build_index` / `main` call in tests |
| Module-scoped fixture `built(tmp_path_factory) -> Path`: one `build_index(ISSUED_KB, <factory dir>/index, transcriptions_dir=TRANSCRIPTIONS, embed=_fake_embed)` reused by read-only tests | — | AC-2, AC-3, AC-5, AC-7, PA-1 |
| Synthetic Markdown (AC-4), written over `services/technician_arrival_and_etas.md` in a KB copy: `# Synthetic Policy\n_Effective: 2026-01-01_\n\n## Long Section\n\n` + four paragraphs joined by `"\n\n"`, paragraph `k` (1…4) = `f"Paragraph {k} " + " ".join(["alpha", "bravo", "charlie", "delta"] * 24)` (each about 635 characters; section about 2,550, so each paragraph becomes its own piece: 4 pieces) | synthetic, labelled in the test docstring | `test_heading_split_and_long_section_cut` |
| Sentinels (AC-8): `SENTINELARCHIVEQX`, `SENTINELSTUBQX`, `SENTINELSTAFFQX`, each appended as `"\n- <sentinel> line\n"` to the KB copy's `archive/comfort_club_overview.md`, `services/duct_cleaning.md`, `internal/agent_discretion_notes.md` | synthetic | `test_excluded_text_absent` |
| The five `STAFF_GUIDANCE_FOR` prefixes, copied as string literals into the test (do not import AEA-14's `policy/handoff.py`): `"Waive the $49 late-cancellation fee once per customer per year"`, `"Waive the diagnostic fee when the technician arrived more than 30 minutes"`, `"Extend a 10% courtesy discount on a repair invoice under $500"`, `"Issue refunds of any kind."` (the BILLING_DISPUTE and COMPLAINT_OR_MANAGER prefixes are the same string) | `stage7/cases.md` §5, quoted from the KB file | `test_staff_notes_written_not_indexed` |

---

## 7. Checks

### 7.1 Tests the implementer writes with the code (names are binding)

`tests/unit/retrieval/test_manifest.py`:

| Test | Asserts |
|---|---|
| `test_manifest_covers_all_17_issued_files` (AC-1) | `{p.relative_to(ISSUED_KB).as_posix() for p in ISSUED_KB.rglob("*") if p.is_file()} == {s.path for s in MANIFEST}`; `len(MANIFEST) == 17`; no duplicate path; `MANIFEST` sorted by path; every CURRENT row has a non-empty `version_label` and `reason is None`; every other row has a non-empty `reason`; EXCLUDED = {`archive/comfort_club_overview.md`, `archive/warranty_terms_2023.txt`, `faq/faq_old_copy.md`, `services/scheduling_guide.md`}, STAFF_ONLY = {`internal/agent_discretion_notes.md`}, STUB = {`services/duct_cleaning.md`}, CURRENT = the other 11; `parse_method` matches the extension map (§4.4) for all 17. Print the 17 `path status parse_method` lines |
| `test_validators_reject_bad_rows` (PA-4) | `ManifestSpec.model_validate` of a CURRENT spec with `version_label=None` and of an EXCLUDED spec with `reason=None` each raise `ValidationError` whose `errors()[0]["type"]` is `manifest_current_row` / `manifest_reason_required`; `ManifestRow` with status EXCLUDED and `chunks=1` → `manifest_noncurrent_chunks`; `StaffGuidance` with a wrong `text_sha256` → `staff_guidance_hash_mismatch`; a valid `StaffGuidance` round-trips |
| `test_manifest_and_settings_import_no_heavy_stack` (PA-3) | AST-scan `src/meridian/retrieval/manifest.py` and `settings.py`: no import whose top-level module is `numpy`, `pypdf`, `fastembed`, `onnxruntime`; `settings.py` imports only `__future__` and `typing` |

`tests/unit/retrieval/test_ingest.py`:

| Test | Asserts |
|---|---|
| `test_unlisted_file_fails_build` (AC-1) | KB copy + extra file `faq/extra_notes.md` → `pytest.raises(UnlistedFile)`, message contains `faq/extra_notes.md`; second KB copy with `archive/warranty_terms_2023.txt` deleted → `UnlistedFile` naming it; in both, `out_dir` does not exist and no `.<name>.tmp-*` entry remains in its parent; `exc.run.status == "failed"`, `exc.run.failure == "UnlistedFile"` |
| `test_only_current_files_indexed` (AC-2) | From `built`: the set of `file` values in `passages.jsonl` equals the 11 CURRENT paths; none of the 6 non-current paths appears; every non-current `manifest.json` row has `chunks == 0`; every CURRENT row has `chunks > 0`; the sum of `chunks` equals the line count |
| `test_each_format_parsed` (AC-3) | PDF: ≥ 1 passage for `pricing/2026_fee_schedule.pdf`, one contains `Diagnostic visit` and `$89`; CSV: passages for `pricing/repair_price_book_2026.csv` = the number of data rows `csv.DictReader` reads from the issued file (21), one contains `sku: HV-CAP-01`; PNG: passages for `policies/holiday_hours_2026.png` contain `Christmas Eve`; the PNG row's `source_sha256 == sha256(png_bytes + transcription_bytes)` and `!= sha256(png_bytes)`; a build on a transcription copy with one line changed gives a different PNG `source_sha256`; every row's `parse_method` matches the extension map |
| `test_heading_split_and_long_section_cut` (AC-4) | Synthetic file (§6): its passages number ≥ 3; every `text` ≤ 1,100 characters; every `section == "Synthetic Policy > Long Section"`; `"\n\n".join(texts)` equals the four paragraphs joined by `"\n\n"` (no repeat, no loss); ids are `services/technician_arrival_and_etas.md#0…#k-1` |
| `test_chunk_provenance` (AC-5) | From `built`: membership passages have `version_label == "Effective 2026-01-01"` and `version_date == "2026-01-01"`; `policies/escalation_and_safety.md` (`Rev 2026-01`) and `faq/troubleshooting_before_you_call.md` (`undated`) have `version_date is None`; the fee PDF has `2026-01-01`; ids unique and, per file, exactly `f"{file}#{n}"` for n = 0…count-1; every line's `embed_text == section + "\n" + text` and no line has a `score` key; `np.load(vectors.npy, allow_pickle=False)` has shape `(lines, 8)`, dtype float32, every row norm 1 ± 1e-5 |
| `test_missing_source_fails_build` (AC-6) | KB copy with `pricing/2026_fee_schedule.pdf` deleted → `MissingSource`, message contains `pricing/2026_fee_schedule.pdf`; transcription copy with `holiday_hours_2026.md` deleted (full KB) → `MissingSource`, message contains `holiday_hours_2026.md`; `out_dir` absent and no temp entry left after both; `exc.run.failure == "MissingSource"` |
| `test_cli_exit_codes` (AC-6) | `main([...], embed=_fake_embed)` on the issued KB → `0`, stdout has `status=completed` and `files=17`; with the PDF removed from a KB copy → `1`, stdout has `failure=MissingSource`, stderr starts with `MissingSource:`; `main(["--kb-dir", "x"])` raises `SystemExit` with code 2 |
| `test_staff_notes_written_not_indexed` (AC-7) | From `built`: `load_staff_guidance(built)` returns ≥ 1 `StaffGuidance`; each `text_sha256 == sha256(text)`; each id starts with `internal/agent_discretion_notes.md#`; it equals the tuple parsed from `staff_notes.json`; none of their ids or texts appears in `passages.jsonl`; for **each** of the five prefixes some passage's `text.startswith(prefix)`; the `Issue refunds of any kind.` passage's `section` ends with `Agents may NOT` |
| `test_excluded_text_absent` (AC-8) | KB copy with the three sentinels (§6), `caplog.set_level(logging.DEBUG)`, `main([...], embed=_fake_embed) == 0`; read all six artefacts as bytes: `SENTINELARCHIVEQX` and `SENTINELSTUBQX` in none of them and not in `capsys` stdout/stderr or `caplog.text`; `SENTINELSTAFFQX` in `staff_notes.json` only (not in the other five, not in captured output) |
| `test_entry_point_writes_wf14_records` (AC-9) | `main` to `out1`: `manifest.json` has 17 rows each with `path, status, version_label, parse_method, reason, source_sha256, chunks`; `index_record.json` has `embedding_model == "BAAI/bge-small-en-v1.5"`, `dimension == 8`, `chunks` = line count, `files == 17`, `manifest_hash`, and `settings` equal to every upper-case name in `meridian.retrieval.settings`; `IndexInfo.model_validate({k: rec[k] for k in IndexInfo.model_fields})` succeeds; `ingest_run.json` has a UUID4 `ingest_run_id`, `status == "completed"`, `failure is None`, and the same `manifest_hash`, `files`, `chunks`, `embedding_model`. Second run to `out2` on the same inputs: same `manifest_hash`. Third run on a KB copy with one byte appended to `policies/service_area.md`: different `manifest_hash`. A failing `build_index` (PDF removed) gives `exc.run.status == "failed"`, `exc.run.failure == "MissingSource"` |
| `test_wp1_stale_twin_by_path` (PA-1, WP-1 worked pair) | From `built`: passages for `membership/comfort_club_overview.md` exist, all with `version_label == "Effective 2026-01-01"`, and one contains `$189`; no passage `file` starts with `archive/`; the `archive/comfort_club_overview.md` row is `excluded` with a reason and `chunks == 0`; some fee-schedule passage contains `$149` (legitimate after-hours fee, WP-2), proving the check is by path, not by text |
| `test_existing_out_dir_refused` (PA-2) | `out_dir` pre-created with a file `keep.txt` → `pytest.raises(IngestError)` (exactly the base class: `type(exc) is IngestError`); `keep.txt` still there, nothing else written |
| `test_plain_text_paragraph_groups` (PA-5) | `ingest._chunk_plain_text("TITLE LINE\n\nPara one.\n\nPara two.", file_name="x.txt")` → one chunk, section `TITLE LINE`, text `Para one.\n\nPara two.`; a one-paragraph text → section `x.txt` |

Use `pytest.raises(...) as ei` and read `ei.value.run`. Type-annotate test functions (mypy runs on `tests/`).

### 7.2 Existing tests that must stay green

`tests/unit/test_skeleton.py` (imports `meridian.retrieval`), `tests/unit/test_import_direction.py`. Find any other test that
imports the changed modules: `grep -rl "meridian.retrieval" tests/ eval/` (expected: only the two new files).

### 7.3 Gates (run in this order; stop at the first red)

```bash
cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-16
export UV_LINK_MODE=hardlink
uv run ruff format --check src/meridian/retrieval tests/unit/retrieval
uv run ruff check src/meridian/retrieval tests/unit/retrieval
uv run mypy src/meridian/retrieval tests/unit/retrieval
uv run pytest tests/unit/retrieval tests/unit/test_skeleton.py tests/unit/test_import_direction.py -q
uv run python -m tests.journeys.affected --base main        # expect "0 journeys affected", exit 0
```

Passing looks like: format and lint clean, `Success: no issues found` from mypy, all listed tests passed (no skips), and
`0 journeys affected`. No full suite: this change touches no shared fixture, settings, dependency or cross-codebase module.
Run pytest serially (the tests take seconds); never above `-n 2`.

### 7.4 The real-embedder run (AC-9 evidence; once, by the implementer, not a test)

```bash
cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-16
FASTEMBED_CACHE_PATH=/home/linuxuser/workspaces/inno-aea-callcenter/var/fastembed \
  uv run python -m meridian.retrieval.ingest \
    --kb-dir docs/data/issued/meridian_dataset/knowledge_base \
    --transcriptions-dir data/kb_transcriptions \
    --out-dir /tmp/aea16-index-real
echo "exit=$?"
rm -rf /tmp/aea16-index-real
```

The cache in the main checkout's `var/fastembed/` already holds `Qdrant/bge-small-en-v1.5-onnx-Q`; if fastembed still
downloads, report it and the disk use. Paste the stdout (17 row lines + the summary line). Expected from the planner's
scratch run: `files=17`, `chunks` about 56, `dimension=384`; these are measurements to report, not targets to meet.

---

## 8. Risks and requests

### 8.1 Engineering decisions made in this plan (each reversible in a follow-up before AEA-33 / AEA-29 / AEA-51 merge)

- **D-1. Missing listed file: which error.** data.md §3 defines `UnlistedFile` as "a MANIFEST row with no file" and
  `MissingSource` as "unreadable answer source"; a deleted current file is both. AC-1 deletes a listed file and expects
  `UnlistedFile`; AC-6 deletes the PDF and expects `MissingSource`. Rule chosen: an absent CURRENT or STAFF_ONLY file →
  `MissingSource`; an absent EXCLUDED or STUB file → `UnlistedFile`. AC-1's test therefore deletes
  `archive/warranty_terms_2023.txt`. Both still write nothing and exit non-zero, so AEA-50's build fails either way.
- **D-2. Staff notes: one passage per bullet, lead-in in `section`.** cases.md §5 keys `STAFF_GUIDANCE_FOR` on "the bullet's
  opening words", and the REFUND reason maps to `Issue refunds of any kind.` alone. Whole-file chunking would attach every
  line to every reason and break a `startswith` resolver. The lead-in (`Agents may NOT`) goes in `section` so the meaning is
  not lost. **Request to the AEA-29 / AEA-51 planners:** show `section` with `text` wherever guidance is displayed.
- **D-3. `index_record.json` shape:** the five `IndexInfo` fields at the top level plus a `settings` object. AEA-33 reads
  `IndexInfo` by selecting `IndexInfo.model_fields` (recorded in DO-4 §13 by step 8.6).
- **D-4. An existing `out_dir` is refused** rather than replaced. **Note for AEA-50:** the Docker `index` stage must write to a
  fresh path, and must set `FASTEMBED_CACHE_PATH` (or pre-download) so the model is cached in the image.
- **D-5. PDF text via pypdf `extraction_mode="layout"`, column gaps → ` | `.** Default extraction puts every table cell on its
  own line, losing which price belongs to which plan; layout mode keeps rows. The fee table (857 characters) is one chunk with
  its header row. If a later PDF grows past 1,100 characters, later pieces would lose the header row; not the case for the
  issued file.
- **D-6. A lone italic metadata line under an H1** (`_Last updated: 2026-03-02_`) is not its own chunk; its date is in
  `version_label`. Bodies with content keep the line.
- **D-7. CSV rows rendered faithfully as `column: value` pairs.** The parked code's added sentence about on-site pricing is
  not in the source and is dropped (source-authority rule 2; a passage holds only what the file says).
- **D-8. Version labels drop the file's colon** ("Effective: 2026-01-01" → "Effective 2026-01-01") to match the ticket's
  examples; the PNG's label is `2026 (image)`.

### 8.2 Collisions with other slices

- `.claude/reference/area-map.md` A3 row: AEA-33 (wave 2) edits the same row later; this plan only changes its last cell.
- `.claude/state/icm-progress.md` (a new row after the last *Routes verified* row) and DO-3 §3 (a new line after the last
  `**Built:**` line): every wave-1 ticket inserts at the same spot. Expect a trivial insert-insert conflict at merge; the
  merge keeps **both** lines (the AEA-03/AEA-04 merges did the same).
- `docs/design/contracts/internal-components.md` §13: AEA-02 does not edit DO-4; AEA-33 may add its own note in §13 later.
  This plan's edit is one blockquote note only. (The earlier version of this plan warned about uncommitted DO-4 edits in the
  main checkout; at `16ca639` the main checkout has none.)
- No source-file overlap with any other ticket: `retrieval/{settings,manifest,ingest}.py` are this ticket's alone.

### 8.3 Shared primitives needed

None. Everything comes from AEA-02 (`MeridianModel`, `PassageId`, `Passage`, `IndexInfo`) and AEA-01 (package, dependencies,
affected-journeys command).

### 8.4 Spec gaps and stale references (report only)

- data.md §3 cites "AEA-16 AC-5 / AC-7 / AC-8" from an earlier numbering (now AC-6, AC-9, AC-11). For AEA-08; not edited here.
- `faq/customer_faq.md` (dated FAQ) and the service catalog both state appointment windows and fees that overlap the fee PDF;
  conflicts between current files are the responder's and E-2's concern, not ingestion's. No action here.

### 8.5 Other risks

- `pypdf` layout output may change between versions; `uv.lock` pins the version. `CHUNKER = "heading-split/1"` is the
  version string to bump when chunking behaviour changes (recorded in `index_record.json`).
- The fastembed cache lives in the main checkout's `var/` (git-ignored). If it is missing, the real run downloads about
  70 MB; check `df -h /home` first.

---

## 9. Readiness

**READY**, **blocked-on AEA-02** only (a true import: `MeridianModel`, `PassageId` from `domain/common.py`, `Passage` from
`domain/records.py`, `IndexInfo` from `ports/runtime.py`; none exists on `main` at `16ca639`). AEA-01 is merged
(`07924f5`: the `meridian.retrieval` package, `numpy`/`pypdf`/`fastembed` in the lock, `tests/unit/retrieval/__init__.py`, the
affected-journeys command). No sibling is called at run time: AEA-33, AEA-29, AEA-50 and AEA-51 consume this ticket's
output, so nothing needs a double. Step 0 verifies AEA-02. No product decision is needed, no signed contract changes, and no
decision D-4…D-15 touches this ticket.

## Gates

None (no human, external, paid or live gate). The one real-embedder run is local and unpaid.
