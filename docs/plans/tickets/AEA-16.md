## [AEA-16] retrieval: manifest and ingestion of the 17 KB files

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

> **US-6.** As a **homeowner**, I need answers about membership, billing fees, warranty, services, hours and the service
> area that come from Meridian's current documents and show where they came from, so that I can trust the number I'm
> given. *(Acceptance: the answer names its source and version date, for example the 2026 fee schedule PDF or the
> holiday-hours image; never an archived copy.)*

**What it does in practice.** One command (the WF-14 entry point) reads the issued knowledge base, decides for each of
the 17 files whether it may be an answer source, cuts every answer-source file into chunks that each carry their file,
section and version, embeds them with `BAAI/bge-small-en-v1.5`, and writes one index directory that the rest of the
system reads. AEA-50's Dockerfile runs the command at `docker build` (DO-1 §11 decision 10); AEA-33's `FastembedIndex`
loads the directory and reports not-ready when the record disagrees. The staff-only discretion notes are written to a
separate file that is never embedded, so staff can see them on a case brief while no customer search can ever return
them.

**How it works: three modules, exactly as stage7/data.md §3 sketches them** (A3; DO-3 §3, §4.3):

1. **`retrieval/settings.py`** (new file owned here, data.md §3, so retrieval rule 5 "configuration lives in one place"
   holds): `EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"` (R-11), `SIMILARITY = "cosine"` (vectors L2-normalised),
   `CHUNKER = "heading-split/1"`, `MAX_SECTION_CHARS = 1100`, `PIECE_CHARS = 900`, `OVERLAP_CHARS = 0`, `SEARCH_K = 3`,
   `MIN_SCORE = 0.60`. All except the model are [A] until the first E-2 run (DAT-11, DAT-17). `SEARCH_K` and
   `MIN_SCORE` are read by AEA-33; they live here so every retrieval constant is recorded in the index record.
2. **`retrieval/manifest.py`**: `FileStatus` (`current`, `excluded`, `staff_only`, `stub`), `ParseMethod` (`markdown`,
   `text`, `pdf_text`, `csv_rows`, `png_transcription`), `ManifestSpec`, `ManifestRow`, and `MANIFEST`, exactly 17 specs
   seeded from the parked `docs/parked/2026-10-21-first-attempt/src_meridian/kb/manifest.py` and checked against PRD R-10 and §4.3a:
   - **excluded, never indexed:** `archive/comfort_club_overview.md`, `archive/warranty_terms_2023.txt`,
     `faq/faq_old_copy.md`, `services/scheduling_guide.md` (R-10, DEC-4);
   - **staff-only, never in the customer index:** `internal/agent_discretion_notes.md` (R-10, audit K-15);
   - **stub, not answered from:** `services/duct_cleaning.md` (R-10, audit K-14; DAT-18);
   - **current:** the other 11 files, each with its version label as the file states it ("Effective 2026-01-01",
     "Rev 2026-01", "undated", …).
   `reason` is required on every non-current row. Also `StaffGuidance` (`passage_id`, `file` =
   `internal/agent_discretion_notes.md`, `section`, `version_label`, `text`, `text_sha256`), placed here, pydantic only,
   so `services/handoff.py` (AEA-29) can import it without the embedding stack (MC-26).
3. **`retrieval/ingest.py`**: `IngestError` with `UnlistedFile` and `MissingSource`; `EmbedFn`; `IngestRun`;
   `build_index(kb_dir, out_dir, *, transcriptions_dir, embed) -> IngestRun`; `load_staff_guidance(index_dir) ->
   tuple[StaffGuidance, ...]` (a pure read); and the CLI
   `python -m meridian.retrieval.ingest --kb-dir PATH --transcriptions-dir PATH --out-dir PATH` (exit 0 on `completed`;
   non-zero with the `IngestError` class name on failure; stdout carries IDs, counts and statuses only).
   - **Chunking (DAT-11, [A]):** Markdown split at headings, the heading path is `section`; a section over 1,100
     characters is cut at blank-line paragraphs into pieces of about 900; no overlap. The price-book CSV
     (`pricing/repair_price_book_2026.csv`) is one chunk per data row. The fee PDF (`pricing/2026_fee_schedule.pdf`) and
     TXT files go by paragraph groups. The holiday PNG goes through the hand-verified transcription
     `data/kb_transcriptions/holiday_hours_2026.md` (verified by eye 2026-10-20), linked to the image (R-9;
     hard-problems *Handled by default*). Basis: every KB file is ≤ 2.1 KB with 1–8 headings, so a ~500-token default
     would make most files one chunk and lose section citations (DAT-11, source-authority rule 2).
   - **Every chunk** becomes a DO-4 §5 `Passage` (without `score`): `passage_id` of the shape `<file path>#<chunk n>`
     (DO-4 §0; minted here, DO-4 superseded note on `build_index.py`), `file`, `section`, `version_label`, and
     `version_date` parsed only when the label holds a full date, else `None` (UXR-24).
   - **Atomic write:** `build_index` writes into a temp directory and renames it into `out_dir` only on success, so a
     failed build leaves no partial index (data.md §3).

**The index directory** (data.md §3 *Index directory layout*):

| File | Holds | Read by |
|---|---|---|
| `manifest.json` | 17 `ManifestRow`s sorted by `path` (`source_sha256` of the issued bytes, and of the transcription for the PNG; `chunks` = 0 on every non-current row) | AEA-33 readiness (`files == 17`), CAP-9 |
| `passages.jsonl` | one `Passage` per line without `score`, plus `embed_text` (`section + "\n" + text`); row order = vector order | AEA-33 |
| `vectors.npy` | float32 `[chunks, dimension]`, L2-normalised | AEA-33 |
| `index_record.json` | the DO-4 §13 `IndexInfo` fields + every `retrieval/settings.py` constant | AEA-33 `info()`, AEA-24 (E-2 names its index), CAP-9 |
| `ingest_run.json` | `IngestRun`: `ingest_run_id` (UUID4), `status` (`started`/`completed`/`failed`), `started_at`, `finished_at`, `manifest_hash`, `files`, `chunks`, `embedding_model`, `failure` (the `IngestError` class name only) | CAP-9; no DB row (DAT-12) |
| `staff_notes.json` | the staff-only file's `StaffGuidance` passages; never embedded, never in `passages.jsonl` | `load_staff_guidance` → AEA-29 via the container (DAT-13, CAS-33) |

**`manifest_hash`** = SHA-256 of the canonical JSON (sorted keys, no whitespace) of the 17 rows including
`source_sha256` and `chunks`: the same inputs give the same hash; one changed KB byte gives a different one (data.md §3).

**Example pair (WP-1, stale twin).** Input: the issued KB, which holds both `membership/comfort_club_overview.md`
(Effective 2026-01-01: $189/year, $16.99/month with a 12-month minimum, Plus $269/year) and its near-identical
`archive/comfort_club_overview.md` ($149, $12.99, "cancel any time"). Expected output: `manifest.json` marks the current
file `current` with version label "Effective 2026-01-01" and the archive file `excluded` with its reason and
`chunks` 0; `passages.jsonl` holds chunks whose `file` is `membership/comfort_club_overview.md` carrying that version, and
**no chunk whose `file` is any excluded, staff-only or stub file**. (Check by file path, not by text: the current fee
schedule legitimately contains "$149" as the after-hours fee, WP-2.)

### Source
- PRD R-9, R-10, R-11 (§4.3), §4.3a knowledge map (the 17 files, current vs never-from); US-6, US-7.
- stage7/data.md §3 (every type, constant, file and the CLI above), §9 item 4 (staff guidance to AEA-29); decision
  ledger `docs/plans/7b-decisions/data.md` DAT-11 (chunking [A]), DAT-12 (`ingest_run.json`, no DB row), DAT-13
  (`staff_notes.json`, `load_staff_guidance`), DAT-17 (k and floor), DAT-18 (stub not indexed); merge-clashes MC-26
  (`StaffGuidance` in `manifest.py`); stage7/cases.md §5 `STAFF_GUIDANCE_FOR` and A-14 (the consumer side).
- DO-4 §0 (`PassageId` shape and the Stage 7 superseded note), §5 (`Passage`), §13 (`IndexInfo`, `RetrievalIndex.info`),
  §16 (addenda win).
- DO-3 §3 (A3), §4.3 (readiness: 17 manifest files, dimension), §6 S-4, S-5 (embedder port deferred: `EmbedFn` is a
  plain callable), §7 rows R-9/R-10/R-11, §2.4 *kb/* row.
- DO-1 §11 decision 10 (index built at deploy, ships in the image), §8.2 *Retrieval index* row, §9 (the build cannot
  write the volume).
- DO-6 registry row WF-14 (ingest_run, ingestion manifest with 17 files and parse method each, index record; EV: E-2;
  M-6, M-7), *Content and redaction* rule 3 (IDs, counts, statuses in logs), CAP-9.
- `.claude/rules/retrieval-and-context.md` rules 2, 5, 6, 7; `.claude/rules/source-authority.md` rule 2; issued data
  `docs/data/issued/README.md`; WP-1, WP-2.
- **Brief check:** serves "The knowledge base may contain tables, images, or inconsistent formatting; your pipeline must
  account for what is actually in the docs, not what you assumed was there."; touches nothing out of scope; weakens
  nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] `MANIFEST` lists **every one of the 17 issued KB files** exactly once with status, parse method, version label on every current row and a reason on every non-current row; a file on disk not in `MANIFEST`, or a `MANIFEST` row with no file, raises `UnlistedFile` and writes nothing — verify: `tests/unit/retrieval/test_manifest.py::test_manifest_covers_all_17_issued_files` and `tests/unit/retrieval/test_ingest.py::test_unlisted_file_fails_build` (temp copy of the KB with one extra file, and one with a file removed from disk but still listed) — evidence: 17 rows asserted against a directory walk of `knowledge_base/`; both bad runs raise `UnlistedFile` naming the path; `out_dir` absent.
- [ ] AC-2 [invariant] Statuses match R-10 exactly: the four excluded files, the staff-only file and the stub are **never** embedded or written to `passages.jsonl`; the 11 current files are — verify: `tests/unit/retrieval/test_ingest.py::test_only_current_files_indexed` (the real issued KB, stand-in `EmbedFn`) — evidence: the set of `file` values in `passages.jsonl` equals the 11 current paths; none of `archive/*`, `faq/faq_old_copy.md`, `services/scheduling_guide.md`, `internal/agent_discretion_notes.md`, `services/duct_cleaning.md` appears; every non-current `ManifestRow.chunks` is 0.
- [ ] AC-3 [invariant] Every format present is parsed by its own method and recorded: Markdown by heading split, TXT and the fee PDF by paragraph groups, the price-book CSV one chunk per data row, the holiday PNG via the linked transcription (DAT-11) — verify: `tests/unit/retrieval/test_ingest.py::test_each_format_parsed` — evidence: the fee-schedule PDF yields chunks containing its fee lines (e.g. the $89 diagnostic); the CSV yields one chunk per data row; the PNG's chunks come from the transcription and its `ManifestRow.source_sha256` covers the transcription; each row's `parse_method` matches.
- [ ] AC-4 [invariant] Chunking follows `retrieval/settings.py`: a section over `MAX_SECTION_CHARS` is cut at blank-line paragraphs into pieces near `PIECE_CHARS` with no overlap; `section` is the heading path — verify: `tests/unit/retrieval/test_ingest.py::test_heading_split_and_long_section_cut` (a synthetic Markdown file in a temp KB copy with one 2,500-character section) — evidence: that section becomes ≥ 3 pieces, none over 1,100 characters, no repeated text between pieces; each piece's `section` equals the heading path.
- [ ] AC-5 [invariant] Every chunk carries a unique `passage_id` of the form `<file path>#<chunk n>`, `file`, `section`, `version_label`, and `version_date` only for full-date labels — verify: `tests/unit/retrieval/test_ingest.py::test_chunk_provenance` — evidence: "Effective 2026-01-01" → `version_date` 2026-01-01; "Rev 2026-01" and "undated" → `None`; no duplicate ids; `embed_text` = `section + "\n" + text`; `vectors.npy` row count equals `passages.jsonl` line count and every row has norm 1 (± 1e-5).
- [ ] AC-6 [failure/refusal] A missing or unreadable answer-source file, or a missing transcription, raises `MissingSource` naming the file; the CLI exits non-zero printing `MissingSource`; no index directory is written (temp dir, rename on success only) — verify: `tests/unit/retrieval/test_ingest.py::test_missing_source_fails_build` (temp KB copy with the PDF removed; a second run with the transcription removed) and `::test_cli_exit_codes` — evidence: raised class and path in the message; exit code ≠ 0; `out_dir` does not exist after either run.
- [ ] AC-7 [invariant] The staff-only file reaches `staff_notes.json` as `StaffGuidance` passages (`passage_id` `internal/agent_discretion_notes.md#<n>`, `version_label`, `text_sha256`), and `load_staff_guidance(index_dir)` returns exactly them; it is never embedded — verify: `tests/unit/retrieval/test_ingest.py::test_staff_notes_written_not_indexed` — evidence: `load_staff_guidance` returns ≥ 1 passage; each `text_sha256` equals the SHA-256 of its `text`; none of their ids appears in `passages.jsonl`; the bullet "Waive the $49 late-cancellation fee once per customer per year" (the first `STAFF_GUIDANCE_FOR` prefix, cases.md §5) is contained in some passage's text.
- [ ] AC-8 [negative] **WF-14 (run through the ingest entry point, `python -m meridian.retrieval.ingest`'s `main`, as AC-9's):** No text from an excluded or stub file reaches any index artefact, staff-only text reaches only `staff_notes.json`, and no stdout or log line prints chunk text (IDs, counts and statuses only; DO-6 *Content and redaction* rule 3) — verify: `tests/unit/retrieval/test_ingest.py::test_excluded_text_absent` (calls the entry point's `main` with a temp KB copy; writes distinctive sentinel lines into temp copies of `archive/comfort_club_overview.md`, `services/duct_cleaning.md` and `internal/agent_discretion_notes.md`; captures stdout and logs) — evidence: the first two sentinels are absent from all six artefacts and the captured output; the staff-only sentinel appears in `staff_notes.json` and nowhere else.
- [ ] AC-9 [capture] Running the WF-14 entry point (the CLI AEA-50 calls) writes `manifest.json` with 17 rows, `index_record.json` (`embedding_model` = `BAAI/bge-small-en-v1.5`, `dimension`, `chunks`, `manifest_hash`, `files` = 17, plus every `retrieval/settings.py` constant) and `ingest_run.json` (`ingest_run_id`, `status` = `completed`, `manifest_hash`, `files`, `chunks`, `embedding_model`); a failing run's `IngestRun` has `status` `failed` and `failure` = the class name — verify: `tests/unit/retrieval/test_ingest.py::test_entry_point_writes_wf14_records` (stand-in embed, temp output dir) plus one run of the real CLI with the real embedder by the implementer, output pasted in the report — evidence: the three records with those fields; `manifest_hash` identical across two runs on the same inputs and different when one KB file's bytes change in a temp copy; the real run's `dimension` and `chunks` as printed (a measurement, no target).
- [ ] AC-10 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-16.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-2 (the ingested KB files, stale twins excluded) as the journeys that will exercise this code once AEA-51 lands, so the seam audit knows where to look — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-11 [regression/context] In the same change: `.claude/reference/area-map.md` A3 row (`retrieval/{settings,manifest,ingest}.py` planned → actual + commit); `.claude/state/icm-progress.md` row for A3 evidence replaced; `docs/design/code-design.md` A3 status (planned → built, `settings.py` added per data.md §3); the index directory layout and the `manifest_hash` definition recorded in DO-4 §13 beside `IndexInfo` (data.md §3 names this ticket for it); a dev-log entry per `.claude/reference/dev-log.md` — verify: `git diff --stat` on those paths — evidence: the diff.

### Observability
- Responsibilities: WF-14's three records (DO-6 registry row WF-14), all as files in the index directory (DAT-12):
  `ingest_run.json` (`ingest_run_id`, status `started` / `completed` / `failed`, `failure` class name only),
  `manifest.json` (17 files, status and parse method each), `index_record.json` (embedding model, dimension, chunk
  count, manifest hash, every retrieval constant). Stdout and log lines carry IDs, counts and statuses only (AC-8).
- Capture evidence: AC-9 drives the WF-14 entry point (the CLI) and finds all three records; AEA-50 owns the CAP-9 test
  in `tests/capture/` that runs it inside the image build ("manifest with 17 file rows").

### Evaluation
- Checks: E-2 (retrieval, R-12) and the M-7 excluded-source gate run on the index this ticket builds (DO-6 WF-14
  "EV: E-2 runs on the index this records"); this ticket adds none of their cases (AEA-06) or harness (AEA-24,
  `eval/run_retrieval.py`, DAT-26). It keeps E-2 meaningful by never indexing an excluded file (AC-2) and by recording
  `manifest_hash` so each E-2 run names its index. The first E-2 run replaces the [A] chunking constants (DAT-11).
- Expected-answer authority: the PRD §4.3a knowledge map and R-10 exclusions (DEC-4) decide which file is current
  (evaluation plan *Expected-answer authority*, rows "Knowledge answers" and "Retrieval").

### Metrics
- References: M-6 (retrieval hit rate @3) and M-7 (answers citing an excluded file), both inherited from WF-14 and
  computed from E-2 / E-1 runs on this index.
- Acceptance conditions: M-6 stays attributable because every E-2 run can read `manifest_hash` and the chunking
  constants from `index_record.json`; with no excluded file indexed (AC-2), M-7's numerator can only come from a
  citation bug, never from ingestion. No target set here (M-6 ≥ 90% and M-7 = 0 are judged at Stage 9 runs).

### Blocked by
- AEA-02 (domain types and ports: `Passage`, `PassageId`, `IndexInfo`, `MeridianModel`).

### Agent handoff
- Area / owner: A3 Retrieval (`.claude/reference/area-map.md`); files `src/meridian/retrieval/{settings,manifest,ingest}.py`
  (`settings.py` added by stage7/data.md §3 to the slice plan's `{manifest,ingest}.py`) and their tests under
  `tests/unit/retrieval/`. No `register_<area>()` hunk (the slice plan's AEA-01 stub list has none for AEA-16).
- Contracts and shared surfaces: **consumes** `domain/records.py` `Passage`, `domain/common.py` `PassageId`,
  `ports/runtime.py` `IndexInfo` (AEA-02), the issued KB (read-only) and `data/kb_transcriptions/holiday_hours_2026.md`
  (read-only); copies and adapts the parked `docs/parked/2026-10-21-first-attempt/src_meridian/kb/{manifest,ingest}.py`. **Produces** the index directory for
  AEA-33 (`FastembedIndex(index_dir)` loads `manifest.json`, `passages.jsonl`, `vectors.npy`, `index_record.json`;
  reads `SEARCH_K`, `MIN_SCORE`), AEA-50 (runs the CLI at image build; CAP-9 reads `ingest_run.json` and `manifest.json`),
  AEA-24 (E-2 scores this index), AEA-29 (`StaffGuidance` type; `load_staff_guidance` resolved against
  `STAFF_GUIDANCE_FOR` by AEA-51's container at start-up, cases.md §5, CAS-33) and AEA-07 (chunking reasoning, DAT-11).
  **Must not edit:** `adapters/retrieval_fastembed.py` and `agent/tools/knowledge.py` (AEA-33), `domain/*`, `ports/*`
  (AEA-02), `policy/handoff.py` (AEA-14), `Dockerfile` (AEA-50), anything under `docs/data/issued/`.
- Scope boundary / refusal: builds and records the index only. No search, relevance floor or readiness check (AEA-33),
  no Dockerfile (AEA-50), no eval cases (AEA-06), no attaching guidance to briefs (AEA-29). Adds no keyword or hybrid
  search (PRD §6.2: only if E-2 shows misses). Writes no database row (DAT-12).
- Wave and gates: wave 1; gates None. The real embedder downloads the ONNX model once (cached in `var/fastembed/`);
  default tests use a stand-in `EmbedFn`; the real-model run is the implementer's command evidence (AC-9).
- Lane: `lane::build-loop` — source and tests that the image build and retrieval read.
- Risk: None (slice plan). The staff-only file is fictional internal guidance, not personal data; AC-8 keeps it out of
  every customer-facing artefact.
- Entry points added or changed: WF-14
