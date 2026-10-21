# Signatures and types added at Stage 7 (2026-10-21), data

**Topic:** data (texts, redaction, eval cases and harness, ingestion and retrieval, deploy, docs, UI verify).
**Tickets:** AEA-03, 04, 06, 07, 08, 09, 11, 16, 24, 25, 33, 50, 54, 55, 56. **Decision log:**
[`docs/plans/7b-decisions/data.md`](../../../plans/7b-decisions/data.md) (DAT-1…DAT-32). **Merged** 2026-10-21 against
[merge-clashes.md](../../../plans/7b-decisions/merge-clashes.md): MC-19, 20, 21, 23, 26, 28 applied here (MC-24 in the ledger).
**Signature-check pass (2026-10-21):** `SearchesPassages` returns a typed structural result (§6, DAT-30); the WF-10
client-side turn timings file (§6, DAT-31); `FixedClock` (§8a, DAT-32).
**Residual pass (2026-10-21):** §2 gains the `amount` placeholder, `format_usd` and `TextId.PERSON_REQUEST_LABEL`
(R-W-6, R-W-7 in [`residuals-web.md`](../../../plans/7b-decisions/residuals-web.md)).
**Status:** planned, nothing built. Written by the Stage 7b data resolver (Claude, Opus 5.5).

These follow the sketch rules of [internal-components.md](../internal-components.md) (DO-4) §0: field names, types and
validators are the agreement; bodies are not. A builder may add a private helper, never a field another ticket reads,
without changing this file first. Types DO-4 already defines (`Passage`, `PassageId`, `IndexInfo`, `RetrievalIndex`,
`RetrievalResult`, `ToolDef`, `ToolCallScope`, `LookupEntry`, `ToolResult`, `TurnIds`) are referenced, not repeated.

**Labels:** [Decided §7, engineering] an interface, name, location or internal type decided here (rule
`system-design-questioning` 3) · [A] an engineering default a named measurement replaces · [Source: …] settled by a
document · **Innocent: DAT-n** waits on his decision; the sketch shows the recommended option and says what changes.

---

## 1. `privacy/redact.py` (AEA-04)

Consumers: AEA-12 (`STORE` at intake), AEA-19 (`TRACE` in `mask_otel_spans`), AEA-20 (`JEV`/`SONNET` per role), AEA-22
(lookup-log snapshots), AEA-23 (`LOG` in the log formatter), AEA-27 (identity), AEA-40 (turn service), AEA-51 (CAP-1).
Standard library only (DO-3 §4.1, AEA-04 AC-9), so these are `enum`/`dataclass` types, not pydantic models.

```python
class RedactionKind(StrEnum):                         # [Decided §7, engineering]
    CARD = "card"; CODE = "code"; PHONE = "phone"; EMAIL = "email"; ADDRESS = "address"; NAME = "name"
    CUSTOMER_ID = "customer_id"; INVOICE_ID = "invoice_id"; FREE_TEXT = "free_text"   # FREE_TEXT: LOG only

class RedactionProfile(StrEnum):                      # names fixed by DO-3 §4.1 / DO-4 §12 RoleSpec.redaction
    STORE = "store"; SONNET = "sonnet"; JEV = "jev"; TRACE = "trace"; LOG = "log"

@dataclass(frozen=True)
class Redacted:
    text: str                                         # the redacted text; LOG: "" (length only, below)
    replaced: Mapping[RedactionKind, int]             # how many values of each kind were replaced; never a value
    length: int                                       # len(input); the only thing LOG keeps
    def __repr__(self) -> str: ...                    # counts and length only (AEA-04 AC-5)

class UnknownRedactionProfile(ValueError): ...        # message names the profile value only, never the text (AC-8)

def redact(text: str, profile: RedactionProfile) -> Redacted: ...
    # Pure, idempotent: redact(redact(x, p).text, p).text == redact(x, p).text (system design §10 "applied again").
    # Signature unchanged from DO-3 §4.1. Innocent: DAT-1 — if he picks option B, a keyword-only
    # `known: Sequence[KnownValue] = ()` is added here and the gateway (AEA-20) passes the located customer's values.

Redactor = Callable[[str, RedactionProfile], Redacted]   # the type of redact (MC-23); models §4 LangfuseTraceSink and
                                                      #   the gateway (DO-4) take `redact: Redactor`. A one-profile
                                                      #   consumer (staff §5 `redact_store: Callable[[str], str]`) is
                                                      #   bound by the container as `lambda t: redact(t, RedactionProfile.STORE).text`.
```

**Placeholders** [Decided §7, engineering]: one token per kind, the same on every call and turn (workspace rule
`context-management-multi-turn` 5), and none of them matches a pattern again (idempotence):

| Kind | Token | Kind | Token |
|---|---|---|---|
| CARD | `[card number removed]` (DO-6 step 1 wording) | NAME | `[name]` |
| CODE | `[code]` | CUSTOMER_ID | `[customer id]` |
| PHONE (JEV) | `[phone]` | INVOICE_ID | `[invoice id]` |
| PHONE (SONNET, TRACE) | `[phone ending NN]`, the last two digits kept (DO-6 table; UI's "phone ending 02") | EMAIL | `[email]` |
| ADDRESS | `[address]` (street line only; city and the 5-digit ZIP stay, AEA-04 AC-6) | | |

**What each profile replaces** (✓ replaced, · left):

| Kind | STORE | SONNET | JEV | TRACE | LOG |
|---|---|---|---|---|---|
| card-like (13–19 digits, spaces/dashes allowed, no checksum) | ✓ | ✓ | ✓ | ✓ | (all text dropped) |
| code (standalone 6 digits) | ✓ | ✓ | ✓ | ✓ | (all text dropped) |
| phone | · | ✓ last 2 kept | ✓ | ✓ last 2 kept | (all text dropped) |
| email | · | ✓ | ✓ | ✓ | (all text dropped) |
| street address | · | ✓ | ✓ | ✓ | (all text dropped) |
| name (introduction patterns, DAT-1) | · | · | ✓ | ✓ | (all text dropped) |
| `MHC-\d{5}`, `INV-\d{6}` | · | · | ✓ | · | (all text dropped) |

SONNET's contact row follows system design §3.2 and §10 *What each vendor sees* [Source: DAT-5]; DO-4 §5's comment
"card-like numbers and codes masked" is the stale half. Names: introduction patterns only ("my name is …", "this is …",
"I'm …" followed by capitalised words; SP-1 build §5 `extract_name`), pending **Innocent: DAT-1**.

---

## 2. `policy/texts.py` (AEA-03)

Consumers: AEA-14, 21, 27, 29, 30, 31, 36, 38, 40, 45, 46; AEA-06 copies the same strings into `must_say` items (DAT-6).

```python
class TextId(StrEnum):                                # [Decided §7, engineering] value = "<group>.<name>",
    ...                                               # groups as AEA-03 lists them: greeting, safety, identity,
                                                      # promise, fee_change, followup, booking, limits, live, demo
class TextRenderError(KeyError):
    text_id: str; placeholder: str | None             # names only; never a supplied value (AEA-03 AC-7)

def render(text_id: TextId, /, **values: str) -> str: ...
    # Named placeholders only (case_ref, due_label, window, digits, rep_name, n, amount). Unknown id, a missing
    # placeholder or an extra one → TextRenderError. Sentences are SCREEN_SPECS copy notes word for word (UXR-18)
    # [Source: DAT-6]. `amount` added at the residual pass (R-W-7): the fee line's dollar figure, already formatted.

def format_usd(cents: int) -> str: ...                # policy/texts.py (AEA-03) [Decided §7, engineering; R-W-7]
    # The ONE money formatter for customer text: whole dollars without decimals ("$89", "$129"), otherwise two decimals
    # ("$12.50"); thousands separated ("$1,250"). ValueError for a negative amount. The fee line is
    # render(<booking fee text>, amount=format_usd(row.cents)) (cases.md §2 FeeNote.line), so no amount is ever typed
    # into a sentence and render itself never formats numbers. OpenAPI example: "Standard diagnostic fee: $89".
```

Text added at the residual pass for the history rebuild (web.md §14, R-W-6): `TextId.PERSON_REQUEST_LABEL =
"live.person_request_label"`, "Talk to a person" (SCR-1's button label, as the greeting quotes it), the customer line a
reloaded thread shows for a CON-4 request.

Texts other topics asked for (merge, 2026-10-21; DAT-29):

- **`live` group (staff.md cross-topic DAT):** the four event lines of OpenAPI `EvRepresentativeJoined`, `EvAiPaused`,
  `EvAiResumed`, `EvChatClosed` ("{name} (demo representative) has joined.", "The assistant is paused while {name} is
  here.", "{name} handed the chat back to the automated assistant.", "{name} closed this chat."), with the OpenAPI's
  `{name}` written as the `rep_name` placeholder.
- **`booking` group (graph-nodes.md cross-topic 5):** `booking.urgent_note`, the one fixed booking-note text that marks
  the urgent burning-ruled-out booking (graph-nodes §6). AEA-03 cites its wording source the same way as every other
  text.
- **`identity` group (graph-tools.md §5 and cross-topic C-5, GRT-2; web.md cross-topic AEA-43):** the two CON-6 inbox
  bodies, `TextId.INBOX_CODE_BODY = "identity.inbox_code_body"` (SCR-2: "Your Meridian Home Comfort verification code
  is {digits}. It expires in 10 minutes.", graph-tools' `{code}` written as the `digits` placeholder) and
  `TextId.INBOX_CODE_GONE = "identity.inbox_code_gone"` ("This code is no longer shown. Ask the chat for a new code if
  you need one.", proposal wording). AEA-43 renders them; the digits reach `render` only inside the CON-6 serialiser.

---

## 3. Retrieval build: `retrieval/{settings,manifest,ingest}.py` (AEA-16)

Consumers: AEA-33 (`FastembedIndex` loads the artefacts), AEA-50 (runs the command at `docker build`; CAP-9), AEA-24
(E-2 on this index), AEA-07 (chunking reasoning), AEA-29 (staff guidance, cross-topic §9). `retrieval/settings.py` is a
new file owned by AEA-16 so that retrieval rule 5 ("configuration lives in one place") holds.

```python
# retrieval/settings.py  [Decided §7, engineering]; every value is recorded in index_record.json at build
EMBEDDING_MODEL: Final = "BAAI/bge-small-en-v1.5"     # PRD R-11
SIMILARITY: Final = "cosine"                          # vectors L2-normalised; score = dot product
CHUNKER: Final = "heading-split/1"                    # DAT-11: split at Markdown headings, heading path = section
MAX_SECTION_CHARS: Final = 1100                       # [A] a longer section is cut at blank-line paragraphs …
PIECE_CHARS: Final = 900                              # [A] … into pieces of about this size
OVERLAP_CHARS: Final = 0                              # [A] sections are self-contained in this KB
SEARCH_K: Final = 3                                   # [A] DAT-17; E-2 scores @3
MIN_SCORE: Final = 0.60                               # [A] DAT-17; the relevance floor (cosine)
# Replaced by: the first E-2 run (hit @3 per query and the off-corpus queries' below-floor rate), never by a prompt change.

class FileStatus(StrEnum):
    CURRENT = "current"; EXCLUDED = "excluded"; STAFF_ONLY = "staff_only"; STUB = "stub"   # PRD R-10
class ParseMethod(StrEnum):
    MARKDOWN = "markdown"; TEXT = "text"; PDF_TEXT = "pdf_text"; CSV_ROWS = "csv_rows"
    PNG_TRANSCRIPTION = "png_transcription"           # data/kb_transcriptions/holiday_hours_2026.md, linked to the PNG

class ManifestRow(MeridianModel):                     # retrieval/manifest.py
    path: str                                         # relative to knowledge_base/, e.g. "membership/comfort_club_overview.md"
    status: FileStatus
    version_label: str | None                         # as the file states it; None only for non-CURRENT rows
    parse_method: ParseMethod
    reason: str | None                                # required when status != CURRENT (R-10, DEC-4, audit K-14/K-15)
    source_sha256: str                                # of the issued file's bytes (and the transcription's, for the PNG)
    chunks: int                                       # 0 for every non-CURRENT row (STAFF_ONLY text goes to staff_notes.json)

class ManifestSpec(MeridianModel):                    # the hand-written static part of a row
    path: str; status: FileStatus; version_label: str | None; parse_method: ParseMethod; reason: str | None
MANIFEST: Final[tuple[ManifestSpec, ...]]             # exactly 17, seeded from the parked src/meridian/kb/manifest.py

class IngestError(Exception): ...                     # named reasons; message holds paths and counts only
class UnlistedFile(IngestError): ...                  # a file on disk not in MANIFEST, or a MANIFEST row with no file
class MissingSource(IngestError): ...                 # unreadable answer source or missing transcription → no output written

EmbedFn = Callable[[Sequence[str]], "np.ndarray"]     # texts → float32 [n, dim]; a stand-in in default tests (DO-3 S-5)

class IngestRun(MeridianModel):                       # WF-14 record [Decided §7, engineering: DAT-12]
    ingest_run_id: str                                # UUID4
    status: Literal["started", "completed", "failed"]
    started_at: datetime; finished_at: datetime | None
    manifest_hash: str; files: int; chunks: int; embedding_model: str
    failure: str | None                               # the IngestError class name only

def build_index(kb_dir: Path, out_dir: Path, *, transcriptions_dir: Path, embed: EmbedFn) -> IngestRun: ...
    # Writes into a temp dir and renames into out_dir only on success (AEA-16 AC-5: no partial index).
# CLI (WF-14 entry point, run by AEA-50's Dockerfile):
#   python -m meridian.retrieval.ingest --kb-dir PATH --transcriptions-dir PATH --out-dir PATH
#   exit 0 on completed; non-zero with the IngestError name on failure; stdout: IDs, counts, statuses only.
```

**Index directory layout** (`out_dir`, inside the image; AEA-16 AC-8 records it beside `IndexInfo` in DO-4 §13):

| File | Holds | Read by |
|---|---|---|
| `manifest.json` | 17 `ManifestRow`s, sorted by `path` | AEA-33 readiness (`files == 17`), CAP-9 |
| `passages.jsonl` | one `Passage` per line without `score`, plus `embed_text` (`section + "\n" + text`), row order = vector order | AEA-33 |
| `vectors.npy` | float32 `[chunks, dimension]`, L2-normalised | AEA-33 |
| `index_record.json` | `IndexInfo` fields + every `retrieval/settings.py` constant | AEA-33 (`info()`), AEA-24 (E-2 names its index), CAP-9 |
| `ingest_run.json` | `IngestRun` | CAP-9; no DB row (DAT-12) |
| `staff_notes.json` | `StaffGuidance` (below); never embedded, never in `passages.jsonl` | the staff side (cross-topic §9) |

**`manifest_hash`** = SHA-256 of the canonical JSON (sorted keys, no whitespace) of the 17 rows including
`source_sha256` and `chunks`. Same inputs → same hash; one changed KB byte → a different hash (AEA-16 AC-7).

`StaffGuidance` lives in `retrieval/manifest.py` (pydantic only, no numpy or fastembed import), so
`services/handoff.py` can type its argument without importing ingest code (MC-26; code-design §2.1).

```python
class StaffGuidance(MeridianModel):                   # retrieval/manifest.py [Decided §7, engineering: DAT-13]
    passage_id: PassageId                             # "internal/agent_discretion_notes.md#<n>"
    file: Literal["internal/agent_discretion_notes.md"]
    section: str; version_label: str; text: str; text_sha256: str
def load_staff_guidance(index_dir: Path) -> tuple[StaffGuidance, ...]: ...   # retrieval/ingest.py; pure read
```

---

## 4. `adapters/retrieval_fastembed.py`, `agent/tools/knowledge.py` (AEA-33)

Consumers: AEA-35 (knowledge specialist through dispatch), AEA-22 (dispatch finds `kb_search` by name), AEA-50
(readiness in the image), AEA-51 (`GraphDeps.retrieval`), AEA-24 via `eval/run_retrieval.py` (E-2).

```python
class Readiness(MeridianModel):                       # [Decided §7, engineering]
    ok: bool
    reasons: tuple[Literal["index_missing", "dimension_mismatch", "manifest_not_17", "record_mismatch"], ...]

class FastembedIndex:                                 # implements RetrievalIndex (DO-4 §13) unchanged
    def __init__(self, index_dir: Path, *, model_cache_dir: Path | None = None,
                 embed_query: Callable[[str], "np.ndarray"] | None = None) -> None: ...   # None → fastembed bge-small
    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult: ...
    def info(self) -> IndexInfo: ...
    def readiness(self) -> Readiness: ...             # read by start-up readiness; never raises

class KbSearchArgs(LLMFacing):
    query: str = Field(min_length=1, max_length=300)
def knowledge_tools(retrieval: RetrievalIndex) -> tuple[ToolDef, ...]: ...
    # graph-tools.md §1 (GRT-1, C-6). Returns one ToolDef, KB_SEARCH, bound to `retrieval`: name "kb_search",
    # kind ToolKind.KB_SEARCH, effect "read", requires_verified False, args_model KbSearchArgs; its executor calls
    # retrieval.search(query, k=SEARCH_K, min_score=MIN_SCORE).
```

No self-registration and no `register_` hunk: AEA-51's wiring builds the one `ToolRegistry` from `knowledge_tools`,
`account_tools` and `scheduling_tools` (graph-tools.md §1; cross-topic §9 item 5).

---

## 5. Eval case files (AEA-06 writes; AEA-24 reads) [Decided §7, engineering: DAT-27]

One JSON file per case script and one per answer key, so a held-out key can sit apart from its script (DO-6 *Capture*,
AEA-06 *Observability*). JSON, not YAML: no new dependency. AEA-06 also writes `eval/cases/case.schema.json` (JSON Schema
of the models below) and `eval/cases/FORMAT.md`; AEA-24's loader validates against that schema when it exists.

```
eval/cases/dev/<case_id>.case.json        CaseScript      eval/cases/dev/<case_id>.key.json        CaseKey
eval/cases/heldout/<case_id>.case.json    CaseScript      <held-out key dir>/<case_id>.key.json    CaseKey  (Innocent: DAT-2)
eval/cases/retrieval/<query_id>.json      RetrievalQuery
eval/cases/split.json                     SplitRecord     eval/cases/mix.json                      MixRecord
```

```python
class ScriptedTurn(BaseModel):                        # discriminated on "kind"; mirrors CON-2 payloads
    kind: Literal["text", "choice", "form", "code_from_inbox", "person_request"]
    text: str | None = None                           # kind "text": the customer's words
    choice: str | None = None                         # kind "choice": the option id the case picks
    form: dict[str, str] | None = None                # kind "form": field → value; contact values are "$seed:<field>"
                                                      # tokens the runner fills from the working copy at run time
    # kind "code_from_inbox": the runner reads listDemoInbox and submits the code; no digits ever in the file

class CaseScript(BaseModel):
    case_id: str                                      # stable across runs: "WP-4", "T-<call_id>", "S-<n>", "R-<n>"
    provenance: Literal["worked-pair", "issued-transcript", "synthetic", "promoted-trace"]
    source_ref: str; template: str | None; category: str | None; family: str | None; support_level: str | None
    split: Literal["dev", "held-out"]
    seeded_customer: str | None                       # CustomerId; never a phone or email literal
    staffing: Literal["nobody", "staffed"] = "nobody" # M-1 segment
    clock: datetime | None                            # the demo clock the case assumes; runner refuses on mismatch
    turns: tuple[ScriptedTurn, ...]
    synthetic: Literal["no", "partly", "yes"]
    synthetic_assumption: str | None; varied_dimension: str | None; synthetic_source_case: str | None
    labelled_by: str; labelled_on: date

class ChecklistItem(BaseModel):
    text: str                                         # must_say / must_not_say: the exact sentence or phrase (DAT-6)
    source: str                                       # KB path, DB row, R-n, decision ID or "SCREEN_SPECS SCR-n"
    hard: bool = False                                # a hard gate (DO-5 E-1 row)

class CaseKey(BaseModel):
    case_id: str
    in_scope: bool; topic: Literal["booking", "membership", "billing", "warranty"] | None
    guards: tuple[Literal["boundary", "invariant", "regression"], ...]
    must_do: tuple[ChecklistItem, ...]; must_say: tuple[ChecklistItem, ...]; must_not_say: tuple[ChecklistItem, ...]
    judge_items: tuple[ChecklistItem, ...] = ()       # free-text meaning only (DO-5 *Scoring*)
    unscored: str | None = None                       # the open question; the case is not scored while set (AC-9)

class RetrievalQuery(BaseModel):
    query_id: str; query: str
    expected_file: str | None                         # a CURRENT manifest path; None for an off-corpus query
    expect_below_floor: bool = False                  # True for off-corpus queries (US-7; DAT-17)
    trap: str | None                                  # the stale twin it guards against, when it does
    source: str; synthetic: bool

class SplitRecord(BaseModel):
    seed: int; method: Literal["template-whole, stratified by family and support level"]
    assignment: dict[str, Literal["dev", "held-out"]] # template → split
    heldout_key_sha256: str | None                    # SHA-256 over the sorted key files' bytes; set at sealing

class MixRecord(BaseModel):
    splits: dict[Literal["dev", "held-out"], "SplitMix"]   # size; categories; transcript vs synthetic counts
```

---

## 6. Eval harness records, report and ledger (AEA-24) [Decided §7, engineering: DAT-14, DAT-16, DAT-26]

Consumers: Stage 9; the start-up loader (cases.md §8 `load_eval_reports`; this file §9 item 3) and AEA-53's reader through the `95_ops` eval tables; AEA-25
and AEA-07 (commands). The harness imports nothing from `src/meridian/` (AEA-24 AC-12); these models live in
`eval/harness/records.py`.

```python
class EvalRunRecord(BaseModel):
    run_id: str                                       # UUID4
    suite: Literal["worked-pairs", "retrieval", "e2e", "load"]
    split: Literal["dev", "held-out"] | None          # None for retrieval and worked-pairs
    agent_version: str                                # from getLatestEval.current_agent_version (CON-20)
    harness_commit: str; harness_digest: str
    experiment_id: str | None                         # "XP-n"; refused when split == "held-out"
    repeats: int; started_at: datetime; finished_at: datetime | None   # UTC, timezone-aware (cases.md §1.1, MC-20)
    status: Literal["started", "completed", "failed", "incomplete"]
    cases_expected: int; cases_scored: int            # differ → "incomplete", never reported (DO-6)
    index_manifest_hash: str | None                   # retrieval runs: the index they scored
    judge_spend_usd: float

class ItemResult(BaseModel):
    item: Literal["must_do", "must_say", "must_not_say", "invariant", "trajectory", "judge"]
    index: int; passed: bool | None                   # None: advisory judge item before calibration
    failing_quote: str | None                         # redacted; never a held-out expected output (AC-11)

class EvalCaseResult(BaseModel):
    run_id: str; case_id: str; repeat: int; thread_id: str | None
    passed_hard: bool; items: tuple[ItemResult, ...]
    outcome: Literal["resolved", "handed_off", "degraded", "environment_error"]
    in_scope: bool | None; topic: str | None
    top3: tuple["RetrievedDoc", ...] = ()             # retrieval: file, version_label, score
    below_floor: bool | None = None

class EvalReportFile(BaseModel):                      # eval/reports/<run_id>.json, committed (DO-6: reports are public)
    run: EvalRunRecord
    results: tuple[EvalCaseResult, ...]               # held-out: item pass/fail only, no expected text
    summary: dict                                     # validates as OpenAPI EvalRun (measures as n of N, mix, dev_failures)

class HarnessLedger:                                  # eval/harness/ledger.py; judge calls only
    def __init__(self, cap_usd: float = 5.0, *, path: Path) -> None: ...   # [A] DAT-16; JSONL per Chicago day
    def charge(self, cost_usd: float) -> None: ...    # raises JudgeSpendCapReached when the day's total would pass the cap
    def spent_today(self) -> float: ...

def preflight_spend(monitoring: dict, *, run_estimate_usd: float, judge_cap_usd: float) -> None: ...
    # reads getMonitoring.spend.today_cents / cap_cents; refuses a paid run when today + estimate + judge cap > cap
```

**Commands** (AEA-24; DO-5 *Verification* names are replaced by these at AC-16):

```
python -m eval.harness run --suite worked-pairs|e2e|load --split dev|held-out --repeats 3 --base-url URL
        [--heldout-key-dir PATH] [--experiment XP-n] [--dry-run]
python -m eval.run_retrieval --index-dir PATH         # E-2: the one entry that imports FastembedIndex (outside
                                                      # eval/harness/, so AC-12's scan holds); passes it to
                                                      # eval/harness/retrieval.py run_retrieval_suite(index, queries)
```

```python
# eval/harness/retrieval.py: structural copies of DO-4 §13's search and its result, read-only, so FastembedIndex and
#   its RetrievalResult / Passage satisfy them without the harness importing src/meridian/ (AC-12) [DAT-30]
class PassageLike(Protocol):                          # the DO-4 `Passage` fields the scorer reads
    @property
    def file(self) -> str: ...
    @property
    def section(self) -> str: ...
    @property
    def version_label(self) -> str: ...
    @property
    def score(self) -> float: ...
class SearchResultLike(Protocol):                     # DO-4 §13 RetrievalResult
    @property
    def passages(self) -> Sequence[PassageLike]: ...  # top k, in score order → EvalCaseResult.top3 (RetrievedDoc)
    @property
    def below_floor(self) -> bool: ...                # → EvalCaseResult.below_floor
class SearchesPassages(Protocol):
    def search(self, query: str, *, k: int, min_score: float) -> SearchResultLike: ...
def run_retrieval_suite(index: SearchesPassages, queries: Sequence[RetrievalQuery], *, k: int,
                        min_score: float) -> EvalReportFile: ...
    # hit @3 computed with min_score = -inf (retrieval quality) AND the below-floor flag at the production floor
    # (floor cost), so the first run can set MIN_SCORE (DAT-17).
```

**Client-side turn timings (WF-10, DO-6 *Required records*)** [DAT-31]. The `load` suite (20 scripted conversations at
once, Stage 9) times every CON-2 call from the client's side, because server timing cannot see queueing in front of the
app or network time. Each call appends one row to the file
`eval/reports/<run_id>.client_side_turn_timings.jsonl` (the `client_side_turn_timings` record, one JSON line per
turn), committed beside `eval/reports/<run_id>.json`; the report's `summary` takes p50/p95/max from it (M-23…M-25).
The server's own `turn` rows for the same `run_id` carry `run_tag = load` (WF-1 records), so the two sides join on
`turn_id`.

```python
class ClientTurnTiming(BaseModel):                    # eval/harness/records.py; one line of that .jsonl file
    run_id: str; thread_id: str; turn_id: str         # the ids the harness sent (X-Meridian-Run-Id; CON-2 turn_id)
    conversation_index: int = Field(ge=0)             # 0…19: which scripted conversation
    turn_index: int = Field(ge=0)                     # position in that conversation's script
    sent_at: datetime                                 # UTC, timezone-aware (MC-20)
    first_byte_ms: int = Field(ge=0)                  # request sent → first response byte
    total_ms: int = Field(ge=0)                       # request sent → body read
    http_status: int
    outcome: Literal["reply", "notice", "error", "client_timeout"]   # client_timeout = 65 s browser give-up (CON-1 limits)
    notice_code: str | None                           # BUSY, TURN_TIMEOUT, SPEND_CAP_REACHED, RATE_LIMITED, …; else None
```

**Headers** the runner sends: `X-Meridian-Eval-Key`, `X-Meridian-Run-Id`, `X-Meridian-Run-Tag` (`eval` | `load`),
as web.md §4 declares them (`EVAL_KEY_HEADER`, `RUN_ID_HEADER`, `RUN_TAG_HEADER`; WEB-7). The runner logs in once per
run and reuses the session cookie (web.md cross-topic, DAT-15).

---

## 7. Deploy: `Dockerfile`, `railway.json`, `scripts/` (AEA-50) [Decided §7, engineering]

```jsonc
// railway.json
{ "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile" },
  "deploy": { "healthcheckPath": "/healthz", "restartPolicyType": "ON_FAILURE",
              "restartPolicyMaxRetries": 10,      // [A] DAT-19: Railway's default; M-28 revisits
              "numReplicas": 1 } }
```

**Image** (stages in order): `web` (only when `apps/web/package.json` exists: `npm ci && npm run build`, reading
`apps/web` only; DAT-21) → `index` (`python -m meridian.retrieval.ingest …` with the fastembed model cached in the
image) → `runtime` (code, issued dataset read-only, `/app/index/`, `/app/apps/web/dist/` when built, `/app/eval/reports/`,
`BUILD_SHA`). No `ARG`/`ENV` holds a secret.

```python
# scripts/agent_version.py  (DAT-22)
def compute_agent_version(git_sha: str, model_config: Mapping[str, Any], prompt_files: Iterable[Path]) -> str: ...
    # f"{git_sha[:12]}+{h[:8]}", h = SHA-256 of canonical JSON {"models": model_config,
    #   "prompts": {relative path: sha256(bytes)}} over src/meridian/agent/prompts/*.py and src/meridian/policy/texts.py.
    # git_sha: $RAILWAY_GIT_COMMIT_SHA when set (git-triggered deploys only), else the BUILD_SHA file written by the
    # deploy step before `railway up` (`git rev-parse HEAD`, "-dirty" appended when the tree is dirty), else "unknown".
# CLI prints the value. Start command:
#   sh -c 'export MERIDIAN_AGENT_VERSION="$(python -m scripts.agent_version)" && exec uvicorn … --workers 1 --port "$PORT"'
```

`scripts/reset.py` (WF-15) calls `ResetService.reset(<wall now>, request_id=<new UUID4>, session_id=None, role=None)`
with the real injected callables (AEA-50 *Seams*) and its own `ResetGate` (web.md §7; `reset`'s signature: cases.md §7;
MC-19). That gate
cannot reach the running server, so the script is for a stopped service only; AEA-54's guide says so. The live path is
CON-9. `<wall now>` is `datetime.now(UTC)` (MC-20).

**Railway variables** (AEA-09 sets them, AEA-54's guide lists them): every `Settings` env name in §9 item 1, plus
`MERIDIAN_COOKIE_SECURE=true`, `MERIDIAN_TRUST_PROXY_HEADERS=true`, `MERIDIAN_REQUIRE_FRONTEND=true` and
`MERIDIAN_WEB_DIST_DIR=/app/apps/web/dist` (web.md cross-topic DAT, WEB-32), so a deployed image without `dist/` fails
start-up instead of serving no UI.

---

## 8. Documents (AEA-07, AEA-54, AEA-55)

| Document | Path | Basis |
|---|---|---|
| Technical documentation (D-4) | `docs/technical-documentation.md` | slice plan §5 Q-1 (DAT-7) |
| Deployment guide (D-5) | `docs/deployment-guide.md` | slice plan §5 Q-1 (DAT-8) |
| UI-verify-again report (checklist §8) | `docs/testing/ui-verify-again.md`, linked from `PROJECT-CHECKLIST.md` §8 | DAT-25 |

The UI-verify-again run (AEA-55) also checks that a staff tab treats `ROLE_NOT_ALLOWED` `wrong_role` as "the role was
switched elsewhere" and re-reads `getSession` (staff.md cross-topic DAT, STF-19). The dev mock's per-tab
`sessionStorage` cannot show this, so the check runs against the real API (DAT-29).

---

## 8a. Test fakes: `FixedClock` (`tests/fakes/clock.py`, AEA-11) [DAT-32]

DO-3 §4.2 names `FixedClock` as the test implementation of the `Clock` port (DO-4 §13). The other five fakes implement
their DO-4 Protocols unchanged (AEA-11); this is the one with a constructor and a helper worth agreeing on, because
AEA-29's promise tests build one clock before and one after a due time.

```python
WORKED_PAIRS_NOW = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
    # [Source: docs/data/worked-pairs.md header "Friday 2026-10-16, 10:00"]; the same instant as cases.md DEMO_START

class FixedClock:                                     # implements Clock (DO-4 §13)
    def __init__(self, at: datetime = WORKED_PAIRS_NOW) -> None: ...
        # ValueError when `at` is naive or its tzinfo is not America/Chicago (R-3: never a server wall clock)
    def now(self) -> datetime: ...                    # returns `at`, the same value on every call (AEA-11 AC-6)
    def advanced(self, by: timedelta) -> "FixedClock": ...   # a NEW clock at at + by; this one never moves
```

Consumers: every test that needs a clock (AEA-29 `test_promise_status_kept_and_missed`, AEA-30, AEA-27's code expiry,
AEA-40), and the eval's in-process runs.

---

## 9. Cross-topic assumptions

Each names the owning topic and the ticket. If that topic's resolver decided otherwise, the owner's version wins and the
data ticket named adapts in its plan.

1. **graph (AEA-02 `config.py` `Settings`):** (a) env names. AEA-09 step 6 copies whatever `Settings` declares. Data's
   recommendation, matching the parked `.env.example` and AEA-19: `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`,
   `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `LANGFUSE_PROJECT_ID` (MC-21; models §4 MOD-6
   turns export on only when all four Langfuse values are set; they are set on Railway only after DAT-4 option A and
   Innocent's creation of the project, models cross-topic 7), `MERIDIAN_DEMO_USERNAME`, `MERIDIAN_DEMO_PASSWORD`,
   `MERIDIAN_SESSION_SECRET`, `MERIDIAN_EVAL_KEY`, `MERIDIAN_DATA_DIR` (`/data` on Railway), `MERIDIAN_INDEX_DIR`
   (`/app/index`). (b) `Settings.agent_version: str` read from `MERIDIAN_AGENT_VERSION`, default `"dev"`; every stamp
   (turn, conversation, `deploy_record`, CON-20 `current_agent_version`) reads it. (c) `Settings` exposes the role →
   model map as a plain mapping for `compute_agent_version` (AEA-01's ticket text already says so). **Settled at merge
   (MC-21):** `config.py` `Settings` is AEA-02's (slice plan row AEA-02, Q-2); AEA-01 owns `policy/limits.py` only.
   The owner's field list is graph-core.md's cross-topic row "models 3, data 1 (MC-21)", which accepts every name above
   including `LANGFUSE_PROJECT_ID`; web.md's cross-topic row (WEB-9) adds the four `MERIDIAN_*` web settings (§7).
2. **web (AEA-23 middleware), settled (WEB-7):** `X-Meridian-Eval-Key`, `X-Meridian-Run-Id`, `X-Meridian-Run-Tag`
   (`eval` | `load`), alongside the OpenAPI's `X-Request-ID`, as web.md §4 declares them; AEA-24's runner uses them (§6).
3. **cases (AEA-10 `95_ops.sql`; AEA-32 `repos_ops` and start-up), settled (CAS-27):** tables `eval_runs`,
   `eval_case_results` (columns from §6; cases.md §1.1) and the idempotent start-up loader
   `load_eval_reports(reports_dir: Path, uow: UnitOfWorkFactory) -> int` (cases.md §8, `services/health.py`) that upserts every `eval/reports/*.json` by `run_id`,
   beside the `deploy_record` write. AEA-53 reads the stored `summary`, never recomputes. No `ingest_runs` table
   (DAT-12) and no experiments table (`eval_runs.experiment_id`). Reset keeps eval tables (DO-6 *Storage*).
4. **cases (AEA-29 `HandoffService`), settled (CAS-33):** `HandoffService` takes
   `staff_guidance: Mapping[HandoffReason, tuple[StaffGuidance, ...]]` and writes one `lookup_log` row per attached
   passage (`source.kind = "lookup_log"`, DO-4 §7); the container resolves `STAFF_GUIDANCE_FOR` against
   `load_staff_guidance()` at start-up (cases.md §5). It imports `StaffGuidance` from `retrieval/manifest.py` (§3, MC-26).
5. **graph (AEA-22 dispatch), settled (GRT-1, graph-tools C-6):** no registry call; AEA-33 exposes
   `knowledge_tools(retrieval)` (§4) and AEA-51 builds the registry from it.
6. **graph (AEA-51):** wires `FastembedIndex(Settings.index_dir)` as `GraphDeps.retrieval`; calls `readiness()` at
   start-up through the container.
7. **models (AEA-20 gateway):** applies `SONNET` (now including contact details, DAT-5) and `JEV` per role. If Innocent
   picks DAT-1 option B, the gateway also passes `known` values; that is a models-topic signature change. The gateway
   and `LangfuseTraceSink` type their argument as `Redactor` (§1, MC-23).
8. **models (`ProviderCall`, `SpanHandle`; AEA-11 shared fakes, a data-topic ticket), MC-28:** scripted model fakes put
   a `ProviderCall` in `Attempt.record` (no `role`, no `attempt`) and set `provider`; `InMemoryTraceSink.turn()` yields
   a `SpanHandle` and `export_status(turn)` takes it (stage7/models.md §1, §4). AEA-11 AC-2's "carry a `CallRecord`"
   becomes "carry a `ProviderCall`".
