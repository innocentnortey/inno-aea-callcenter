# Plan — [AEA-33] retrieval: vector index and the knowledge tool

**Status:** READY. Every prerequisite is on `main` now: AEA-02 (types), AEA-11 (`FakeIndex`), AEA-16 (index build) and
AEA-22 (dispatch). No `blocked-on`.
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #33 (body = `docs/plans/tickets/AEA-33.md`).
**Base revision:** refreshed 2026-10-21 against `main` `d76092f` ("Merge AEA-22: tool dispatch, guard, lookup log"),
the DO-4 / stage7 signatures, and a planner scratch measurement on the real AEA-16 index (§1.1, §5 step 6). The first
version of this plan was written against `16ca639` from sibling plans. Every shape below was re-checked against the
merged code.
**Lane and risk:** `lane::build-loop`. Risk: none, so no test-writer and no security agent. Wave 2. Gates: none.
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21. **Implementer:** `fanout-implementer` on Sonnet.
**Worktree / branch:** `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-33`, branch `aea-33-retrieval-index`.
If the orchestrator gave you other names, use those.

**What changed in this refresh (for the reviewer):**
1. AEA-22 is merged, so `tests/unit/agent/tools/__init__.py` already exists and is no longer an owned file.
2. A new seam test (PA-11) runs `kb_search` through the real `ToolRegistry` / `ToolDispatcher`.
3. R-3 is closed by a test: `_FOR_MODEL_MAX_CHARS == dispatch.MAX_CONTENT_CHARS`. The source file still does not import
   dispatch, because A3 must not depend on A7b.
4. Measured scores now come from AEA-16's real chunker (56 chunks).
5. The ICM edit targets the A3 row, since each area now has its own row.
6. `_Reason` uses `TypeAlias`, following ingest.py; ruff ignores UP040.
7. Readiness catches `Exception` per artefact block, so each fault keeps its own reason.

---

## 1. Goal and sources

### 1.1 Goal (from the issue's *What to build*)

> **US-6:** As a **homeowner**, I need answers about membership, billing fees, warranty, services, hours and the service
> area that come from Meridian's current documents and show where they came from, so that I can trust the number I'm given.
> **US-7:** As a **homeowner** asking something Meridian's files don't cover, I need the assistant to say it doesn't have
> that information and offer a person, so that I'm never given a confident guess.

This slice builds two modules, exactly as `docs/design/contracts/stage7/data.md` §4 signs them:

1. **`src/meridian/adapters/retrieval_fastembed.py`** holds `Readiness` and `FastembedIndex`. `FastembedIndex` implements
   DO-4 §13 `RetrievalIndex` unchanged. It loads the index directory AEA-16 writes, answers
   `search(query, *, k, min_score)` by cosine similarity with a relevance floor, reports `info()` and checks
   `readiness()`.
2. **`src/meridian/agent/tools/knowledge.py`** holds `KbSearchArgs` and `knowledge_tools(retrieval)`. The factory returns
   one `ToolDef` named `kb_search`, bound to the index it is given. Its executor searches with `SEARCH_K` / `MIN_SCORE`
   and returns a `ToolResult` carrying `for_model`, a `KnowledgeCapture` and a `LookupEntry`.

**Concrete example (WP-1, stale twin; DEC-4).** These numbers come from the planner's scratch run on 2026-10-21: AEA-16's
`build_index` with the cached bge-small model gave 56 chunks, and queries used `query_embed`.
- Input: "How much is the Comfort Club?" against the real index.
- `search(k=3, min_score=0.60)` returns `membership/comfort_club_overview.md#1` (0.835; section
  `Comfort Club Maintenance Plan > Plans > Comfort Club (Standard)`; label "Effective 2026-01-01"; its text holds "$189"
  and "$16.99"), then `membership/comfort_club_overview.md#2` (0.813) and `services/service_catalog.md#1` (0.756).
- No passage comes from `archive/comfort_club_overview.md`, because AEA-16 never embedded it. `below_floor` is False.
- Input "How long have you been in business?" (US-7) gives `below_floor = True` with no passage. Its top score was
  0.555, against the 0.60 floor.
- The tool then hands the model `{"below_floor":true,"passages":[]}`. It never hands over a nearest-match passage
  dressed up as an answer.

### 1.2 Context

This is a wave-2 ticket of Stage 8. `src/meridian/adapters/retrieval_fastembed.py` and
`src/meridian/agent/tools/knowledge.py` do not exist yet. The other tickets connect to it like this:
- **AEA-16** (merged, `fe12657`) writes the index directory that this adapter reads.
- **AEA-22** (merged, `5d0a4e4`) `agent/tools/dispatch.py` runs this ticket's executor, writes the `lookup_log` row and
  renders `for_model`.
- **AEA-35** (wave 2) runs the knowledge specialist through dispatch.
- **AEA-51** (wave 3) wires `FastembedIndex(Settings.index_dir)` as `GraphDeps.retrieval`, calls `readiness()` at
  start-up, and builds the `ToolRegistry` from `knowledge_tools`.
- **AEA-24**'s `eval/run_retrieval.py` uses `FastembedIndex` for E-2.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-33.md` (= issue #33) | AC-1…AC-11, scope, owned files, *must not edit* list |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-33 (blocked by 16; owns `adapters/retrieval_fastembed.py`, `agent/tools/knowledge.py`), §0a journey map (J-2 first landed by AEA-51; extended by 33) | Boundary; AC-10 level |
| Requirements | PRD `docs/prd/inno-aea-callcenter-prd.md`: R-10 (exclusions, staff-only, stub); R-11 (bge-small; citation with file, section, version); R-12 (retrieval evaluated alone); R-13 (answer only from sources; refusal); R-14 (public questions need no code); §4.3a knowledge map (the expected current document per question kind); US-6, US-7 | AC-2, AC-4, AC-5, AC-7 |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md`: §5 (`ToolDef`, `ToolCallScope`, `LookupEntry`, `ToolResult`, `Passage`, lookup-log rule, "≤ 4,000 chars rendered"); §13 (`RetrievalIndex`, `RetrievalResult`, `IndexInfo`, plus the *Built (AEA-16)* note on the index directory); §16 (addenda win) | Exact shapes, §4 below |
| Addenda (win over DO-4) | `stage7/data.md`: §3 (`retrieval/settings.py` constants, index directory layout, `ManifestRow`, `manifest_hash`); §4 (`Readiness`, `FastembedIndex`, `KbSearchArgs`, `knowledge_tools`); §6 (`SearchesPassages`; E-2 calls with `min_score = -inf` and at the floor); §9 items 5–6. `stage7/graph-tools.md`: §1 (registration by factory, `ToolKind`, dispatch guard order, `ToolCallRecord`); §3 (`KnowledgeCapture`); §6 (quick-check call: `kb_search` with `query = customer_text[:300]`); C-6 | Signatures copied in §4 |
| Decision ledger | `docs/plans/7b-decisions/data.md`: DAT-17 (k = 3, floor 0.60 [A]); DAT-18 (stub never indexed); DAT-26; DAT-29 (d); DAT-30. `graph-tools.md` GRT-1 | Floor and k come from settings only; no registry hunk |
| Code design | DO-3 `docs/design/code-design.md`: §2.1 (agent/ never imports `fastembed`; adapters implement ports); §3 tree rows (lines `retrieval_fastembed.py`, `tools/knowledge.py`); §4.2 (`RetrievalIndex` port); §4.3 `adapters/retrieval_fastembed.py` row; §6 S-4 (cut), S-5 (embedder port deferred, so `embed_query` is a plain callable), S-13; §8 area table (A3 is layer 1, depends on A0 only; dispatch is A7b, layer 3); §9 `tests/contract/test_retrieval_contract.py` | Module boundaries; no new seam; A3 must not import A7b |
| Evaluation plan | DO-5 E-2 (current doc in the top 3, no excluded file in the top 3, off-corpus below the floor) and *Expected-answer authority* | AC-2, AC-4 and AC-7 hold the traps in the default suite; E-2 itself is AEA-06/24 |
| Observability contract | DO-6: WF-1 (`lookup_log`, one row per tool call, dispatch writes it); WF-8; WF-14 (index record); *Content and redaction* (no query or passage text in logs) | AC-8, AC-9; the executor writes nothing |
| Key-metrics registry | DO-7: M-6 (hit @3); M-7 (answers from excluded or stale files) | M-7 computable from `lookup_log.passage_ids` (every id names its file) |
| Rules | `.claude/rules/retrieval-and-context.md` 4 (relevance floor, "no supporting evidence"), 5 (one config place), 6 (one embedding model), 7 (readiness at start-up); `agent-tools.md` 2 (description names when not and the sibling), 3 (schema from model), 5; `build-loop-test-scope.md` (+ AEA addition); `integrated-journeys.md` §4; `context-maintenance.md` 3, 6; `source-authority.md` 4, 7 | §5 steps; §7 checks |
| Merged code (read) | `src/meridian/domain/{common,records,specialists,tools,turn}.py`, `ports/runtime.py` (AEA-02); `retrieval/{settings,manifest,ingest}.py` (AEA-16); `tests/fakes/{index,clock}.py` (AEA-11); `agent/tools/dispatch.py`, `tests/unit/agent/tools/dispatch_doubles.py` (AEA-22); `tests/journeys/affected.py` (AEA-01) | §4 copies |
| Sign-off | `docs/plans/stage7-signoff.md` D-4…D-15 | None touches AEA-33 |
| Issued data | `docs/data/issued/meridian_dataset/knowledge_base/` (17 files) and `data/kb_transcriptions/holiday_hours_2026.md`, both tracked, read only | Real-index tests read them through AEA-16's `build_index` into a temp dir |

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files you may create or edit)

| File | Action |
|---|---|
| `src/meridian/adapters/retrieval_fastembed.py` | create |
| `src/meridian/agent/tools/knowledge.py` | create |
| `tests/unit/adapters/test_retrieval_fastembed.py` | create (also holds the shared test helpers, §6) |
| `tests/unit/agent/tools/test_knowledge.py` | create |
| `tests/contract/test_retrieval_contract.py` | create |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-33.md` | create (AC-10; date = your day, America/Chicago) |
| `.claude/reference/area-map.md` | modify **only the last cell of the A3 row** (AC-11) |
| `.claude/state/icm-progress.md` | modify **only the evidence cell (third cell) of the A3 row**: the `Routes verified against code and tests` row whose evidence cell begins `2026-10-21: area map A3 →` (AC-11) |
| `docs/design/code-design.md` | modify **only** the §4.3 row `adapters/retrieval_fastembed.py` (its Notes cell) and the two §3 tree lines `retrieval_fastembed.py` and `tools/knowledge.py` (append the built marker) (AC-11) |
| `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<YYYY-MM-DD>-aea-33-retrieval-index-claude-01.md` | create (outside this repo; never `git add` it here) |

### 2.2 Shared surfaces you read and never edit

- AEA-02: `src/meridian/domain/common.py`, `domain/records.py`, `domain/specialists.py`, `domain/tools.py`,
  `domain/turn.py`, `ports/runtime.py`, `ports/models.py`.
- AEA-16: `src/meridian/retrieval/settings.py`, `retrieval/manifest.py`, `retrieval/ingest.py`.
- AEA-22: `src/meridian/agent/tools/dispatch.py`, `tests/unit/agent/tools/dispatch_doubles.py` (imported by PA-11),
  `tests/unit/agent/tools/__init__.py`.
- AEA-11: `tests/fakes/`.
- AEA-01: `src/meridian/adapters/__init__.py`, `src/meridian/agent/tools/__init__.py`, `tests/unit/adapters/__init__.py`,
  `tests/contract/__init__.py` (leave them empty); `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `tests/journeys/**`
  (AEA-01, AEA-57).
- `src/meridian/web/container.py`.
- The issued KB and `data/kb_transcriptions/`.

### 2.3 Owned by other tickets: do not create or edit

- `retrieval/*` (AEA-16), `agent/tools/dispatch.py` (AEA-22), `agent/tools/account.py` (27), `agent/tools/scheduling.py`
  (28), `web/container.py` (01 / 51). There is **no `register_` hunk** for this ticket: leave `register_retrieval` a
  no-op.
- `domain/*`, `ports/*`, `config.py` (02), `tests/fakes/` (11), `tests/unit/agent/tools/dispatch_doubles.py` (22),
  `eval/**` (06, 24), `Dockerfile` (50).
- Anything under `tests/journeys/` (no journey file for this ticket yet, see §3.1 AC-10), `tests/contract/cases/` (59),
  `docs/data/issued/`, `docs/parked/`, `docs/archive/`, `docs/ux/**`, `apps/web/**`, `ui-contracts.openapi.yaml`,
  `UI_CONTRACTS.md`, the briefing.
- Do not add a `conftest.py` anywhere, a pytest marker (`pyproject.toml` is AEA-01's; `--strict-markers` is on), a new
  dependency, or any module beyond §2.1.

---

## 3. Requirements table

### 3.1 Acceptance criteria (issue #33, verbatim IDs) → implementation → verification

| AC | Requirement (short; full text in the issue) | Implemented by | Verified by |
|---|---|---|---|
| AC-1 [invariant] | `FastembedIndex` honours `RetrievalIndex`: at most k passages, each with score ≥ `min_score`, score descending, each with `passage_id`, `file`, `section`, `version_label`, `version_date` (None when no full date), `score`; `below_floor` iff none clears; `min_score = -inf` returns k. The same assertions pass on AEA-11's `FakeIndex` | §5 step 3 (`search`) | `tests/contract/test_retrieval_contract.py::test_search_shape_and_floor` (parametrised `fastembed-fixture`, `fake-index`) |
| AC-2 [invariant] | DEC-4 stale traps on the real index: five queries at `SEARCH_K`/`MIN_SCORE` return no `archive/*`, `faq/faq_old_copy.md` or `services/scheduling_guide.md`, and the §4.3a current document is among the results | AEA-16 embeds only CURRENT files; step 3 searches them | `test_retrieval_contract.py::test_stale_traps_on_real_index` (skips only if bge-small is not cached; builds the index with `build_index` into a temp dir) |
| AC-3 [failure/refusal] | Readiness never raises; `index_missing`, `dimension_mismatch`, `manifest_not_17` and `record_mismatch` each appear alone for their fault; the good fixture gives `ok=True, reasons=()` | §5 step 2 (`_check`) | `tests/unit/adapters/test_retrieval_fastembed.py::test_readiness_failures` (11 parametrised cases) |
| AC-4 [failure/refusal] | US-7 off-corpus query → `below_floor=True` and no passage on the real index; `kb_search` gives `below_floor: true` and no passage text | steps 3, 5 | `test_retrieval_contract.py::test_off_corpus_below_floor`; `tests/unit/agent/tools/test_knowledge.py::test_no_source_below_floor` |
| AC-5 [invariant] | `knowledge_tools(index)` returns exactly one `ToolDef` (`kb_search`, `ToolKind.KB_SEARCH`, `"read"`, `requires_verified=False`, `KbSearchArgs`); empty, 301-char and extra-field args fail; the executor calls the index with `SEARCH_K`, `MIN_SCORE`; importing registers nothing; two calls give two independent defs | §5 steps 4–5 | `test_knowledge.py::test_factory_tooldef_and_binding` |
| AC-6 [invariant] | `for_model` ≤ 4,000 chars; 3 × 1,100-char passages fit whole; longer ones are cut, never dropping id, file or version label | §5 step 5.3 (`_fit`) | `test_knowledge.py::test_for_model_within_limit` |
| AC-7 [negative] | Staff-only `internal/agent_discretion_notes.md` and stub `services/duct_cleaning.md` never come back from `kb_search` on the real index | AEA-16 never indexes them; step 5 | `test_retrieval_contract.py::test_staff_only_and_stub_not_returned` |
| AC-8 [negative] | Query and passage text never reach the lookup row or any log; `result_seen` holds ids and scores only (no run over 80 chars) | steps 2–5: no logging at all; `_result_seen` | `test_knowledge.py::test_lookup_and_logs_hold_no_text` (caplog, DEBUG) |
| AC-9 [capture] | `ToolResult` carries what WF-1's row needs: `tool="kb_search"`, `passage_ids` in order, `result_seen`, `message_id`, `turn_id`, `lookup_written=False`, `captured=KnowledgeCapture(result)` | step 5.4 | `test_knowledge.py::test_lookup_entry_and_capture_complete` |
| AC-10 [journey] | Extends J-2. The integrated step needs AEA-57 (harness, wave 2, not merged) and AEA-51 (lands J-2, wave 3). So this ticket writes **no** `tests/journeys/j2/test_aea_33.py`. Per the AC's own fallback, the record `docs/testing/journeys/YYYY-MM-DD-AEA-33.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51, and lists the J-2 step to add later (§5 step 8) | §5 step 8 | The record's fields; `uv run python -m tests.journeys.affected --base main --list-only` output |
| AC-11 [regression/context] | Area map A3 row, ICM A3 row, DO-3 §4.3 row (plus the two §3 tree lines) updated with the code commit SHA | §5 step 8 | `git diff --name-only main...HEAD` |

### 3.2 Plan-added criteria (the orchestrator posts them on issue #33 as one comment)

| ID | Criterion | Verified by |
|---|---|---|
| PA-1 (WP-1 worked pair) | Real index, "How much is the Comfort Club?" at `SEARCH_K`/`MIN_SCORE`. A returned passage has `file == "membership/comfort_club_overview.md"`, `version_label == "Effective 2026-01-01"`, `version_date == date(2026, 1, 1)`, and text containing `$189` and `$16.99`. No returned file starts with `archive/`. `below_floor is False` | `test_retrieval_contract.py::test_wp1_stale_twin_on_real_index` |
| PA-2 | Seam with AEA-16: `build_index` on the issued KB (stand-in embedder, no model) gives `readiness() == Readiness(ok=True, reasons=())`. `info()` equals the run's `manifest_hash` and `chunks`, with `files == 17`. A search with `min_score=-inf` over every chunk returns only CURRENT files | `test_retrieval_fastembed.py::test_readiness_ok_on_ingest_output` |
| PA-3 | `search` and `info` on a not-ready index raise `RuntimeError` whose message names the reason codes; the embedder is never called | `test_retrieval_fastembed.py::test_search_and_info_refuse_when_not_ready` |
| PA-4 | `info()` returns the `IndexInfo` recorded in `index_record.json` (WF-14: the deployed index and the build record agree) | `test_retrieval_fastembed.py::test_info_reads_index_record` |
| PA-5 | The query vector is normalised: a stand-in returning `[2,0,0,0]` gives the same scores as `[1,0,0,0]`. Ties keep row order | `test_retrieval_fastembed.py::test_search_normalises_query_and_keeps_row_order_on_ties` |
| PA-6 | A query vector whose length differs from the index dimension raises `ValueError` (dispatch turns it into `tool_failed`) | `test_retrieval_fastembed.py::test_query_dimension_mismatch_raises` |
| PA-7 (DO-3 S-5) | Constructing the index, `readiness()` and `info()` load neither `fastembed` nor `onnxruntime` (checked in a fresh subprocess) | `test_retrieval_fastembed.py::test_default_embedder_loads_nothing_until_search` |
| PA-8 (DO-3 §2.1, §8; retrieval rule 5) | `knowledge.py` imports no `fastembed`, `numpy`, `meridian.adapters`, `meridian.agent` or `meridian.retrieval.ingest`, and holds no second literal for k or the floor. Its `_FOR_MODEL_MAX_CHARS` equals dispatch's `MAX_CONTENT_CHARS` (checked from the test, not imported by the source) | `test_knowledge.py::test_knowledge_imports_and_literals` |
| PA-9 (graph-tools §1) | An index that raises makes the executor raise the same exception. Dispatch owns `tool_failed`; the executor never builds a `ToolError` | `test_knowledge.py::test_search_error_propagates` |
| PA-10 (DAT-18 example) | "Do you do duct cleaning?" on the real index returns `services/service_catalog.md` among the results | `test_retrieval_contract.py::test_duct_cleaning_answered_from_catalog` |
| PA-11 (seam with AEA-22) | `ToolRegistry(knowledge_tools(index))` passes dispatch's start-up checks. Through `ToolDispatcher.dispatch`: a valid call is `ok`, its `content` is the untruncated JSON of `for_model`, one lookup row is appended with our `passage_ids` and `result_seen`, and `record.passage_ids` matches. An empty query is `refused` / `bad_arguments` and never reaches the index | `test_knowledge.py::test_kb_search_through_dispatcher` |

### 3.3 Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| `RetrievalIndex` honoured unchanged; E-2 uses `min_score=-inf` | DO-4 §13; data.md §4, §6 | AC-1 | in-ticket | step 3 |
| Relevance floor; "no supporting evidence" to the model | retrieval rule 4; R-13 | AC-4 | in-ticket | steps 3, 5.3 |
| k and floor only from `retrieval/settings.py` | retrieval rule 5; DAT-17 | AC-5 | in-ticket | step 5; PA-8 |
| Readiness: index exists, dimension matches, 17 files, record agrees; never raises | retrieval rule 7; data.md §4 | AC-3 | in-ticket | step 2 |
| One embedding model per index | retrieval rule 6 | AC-3 (`record_mismatch`) | added | step 2.3: build-time settings in the record must equal `settings.py` |
| `manifest_hash` recomputed exactly as AEA-16 does | data.md §3; DO-4 §13 *Built (AEA-16)* note | — | added | step 2.7; PA-2 proves it against the real `build_index` output |
| Default tests download nothing | DO-3 S-5; ticket conventions | Agent handoff | in-ticket | `embed_query` stand-ins; lazy fastembed import; real-index tests skip without the cached model; PA-7 |
| Thread safety (parallel specialists in one process) | DO-3 §2.2 | — | added | step 1: one `threading.Lock` for loading, one for embedding |
| `kb_search` description routes (says when not to use it and names the sibling) | agent-tools rule 2 | — | added | step 4 (text fixed in §4.5) |
| Executor writes nothing, opens no unit of work; dispatch writes the row | DO-4 §5 lookup-log rule; graph-tools §1 | AC-9 | in-ticket | step 5; PA-11 shows dispatch does it |
| `for_model` within what dispatch sends untruncated | DO-4 §5; `dispatch.MAX_CONTENT_CHARS = 4_000`, `_dumps` | AC-6 | in-ticket | step 5.3 uses dispatch's exact serialisation; PA-8 equality; PA-11 |
| No query or passage text in logs | DO-6 *Content and redaction* | AC-8 | in-ticket | neither module logs |
| No self-registration, no `register_` hunk | GRT-1; DAT-29 (d) | AC-5 | in-ticket | step 4 |
| `Readiness` called at start-up; false blocks the deploy | data.md §9 item 6; system design §8.2 | Produces | other-ticket | AEA-51 (wiring), AEA-50 (image) |
| `lookup_log` row written and timed; `tool:kb_search` span | WF-1, R-G-17 | Observability | other-ticket | AEA-22 (merged: row, `elapsed_ms`), AEA-35 (span) |
| E-2 suite and cases | DO-5 E-2; R-12 | Evaluation | other-ticket | AEA-06 (cases), AEA-24 (runner) |
| J-2 integrated step | integrated-journeys §3 rule 1 | AC-10 | other-ticket (blocked) | AEA-57 + AEA-51; the record names the step (§5 step 8) |
| Where `Readiness` lives | data.md §4 (the section heading names this file) | — | added (engineering) | defined in `adapters/retrieval_fastembed.py`; AEA-51 imports it from there |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None. `kb_search` is reached through dispatch inside the WF-1 turn (CON-2). `FastembedIndex` is used by WF-1 and by E-2's `eval/run_retrieval.py` (AEA-24) | WF-1, WF-8 | DO-6 rows WF-1, WF-8, WF-14 already exist | E-2; M-6, M-7; CAP-1 (AEA-51) |

---

## 4. Shared code to use (exact shapes, copied from `main` `d76092f`)

### 4.1 From AEA-02

```python
# src/meridian/domain/common.py
class MeridianModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)
class LLMFacing(MeridianModel): ...
class PassageId(_PatternId):  PATTERN = r"^[^#\s]+#[0-9]+$"     # "<file path>#<chunk n>"; strict str schema
class TurnId(_PatternId):     PATTERN = _UUID4_PATTERN          # lower-case UUID4
class ToolKind(StrEnum):      # re-exported from domain/tools.py
    KB_SEARCH = "kb_search"; ACCOUNT_READ = "account_read"; SLOT_SEARCH = "slot_search"
    BOOK = "book"; MOVE = "move"; CANCEL = "cancel"; CHANGE_REQUEST = "change_request"

# src/meridian/domain/records.py   (also re-exported as meridian.ports.runtime.Passage / RetrievalResult)
class Passage(MeridianModel):
    passage_id: PassageId
    file: str
    section: str
    version_label: str
    version_date: dt.date | None
    text: str
    score: float
class RetrievalResult(MeridianModel):
    passages: tuple[Passage, ...]
    below_floor: bool

# src/meridian/ports/runtime.py
class IndexInfo(MeridianModel):
    embedding_model: Literal["BAAI/bge-small-en-v1.5"]
    dimension: int
    chunks: int
    manifest_hash: str
    files: int
class RetrievalIndex(Protocol):
    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult: ...
    def info(self) -> IndexInfo: ...

# src/meridian/domain/specialists.py
class KnowledgeCapture(MeridianModel):
    kind: Literal["knowledge"] = "knowledge"
    result: RetrievalResult

# src/meridian/domain/turn.py
class TurnIds(MeridianModel):
    thread_id: ThreadId; turn_id: TurnId; request_id: RequestId
    run_tag: RunTag                      # "live" | "eval" | "load"
    run_id: str | None; agent_version: str

# src/meridian/domain/tools.py
class ToolCallScope(MeridianModel):
    ids: TurnIds
    customer_id: CustomerId | None
    shown_slot_ids: frozenset[int]
    now: dt.datetime
    message_id: int
class LookupEntry(MeridianModel):
    tool: str
    record_ids: tuple[str, ...]
    passage_ids: tuple[PassageId, ...]
    result_seen: str
    message_id: int
    turn_id: TurnId
Capture = Annotated[KnowledgeCapture | AccountCapture | SchedulingCapture, Field(discriminator="kind")]
class ToolResult(MeridianModel):
    ok: bool
    for_model: ToolError | JsonValue = Field(union_mode="left_to_right")
    captured: Capture | None
    lookup: LookupEntry
    lookup_written: bool
class ToolDef(MeridianModel):
    name: str
    description: str
    args_model: type[LLMFacing]
    kind: ToolKind
    effect: Literal["read", "write"]
    requires_verified: bool
    executor: Callable[[LLMFacing, ToolCallScope], ToolResult] = Field(exclude=True)
```

Imports to write, exactly:
- `from meridian.domain.common import LLMFacing, MeridianModel` (the adapter needs only `MeridianModel`)
- `from meridian.domain.records import Passage, RetrievalResult`
- `from meridian.domain.specialists import KnowledgeCapture`
- `from meridian.domain.tools import LookupEntry, ToolCallScope, ToolDef, ToolKind, ToolResult`
- `from meridian.ports.runtime import IndexInfo, RetrievalIndex`

The house module rules apply to both new files (see `retrieval/ingest.py` for an example):
1. `from __future__ import annotations` comes first after the docstring.
2. One statement per line. Absolute imports only.
3. No module-level instances except immutable constants.
4. Never `assert` in `src/`.
5. Under mypy's `init_typed = true`, build a model that has validated-id fields with `Model.model_validate({...})` in
   tests, or pass values that already have the id type (`p.passage_id`, `scope.ids.turn_id`).

### 4.2 From AEA-16 (merged, `fe12657`)

```python
# src/meridian/retrieval/settings.py  (constants only)
EMBEDDING_MODEL: Final = "BAAI/bge-small-en-v1.5"
SIMILARITY: Final = "cosine"
CHUNKER: Final = "heading-split/1"
MAX_SECTION_CHARS: Final = 1100
PIECE_CHARS: Final = 900
OVERLAP_CHARS: Final = 0
SEARCH_K: Final = 3
MIN_SCORE: Final = 0.60

# src/meridian/retrieval/manifest.py  (pydantic only; no numpy/fastembed)
class FileStatus(StrEnum): CURRENT = "current"; EXCLUDED = "excluded"; STAFF_ONLY = "staff_only"; STUB = "stub"
class ParseMethod(StrEnum): MARKDOWN = "markdown"; TEXT = "text"; PDF_TEXT = "pdf_text"; CSV_ROWS = "csv_rows"; PNG_TRANSCRIPTION = "png_transcription"
class ManifestRow(MeridianModel):
    path: str; status: FileStatus; version_label: str | None; parse_method: ParseMethod
    reason: str | None
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    chunks: int = Field(ge=0)
    # model validator: CURRENT needs a version_label and reason None; non-CURRENT needs a reason and chunks == 0
MANIFEST: Final[tuple[ManifestSpec, ...]]        # exactly 17, sorted by path; ManifestSpec has .path and .status

# src/meridian/retrieval/ingest.py  (tests only; the adapter never imports ingest)
EmbedFn: TypeAlias = Callable[[Sequence[str]], npt.NDArray[np.float32]]
class IngestRun(MeridianModel): ingest_run_id; status; started_at; finished_at; manifest_hash: str; files: int; chunks: int; embedding_model: str; failure
def build_index(kb_dir: Path, out_dir: Path, *, transcriptions_dir: Path, embed: EmbedFn) -> IngestRun: ...
    # refuses an existing out_dir (IngestError); normalises the vectors itself; returns IngestRun(status="completed", ...)
```

**The index directory** that `build_index` writes (code read on `main`; data.md §3; DO-4 §13 *Built* note):

| File | Exactly what is written |
|---|---|
| `manifest.json` | `json.dumps(rows, indent=2, sort_keys=True, ensure_ascii=False) + "\n"`, where rows is a list of 17 `ManifestRow.model_dump(mode="json")`, sorted by `path` |
| `passages.jsonl` | one line per passage: `json.dumps({**p.model_dump(mode="json", exclude={"score"}), "embed_text": p.section + "\n" + p.text}, sort_keys=True, ensure_ascii=False)`; line order = vector row order; `version_date` is an ISO string or `null` |
| `vectors.npy` | `np.save(..., vecs, allow_pickle=False)`, float32 `[chunks, dimension]`, rows L2-normalised |
| `index_record.json` | `{**IndexInfo(...).model_dump(mode="json"), "settings": {name: value for name, value in vars(settings).items() if name.isupper()}}`, written with indent=2 |
| `ingest_run.json`, `staff_notes.json` | not read by this ticket |

**`manifest_hash`**, exactly as `build_index` computes it:

```python
hashlib.sha256(
    json.dumps([r.model_dump(mode="json") for r in sorted(rows, key=lambda r: r.path)],
               sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
).hexdigest()
```

The real KB gives 17 files and 56 chunks (dimension 384 with bge-small; AEA-16 journey record and the planner's run). The
longest passage text is 857 characters.

### 4.3 From AEA-11 (merged)

```python
from tests.fakes import FakeIndex, WORKED_PAIRS_NOW
# FakeIndex(passages: Sequence[Passage] = (), *, by_query: Mapping[str, Sequence[Passage]] | None = None,
#           info: IndexInfo | None = None)
#   .search(query, *, k, min_score): pool = by_query[query] if query in by_query else passages; keeps score >= min_score;
#       sorts by score desc (stable); returns the first max(k, 0); below_floor = no passage cleared; returns the SAME objects.
#   .searches: list[tuple[str, int, float]]   # every (query, k, min_score), in call order
#   .info(): the given IndexInfo, else bge-small / 384 / chunks = distinct ids / "fake-index" / 17
# WORKED_PAIRS_NOW = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
```

### 4.4 From AEA-22 (merged, `5d0a4e4`); used by tests only, never by `knowledge.py`

```python
# src/meridian/agent/tools/dispatch.py   __all__ = ["MAX_CONTENT_CHARS", "DispatchedCall", "ToolDispatcher", "ToolRegistry"]
MAX_CONTENT_CHARS: Final = 4_000
def _dumps(value) -> str: return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
#   _render: if len(_dumps(for_model)) > MAX_CONTENT_CHARS it sends {"truncated": true, "partial": ...} instead
class ToolRegistry:
    def __init__(self, defs: Iterable[ToolDef]) -> None   # ValueError on: name not [a-z_]{1,64}, duplicate name,
                                                          # private kind with requires_verified False, args field named
                                                          # like a ToolCallScope field, no JSON schema
    def get(self, name: str) -> ToolDef | None
    def for_kinds(self, kinds: frozenset[ToolKind]) -> tuple[ToolDef, ...]
    def check_covers(self, kinds: frozenset[ToolKind]) -> None
class DispatchedCall(MeridianModel): tool_call_id: str; content: str; result: ToolResult; record: ToolCallRecord
class ToolDispatcher:
    def __init__(self, registry: ToolRegistry, uow: UnitOfWorkFactory) -> None
    def schemas(self, kinds: frozenset[ToolKind]) -> tuple[ToolSchema, ...]       # ToolSchema.name, .input_schema
    def dispatch(self, calls: Sequence[ToolCall], *, kinds: frozenset[ToolKind], scope: ToolCallScope) -> tuple[DispatchedCall, ...]
    # For a read tool, dispatch writes one lookup row: LookupEntry(tool=defn.name, record_ids, passage_ids,
    # result_seen=redact(result_seen, STORE).text, message_id=scope.message_id, turn_id=scope.ids.turn_id).
    # The planner checked that STORE redaction leaves "below_floor=false; <id>=<score>; …" unchanged.

# src/meridian/ports/models.py
class ToolCall(...): id: str; name: str; args: ... | None      # built as ToolCall(id="c1", name="kb_search", args={"query": "..."})
# ToolCallRecord (domain/common.py): tool_call_id, name, kind, outcome ("ok"|"refused"|"failed"), error, record_ids,
#   passage_ids, lookup_id, elapsed_ms

# tests/unit/agent/tools/dispatch_doubles.py
class RecordingUow:          # callable UnitOfWorkFactory stand-in; .appended: list[LookupEntry]
    def __init__(self, recorder: Recorder | None = None, fail_on_appends: frozenset[int] = frozenset()) -> None
# Precedent for typing it: dispatch.ToolDispatcher(registry, cast(UnitOfWorkFactory, uow))  (tests/unit/agent/tools/test_registry.py)
```

### 4.5 This ticket's public names (data.md §4, copied; nothing else is public)

```python
# src/meridian/adapters/retrieval_fastembed.py
class Readiness(MeridianModel):                       # [Decided §7, engineering]
    ok: bool
    reasons: tuple[Literal["index_missing", "dimension_mismatch", "manifest_not_17", "record_mismatch"], ...]

class FastembedIndex:                                 # implements RetrievalIndex (DO-4 §13) unchanged
    def __init__(self, index_dir: Path, *, model_cache_dir: Path | None = None,
                 embed_query: Callable[[str], npt.NDArray[np.float32]] | None = None) -> None: ...   # None → fastembed bge-small
    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult: ...
    def info(self) -> IndexInfo: ...
    def readiness(self) -> Readiness: ...             # never raises

# src/meridian/agent/tools/knowledge.py
class KbSearchArgs(LLMFacing):
    query: str = Field(min_length=1, max_length=300,
                       description="The customer's question in plain words, for example 'How much is the Comfort Club?'")
def knowledge_tools(retrieval: RetrievalIndex) -> tuple[ToolDef, ...]: ...
```

`embed_query` is typed `npt.NDArray[np.float32]` instead of the sketch's bare `"np.ndarray"`, because mypy strict rejects
an unparameterised generic. The meaning is the same; AEA-16 made the same change for `EmbedFn`. The `description=` on
`query` only adds text to the JSON schema the model sees. It changes no signed shape.

**The `kb_search` description.** Use this text exactly. It is one string:

> Search Meridian Home Comfort's current company documents: membership plans and prices, fees and the repair price list,
> warranty terms, services offered and not offered, phone and holiday hours, the service area, safety guidance and
> troubleshooting steps. Returns {"below_floor": false, "passages": [...]} with up to 3 passages, each with passage_id,
> file, section, version_label and text, highest relevance first; cite passage_id for every fact you use. Returns
> {"below_floor": true, "passages": []} when no current document is relevant enough: then say Meridian's documents don't
> cover it and offer a person; never answer from memory. Use it for general company and policy questions. Do not use it
> for one customer's own invoices, membership or warranty records (use read_invoices, read_membership or read_warranty
> after the customer is verified), or to find or change appointments (use the scheduling tools).

**The `for_model` shapes.** AEA-35's prompt and AEA-60's checks read these keys:

```json
{"below_floor":false,"passages":[{"passage_id":"membership/comfort_club_overview.md#1","file":"membership/comfort_club_overview.md","section":"Comfort Club Maintenance Plan > Plans > Comfort Club (Standard)","version_label":"Effective 2026-01-01","text":"..."}]}
{"below_floor":true,"passages":[]}
```

**The `result_seen` format.**
- Above the floor: `below_floor=false; <passage_id>=<score:.3f>; …`, one token per returned passage, in order. For
  example: `below_floor=false; membership/comfort_club_overview.md#1=0.835; membership/comfort_club_overview.md#2=0.813`.
- Below the floor: exactly `below_floor=true`.

---

## 5. Steps (build order; each step ends with a check)

The slice stays inside DO-3's A3 boundary (layer 1, depends on A0 only). The dependencies run one way:
- **The adapter** depends on `domain/`, `ports/runtime.py`, `retrieval/settings.py` and `retrieval/manifest.py`, plus
  `numpy`. Only the adapter imports `fastembed`, and only lazily. It implements `RetrievalIndex`.
- **The executor module** depends only on `domain/`, `ports/runtime.py` (the `RetrievalIndex` Protocol) and
  `retrieval/settings.py`. It consumes `RetrievalIndex` and produces `ToolDef`. **It must not import
  `meridian.agent.tools.dispatch`:** dispatch is A7b (layer 3), and A3 must not depend upward.

No new Protocol, module or seam. The embedder port stays deferred (S-5): `embed_query` is a plain callable.

### Step 0. Preflight (no edits)

```bash
cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-33
export UV_LINK_MODE=hardlink
export FASTEMBED_CACHE_PATH=/home/linuxuser/workspaces/inno-aea-callcenter/var/fastembed   # cached bge-small (65 MB); never download
df -h /home                                   # stop and report if under 4 GB free
git log --oneline -5                          # must contain d76092f (AEA-22 merge) or later
grep -n "class Passage(\|class RetrievalResult(" src/meridian/domain/records.py
grep -n "class IndexInfo\|class RetrievalIndex" src/meridian/ports/runtime.py
grep -n "class KnowledgeCapture" src/meridian/domain/specialists.py
grep -n "class ToolDef\|class ToolResult\|class LookupEntry\|class ToolCallScope" src/meridian/domain/tools.py
grep -n "SEARCH_K\|MIN_SCORE" src/meridian/retrieval/settings.py
grep -n "def build_index\|class ManifestRow" src/meridian/retrieval/ingest.py src/meridian/retrieval/manifest.py
grep -n "class FakeIndex" tests/fakes/index.py
grep -n "MAX_CONTENT_CHARS: Final\|class ToolRegistry\|class ToolDispatcher" src/meridian/agent/tools/dispatch.py
grep -n "class RecordingUow" tests/unit/agent/tools/dispatch_doubles.py
ls "$FASTEMBED_CACHE_PATH"/models--Qdrant--bge-small-en-v1.5-onnx-Q/snapshots/*/model_optimized.onnx
uv sync
uv run python -c "import meridian.domain.tools, meridian.ports.runtime, meridian.retrieval.manifest, meridian.agent.tools.dispatch, numpy; print('ok')"
```

Stop and report to the orchestrator in these cases. Do not define a missing type locally, and do not work around a
difference.
- Any grep finds nothing.
- A shape differs from §4.
- `build_index`'s output differs from §4.2's table.

### Step 1. `adapters/retrieval_fastembed.py`: module frame

1. Docstring: "FastembedIndex: the built KB index behind RetrievalIndex (DO-4 §13; stage7/data.md §4). Loads AEA-16's
   index directory, searches by cosine similarity with a relevance floor, and checks readiness. Logs nothing."
2. Imports:
   - Standard library: `from __future__ import annotations`, `hashlib`, `json`, `threading`,
     `from collections.abc import Callable`, `from dataclasses import dataclass`, `from pathlib import Path`,
     `from typing import Final, Literal, TypeAlias`.
   - Third party: `numpy as np`, `numpy.typing as npt`.
   - Project: `from meridian.domain.common import MeridianModel`,
     `from meridian.domain.records import Passage, RetrievalResult`, `from meridian.ports.runtime import IndexInfo`,
     `from meridian.retrieval import settings`, `from meridian.retrieval.manifest import ManifestRow`.
   - **Never** import `fastembed` at module level. Never import `meridian.retrieval.ingest`.
3. Private constants:
   - `_REQUIRED_FILES: Final = ("manifest.json", "passages.jsonl", "vectors.npy", "index_record.json")`.
   - `_BUILD_SETTINGS: Final = ("EMBEDDING_MODEL", "SIMILARITY", "CHUNKER", "MAX_SECTION_CHARS", "PIECE_CHARS", "OVERLAP_CHARS")`.
     These are the settings that shape the vectors. `SEARCH_K` and `MIN_SCORE` are query-time settings, so the first E-2
     run can change `MIN_SCORE` without a rebuild.
   - `_MANIFEST_FILES: Final = 17`.
   - `_Reason: TypeAlias = Literal["index_missing", "dimension_mismatch", "manifest_not_17", "record_mismatch"]`.
     Use `TypeAlias`, not a PEP 695 `type` statement: ruff's UP040 is ignored in `pyproject.toml`, and `ingest.py` uses
     the same form.
   - `_REASON_ORDER: Final[tuple[_Reason, ...]] = ("index_missing", "dimension_mismatch", "manifest_not_17", "record_mismatch")`.
4. `Readiness` exactly as §4.5, written as `reasons: tuple[_Reason, ...]`, which is the same type as the inline Literal.
5. `@dataclass(frozen=True, slots=True) class _Loaded:`, one field per line:
   - `info: IndexInfo`
   - `passages: tuple[Passage, ...]`
   - `matrix: npt.NDArray[np.float64]`: the vectors as float64, so a score compares exactly against a Python-float floor.
6. `FastembedIndex.__init__` stores `self._index_dir`, `self._model_cache_dir` and `self._embed_query` (may be None),
   and sets `self._loaded: _Loaded | None = None`, `self._load_lock = threading.Lock()`,
   `self._embed_lock = threading.Lock()`. **No I/O in the constructor.** A missing index must still let `readiness()` run
   and report it.

Check: `uv run python -c "from meridian.adapters.retrieval_fastembed import FastembedIndex, Readiness"`.

### Step 2. Readiness: `_check(index_dir: Path) -> tuple[_Loaded | None, tuple[_Reason, ...]]` (module-level private function)

*Invariant: each fault gives exactly its own reason. No exception leaves `readiness()`. A not-ready index never serves a
search.* Collect reasons into `found: set[_Reason]`, and return `tuple(r for r in _REASON_ORDER if r in found)`.

Wrap each of sub-steps 2–6 in its own `try: … except Exception:` (ruff's selected rules allow it; add a one-line comment
`# any failure reading this artefact is this reason, never an exception`). That way a fault in one artefact always maps
to its own reason, whatever numpy or json raises.

1. **Missing.** If `not index_dir.is_dir()`, or any `_REQUIRED_FILES` entry is not `is_file()`, return
   `(None, ("index_missing",))` at once.
2. **Record.** Read `index_record.json` as UTF-8 and `json.loads` it into `raw`.
   - If it is not a `dict`, or reading fails, set `raw = None`, `info = None` and add `record_mismatch`.
   - Otherwise set `info = IndexInfo.model_validate({name: raw[name] for name in IndexInfo.model_fields if name in raw})`.
     A validation error sets `info = None` and adds `record_mismatch`.
3. **Build settings.** If `raw` is a dict, set `recorded = raw.get("settings")`. Add `record_mismatch` unless `recorded`
   is a dict and `recorded.get(name) == getattr(settings, name)` for every name in `_BUILD_SETTINGS`.
4. **Manifest.** Read `manifest.json` and `json.loads` it. It must be a `list`; then
   `rows = tuple(ManifestRow.model_validate(item) for item in data)`.
   - If any of that fails, set `rows = None` and add `manifest_not_17`.
   - Otherwise, if `len(rows) != _MANIFEST_FILES` or `len({r.path for r in rows}) != len(rows)`, add `manifest_not_17`
     and keep `rows`.
5. **Vectors.** `vectors = np.load(index_dir / "vectors.npy", allow_pickle=False)`.
   - On failure, set `vectors = None` and add `dimension_mismatch`.
   - Otherwise, if `vectors.ndim != 2` or `vectors.dtype != np.float32`, add `dimension_mismatch` and set
     `vectors = None`.
   - Otherwise, if `info is not None and vectors.shape[1] != info.dimension`, add `dimension_mismatch`.
6. **Passages.** Read `passages.jsonl` as UTF-8. For each non-blank line:
   - `obj = json.loads(line)`. It must be a dict.
   - Drop the key `embed_text`.
   - `Passage.model_validate({**obj, "score": 0.0})`.
   On any failure, set `passages = None` and add `record_mismatch`.
7. **Record agrees with the artefacts.** Only when `info is not None`. Add `record_mismatch` when any of these holds:
   - `rows is not None and info.files != len(rows)`;
   - `rows is not None and info.manifest_hash != _manifest_hash(rows)` (the §4.2 formula, as a private helper);
   - `passages is not None and info.chunks != len(passages)`;
   - `vectors is not None and info.chunks != vectors.shape[0]`.
8. If `found` is empty, return `(_Loaded(info, tuple(passages), np.asarray(vectors, dtype=np.float64)), ())`.
   Otherwise return `(None, <ordered reasons>)`.

`readiness(self) -> Readiness`:
- `try: loaded, reasons = _check(self._index_dir)`, with
  `except Exception: return Readiness(ok=False, reasons=("index_missing",))`. This is the never-raises net for anything
  outside the per-artefact blocks (for example a permission error on `is_dir`). Add a one-line comment saying why.
- If `loaded is not None`: `with self._load_lock:` set `self._loaded = loaded` if it is still None.
- Return `Readiness(ok=not reasons, reasons=reasons)`.

`_ensure_loaded(self) -> _Loaded`:
- `with self._load_lock:` if `self._loaded is None`, run `_check`. If the result is None, raise
  `RuntimeError("retrieval index not ready: " + ", ".join(reasons))`. The message holds reason codes only, never a path
  or any text.
- Store the result and return it.

`info(self) -> IndexInfo`: return `self._ensure_loaded().info`.

Check: write the §6 helpers and `test_readiness_failures` now, then
`uv run pytest tests/unit/adapters/test_retrieval_fastembed.py -q -k readiness`.

### Step 3. Search

`search(self, query: str, *, k: int, min_score: float) -> RetrievalResult`.

*Invariant: every returned passage's `score` is the exact Python float that was compared with `min_score`, so
`score >= min_score` holds. At most `k` are returned, score descending; ties keep `passages.jsonl` order.*

1. If `k < 1`, raise `ValueError("k must be at least 1")`.
2. `loaded = self._ensure_loaded()`.
3. `q = np.asarray(self._embed(query), dtype=np.float64).reshape(-1)`.
4. If `q.shape[0] != loaded.info.dimension`, raise `ValueError("query vector dimension does not match the index")`.
5. `norm = float(np.linalg.norm(q))`. If `not np.isfinite(norm) or norm == 0.0`, raise
   `ValueError("query vector is empty")`. Otherwise `q = q / norm`.
6. `scores = loaded.matrix @ q`. Stored rows are already unit length (AEA-16 normalises them), so this is cosine
   (`SIMILARITY = "cosine"`).
7. `order = np.argsort(-scores, kind="stable")`.
8. Walk `order`:
   - `s = float(scores[i])`.
   - If `s < min_score`, break. Every later score is lower; `-inf` never breaks.
   - Otherwise append `loaded.passages[i].model_copy(update={"score": s})`.
   - Stop when `k` passages are collected.
9. `return RetrievalResult(passages=tuple(hits), below_floor=not hits)`.

`_embed(self, query: str) -> npt.NDArray[np.float32]`:
- `with self._embed_lock:` if `self._embed_query is None`, set
  `self._embed_query = _fastembed_query_embedder(self._model_cache_dir)`. Then `return self._embed_query(query)`.
- The lock is held during the call too. fastembed's tokenizer is not documented as thread-safe, and one query takes
  milliseconds.

`_fastembed_query_embedder(cache_dir: Path | None) -> Callable[[str], npt.NDArray[np.float32]]` (module-level, private):
- `from fastembed import TextEmbedding`, as a local import, so tests, `readiness()` and `info()` never load onnxruntime.
- `model = TextEmbedding(settings.EMBEDDING_MODEL, cache_dir=None if cache_dir is None else str(cache_dir))`.
  fastembed 0.9.0's signature is `TextEmbedding(model_name, cache_dir: str | None = None, ...)`.
- Return an inner function `def embed(query: str) -> npt.NDArray[np.float32]` that returns
  `np.asarray(next(iter(model.query_embed(query))), dtype=np.float32)`.
- Use `query_embed`: the planner's measurements (§1.1, step 6) used it.
- Do not pass `local_files_only` here. With `cache_dir=None`, fastembed reads `FASTEMBED_CACHE_PATH`.

Check: `uv run pytest tests/unit/adapters/test_retrieval_fastembed.py -q`.

### Step 4. `agent/tools/knowledge.py`: args model and factory

1. Docstring: "kb_search: the knowledge specialist's one tool (stage7/data.md §4; graph-tools.md §1). knowledge_tools()
   binds it to a RetrievalIndex; nothing registers itself. Reads only; writes and logs nothing."
2. Imports:
   - Standard library: `from __future__ import annotations`, `json`, `from typing import Final`.
   - Third party: `from pydantic import Field, JsonValue`.
   - Project: `LLMFacing` (domain.common), `Passage` and `RetrievalResult` (domain.records), `KnowledgeCapture`
     (domain.specialists), `LookupEntry`, `ToolCallScope`, `ToolDef`, `ToolKind` and `ToolResult` (domain.tools),
     `RetrievalIndex` (ports.runtime), and `from meridian.retrieval.settings import MIN_SCORE, SEARCH_K`.
   - Nothing else (PA-8). In particular, no `meridian.agent.tools.dispatch`.
3. Constants:
   - `KB_SEARCH_NAME: Final = "kb_search"`.
   - `_FOR_MODEL_MAX_CHARS: Final = 4_000`, with the comment
     `# DO-4 §5 "≤ 4,000 chars rendered"; equals dispatch.MAX_CONTENT_CHARS (AEA-22), asserted by test_knowledge.py`.
   - `_CUT_MARK: Final = "…"`.
   - `_SECTION_FALLBACK_CHARS: Final = 80`.
   - `_DESCRIPTION: Final = (...)`: the §4.5 text as one implicitly concatenated string. Keep line breaks out; words are
     separated by single spaces.
4. `class KbSearchArgs(LLMFacing)`, exactly as §4.5.
5. `def knowledge_tools(retrieval: RetrievalIndex) -> tuple[ToolDef, ...]`:
   - Define the closure `def _execute(args: LLMFacing, scope: ToolCallScope) -> ToolResult:` (step 5).
   - Return `(ToolDef(name=KB_SEARCH_NAME, description=_DESCRIPTION, args_model=KbSearchArgs,
     kind=ToolKind.KB_SEARCH, effect="read", requires_verified=False, executor=_execute),)`.
   - No module-level list, dict or registry. Each call builds a new closure and a new `ToolDef`.

### Step 5. The executor (`_execute`, numbered)

*Invariant: the executor reads one search result and returns one `ToolResult`. It writes nothing, opens no unit of work,
logs nothing, and raises whatever the index raises. Dispatch (AEA-22) owns `tool_failed`, the lookup-log write and the
timing.*

1. If `not isinstance(args, KbSearchArgs)`, raise `TypeError("kb_search expects KbSearchArgs")`. Dispatch validates
   against `args_model` first, so this only narrows the type for mypy.
2. `result = retrieval.search(args.query, k=SEARCH_K, min_score=MIN_SCORE)`. Never a literal.
3. `for_model, shown = _for_model(result)`. This private helper returns the JSON value and the passages actually
   rendered.
   - **Below the floor** (`result.below_floor` or no passages): return `({"below_floor": True, "passages": []}, ())`.
   - **Otherwise**, `_fit(result.passages)`:
     1. `_entry(p, text, section) -> dict[str, JsonValue]` returns
        `{"passage_id": p.passage_id, "file": p.file, "section": section, "version_label": p.version_label, "text": text}`.
        Annotate the return type so mypy accepts the dict as `JsonValue`. `PassageId` is a `str` subclass.
     2. `_render(entries) -> dict[str, JsonValue]` returns `{"below_floor": False, "passages": entries}`.
        `_length(value)` is `len(json.dumps(value, ensure_ascii=False, separators=(",", ":")))`. That is exactly how
        dispatch's `_dumps` serialises `for_model`, so a fitted value is never re-truncated.
     3. `cut(text, m)` returns `text` if `len(text) <= m`, else `text[:m] + _CUT_MARK`.
     4. **Full render:** every passage's text and section unchanged. If its `_length` is ≤ `_FOR_MODEL_MAX_CHARS`,
        return it with `shown = passages`.
     5. **Binary search** for the largest `m` in `[0, max(len(p.text))]` for which the render with `text = cut(p.text, m)`
        for every passage has `_length <= _FOR_MODEL_MAX_CHARS`. Binary search is valid because the length never
        decreases as `m` grows. If such an `m` exists, return that render with `shown = passages`.
     6. **Fallback**, only when ids and sections alone exceed the limit (unreachable with k = 3 on this KB): set `m = 0`
        and cut each section to `_SECTION_FALLBACK_CHARS`. Then drop passages from the end while the render is still
        over the limit and more than one passage remains. Return the render, with `shown` = the kept passages.

     *Invariant: the result's `_length` is ≤ 4,000. Passage order is kept. Every kept passage keeps its `passage_id`,
     `file` and `version_label` unchanged (AC-6).*
4. Build the lookup entry:
   - `lookup = LookupEntry(tool=KB_SEARCH_NAME, record_ids=(), passage_ids=tuple(p.passage_id for p in shown),
     result_seen=_result_seen(result.below_floor or not shown, shown), message_id=scope.message_id,
     turn_id=scope.ids.turn_id)`.
   - `_result_seen(below, shown)` returns `"below_floor=true"` when `below`. Otherwise it returns
     `"; ".join(["below_floor=false", *(f"{p.passage_id}={p.score:.3f}" for p in shown)])`.
   - The query and the passage text never enter it.
5. `return ToolResult(ok=True, for_model=for_model, captured=KnowledgeCapture(result=result), lookup=lookup,
   lookup_written=False)`. `captured` holds the **whole** `RetrievalResult` (graph-tools §3); AEA-35 validates the
   model's cited ids against it.

Check: `uv run pytest tests/unit/agent/tools/test_knowledge.py -q`.

### Step 6. Tests

Write the three test files per §7.1, with the helpers per §6. Check: §7.2 row 1, green with **0 skipped**. If the
real-index tests skip, the model cache was not found: fix the environment (`FASTEMBED_CACHE_PATH`), never the test.

**What the real index should show.** The planner measured these on 2026-10-21 with AEA-16's `build_index` on the cached
bge-small (56 chunks), queries through `query_embed`. Each line gives the top results, with the 0.60 floor applied.

| Query | Top results (score) | At the floor |
|---|---|---|
| How much is the Comfort Club? | `membership/comfort_club_overview.md#1` 0.835 (holds $189, $16.99), `#2` 0.813, `services/service_catalog.md#1` 0.756 | 3 passages |
| How long is the repair warranty? | `warranty/warranty_policy.md#0` 0.779, `#1` 0.726, `#2` 0.724 | 3 |
| What's the diagnostic fee? | `warranty/warranty_policy.md#4` 0.802, `faq/customer_faq.md#2` 0.768, `pricing/repair_price_book_2026.csv#15` 0.763 | 3 |
| Can I cancel any time for a full refund? | `membership/comfort_club_overview.md#4` 0.749, `faq/customer_faq.md#4` 0.641, `services/technician_arrival_and_etas.md#0` 0.618 | 3 |
| What are your phone hours? | `faq/customer_faq.md#1` 0.641; next `faq/customer_faq.md#0` 0.595 | **1** (closest to the floor) |
| How long have you been in business? | top 0.555 (`warranty/warranty_policy.md#2`) | **0, below_floor** |
| Do you do duct cleaning? | `services/service_catalog.md#4` 0.642, `faq/troubleshooting_before_you_call.md#4` 0.608 | 2 |
| Can you waive the late-cancellation fee? / Can I get a courtesy discount? / The technician was late, can you waive the diagnostic fee? | none from `internal/` (never indexed) | 3 each |

**If a real-index test fails on a measured score** (AC-2, AC-4, PA-1, PA-10), treat it as a measurement, not a code
bug. The model and chunker are deterministic, so a failure means something changed upstream.
- Do **not** change `MIN_SCORE` (AEA-16's file; it changes only after an E-2 run).
- Do **not** loosen an expected-document set, and do **not** mark the test xfail.
- Stop and report to the orchestrator with the printed per-query files and scores. This needs a DAT-17 / E-2 decision.

### Step 7. Fast gates and the code commit

Run §7.2 rows 2–6, cheapest first. Then:

```bash
git add src/meridian/adapters/retrieval_fastembed.py src/meridian/agent/tools/knowledge.py \
        tests/unit/adapters/test_retrieval_fastembed.py tests/unit/agent/tools/test_knowledge.py \
        tests/contract/test_retrieval_contract.py
git commit -F - <<'EOF'
AEA-33: FastembedIndex and the kb_search tool

FastembedIndex loads AEA-16's index directory, searches by cosine with the
relevance floor and reports readiness (index_missing, dimension_mismatch,
manifest_not_17, record_mismatch; never raises). knowledge_tools(retrieval)
returns the one kb_search ToolDef; its executor searches with SEARCH_K and
MIN_SCORE from retrieval/settings.py and returns for_model within 4,000
chars, a KnowledgeCapture and a LookupEntry. No registry hunk (GRT-1).

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
git rev-parse --short HEAD     # <code-sha>, used in step 8
```

### Step 8. Context, journey record, dev log (AC-10, AC-11), then the docs commit

1. **`.claude/reference/area-map.md`**, A3 row, last cell only. It reads today:
   ``partly built: `retrieval/{settings,manifest,ingest}.py` actual (AEA-16, `fe12657`); `adapters/retrieval_fastembed.py`, `agent/tools/knowledge.py` planned (AEA-33)``.
   Replace it with:
   ``built: `retrieval/{settings,manifest,ingest}.py` actual (AEA-16, `fe12657`); `adapters/retrieval_fastembed.py`, `agent/tools/knowledge.py` actual (AEA-33, `<code-sha>`)``.
   If the cell differs from today's text, keep AEA-16's part as you find it and change only the AEA-33 part.
2. **`.claude/state/icm-progress.md`**: the `Routes verified against code and tests` row whose evidence cell begins
   `2026-10-21: area map A3 →`. Replace only that evidence cell (third cell), ≤ 400 characters:
   ``<YYYY-MM-DD>: area map A3 → `retrieval/{settings,manifest,ingest}.py` (AEA-16, `fe12657`; `tests/unit/retrieval/`) and `adapters/retrieval_fastembed.py`, `agent/tools/knowledge.py` (AEA-33, `<code-sha>`; <N> pass in `test_retrieval_fastembed.py`, `test_knowledge.py`, `test_retrieval_contract.py`, 0 skipped, real index on cached bge-small)``.
   Leave every other row alone.
3. **`docs/design/code-design.md`**:
   - The §4.3 row `adapters/retrieval_fastembed.py`: append to its Notes cell
     `. **Built** AEA-33 `<code-sha>`: `Readiness.reasons` `index_missing`, `dimension_mismatch`, `manifest_not_17`, `record_mismatch` (stage7/data.md §4)`.
   - In the §3 tree, append `   built AEA-33 <code-sha>` (three spaces first) to the end of the `retrieval_fastembed.py`
     line and of the `tools/knowledge.py` line. This follows the `tools/dispatch.py` / `privacy/redact.py` precedent.
   - Change nothing else in the file.
4. **`docs/testing/journeys/<YYYY-MM-DD>-AEA-33.md`**: the `integrated-journeys.md` §4 table, in the shape of
   `docs/testing/journeys/2026-10-21-AEA-16.md`:
   - Claim: AEA-33 `FastembedIndex` and `kb_search` (AC-1…AC-9, PA-1…PA-11). No journey run.
   - Level: `mock-tested`. The real-index tests use the real index and the real model, but no graph and no server. PA-11
     uses the real dispatcher with a recording unit of work.
   - Tested revision: `<code-sha>`.
   - Environment: VPS worktree `inno-aea-callcenter-wt/AEA-33`, Python 3.12, `FASTEMBED_CACHE_PATH` = the main checkout's
     `var/fastembed`, no server, no paid call.
   - Command: §7.2 row 1, and row 6.
   - Result: `<N> passed, 0 skipped`, the per-query files and scores the AC-2/AC-4 tests printed, and the affected-journeys
     output.
   - Evidence location: GitLab issue #33 comment; this file.
   - Remaining limitations: DAT-17's floor is [A] until E-2; "What are your phone hours?" clears it by 0.041; the stored
     `lookup_log` row at the real CON-2 entry point and the `tool:kb_search` span are not exercised here (AEA-51 CAP-1,
     AEA-35).
   - Blocked by: AEA-57 (journey harness, wave 2); AEA-51 (lands J-2, wave 3).
   - Journey step to add once both land (`tests/journeys/j2/test_aea_33.py`, marked `journey`): a membership question
     ("How much is the Comfort Club?") through CON-2 with the scripted model.
     - The reply's source chip names `membership/comfort_club_overview.md` with "Effective 2026-01-01".
     - The turn's `lookup_log` row has `tool = "kb_search"`, and its `passage_ids` include the cited passage.
     - No `archive/` id is in any `lookup_log` row for the turn.
5. **Dev log** `/home/linuxuser/workspaces/Gauntlet AI/devlogs/aea-callcenter/<YYYY-MM-DD>-aea-33-retrieval-index-claude-01.md`.
   Use the header and the four fields of `.claude/reference/dev-log.md` (Changed, Why, Checked, Remaining), 50–100 words.
   It is not committed in this repo.
6. Commit:

```bash
git add .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md \
        docs/testing/journeys/<YYYY-MM-DD>-AEA-33.md
git commit -F - <<'EOF'
docs(AEA-33): journey record and context for the retrieval index

Area map A3, ICM A3 routes row and DO-3 §3/§4.3 marked built at <code-sha>;
journey record at mock-tested, blocked by AEA-57 and AEA-51 (J-2).

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
EOF
```

---

## 6. Data and fixtures (synthetic or issued only)

All shared helpers live in `tests/unit/adapters/test_retrieval_fastembed.py` as public names without a `test` prefix.
The other two test files import them from `tests.unit.adapters.test_retrieval_fastembed`. No conftest is added.

| Helper | Definition |
|---|---|
| `ROOT` | `Path(__file__).resolve().parents[3]` (the repo root) |
| `KB_DIR`, `TRANSCRIPTIONS_DIR` | `ROOT / "docs/data/issued/meridian_dataset/knowledge_base"`, `ROOT / "data/kb_transcriptions"` (read only; `build_index` writes only into `tmp_path`) |
| `FIXTURE_DIM` | `4` |
| `FIXTURE_SCORES` | `(0.9, 0.7, 0.65, 0.5, 0.2)` |
| `QUERY_VECTOR` | `(1.0, 0.0, 0.0, 0.0)` |
| `fixture_passages() -> tuple[Passage, ...]` | Five synthetic passages, each built with `Passage.model_validate` and `score` 0.0, each text starting with the marker `FIXTURE-PASSAGE-<n>`. See the list below this table |
| `fixture_vectors(scores=FIXTURE_SCORES) -> npt.NDArray[np.float32]` | Row i = `[s, sqrt(1 - s*s), 0, 0]`, float32. The dot product with `QUERY_VECTOR` is `s` |
| `fixture_manifest(n=17) -> list[dict[str, object]]` | n rows: `{"path": f"fixture/doc_{i:02d}.md", "status": "current", "version_label": "Effective 2026-01-01", "parse_method": "markdown", "reason": None, "source_sha256": "0" * 64, "chunks": 0}`. These pass `ManifestRow`'s validators |
| `manifest_hash(rows) -> str` | The §4.2 formula over `ManifestRow.model_validate(r).model_dump(mode="json")` of each row |
| `build_settings() -> dict[str, object]` | `{name: value for name, value in vars(settings).items() if name.isupper()}` (`from meridian.retrieval import settings`), the same expression `build_index` uses |
| `write_index_dir(index_dir, *, passages=None, vectors=None, manifest=None, record_overrides=None) -> Path` | See the paragraph below this table |
| `StandInEmbed(vector=QUERY_VECTOR)` | Callable class. `__call__(query: str)` appends the query to `self.queries: list[str]` and returns `np.asarray(vector, dtype=np.float32)` (a copy). It stands in for bge-small (DO-3 S-5) |
| `hash_embed(texts: Sequence[str]) -> npt.NDArray[np.float32]` | Stand-in `EmbedFn` for `build_index`. Each row is `np.frombuffer(hashlib.sha256(t.encode("utf-8")).digest()[:8], dtype=np.uint8).astype(np.float32) + 1.0`, stacked to `[n, 8]`. Never all-zero |
| `cached_model_dir() -> Path \| None` | See the paragraph below this table |
| `requires_model` | `pytest.mark.skipif(cached_model_dir() is None, reason="bge-small-en-v1.5 is not cached locally; set FASTEMBED_CACHE_PATH (tests never download)")`. It is a builtin mark, so no marker registration is needed |

The five `fixture_passages()`, by index:

| # | `passage_id` (file is the part before `#`) | `section` | `version_label` | `version_date` | `text` |
|---|---|---|---|---|---|
| 0 | `membership/comfort_club_overview.md#0` | `Comfort Club Maintenance Plan > Plans` | `Effective 2026-01-01` | 2026-01-01 | `FIXTURE-PASSAGE-0 Price: $189 per year per system, or $16.99 per month` |
| 1 | `faq/customer_faq.md#1` | `Meridian Home Comfort — Customer FAQ > Hours & Contact` | `Last updated 2026-03-02` | 2026-03-02 | `FIXTURE-PASSAGE-1 Phone lines are open on weekdays.` |
| 2 | `policies/escalation_and_safety.md#0` | `Escalation and Safety` | `Rev 2026-01` | None | `FIXTURE-PASSAGE-2 Safety first.` |
| 3 | `faq/troubleshooting_before_you_call.md#2` | `Before you call` | `undated` | None | `FIXTURE-PASSAGE-3 Check the thermostat.` |
| 4 | `pricing/repair_price_book_2026.csv#4` | `HVAC repair > Run capacitor replacement` | `2026` | None | `FIXTURE-PASSAGE-4 sku: HV-CAP-01` |

**`write_index_dir`.**
- Defaults are the three fixtures above (`fixture_passages()`, `fixture_vectors()`, `fixture_manifest()`).
- It writes the four files in §4.2's format:
  - `passages.jsonl` lines are
    `json.dumps({**p.model_dump(mode="json", exclude={"score"}), "embed_text": p.section + "\n" + p.text}, sort_keys=True, ensure_ascii=False)`.
  - `vectors.npy` is written with `np.save(..., allow_pickle=False)`.
- The record is computed from the written artefacts: `embedding_model` `"BAAI/bge-small-en-v1.5"`,
  `dimension = vectors.shape[1]`, `chunks = len(passages)`, `manifest_hash`, `files = len(manifest)`,
  `settings = build_settings()`.
- Then it applies `record.update(record_overrides or {})`.

**`cached_model_dir`.** It tries these candidates in order:
1. `Path(os.environ["FASTEMBED_CACHE_PATH"])`, if the variable is set;
2. `ROOT / "var/fastembed"`;
3. the main checkout's `var/fastembed`: the parent of `git rev-parse --git-common-dir` run with `cwd=ROOT`. Resolve a
   relative output against `ROOT`, and ignore `OSError` / `CalledProcessError`.

It returns the first candidate where
`(c / "models--Qdrant--bge-small-en-v1.5-onnx-Q" / "snapshots").glob("*/model_optimized.onnx")` finds a file, and None
if none does.

In `tests/unit/agent/tools/test_knowledge.py` (the contract test imports these):
- `THREAD = "3f2b8c1e-5d4a-4e7b-9c2d-1a2b3c4d5e6f"`, `TURN = "7c9e6679-7425-40de-944b-e07fc1f90ae7"`,
  `REQUEST = "16fd2706-8baf-433b-82eb-8c7fada847da"`. These are canonical lower-case UUID4s.
- `make_scope(message_id: int = 41) -> ToolCallScope` builds through `ToolCallScope.model_validate` with
  `{"ids": {"thread_id": THREAD, "turn_id": TURN, "request_id": REQUEST, "run_tag": "live", "run_id": None,
  "agent_version": "test"}, "customer_id": None, "shown_slot_ids": frozenset(), "now": WORKED_PAIRS_NOW,
  "message_id": message_id}`.
- `scored(passages, scores) -> tuple[Passage, ...]`: `p.model_copy(update={"score": s})`, pairwise.
- Do not import `make_scope` from `dispatch_doubles`. Import only `RecordingUow` from there (PA-11).

No real customer data anywhere. The only issued data used is the KB, read through `build_index` into `tmp_path`.
Synthetic fixture texts are labelled by their `FIXTURE-PASSAGE-<n>` markers. No codes, card-like numbers or phone
numbers appear in fixtures or test names.

---

## 7. Checks

### 7.1 The tests you write, with the code

This is not a `risk::security` ticket, so nothing is frozen.

**`tests/unit/adapters/test_retrieval_fastembed.py`**

**`test_readiness_failures` (AC-3).**
- Setup: `@pytest.mark.parametrize` with ids. Each case writes `write_index_dir(tmp_path / "index", ...)`, mutates it,
  then calls `FastembedIndex(dir, embed_query=StandInEmbed()).readiness()`.

  | Case id | Mutation | Expected |
  |---|---|---|
  | `good` | none | `(True, ())` |
  | `missing_dir` | path never written | `index_missing` |
  | `missing_passages` | unlink `passages.jsonl` | `index_missing` |
  | `dimension` | `record_overrides={"dimension": 384}` | `dimension_mismatch` |
  | `vectors_garbage` | write `b"not a numpy file"` to `vectors.npy` | `dimension_mismatch` |
  | `manifest_16` | `manifest=fixture_manifest(16)` | `manifest_not_17` |
  | `manifest_garbage` | write `"{not json"` to `manifest.json` | `manifest_not_17` |
  | `record_chunks` | `record_overrides={"chunks": 6}` | `record_mismatch` |
  | `record_hash` | `record_overrides={"manifest_hash": "f" * 64}` | `record_mismatch` |
  | `record_settings` | `record_overrides={"settings": {**build_settings(), "CHUNKER": "other/0"}}` | `record_mismatch` |
  | `record_garbage` | write `"[]"` to `index_record.json` | `record_mismatch` |

- Asserts: the result `== Readiness(ok=expected_ok, reasons=expected)` exactly, with exactly one reason in every failing
  case. No exception escapes. `StandInEmbed.queries == []`. Print `case → reasons`.

**`test_search_and_info_refuse_when_not_ready` (PA-3).**
- Setup: missing directory.
- Asserts: `search("x", k=3, min_score=0.6)` and `info()` each raise `RuntimeError` whose message contains `index_missing`
  and not the directory path. The embed stand-in was never called.

**`test_info_reads_index_record` (PA-4).**
- Setup: `write_index_dir`.
- Asserts: `info() == IndexInfo(embedding_model="BAAI/bge-small-en-v1.5", dimension=4, chunks=5,
  manifest_hash=manifest_hash(fixture_manifest()), files=17)`.

**`test_search_normalises_query_and_keeps_row_order_on_ties` (PA-5).**
- Setup and asserts, case (a): with `StandInEmbed((2.0, 0, 0, 0))`, scores ≈ `FIXTURE_SCORES[:3]` (abs 1e-6) at
  `k=3, min_score=-inf`.
- Setup and asserts, case (b): vectors where rows 1 and 2 are both `fixture_vectors((0.7,))[0]`. The two tied passages
  come back in row order (`#1` before `#2`).

**`test_query_dimension_mismatch_raises` (PA-6).**
- Setup: `StandInEmbed((1.0, 0.0, 0.0))`.
- Asserts: `search` raises `ValueError`.

**`test_default_embedder_loads_nothing_until_search` (PA-7).**
- Setup: `write_index_dir`, then
  `subprocess.run([sys.executable, "-c", CODE, str(dir)], cwd=ROOT, capture_output=True, text=True, check=True)`.
  `CODE` imports `FastembedIndex`, builds it with only `index_dir`, calls `readiness()` and `info()`, and prints
  `ok, "fastembed" in sys.modules, "onnxruntime" in sys.modules`.
- Asserts: stdout stripped == `"True False False"`.

**`test_readiness_ok_on_ingest_output` (PA-2).**
- Setup: `run = build_index(KB_DIR, tmp_path / "index", transcriptions_dir=TRANSCRIPTIONS_DIR, embed=hash_embed)` and
  `ix = FastembedIndex(tmp_path / "index", embed_query=StandInEmbed((1.0,) * 8))`.
- Asserts:
  - `ix.readiness() == Readiness(ok=True, reasons=())`.
  - `ix.info()` has `files == 17`, `chunks == run.chunks`, `manifest_hash == run.manifest_hash` and `dimension == 8`.
  - `ix.search("x", k=run.chunks, min_score=float("-inf"))` returns `run.chunks` passages.
  - Every returned `file` is a `MANIFEST` path with `status == FileStatus.CURRENT`.
  - None is `internal/agent_discretion_notes.md`, `services/duct_cleaning.md`, `faq/faq_old_copy.md`,
    `services/scheduling_guide.md`, or under `archive/`.

**`tests/unit/agent/tools/test_knowledge.py`**

**`test_factory_tooldef_and_binding` (AC-5).**
- Setup: `ix1 = FakeIndex(scored(fixture_passages()[:3], (0.9, 0.7, 0.65)))`, `ix2 = FakeIndex()`.
- Asserts:
  - `knowledge_tools(ix1)` has length 1. Its def `d` has `d.name == "kb_search"`, `d.kind is ToolKind.KB_SEARCH`,
    `d.effect == "read"`, `d.requires_verified is False`, `d.args_model is KbSearchArgs`.
  - `"read_invoices" in d.description` and `"below_floor" in d.description`.
  - `KbSearchArgs.model_validate` raises `ValidationError` for `{"query": ""}`, `{"query": "a" * 301}` and
    `{"query": "fees", "extra": 1}`; `{"query": "a" * 300}` passes.
  - Running `d.executor(KbSearchArgs(query="How much is the Comfort Club?"), make_scope())` gives
    `ix1.searches == [("How much is the Comfort Club?", SEARCH_K, MIN_SCORE)]`. Print the values (`3`, `0.6`).
  - With `d2 = knowledge_tools(ix2)[0]`: `d2 is not d`, `d2.executor is not d.executor`, and running `d2` touches `ix2`
    only (`len(ix1.searches) == 1`).
  - No attribute of the `meridian.agent.tools.knowledge` module is a `ToolDef`, or a list, tuple, set or dict that
    contains one.
  - Calling `d.executor` with a different `LLMFacing` subclass raises `TypeError`.

**`test_no_source_below_floor` (AC-4, double).**
- Setup: `FakeIndex(scored(fixture_passages()[:2], (0.55, 0.4)))`; both are below 0.60.
- Asserts:
  - `result.ok is True`.
  - `result.for_model == {"below_floor": True, "passages": []}`.
  - Neither passage's text appears in `json.dumps(result.for_model)`.
  - `result.lookup.passage_ids == ()` and `result.lookup.result_seen == "below_floor=true"`.
  - `result.captured.result.below_floor is True`.

**`test_for_model_within_limit` (AC-6).**
- Setup, three cases:
  - (a) three passages via `Passage.model_validate`: ids `membership/comfort_club_overview.md#0…#2`, file
    `membership/comfort_club_overview.md`, section `Plans`, label `Effective 2026-01-01`, text `"a" * 1100`, scores
    0.9 / 0.8 / 0.7;
  - (b) the same, with text `"b" * 1500`;
  - (c) the same as (b), with section `"Very long section " * 30`.
- Asserts:
  - For each case, `n = len(json.dumps(for_model, ensure_ascii=False, separators=(",", ":"))) <= 4000`. Print n; the
    planner's arithmetic gives about 3,840 for (a).
  - (a): every text equals the original.
  - (b) and (c): all three passages are present, in order, with `passage_id`, `file` and `version_label` unchanged. Each
    text ends with `"…"`, and `text[:-1]` is a prefix of the original.
  - `lookup.passage_ids` equals the three ids, in order.

**`test_lookup_and_logs_hold_no_text` (AC-8).**
- Setup: `caplog.set_level(logging.DEBUG)`. The index is
  `FastembedIndex(write_index_dir(tmp_path / "i"), embed_query=StandInEmbed())`. The query is
  `"zebra-quartz-7731 how much is the Comfort Club"`, a sentinel phrase with no digits that look like a code.
- Asserts:
  - `"zebra-quartz-7731"` is not in `result.lookup.model_dump_json()`, not in
    `json.dumps(result.for_model, ensure_ascii=False)`, and not in `caplog.text` or any `record.getMessage()`.
  - No `FIXTURE-PASSAGE-` marker is in `result.lookup.result_seen` or `caplog.text`.
  - Every `"; "`-separated token of `result_seen` is ≤ 80 chars.
  - `caplog.records == []` (neither module logs).

**`test_lookup_entry_and_capture_complete` (AC-9).**
- Setup: `FakeIndex(scored(fixture_passages(), FIXTURE_SCORES))` and `scope = make_scope(message_id=41)`.
- Asserts:
  - `lookup.tool == "kb_search"` and `lookup.record_ids == ()`.
  - `lookup.passage_ids` equals the ids of passages #0, #1 and #2, in that order.
  - `lookup.result_seen == "below_floor=false; membership/comfort_club_overview.md#0=0.900; faq/customer_faq.md#1=0.700; policies/escalation_and_safety.md#0=0.650"`.
  - `lookup.message_id == 41` and `lookup.turn_id == scope.ids.turn_id`.
  - `result.lookup_written is False` and `result.ok is True`.
  - `result.captured == KnowledgeCapture(result=RetrievalResult(passages=<those three scored passages>, below_floor=False))`.
  - `for_model["passages"][0] == {"passage_id": "membership/comfort_club_overview.md#0", "file": ..., "section": ...,
    "version_label": "Effective 2026-01-01", "text": <full text>}`.

**`test_knowledge_imports_and_literals` (PA-8).**
- Setup: `ast.parse` of `src/meridian/agent/tools/knowledge.py`; `from meridian.agent.tools import dispatch` and
  `from meridian.agent.tools import knowledge` (test-side imports).
- Asserts:
  - The imported modules (from `Import` / `ImportFrom`) include none starting with `fastembed`, `numpy`, `onnxruntime`,
    `meridian.adapters` or `meridian.agent`, and not `meridian.retrieval.ingest`.
  - Every `meridian.*` import starts with `meridian.domain.` or `meridian.ports.`, or is `meridian.retrieval.settings`.
  - The source contains no `0.6` and no `k=3` (after removing spaces).
  - `knowledge._FOR_MODEL_MAX_CHARS == dispatch.MAX_CONTENT_CHARS`. Print both.

**`test_search_error_propagates` (PA-9).**
- Setup: a local class `_Boom` whose `search(...)` raises `RuntimeError("index not ready")` and whose `info()` raises
  too.
- Asserts: `pytest.raises(RuntimeError)` around
  `knowledge_tools(_Boom())[0].executor(KbSearchArgs(query="x"), make_scope())`.

**`test_kb_search_through_dispatcher` (PA-11, seam with AEA-22).**
- Setup:
  - `ix = FakeIndex(scored(fixture_passages()[:3], (0.9, 0.7, 0.65)))`.
  - `registry = ToolRegistry(knowledge_tools(ix))`; `registry.check_covers(frozenset({ToolKind.KB_SEARCH}))`.
  - `uow = RecordingUow()` from `tests.unit.agent.tools.dispatch_doubles`;
    `d = ToolDispatcher(registry, cast(UnitOfWorkFactory, uow))`.
  - `kinds = frozenset({ToolKind.KB_SEARCH})`.
  - Call 1: `ToolCall(id="c1", name="kb_search", args={"query": "How much is the Comfort Club?"})`.
  - Call 2: `ToolCall(id="c2", name="kb_search", args={"query": ""})`.
  - Run `d.dispatch([call1, call2], kinds=kinds, scope=make_scope())`.
- Asserts:
  - `[s.name for s in d.schemas(kinds)] == ["kb_search"]`, and that schema's `input_schema["properties"]` has exactly
    the key `query`.
  - `out[0].record.outcome == "ok"`, and `json.loads(out[0].content) == out[0].result.for_model`; the content does not
    start with `{"truncated"`.
  - `out[0].record.passage_ids` equals the three ids, in order.
  - Exactly one entry was appended to `uow.appended`, with `tool == "kb_search"`, our `passage_ids`, and `result_seen`
    equal to the executor's.
  - `out[1].record.outcome == "refused"` and `out[1].record.error` is `ToolErrorCode.BAD_ARGUMENTS`.
  - `ix.searches` has exactly one entry: the empty query never reached the index.

  Imports: `ToolRegistry`, `ToolDispatcher` from `meridian.agent.tools.dispatch`; `ToolCall` from `meridian.ports.models`;
  `UnitOfWorkFactory` from `meridian.ports.runtime`; `ToolErrorCode` from `meridian.domain.common`.

**`tests/contract/test_retrieval_contract.py`**

**`test_search_shape_and_floor` (AC-1).**
- Setup: a fixture `index_impl` with `params=["fastembed-fixture", "fake-index"]`. The first is
  `FastembedIndex(write_index_dir(tmp_path / "i"), embed_query=StandInEmbed())`; the second is
  `FakeIndex(scored(fixture_passages(), FIXTURE_SCORES))`.
- Cases `(k, min_score)` → expected count: `(3, 0.6)` → 3; `(2, 0.6)` → 2; `(5, 0.6)` → 3; `(1, 0.0)` → 1;
  `(5, 0.95)` → 0; `(3, -inf)` → 3; `(10, -inf)` → 5. In general,
  `expected = min(k, sum(s >= min_score for s in FIXTURE_SCORES))`.
- Asserts:
  - `len(r.passages) == expected`.
  - Every `p.score >= min_score`; scores are non-increasing; scores ≈ `FIXTURE_SCORES[:expected]` (abs 1e-5).
  - Each `p.passage_id.startswith(p.file + "#")`; `p.section` and `p.version_label` are non-empty.
  - `p.version_date is None` exactly when
    `re.search(r"(?<![0-9])[0-9]{4}-[0-9]{2}-[0-9]{2}(?![0-9])", p.version_label)` finds nothing; otherwise it equals
    that date.
  - `r.below_floor == (expected == 0)`.

**Module fixture `real_index` (scope `"module"`).**
- `cache = cached_model_dir()`; skip if None.
- `out = tmp_path_factory.mktemp("real") / "index"`.
- `model = TextEmbedding(EMBEDDING_MODEL, cache_dir=str(cache), local_files_only=True)`, with a local import of
  `fastembed`. fastembed 0.9.0 accepts `local_files_only` through `**kwargs`.
- A nested `def embed(texts)` returns `np.asarray(list(model.embed(list(texts))), dtype=np.float32)`.
- `run = build_index(KB_DIR, out, transcriptions_dir=TRANSCRIPTIONS_DIR, embed=embed)`.
- Assert `run.status == "completed"`. Build `FastembedIndex(out, model_cache_dir=cache)` (the default embedder path),
  assert its `readiness() == Readiness(ok=True, reasons=())`, and return it.

**`test_stale_traps_on_real_index` (AC-2), `@requires_model`.**
- The expected current documents per query (PRD §4.3a):

  | Query | Expected set (any one returned is enough) |
  |---|---|
  | "How much is the Comfort Club?" | `membership/comfort_club_overview.md` |
  | "How long is the repair warranty?" | `warranty/warranty_policy.md` |
  | "What's the diagnostic fee?" | `faq/customer_faq.md`, `pricing/2026_fee_schedule.pdf`, `pricing/repair_price_book_2026.csv` |
  | "Can I cancel any time for a full refund?" | `membership/comfort_club_overview.md`, `faq/customer_faq.md` |
  | "What are your phone hours?" | `faq/customer_faq.md`, `policies/service_area.md`, `policies/holiday_hours_2026.png` |

- Asserts, per query at `k=SEARCH_K, min_score=MIN_SCORE`:
  - Print `query → [(file, round(score, 3)), …]`.
  - `below_floor is False`.
  - No returned file starts with `archive/` or equals `faq/faq_old_copy.md` / `services/scheduling_guide.md`.
  - The expected set intersects the returned files.

**`test_off_corpus_below_floor` (AC-4), `@requires_model`.**
- Query: "How long have you been in business?"
- Asserts:
  - At the floor, `below_floor is True` and `passages == ()`.
  - Print the top score from a second search at `k=1, min_score=-inf` (the planner measured 0.555).
  - Through `knowledge_tools(real_index)[0].executor(KbSearchArgs(query=...), make_scope())`,
    `for_model == {"below_floor": True, "passages": []}`.

**`test_staff_only_and_stub_not_returned` (AC-7), `@requires_model`.**
- Queries: "Can you waive the late-cancellation fee?", "Can I get a courtesy discount?", "The technician was late, can
  you waive the diagnostic fee?", "Do you do duct cleaning?".
- Asserts:
  - For each query, through the `kb_search` executor: no file in `captured.result.passages` equals
    `internal/agent_discretion_notes.md` or `services/duct_cleaning.md`, and neither string is a substring of
    `json.dumps(for_model)`.
  - `real_index.search("x", k=real_index.info().chunks, min_score=float("-inf"))` (every chunk) contains neither file.
  - Print the returned files.

**`test_wp1_stale_twin_on_real_index` (PA-1, WP-1), `@requires_model`.**
- Query: "How much is the Comfort Club?" at `SEARCH_K` / `MIN_SCORE`.
- Asserts: PA-1's assertions (§3.2). Check `$149` by path only: the fee PDF may legitimately hold it.

**`test_duct_cleaning_answered_from_catalog` (PA-10), `@requires_model`.**
- Query: "Do you do duct cleaning?"
- Asserts: `services/service_catalog.md` is among the returned files. Print the scores (the planner measured 0.642).

### 7.2 Commands (run from the worktree with step 0's two `export`s set)

Run them cheapest first and stop at the first red.

| # | When | Command | Passing looks like |
|---|---|---|---|
| 1 | While iterating, and for evidence | `uv run pytest tests/unit/adapters/test_retrieval_fastembed.py tests/unit/agent/tools/test_knowledge.py tests/contract/test_retrieval_contract.py -q -rsP` | All pass, **0 skipped**; the printed per-query files and scores appear |
| 2 | Before the code commit: lint | `uv run ruff check src tests eval` | `All checks passed!` |
| 3 | Format | `uv run ruff format --check src tests eval` | No file would be reformatted. To fix, run `uv run ruff format <your files>` on owned files only |
| 4 | Type check | `uv run mypy` | `Success: no issues found` |
| 5 | Other affected tests (the folders that mirror the changed packages, plus importers) | `grep -rlE "retrieval_fastembed\|agent\.tools\.knowledge\|agent/tools/knowledge" tests eval`, then `uv run pytest tests/unit/adapters tests/unit/agent/tools tests/unit/test_skeleton.py tests/unit/test_import_direction.py <any other listed file> -q` | Green. Today the grep should list only this ticket's three files |
| 6 | Affected journeys | `uv run python -m tests.journeys.affected --base main --list-only`; if it lists any journey, run it again without `--list-only` | Expected `0 journeys affected` (no journey imports these modules yet, and `tests/journeys/j2/` holds only `__init__.py`); any listed journeys pass |

- **No full suite.** Nothing here reaches everything: no `conftest.py`, settings, dependency, lockfile or widely imported
  module changes (`build-loop-test-scope.md`).
- **No `-n` / xdist.** Each worker would rebuild the module-scoped real-index fixture.
- The real-index tests embed 56 chunks once per module (a few seconds) with the cached model. **No paid call and no
  network download.**

### 7.3 Checks and evidence (template)

| Check | Command | Evidence |
|---|---|---|
| Capture verification (the WF-1 fields the row needs) | §7.2 row 1 (`test_lookup_entry_and_capture_complete`, `test_kb_search_through_dispatcher`) | Every `LookupEntry` field equals the scope and the result; dispatch appends exactly one row. The row at the real entry point is AEA-51's CAP-1 |
| WF-14 (deployed index = build record) | `test_info_reads_index_record`, `test_readiness_ok_on_ingest_output` | `info()` equals the record and the run |
| Evaluation check (E-2 traps in the default suite) | `test_stale_traps_on_real_index`, `test_off_corpus_below_floor`, `test_staff_only_and_stub_not_returned` | Printed files and scores per query, in the report and the journey record |
| Fast gates | §7.2 rows 2–4 | Outputs pasted in the report |
| Affected journeys | §7.2 row 6 | Output pasted in the report and the journey record |
| Context | `git diff --name-only main...HEAD` | Exactly §2.1's repo files |

### 7.4 Gates

None: no human, external, paid or live gate. The bge-small model is already cached on the VPS at
`/home/linuxuser/workspaces/inno-aea-callcenter/var/fastembed` (git-ignored). Do not download it again.

### 7.5 What you must not do

- Edit any file outside §2.1. Add a `register_retrieval` body, a conftest, a marker or a dependency.
- Put `3`, `0.6` or `0.60` in `knowledge.py`; change `retrieval/settings.py`; add a keyword or hybrid search, a reranker,
  answer writing or a card id.
- Import `meridian.agent.tools.dispatch` (or anything under `meridian.agent`) from `knowledge.py`. The equality with
  `MAX_CONTENT_CHARS` is checked by the test only.
- Log anything (no `logging.getLogger` in either module). Put the query or passage text into `result_seen`, an exception
  message or a log.
- Write to the lookup log, open a unit of work, or catch the index's exceptions in the executor.
- Import `fastembed` at module level, or import `meridian.retrieval.ingest` from the adapter.
- Re-normalise or re-embed the stored vectors, or re-chunk anything (that is AEA-16's job).
- Make the real-index tests download a model, weaken an expected-document set, or change a measured expectation to go
  green (step 6 stop rule).
- `git add -A`, push or force-push. Never read or print `.env`.

---

## 8. Risks and requests

| # | Risk or request | Handling |
|---|---|---|
| R-1 | **Near-floor queries.** On AEA-16's real index, "What are your phone hours?" clears the 0.60 floor by 0.041 with one passage (`faq/customer_faq.md#1` 0.641; next 0.595). "Do you do duct cleaning?" scores 0.642. The model and chunker are deterministic, so the tests are stable, but a KB or chunker change could flip them | Step 6 stop rule: report the numbers. The floor is DAT-17 [A] until E-2, and this ticket never tunes it. The journey record lists the margin as a limitation |
| R-2 | **`manifest_hash` and the record layout are written by AEA-16 and re-read here** (two copies of one formula) | PA-2 builds the real AEA-16 output and asserts readiness is ok, so any drift fails the default suite |
| R-3 | **`_FOR_MODEL_MAX_CHARS = 4_000` duplicates `dispatch.MAX_CONTENT_CHARS`.** Importing it would make A3 depend on A7b (DO-3 §8 layering) | Closed inside this ticket: PA-8 asserts the two are equal, and PA-11 shows dispatch sends our content untruncated |
| R-4 | **AC-10's journey file is deferred.** J-2 is landed by AEA-51 (wave 3) on AEA-57's harness (wave 2, not merged), so `tests/journeys/j2/test_aea_33.py` cannot be written against a real harness now | The record lists the exact step (step 8.4). **Request to the orchestrator:** once AEA-51 merges, add the J-2 step through AEA-51 or as a small AEA-33 follow-up (same pair) |
| R-5 | **Production model location.** AEA-51 wires `FastembedIndex(Settings.index_dir)` with no `model_cache_dir`, so the first search loads bge-small from fastembed's default (`FASTEMBED_CACHE_PATH` or the temp dir) and could download at run time | **Request to AEA-50:** bake the model into the image and set `FASTEMBED_CACHE_PATH`. **Request to AEA-51:** call `readiness()` before serving (it does not load the model); `info()` and `search()` raise `RuntimeError` on a not-ready index |
| R-6 | The `for_model` keys (`below_floor`, `passages`, `passage_id`, `file`, `section`, `version_label`, `text`) are a model-facing interface | AEA-35's knowledge prompt and AEA-60's checks read §4.5; changes go through this ticket's owner |
| R-7 | `.claude/state/icm-progress.md` has one `Routes verified against code and tests` row per landed area, and parallel tickets edit the same file | This ticket edits only the A3 row's evidence cell, so line-level merges with other tickets' rows stay clean. The merge agent resolves any adjacent-line conflict by keeping both rows |
| R-8 | The test helpers are imported across test files (the contract and knowledge tests import from the adapter unit-test module); PA-11 imports AEA-22's `dispatch_doubles` | Chosen over a new shared helper file or conftest, to stay inside the owned files. The helpers have no `test` prefix, so nothing is collected twice. `dispatch_doubles` is read-only here |

No shared primitive is requested from the integrator, and no contract change is needed: every shape is in data.md §4 /
DO-4 as signed.

---

## 9. Readiness

**READY.** Every decision is made in this plan, and every import it needs is on `main` `d76092f`:
- **AEA-02:** `domain/*`, `ports/runtime.py`, `ports/models.py`.
- **AEA-11:** `tests.fakes.FakeIndex`, `WORKED_PAIRS_NOW`.
- **AEA-16:** `retrieval/settings.py`, `retrieval/manifest.py`, `retrieval/ingest.build_index`, and the index layout.
- **AEA-22:** `agent/tools/dispatch.py` and `tests/unit/agent/tools/dispatch_doubles.py`, used by tests only.

No `blocked-on`. Step 0 still stops if a shape differs. No `NEEDS-DECISION`: nothing needs Innocent, no signed contract
changes, and nothing answers D-4…D-15 differently.

## Deviations

- `test_kb_search_through_dispatcher`: the plan said exactly one lookup row is appended. AEA-22's dispatch also writes a row
  for the refused call (`result_seen` "refused:bad_arguments", no passage ids), so the test asserts two rows: the ok row
  with our ids and the refused row with none. The empty query still never reaches the index.
