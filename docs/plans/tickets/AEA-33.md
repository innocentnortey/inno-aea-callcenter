## [AEA-33] retrieval: vector index and the knowledge tool

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

> **US-6:** As a **homeowner**, I need answers about membership, billing fees, warranty, services, hours and the service area
> that come from Meridian's current documents and show where they came from, so that I can trust the number I'm given.
>
> **US-7:** As a **homeowner** asking something Meridian's files don't cover, I need the assistant to say it doesn't have
> that information and offer a person, so that I'm never given a confident guess.

Two files, exactly as `docs/design/contracts/stage7/data.md` §4 signs them:

- **`adapters/retrieval_fastembed.py` — `FastembedIndex`**, implementing DO-4 §13's `RetrievalIndex` unchanged.
  - `FastembedIndex(index_dir, *, model_cache_dir=None, embed_query=None)` loads the artefacts AEA-16's ingest writes into
    the index directory (data.md §3 table): `manifest.json` (17 `ManifestRow`s), `passages.jsonl` (one `Passage` per line
    without `score`, row order = vector order), `vectors.npy` (float32, L2-normalised) and `index_record.json` (`IndexInfo`
    fields plus every `retrieval/settings.py` constant). `embed_query=None` means fastembed's `BAAI/bge-small-en-v1.5`; a
    test passes a stand-in so default tests download nothing (DO-3 S-5).
  - `search(query, *, k, min_score) -> RetrievalResult`: cosine similarity (score = dot product of normalised vectors,
    `SIMILARITY = "cosine"`), the top `k` passages whose score is at least `min_score`, highest first, each a DO-4 §5
    `Passage` (`passage_id`, `file`, `section`, `version_label`, `version_date`, `text`, `score`). `below_floor = True`
    exactly when no passage clears `min_score`. Only CURRENT files were embedded (AEA-16), so excluded, staff-only and
    stub files can never come back. The E-2 runner calls it with `min_score = -inf` to score hit @3 and again at the
    production floor (data.md §6), so filtering by `min_score` here is what both rely on.
  - `info() -> IndexInfo` (embedding model, dimension, chunks, manifest hash, files) read from `index_record.json`.
  - `readiness() -> Readiness(ok, reasons)` never raises; reasons are exactly `index_missing`, `dimension_mismatch`,
    `manifest_not_17`, `record_mismatch` (data.md §4; retrieval rule 7). AEA-51 calls it at start-up through the container
    and a false result keeps the deploy from going live (data.md §9 item 6; system design §8.2 *Retrieval index*).
- **`agent/tools/knowledge.py` — `knowledge_tools(retrieval: RetrievalIndex) -> tuple[ToolDef, ...]`** returns one
  `ToolDef`, `KB_SEARCH`, bound to the index it is given (graph-tools §1, GRT-1; data.md §4, DAT-29 (d)):
  name `"kb_search"`, `kind = ToolKind.KB_SEARCH`, `effect = "read"`, `requires_verified = False` (R-14: public questions
  need no code), `args_model = KbSearchArgs` (`LLMFacing`, `query: str` 1–300 characters), a description that says what it
  returns, when to use it and when not (agent-tools rule 2). Its executor `(KbSearchArgs, ToolCallScope) -> ToolResult`
  calls `retrieval.search(query, k=SEARCH_K, min_score=MIN_SCORE)` with the constants imported from
  `retrieval/settings.py` (`SEARCH_K = 3`, `MIN_SCORE = 0.60`, both [A], DAT-17; no second literal, retrieval rule 5) and
  returns: `ok = True`; `for_model` = the passages rendered (passage id, file, section, version label, text) within 4,000
  characters, or `below_floor: true` with no passage; `captured = KnowledgeCapture(result=<the RetrievalResult>)`
  (graph-tools §3); `lookup = LookupEntry(tool="kb_search", record_ids=(), passage_ids=<returned ids>, result_seen=<ids
  and scores, no free text over 80 characters>, message_id=scope.message_id, turn_id=scope.ids.turn_id)` (DO-4 §5,
  R-29); `lookup_written = False`. It is a read tool: dispatch (AEA-22) writes the `lookup_log` row and times the call
  (`ToolCallRecord.elapsed_ms`; AEA-35's runner turns it into the `tool:kb_search` span, R-G-17);
  this executor writes nothing and opens no unit of work. Nothing self-registers and there is no `register_` hunk for
  this ticket: AEA-51 builds the one `ToolRegistry` from `knowledge_tools`, `account_tools` and `scheduling_tools`
  (graph-tools §1; AEA-01's stub for this area stays empty).

Produces `FastembedIndex` (wired as `GraphDeps.retrieval` by AEA-51 from `Settings.index_dir`; built in the image by
AEA-50; used by `eval/run_retrieval.py`, whose `SearchesPassages` Protocol it satisfies structurally, AEA-24, DAT-26,
DAT-30) and `knowledge_tools` (the knowledge specialist's tool through dispatch, AEA-35; the runner's R-44 quick-check
call, graph-tools §6).

**Example pair (WP-1, stale twin; DEC-4).** Input: query "How much is the Comfort Club?" against the index AEA-16 builds
→ output: `RetrievalResult` whose passages include one from `membership/comfort_club_overview.md` (version label
"Effective 2026-01-01") carrying "$189/year, or $16.99/month with a 12-month minimum"; no passage from
`archive/comfort_club_overview.md` (whose "$149" is the trap) anywhere in the result; `below_floor = False`. Input "How
long have you been in business?" (US-7) → `below_floor = True` and no passage: measured 0.563 against the 0.60 floor
(data ledger DAT-17 [M]). "Do you do duct cleaning?" → the answer comes from `services/service_catalog.md` ("not
offered"), never from the stub `services/duct_cleaning.md`, which is not indexed (DAT-18; R-10).

### Source

- `docs/design/contracts/stage7/data.md` §3 (`retrieval/settings.py` constants, index directory layout, `ManifestRow`), §4
  (`Readiness`, `FastembedIndex`, `KbSearchArgs`, `knowledge_tools`), §6 (`SearchesPassages`, `run_retrieval_suite`
  floor handling), §9 items 5–6; `stage7/graph-tools.md` §1 (registration by factory, `ToolKind`, `ToolCallRecord`), §3
  (`KnowledgeCapture`), §6 (quick-check call), C-6; DO-4 §5 (`ToolDef`, `ToolCallScope`, `LookupEntry`, `ToolResult`,
  `Passage`, lookup-log rule), §13 (`RetrievalIndex`, `RetrievalResult`, `IndexInfo`), §16.
- Decisions: `docs/plans/7b-decisions/data.md` DAT-17 (k = 3, floor 0.60 [A], replaced by the first E-2 run), DAT-18 (stub
  never indexed), DAT-26, DAT-29 (d), DAT-30; `graph-tools.md` GRT-1.
- DO-3 §3, §4.2 (`RetrievalIndex` port), §4.3 (`adapters/retrieval_fastembed.py` row), §6 S-4, S-5, S-13; §9
  `tests/contract/test_retrieval_contract.py`.
- PRD R-10 (exclusions; staff-only `internal/agent_discretion_notes.md`; stub `services/duct_cleaning.md`), R-11 (bge-small,
  citation with file, section and version date), R-12, R-13, R-14; consolidated §9.7 DEC-4 (stale traps: $189 not $149;
  1 year not 90 days; $89 not $79; phone hours Mon–Fri 7–7, Sat 8–4).
- `.claude/rules/retrieval-and-context.md` rules 4–7; `.claude/rules/agent-tools.md`; system design §8.2 *Retrieval index*,
  §8.3 *KB answers*.
- DO-5 E-2 and *Expected-answer authority*; DO-6 WF-1 (`lookup_log`), WF-8, WF-14; DO-7 M-6, M-7; WP-1; HP-1.
- Router rows: area map A3 Retrieval; ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "Make deliberate choices about chunking, embedding, and retrieval … Evaluate retrieval on its
  own. Show that the right documents come back before you trust the agent's answers."; touches nothing out of scope;
  weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `FastembedIndex` honours DO-4 §13's `RetrievalIndex` contract: at most `k` passages, every one with score ≥ `min_score`, sorted by score descending, each carrying `passage_id`, `file`, `section`, `version_label`, `version_date` (None when the label holds no full date, UXR-24) and `score`; `below_floor` is True exactly when no passage clears `min_score`; with `min_score = -inf` it returns `k` passages — verify: `tests/contract/test_retrieval_contract.py::test_search_shape_and_floor` run against a small fixture index directory with fixed vectors and an `embed_query` stand-in, and the same assertions run against AEA-11's `FakeIndex` — evidence: both implementations pass the same assertions.
- [ ] AC-2 [invariant] DEC-4 stale traps on the real index: for "How much is the Comfort Club?", "How long is the repair warranty?", "What's the diagnostic fee?", "Can I cancel any time for a full refund?" and "What are your phone hours?", searched with `SEARCH_K` and `MIN_SCORE`, no passage from `archive/*`, `faq/faq_old_copy.md` or `services/scheduling_guide.md` appears, and the current document the PRD §4.3a knowledge map names is among the results — verify: `tests/contract/test_retrieval_contract.py::test_stale_traps_on_real_index` (marked to need the cached bge-small model; builds the index with AEA-16's `build_index` into a temp dir) — evidence: per query, the returned files listed; zero excluded files.
- [ ] AC-3 [failure/refusal] Readiness fails loudly and never raises: a missing index directory, vectors whose dimension does not match `index_record.json`'s `bge-small-en-v1.5` dimension, a manifest without 17 rows, and an `index_record.json` that disagrees with the loaded artefacts each give `ok = False` with exactly the named reason (`index_missing`, `dimension_mismatch`, `manifest_not_17`, `record_mismatch`); the good fixture gives `ok = True`, `reasons = ()` — verify: `tests/unit/adapters/test_retrieval_fastembed.py::test_readiness_failures` — evidence: four failing cases with their reasons; no exception escapes.
- [ ] AC-4 [failure/refusal] US-7: the off-corpus query "How long have you been in business?" on the real index returns `below_floor = True` with no passage, and `kb_search` hands the model `below_floor: true` with no passage, never a nearest-match passage presented as an answer (R-13) — verify: `tests/contract/test_retrieval_contract.py::test_off_corpus_below_floor` (real index, cached model) and `tests/unit/agent/tools/test_knowledge.py::test_no_source_below_floor` (index double) — evidence: `below_floor` true in both; `for_model` holds no passage text.
- [ ] AC-5 [invariant] `knowledge_tools(index)` returns exactly one `ToolDef`: name `kb_search`, `kind = ToolKind.KB_SEARCH`, `effect = "read"`, `requires_verified = False`, `args_model = KbSearchArgs` (an empty query, a 301-character query and an extra field each fail validation); its executor calls the given index with `k = SEARCH_K` and `min_score = MIN_SCORE` from `retrieval/settings.py`; importing `agent/tools/knowledge.py` registers nothing anywhere (two calls with two index doubles return two independent defs) — verify: `tests/unit/agent/tools/test_knowledge.py::test_factory_tooldef_and_binding` — evidence: field values; the index double records `k=3`, `min_score=0.60`; validation errors on the three bad inputs; no module-level registry.
- [ ] AC-6 [invariant] `for_model` stays within 4,000 characters: three passages of 1,100 characters each fit whole, and longer inputs are cut to the limit without dropping a passage's id, file or version label — verify: `tests/unit/agent/tools/test_knowledge.py::test_for_model_within_limit` — evidence: rendered length ≤ 4,000 in both cases; ids and labels present.
- [ ] AC-7 [negative] Staff-only, stub and excluded text never reaches a customer-facing result: no passage from `internal/agent_discretion_notes.md` (queries naming a fee waiver, a courtesy discount, the late-technician diagnostic waiver) or from `services/duct_cleaning.md` ("Do you do duct cleaning?") is returned by `kb_search` on the real index (R-10, HP-3, DAT-18) — verify: `tests/contract/test_retrieval_contract.py::test_staff_only_and_stub_not_returned` — evidence: neither file in any result.
- [ ] AC-8 [negative] The query and passage text never enter the lookup row or a log: with a query holding a distinctive sentinel phrase, `LookupEntry.result_seen` holds only passage ids and scores (no run of free text over 80 characters, DO-4 §5), and no log record emitted by the adapter or the executor contains the sentinel or any passage text — verify: `tests/unit/agent/tools/test_knowledge.py::test_lookup_and_logs_hold_no_text` (caplog) — evidence: sentinel absent from `result_seen` and every captured record.
- [ ] AC-9 [capture] The executor's `ToolResult` carries what WF-1's `lookup_log` row needs: `lookup.tool = "kb_search"`, the returned `passage_ids` in order, `result_seen`, `message_id` = `scope.message_id`, `turn_id` = `scope.ids.turn_id`, `lookup_written = False`, and `captured` = `KnowledgeCapture` holding the same `RetrievalResult` — verify: `tests/unit/agent/tools/test_knowledge.py::test_lookup_entry_and_capture_complete` — evidence: every field equal to the scope and result. (The row dispatch writes at the real CON-2 entry point is AEA-51's CAP-1.)
- [ ] AC-10 [journey] Extends J-2 (slice plan §0a journey map; backend-amendments §3): a membership question retrieves the current membership document above the relevance floor and never its stale twin, and the stored `lookup_log` row names the passage the answer cites; asserting what the user sees and what is stored, in `tests/journeys/j2/test_aea_33.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j2/test_aea_33.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-33.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-11 [regression/context] Docs updated in the same change — verify: `git diff --name-only` — evidence: `.claude/reference/area-map.md` A3 row (`adapters/retrieval_fastembed.py`, `agent/tools/knowledge.py` planned → actual with the commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §4.3 `adapters/retrieval_fastembed.py` row status planned → built, all three in the diff with only this ticket's rows changed.

### Observability

- Responsibilities (WF-1, knowledge answers): every `kb_search` call yields one complete `LookupEntry` (AC-9) so dispatch
  (AEA-22) writes exactly one `lookup_log` row per call and DO-6's *Missing instrumentation* check "a tool call left no
  lookup-log row" holds; the `tool:kb_search` span is the specialist runner's (AEA-35; graph-tools §2, R-G-17), built
  from dispatch's `ToolCallRecord`. WF-14 (index build): `info()` reports the same `IndexInfo` the
  build recorded in `index_record.json`, so the deployed index and CAP-9's record agree. DO-1 §8.2's `index_unavailable`
  is carried, in the final contracts, as `Readiness.reasons` read at start-up (data.md §4, §9 item 6) and, at run time, as
  dispatch's `tool_failed` `ToolCallRecord` when a search raises (graph-tools §1). No query or passage text in any log
  (AC-8).
- Capture evidence: AC-9 for the entry contents, AC-3 for the readiness reasons; CAP-1 (AEA-51) finds the rows at the
  real CON-2 entry point; CAP-9 (AEA-50) finds the 17-row manifest and the index record in the image.

### Evaluation

- Checks: E-2 retrieval suite (R-12): the expected current document in the top 3, no excluded file in the top 3 for
  stale-trap queries, and the off-corpus queries (`expect_below_floor`, DAT-17) below the floor; cases are AEA-06's
  `eval/cases/retrieval/`, the runner AEA-24's `eval/run_retrieval.py`. AC-2, AC-4 and AC-7 hold the DEC-4 traps, US-7
  and the staff-only file in the default suite.
- Expected-answer authority: the current document the PRD §4.3a knowledge map names for each question, including when a
  stale twin is the closer text match (DO-5 *Expected-answer authority*; audit C-14).

### Metrics

- References: M-6 retrieval current-document hit rate @3; M-7 answers from excluded or stale files.
- Acceptance conditions: M-6 stays computable from `eval_case_result` rows of retrieval runs (top-3 files and version
  dates, WF-8) and M-7 from `lookup_log` passage ids (every passage id names its file). Targets are DO-7's approved ones
  (M-6 ≥ 90%, M-7 = 0), measured at the first E-2 run, not claimed here; that run also replaces `MIN_SCORE` [A].

### Blocked by

AEA-16 (index directory layout, `build_index`, `retrieval/settings.py` constants, the 17-row manifest). The `[journey]`
AC-10's integrated level only (not this ticket's merge): AEA-57 (harness) and AEA-51 (lands J-2, wave 3).

### Agent handoff

- Area / owner: A3 Retrieval; owns `src/meridian/adapters/retrieval_fastembed.py`, `src/meridian/agent/tools/knowledge.py`,
  `tests/contract/test_retrieval_contract.py`, `tests/unit/adapters/test_retrieval_fastembed.py`,
  `tests/unit/agent/tools/test_knowledge.py`.
- Contracts and shared surfaces: consumes `RetrievalIndex`, `RetrievalResult`, `IndexInfo`, `Passage`, `ToolDef`,
  `ToolKind`, `ToolCallScope`, `LookupEntry`, `ToolResult`, `KnowledgeCapture`, `LLMFacing` (AEA-02), the index artefacts,
  `build_index` and `retrieval/settings.py` (AEA-16), `FakeIndex` (AEA-11). Produces `FastembedIndex` and `Readiness` for
  AEA-51 (wiring, start-up readiness), AEA-50 (image) and AEA-24 (E-2 entry), and `knowledge_tools` for AEA-51's registry,
  AEA-22's dispatch and AEA-35's knowledge specialist and quick-check call. Must not edit `retrieval/*`,
  `agent/tools/dispatch.py`, `web/container.py`, `domain/*`, `eval/**`.
- Scope boundary / refusal: no re-ingestion or chunking change (AEA-16), no keyword or hybrid rung, no reranker (only if
  E-2 shows misses, PRD §6.2; retrieval rule 3), no answer writing, no card ids; the executor never writes the lookup
  log; a below-floor result is never dressed up as an answer; the floor and `k` change only through `retrieval/settings.py`
  after an E-2 run, never in a prompt.
- Evidence level (`.claude/rules/integrated-journeys.md` §4): the unit and contract tests are `mock-tested` (the real-index
  ones use the real index and model, no graph); the J-2 journey step (AC-10) records `mock-tested` and `Blocked by:
  AEA-57, AEA-51` until both merge.
- Wave and gates: wave 2; no human gate. The real-index tests need the bge-small model cached locally (no paid call;
  check `df -h /home` before downloading).
- Lane: build-loop — changes source and tests (ticket-lanes).
- Risk: None (slice plan row: no `risk::security`; it reads public KB text only and writes nothing).
- Entry points added or changed: None
