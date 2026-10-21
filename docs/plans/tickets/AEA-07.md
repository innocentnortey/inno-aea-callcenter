## [AEA-07] docs: technical documentation

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

The portal's **Technical Documentation** deliverable (D-4), written now from the decision records and the final Stage 7
contracts, so it is ready before the build finishes. Lines that need a measured result (eval numbers, the built index's
chunk count, the URL) read `pending: <who fills it>`; the ticket that produces the number replaces its own line.

**File:** `docs/technical-documentation.md` (stage7/data.md §8; DAT-7, settled by slice plan §5 Q-1). Plain Markdown; no
HTML render is required.

**Order (rule `hiring-partner-framing`):** open with the business layer, prove the build, close on how the system moves the
business metric. Each section cites its decision record by path and section; it summarises and links, and never restates
a fact whose owner is another file (rule `source-authority` 9). Every choice carries its status as its record gives it:
*Decided* (owner, date), *[A]* engineering default with the measurement that replaces it, or *Proposed, awaiting
Innocent* for the open decisions named in the handoff.

| # | Section | Must contain | Draws from |
|---|---|---|---|
| 1 | The problem behind the brief | Brief said X → we found Y → we built Z; the north star and why containment is reported as coverage × correct resolution | `docs/delivery/2026-10-20-angle-and-demo-framing.md` §1–§3; brief audit *The problem behind this brief*; DO-7 M-1, M-4, M-5 |
| 2 | Discovery: call drivers | Drivers ranked by volume (all 420 calls), the method (how every call was classified, reproducible by `docs/data/scripts/classify_calls.py` and `call_classification.csv`), limits of the evidence, uncertain classifications | PRD §3.1; `docs/data/handoff-information-inventory.md` §2, §3.1–§3.4, §10.3, §11.1 |
| 3 | Scope decision: the right 3, not just the top 3 | What is handled (scheduling + membership, billing, warranty answers), what escalates by design, coverage per step (58.3% tonight, 57.8% without wrong numbers, both measured on the 420 issued calls) and the roadmap | PRD §3.2–§3.3; consolidated direction §9.4 (D4), §9.7; brief audit DEC-1…DEC-5 |
| 4 | Data traps we caught | One row per trap: location, what it is, what the system does (stale archive copies K-6/K-8, excluded files, the duct-cleaning stub never indexed (DAT-18), staff-only notes kept out of every customer index (DAT-13), the holiday PNG via its transcription, contradictions, transcript oddities) | Brief audit §1–§4 (C-, K-, D-); PRD R-10; inventory §5.3, §10.2; stage7/data.md §3 |
| 5 | Knowledge base: ingestion, chunking, retrieval | Every format and how it is parsed (MD, TXT, fee PDF, price-book CSV one row per chunk, holiday PNG via transcription); the exclusions and why; the chunking method (heading-aware split, heading path as `section`, sections over 1,100 characters cut at paragraphs into about 900, no overlap) and why it comes from the KB's own shape (every file ≤ 2.1 KB with 1–8 headings) [A] until the first E-2 run; `BAAI/bge-small-en-v1.5` and the local index built into the image; `k = 3` and the relevance floor 0.60 [A], with the pre-build measurement that chose them (labelled [M], 12 in-corpus and 8 off-corpus questions, DAT log) and its stated limit (the two score ranges overlap, so R-13 and the R-46 fact check still carry off-corpus refusals); citations with file and version date; why retrieval is evaluated on its own (E-2). **Built index chunk count:** `pending: AEA-16 index record` | PRD R-9…R-13, §4.3a; DO-1 §11 decision 10; DO-5 E-2; stage7/data.md §3, §4; DAT-11, DAT-12, DAT-17, DAT-18 |
| 6 | How one turn works | The two-layer turn (rules and code decide what they can; models plan, act and word), every place a model chooses and why, model mix B, turn-to-turn context rebuilt each turn (R-45), the R-46 checks on the model's words; what each vendor sees: Anthropic gets redacted text with cards, codes, emails, street addresses masked and phones reduced to their last two digits (SONNET profile, DAT-5); Jev via OpenRouter gets redacted text and typed flags with `data_collection: deny`; how loose names in free chat are handled (DAT-1) | PRD §6.1; DO-2 §A.1, §A.2, §A.6; HP-1, HP-4; SP-1 §3–§4; DO-1 §3.2, §10 *What each vendor sees*, §11 decisions 3, 6, 7, 9; stage7/data.md §1 |
| 7 | Scheduling | Booking rules (zones incl. 78620/Manor, the 24-hour rule, fees by tier), one-transaction writes with a re-read, fee-bearing changes become staff requests | PRD §4.5 (R-18…R-23); HP-3; consolidated §9.3; stage7/cases.md §2, §4 |
| 8 | Escalation and handoff | Safety first (R-5…R-8), including while a representative holds the chat (GRC-3), and danger detection (R-47, HP-2 C); the burning-smell paths and the priority of the "both ruled out" case (CAS-16); the trigger list (R-24); the promise table (R-26) and why the model never writes it; the brief and its fact check; staffing and same-chat takeover; what the customer sees | PRD §4.2, §4.6; HP-2, HP-4; consolidated §4–§6, §9.1–§9.5; stage7/cases.md §3; stage7/graph-core.md GRC-3 ledger |
| 9 | Monitoring and the feedback loop | What the monitoring page shows (volume, containment, escalations, failures, latency, spend, alerts as decision lines, trace export `sent n of N` or off), traces to the VPS Langfuse and the ingestion-only route (SDQ-3; DAT-4), the flag → review list loop, and what is deliberately not automatic | PRD R-35…R-37; DO-6 (records, *Content and redaction*, *Open items*); DO-7 M-22…M-29; consolidated C5; stage7/models.md §4 (MOD-6 project check) |
| 10 | Evaluation method | The test set from transcripts, dev vs sealed held-out split by template (EVQ-1 = A), expected-answer authority, synthetic cases labelled, the case-file format (script and key in separate files), how the held-out key is kept from build agents until scoring (DAT-2), the judge's own $5/day cap [A] inside the $30 cap (DAT-16), how containment is computed. **Results:** a link to the test results (D-6) and `pending: Stage 9` for every number | DO-5 (all sections); PRD R-38, R-39; stage7/data.md §5, §6; DAT-2, DAT-16, DAT-27 |
| 11 | Production thinking | What survives a restart (the `/data` volume), the watchdog, the $30/day spend cap and other abuse limits (`policy/limits.py` [A] rate limits, WEB-2), the 60 s deadline and 30-turn admission, the one demo login and which paths answer without it (WEB-1), the 10× scale path (written, not built) | DO-1 §2.3, §6–§9, §11 decisions 1, 2, 4, 5, 11; PRD R-41, R-48; stage7/web.md §5, §6 |
| 12 | Known gaps and assumptions | Each labelled assumption with how it would be checked: the open owner decisions as *Proposed, awaiting Innocent* (handoff list), Jev's unstated retention, losing the volume, synthetic-only escalation thresholds, every [A] engineering default the DAT/WEB/CAS ledgers name with its replacing measurement, conflicts still open in DO-3 §10 | Interview Q-046; PRD §9 risks; DO-1 §9; DO-3 §10; `docs/plans/7b-decisions/*.md` |
| 13 | What we chose not to build | The out-of-scope list and the cut order | PRD §7, §8 cut order |

### Source
- Brief: Part A *Required Deliverables* ("Technical Documentation"); Part B goal 1 ("Document your findings: what the
  drivers are, how you found them, and why you chose the scope you chose"), goal 7 ("Describe how the loop works even if
  you only implement the first step").
- PRD R-43 (deliverables), R-37 (feedback loop described); `SUBMISSION.md` D-4 and *Required goals* rows 1 and 7.
- Final contracts: DO-4 §16 (the addenda win over earlier DO-4 text); stage7/data.md §1, §3–§6, §8; stage7/web.md §5–§6;
  stage7/cases.md §2–§3; stage7/models.md §4. Ledgers: `docs/plans/7b-decisions/data.md` (DAT-1, 2, 4, 5, 7, 11, 12, 13,
  16, 17, 18, 27), `web.md` (WEB-1, WEB-2), `cases.md` (CAS-16), `graph-core.md` (GRC-3).
- Slice plan §1 wave 0 row AEA-07; §3 collision row `README.md, SUBMISSION.md, docs/`; §5 Q-1.
- User story / worked pair / hard problem: none of its own; it explains US-1…US-28, WP-1…WP-8 and HP-1…HP-4 as built.
- **Brief check:** serves "Technical Documentation" and "why you chose the scope you chose"; touches nothing out of scope;
  weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] All 13 sections exist as `##` headings in `docs/technical-documentation.md`, in the table's order, each with a line citing its decision record(s) by path and section — verify: `grep -n '^## ' docs/technical-documentation.md` and read each section's first paragraph — evidence: 13 headings in order; each section names at least one source path.
- [ ] AC-2 [invariant] Every relative link resolves — verify: `grep -o '](\([^)#]*\)' docs/technical-documentation.md | sed 's/^](//' | grep -v '^http' | while read p; do [ -e "docs/$p" ] || echo "MISSING $p"; done` — evidence: no `MISSING` lines (a file not yet written is plain text marked `pending`, not a link).
- [ ] AC-3 [negative] No figure is stated as a result unless a run or the issued data produced it: every percentage, count and score is from PRD §3 / the inventory (measured on the 420 issued calls, so labelled), a ledger measurement labelled [M] with its ledger row (DAT-11, DAT-17), a configured value labelled [A] with its ledger row, or reads `pending: Stage 9` / `pending: AEA-16` — verify: `grep -n -E '[0-9]+(\.[0-9]+)?%|[0-9]+ of [0-9]+|0\.[0-9]{2,3}' docs/technical-documentation.md`, each hit checked against its cited source — evidence: the hit list on the issue, each with its source or `pending`; the 60–75% target appears only labelled as the brief's target.
- [ ] AC-4 [invariant] Decided, [A] and proposed are told apart: each item named in the handoff's *Awaiting Innocent* lines (DAT-1, DAT-2, DAT-4, WEB-1, CAS-16, GRC-3) is written as *Proposed, awaiting Innocent* with the recommended option it describes; every PRD §3.2 `[Proposed]` label is kept; every [A] value names its replacing measurement — verify: `grep -n -E 'DAT-1|DAT-2|DAT-4|WEB-1|CAS-16|GRC-3' docs/technical-documentation.md` and read sections 3, 5–12 against PRD §3.2 and the ledgers — evidence: six hits, each labelled proposed; no open item written as decided.
- [ ] AC-5 [negative] The document holds no secret, credential, verification code, card-like number or full phone number, and no demo-login value — verify: `grep -n -i -E 'password|api[_ -]?key|secret|token|[0-9]{3}[- .]?[0-9]{3}[- .]?[0-9]{4}|([0-9][ -]?){13,19}' docs/technical-documentation.md` — evidence: hits are variable names or descriptions only.
- [ ] AC-6 [negative] Nothing code or tests read is touched — verify: `git diff --name-only <base>..HEAD` — evidence: only `docs/technical-documentation.md`, the `SUBMISSION.md` D-4 row and the context files of AC-7; no path under `src/`, `tests/`, `eval/`, `apps/`, `docs/ux/`, `docs/data/issued/`, nor `pyproject.toml`, `uv.lock`, `Dockerfile`, `railway.json`.
- [ ] AC-7 [regression/context] Same commit: `SUBMISSION.md` D-4 row Evidence points at `docs/technical-documentation.md`, Status `drafted, numbers pending Stage 9`, and *Required goals* rows 1 and 7 name it; `.claude/state/icm-progress.md` needs no row change (no route moves; say so on the issue); no area-map or DO-3 row changes (documentation only); one dev-log entry (`.claude/reference/dev-log.md` contract); the resume note's next action — verify: `git diff` — evidence: the changes in the same commit.

### Observability
N/A — documentation only; no code path runs and no entry point is added or changed, so there is no record to emit or
capture (it describes DO-6's WF-1…WF-19 as designed).

### Evaluation
N/A — documentation only. It describes DO-5's suites and links to their results; it adds no case, runs no suite and sets
no expected answer.

### Metrics
N/A — documentation only. It names M-1, M-4, M-5 and M-22…M-29 as DO-7 defines them and computes none; every value
reads `pending: Stage 9`.

### Blocked by
None. (Lines marked `pending` are filled by AEA-16's merge and Stage 9; neither blocks this ticket.)

### Agent handoff
- Area / owner: delivery documents; `SUBMISSION.md` D-4 (slice plan §3: one owner per document).
- Contracts and shared surfaces: reads every decision record above; writes only `docs/technical-documentation.md` and its
  `SUBMISSION.md` rows (one line per ticket). Consumed by: AEA-25 (the README links to it), AEA-54 (the guide links its
  section 9), Stage 10 demo decision inventory. Must not edit the PRD, design documents, ledgers, README (AEA-25) or the
  deployment guide (AEA-54).
- Scope boundary / refusal: no eval numbers, chunk counts or URL invented; no new decision made in the document (a gap
  found while writing goes to section 12 and onto the issue for Innocent).
- Awaiting Innocent: DAT-1 — built on the recommended option A (introduction and street-address patterns, the limit
  written down); if he picks B or C, section 6's masking paragraph names the located-customer values or the
  name-recognition model instead.
- Awaiting Innocent: DAT-2 — built on the recommended option B (held-out keys outside the repo until the E-4 run, then
  committed with their hash); if he picks A or C, section 10 says the keys sit in `eval/cases/heldout/` behind a deny rule,
  or were written by Innocent.
- Awaiting Innocent: DAT-4 — built on the recommended option A (ingestion-only route on a hostname he names); if he picks
  B, section 9 says deployed traces are off and the `trace_export_failed` alert shows for the life of the app (MC-24).
- Awaiting Innocent: WEB-1 — built on the recommended option A (`/login`, `/assets/`, `/fonts/` public); if he picks B or
  C, section 11 names a self-contained login page or a public app shell instead.
- Awaiting Innocent: CAS-16 — built on the recommended option A (P2 time-sensitive, reason `burning_ruled_out`); if he
  picks B or C, section 8 gives P1 or P3 for that case.
- Awaiting Innocent: GRC-3 — built on the recommended option A (the safety card shows even while a representative holds
  the chat); if he picks B or C, section 8 says the message goes only to the representative, or that every code-only
  safety gate runs first.
- Wave and gates: wave 0; no gate. Labels: `slice::docs`, `wave::0`, `lane::direct`.
- Lane: direct — a Markdown deliverable no code or test reads (rule `ticket-lanes`).
- Risk: None (no value written; AC-5).
- Entry points added or changed: None.
