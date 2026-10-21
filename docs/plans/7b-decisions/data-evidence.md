# 7b decision evidence (data and source sweep)

Read-only sweep. Nothing is decided here. Each item is the ticket's own `needs-decision` text, verbatim, followed by quotes from the source files with path:line. "no source found" means the searched keywords bore on nothing in the listed sources.

Sources searched: docs/design/evaluation-plan.md, docs/design/*.md, docs/design/contracts/*.md, docs/data/**, docs/prd/*.md, docs/analysis/*.md, docs/research/*.md, docs/ux/03-structure/*.md, SUBMISSION.md, .claude/rules/*.md, docs/ux/04-prototype/**.

---

## AEA-03 cross-reference: wording of fixed sentences (see AEA-06 #2)

Item (docs/plans/tickets/AEA-03.md:32 and :104): "the case wording is AEA-06's `needs-decision`." and "Where a worked pair words a fixed sentence differently (WP-4 fee line, WP-5 second safety line, WP-6 burning question), the case wording is AEA-06's `needs-decision`."

Quotes: same sources as AEA-06 #2 below. Not a separate decision.

---

## AEA-04 #1: how names and street addresses are found in free text

Item (docs/plans/tickets/AEA-04.md:52): "`needs-decision: how names and street addresses are found in free text.` The signature is `redact(text, profile)`, with no list of the conversation's known values, so a name is found only by pattern"

- docs/design/code-design.md:308: "| `privacy/redact.py` | Replace private values before anything stores them or leaves the process. | `redact(text, profile) -> Redacted` | none |"
- docs/design/system-design.md:163: "App → OpenRouter → TypeSafe (Jev) | The latest customer message and a short chat window **after redaction** (names, phones, emails, addresses, customer and invoice IDs, codes and card-like numbers replaced by placeholders)"

---

## AEA-04 #2: does SONNET also mask contact details?

Item (docs/plans/tickets/AEA-04.md:57): "`needs-decision: does SONNET also mask contact details?` DO-4 §5 says "card-like numbers and codes masked"; system design §10 *What each vendor sees* says Anthropic sees "never codes, card numbers or full contact details`"

- docs/design/system-design.md:478: "**What each vendor sees** | Anthropic: the redacted chat window, task fields and passages; never codes, card numbers or full contact details."
- docs/design/system-design.md:162: "App → Anthropic (Sonnet) | System prompts, the clean chat window, turn facts, ... Card-like numbers and codes are masked first"

---

## AEA-06 #1: how the held-out answer key is kept from build agents

Item (docs/plans/tickets/AEA-06.md:75-77): "`needs-decision: how the held-out answer key is kept from build agents.` DO-5 says the key "sits in a directory their prompts and permissions exclude, and its SHA-256 is recorded here at sealing"; ... the repository is public (R-42)"

- docs/design/evaluation-plan.md:253: "| E-4 | The eval runner, suite `e2e --split held-out`, 3 repeats, run once on the submitted agent version; held-out key hash checked before scoring |"
- docs/design/code-design.md:281: "eval/cases/{dev,heldout,retrieval}/ · eval/reports/"
- docs/design/system-design.md:858: "**The story.** The deployed app is one Docker image on Railway. Stage 9 runs the sealed held-out eval"
- Note: the DO-5 phrase "sits in a directory their prompts and permissions exclude" was not found in these sources (searched: "sits in a directory", "answer key", "held-out"). The repository-public point (R-42) is in docs/prd/ and .claude/rules/project-provenance.md:11 ("project id 2318, public (R-42)"). The answer key is described as the KB and DB in docs/analysis/2026-10-20-brief-audit.md:147: "database state, not human transcript answers, as the answer key."

---

## AEA-06 #2: which wording a case's must_say uses where a worked pair and SCREEN_SPECS differ

Item (docs/plans/tickets/AEA-06.md:81-84): "`needs-decision: which wording a case's must_say uses where a worked pair and SCREEN_SPECS differ.` WP-4's fee line ("Under our current policy, a $49 late-change fee applies to changes within 24 hours of your appointment window.") vs SCREEN_SPECS "The $49 fee applies under current policy."; WP-5's ..."

- docs/design/hard-problems.md:185: "Input → output: "Can I move it?" (appointment in 2 hours) → "Under our current policy, a $49 late-change fee applies to"
- docs/design/design.md:1001: "| 4 | Safety lines in the mockup: "Leave the home immediately." / "Call 911 or your gas utility from outside." / "Don't flip any light switches…" | The KB words in SCREEN_SPECS (two numbered lines) |"
- docs/design/evaluation-plan.md:149: "- `must_say` and `must_not_say`), never a judge item;" (the rule that must_say items are assertions)
- Note: the SCREEN_SPECS sentence "The $49 fee applies under current policy." was not found in docs/ux/03-structure/*.md (searched: "\$49"; the only $49 hits were in hard-problems.md, design.md and docs/data).

---

## AEA-07: path of the technical documentation

Item (docs/plans/tickets/AEA-07.md:26): "**File:** `needs-decision: path of the technical documentation` (no source names one; recommended `docs/technical-documentation.md`, beside the deployment guide AEA-54 writes)."

- SUBMISSION.md:35: "| D-4 | Technical documentation | Portal | "Technical Documentation" (incl. discovery findings: drivers, method, scope choice — PDF goal 1) | — | not started |"
- docs/prd/inno-aea-callcenter-interview.md:797: "- Affects: Technical documentation (D-4)"
- Note: the deliverable is named; no source names a file path (searched: "technical documentation", "technical-documentation").

---

## AEA-09 #1: which VPS hostname and DNS record carry the Langfuse route

Item (docs/plans/tickets/AEA-09.md:48): "pick the hostname (`needs-decision: which VPS hostname and DNS record carry the route`), create its DNS record, and identify what owns ports 80/443"

- docs/design/system-design.md:842: "- **A. A reverse proxy with automatic TLS (for example Caddy) on a VPS hostname, exposing only Langfuse's ingestion"
- docs/design/system-design.md:844: "trace writes. Cost: a hostname and DNS record, about 30 minutes."
- docs/design/system-design.md:845: "- **B. A Cloudflare Tunnel with the same path restriction.** No open inbound port on the VPS. Cost: the hostname must be"
- docs/design/system-design.md:485: "| **The Langfuse route** | Only the ingestion path is reachable from the internet ... (**Decided, SDQ-3**). Turning the route on is Innocent's yes at deploy (Q-062)"

---

## AEA-09 #2: exact variable names for the keys, session secret, eval key, Langfuse and data directory

Item (docs/plans/tickets/AEA-09.md:66-67): "**`needs-decision: the exact variable names for the Anthropic key, OpenRouter key, session secret, eval key, Langfuse keys and host, and the data directory`**: they are fixed by AEA-01's `config.py` and `.env.example`"

- docs/design/code-design.md:568: "credentials from `config.py` (`M..."  (R-48 row: "`web/middleware.py` ... credentials from `config.py`")
- docs/design/observability-contract.md:144-145: "each scripted conversation is a new `thread_id`; the `run_id` header is honoured **only with the eval key** (a Railway variable)"
- docs/design/observability-contract.md:186: "| Key values: API keys, Langfuse keys, the eval key, staff demo passwords, session cookies | Never | Never | Never | Never | Never |"
- Note: no source names the exact variable names (searched: ANTHROPIC_API_KEY, OPENROUTER, SESSION_SECRET, DATA_DIR, MERIDIAN_DEMO). `config.py` is not in the listed sources.

---

## AEA-11 cross-reference: AEA-10's needs-decision on its file (temp_sqlite)

Item (docs/plans/tickets/AEA-11.md:43): "`temp_sqlite()` is not in this ticket (AEA-10 owns it; see AEA-10's needs-decision on its file)."

- no source found (searched: temp_sqlite, file). The AEA-10 ticket itself was not in the scope of this sweep.

---

## AEA-16 #1: chunking method

Item (docs/plans/tickets/AEA-16.md:123-124): "needs-decision: chunking method — no decision record names one. Options: the parked heading-aware split (sections, long ones cut to ~900–1,100 characters, `src/meridian/kb/ingest.py`) or the retrieval rule's default (recursive splitting at ~500 tokens)."

- no source found (searched: chunk, 900, 500 tokens, heading-aware). Consistent with the ticket's claim that no decision record names a method.

---

## AEA-16 #2: where the WF-14 ingest_run record lives

Item (docs/plans/tickets/AEA-16.md:126-127): "needs-decision: where the WF-14 `ingest_run` record lives — DO-6 names it but not its store; the build has no volume DB (index ships in the image)."

- docs/design/observability-contract.md:89: "| WF-14 | Knowledge-base ingestion and index build (R-9, R-11) | runtime-operation | ... | ingest_run, ingestion manifest (17 files, status and parse method each), index record ..."
- docs/design/observability-contract.md:160: "| Conversations, turns, lookup log, check events, cases, case events, promises | SQLite on the Railway volume, beside the working DB copy (PRD §6.2) |"
- docs/design/code-design.md:220: "│   ├── sqlite/repos_ops.py                      health_events, deploy_records, eval results (read)"

---

## AEA-16 #3: how internal/agent_discretion_notes.md reaches staff

Item (docs/plans/tickets/AEA-16.md:128-130): "needs-decision: how `internal/agent_discretion_notes.md` reaches staff (R-10: staff-only; DO-4 §7: it enters the brief as heading 3 or 7 items with `source.kind = "lookup_log"`)."

- docs/design/contracts/internal-components.md:566-567: "Staff-only text (`internal/agent_discretion_notes.md`, record-vs-policy mismatches such as INV-204411) enters the brief as heading 3 or 7 items with `source.kind = "lookup_log"` and is never part of any `ResponderInput` (R-10, HP-3)."
- docs/design/code-design.md:541: "| R-9, R-10 | Ingestion; exclusions | `retrieval/manifest.py`, `retrieval/ingest.py`; staff-only notes to staff fields in `services/handoff.py` |"
- docs/design/contracts/internal-components.md:378: "staff_notes: tuple[StaffNote, ...] = ()           # staff-only (HP-3): to the brief and case view, NEVER the responder"

---

## AEA-24 #1: how eval_run / eval_case_result rows reach the tables CON-20 reads on the deployed app

Item (docs/plans/tickets/AEA-24.md:157-160): "How `eval_run` / `eval_case_result` rows reach the tables CON-20 reads on the deployed app: the harness is HTTP-only, no OpenAPI operation accepts results, and DO-2 §A.5 says results are "`eval/` output written by the harness" while the slice plan puts eval-result tables in `95_ops.sql` (AEA-32)."

- docs/design/observability-contract.md:118: "| `job_run`, `eval_run`, `eval_case_result`, `experiment`, `ingest_run`, `deploy_record`, `reset_event`, `seed_event`, `demo_event` | the run records named in the registry | Their workflows |"
- docs/design/code-design.md:220: "│   ├── sqlite/repos_ops.py                      health_events, deploy_records, eval results (read)"
- docs/design/key-metrics-registry.md:54: "| M-2 | North star on the dev split and worked pairs | ... | `eval_case_result`,"
- docs/design/evaluation-plan.md:253: "| E-4 | ... run report per R-39; the headline on SCR-11 (CON-20) and in the README"
- Note: "95_ops.sql" appears in docs/design/code-design.md:213 ("50_booking,60_cases,90_staff,95_ops}.sql"). No source states where eval results are written on the deployed app.

---

## AEA-24 #2: header names for the eval key, run_id and eval/load choice

Item (docs/plans/tickets/AEA-24.md:161): "The header names for the eval key, `run_id` and eval/load choice (shared with AEA-23)."

- docs/design/observability-contract.md:144-145: "- **Eval runner and load harness → app:** each scripted conversation is a new `thread_id`; the `run_id` header is honoured **only with the eval key** (a Railway variable), so public traffic cannot label itself as test traffic and"
- docs/design/observability-contract.md:126: "| `request_id` | API middleware, on every HTTP request; returned in a response header |"
- Note: no source names the eval-key header or the eval/load header (searched: header, X-Eval, eval key).

---

## AEA-24 #3: the harness judge's own spend cap

Item (docs/plans/tickets/AEA-24.md:162-163): "The harness judge's own spend cap (DO-5 says a ledger "that stops at its cap"; eval spend also counts toward the app's $30/day, M-26)."

- docs/design/evaluation-plan.md:154-155: "tamper check compares them, a dry run on mocked responses comes first, and paid calls go through a spend ledger that / stops at its cap."
- docs/design/evaluation-plan.md:225: "$30/day cap [T, Q-061]. Eval runs and live traffic share that cap"
- docs/design/key-metrics-registry.md:78: "Sum of model-call cost in the calendar day; eval and load runs included, since they share the cap"

---

## AEA-25 #1: where the reviewer gets the demo login

Item (docs/plans/tickets/AEA-25.md:32-33): "**Where the reviewer gets the login:** `needs-decision` (see Agent handoff)."

- docs/design/code-design.md:568: "| R-48 | One demo login gates every route; role switch for a signed-in session (Innocent, 2026-10-21) |"
- docs/design/contracts/api-con-mapping.md:102: "Add an app-wide **demo login** (username + password, one pair from Railway variables): a login operation and screen before anything else"
- docs/design/system-design.md:474: "| **Demo login (whole app)** | One username and password from Railway variables gate every route except the login and `/healthz`"

---

## AEA-25 #2: README holds the login values, or says the login is sent elsewhere

Item (docs/plans/tickets/AEA-25.md:101-103): "**`needs-decision`:** R-48 says the demo login is "given to the reviewer in the README", and R-42 makes the repository public, so a password in the README is readable by anyone"

- docs/design/contracts/api-con-mapping.md:112: "| 3 (superseded by R-48) | **No-passcode demo staff sign-in** | DO-1 §10 and §3.3: "a label, not security", acceptable only because every record is fictional, stated in the README (OD-1, N-15)"
- docs/design/contracts/api-con-mapping.md:112 (continued): "say it plainly on SCR-4 and in the READM..."
- .claude/rules/project-provenance.md:11: "project id 2318, public (R-42)"
- Note: the phrase "given to the reviewer in the README" was not found in these sources (searched: "given to the reviewer", R-48, "submission form", README).

---

## AEA-33 #1: relevance floor min_score and k

Item (docs/plans/tickets/AEA-33.md:83-85): "`needs-decision (measurement-settled):` the relevance floor `min_score` and `k`. No source sets either; E-2 measures hit rate @3 (R-12)."

- docs/design/evaluation-plan.md:161: "| E-2 Retrieval (R-12) | Assertion: the expected current document is in the top 3; no excluded file in the top 3 for stale-trap queries | Hit or miss | Hit rate @3 = hits ÷ queries (M-6)"
- docs/design/evaluation-plan.md:239: "| E-2 | Retrieval current-document hit rate ≥ 90% @3 [T] | M-6 | Framing §2 V1 |"
- Note: no source sets min_score or a floor value (searched: min_score, relevance floor, k = 3, hit rate, @3).

---

## AEA-33 #2: whether the stub services/duct_cleaning.md is indexed

Item (docs/plans/tickets/AEA-33.md:86-88): "whether the stub `services/duct_cleaning.md` ("Stub, not answered from", R-10) is indexed at all; if indexed, how the knowledge specialist is kept from answering from it."

- docs/design/evaluation-plan.md:43: "| Knowledge answers ... | The **current** knowledge-base file for that question; excluded files are never an answer source |"
- docs/design/code-design.md:541: "| R-9, R-10 | Ingestion; exclusions | `retrieval/manifest.py`, `retrieval/ingest.py`; staff-only notes to staff fields in `services/handoff.py` |"
- Note: the phrase "Stub, not answered from" and the file duct_cleaning.md were not found (searched: duct, "Stub, not answered").

---

## AEA-50 ND-50a: Railway restart retry count

Item (docs/plans/tickets/AEA-50.md:122): "**ND-50a** `needs-decision:` How many times should Railway restart a failing process before it stops (the restart policy's retry count)? No source sets it (Q-045 = A says only that the health check restarts the service)."

- docs/design/system-design.md:413: "in-process watchdog probes `/healthz` every 15 s [A]; three failures → the process exits, and Railway's restart policy starts it again (decided Q-045 = A)."
- docs/design/system-design.md:993: "| In-process watchdog that exits the process after 3 failed `/healthz` probes, so Railway restarts it (Q-045 = A) | §8.2 | Rely on Railway's own checks only (check its docs at deploy) |"
- docs/design/key-metrics-registry.md:80: "| M-28 | Health-check restarts | operational | Did the service stop responding and restart? | Count of restarts by the health check, per day"
- Note: no source gives a retry count (searched: restart, retry, Q-045).

---

## AEA-50 ND-50b: is Railway's 15-minute limit enough for a 65 s turn

Item (docs/plans/tickets/AEA-50.md:123): "Is Railway's documented 15-minute request limit (S-232, DO-1 §8.1) enough evidence that a 65 s turn survives the proxy, or must AEA-56 run a live 65 s hold check (DO-3 §2.3 rule 7 still marks it [A])?"

- docs/design/code-design.md:155: "7. **Hosting check.** Railway must keep an HTTP request open for 65 s [A: check its proxy timeout at first deploy; A12]."
- docs/design/code-design.md:151: "5. **The browser waits 65 s** (deadline + 5 s) before "That didn't send";"
- Note: "15-minute" and "S-232" were not found in these sources (searched: 15-minute, 65 s, S-232, proxy).

---

## AEA-50 ND-50c: which issue adds the apps/web build stage to the image

Item (docs/plans/tickets/AEA-50.md:124): "Which issue adds the `apps/web` build stage to the image so AEA-49 has a `dist/` to serve? DO-1 §9 lists the image contents before the React frontend existed, and no slice-plan row owns it."

- no source found (searched: apps/web, dist/). DO-1 §9 is not in the listed sources.
- Nearest: docs/design/observability-contract.md:88: "| WF-13 | Deploy to Railway (R-40) | runtime-operation | Railway build, app start-up |" (names the build step, not the frontend stage).

---

## AEA-50 ND-50d: where the ingest_run record is kept

Item (docs/plans/tickets/AEA-50.md:125): "Where is the `ingest_run` record kept: a file in the image beside the index record, or a `repos_ops` row written at start-up? DO-6 names the record (WF-14) but not its store, and the image build cannot write to the volume."

- Same sources as AEA-16 #2: docs/design/observability-contract.md:89 and :160; docs/design/code-design.md:220 ("repos_ops.py ... health_events, deploy_records, eval results (read)").

---

## AEA-50 ND-50e: which module computes agent_version

Item (docs/plans/tickets/AEA-50.md:126): "Which module computes `agent_version` (DO-6: git SHA plus a hash of the model configuration and prompt versions) and from what (a build argument, or Railway's commit variable [A: confirm its name in Railway's docs])?"

- docs/design/observability-contract.md:133: "| `deploy_id` and `agent_version` | At deploy: Railway's deployment ID; `agent_version` = git SHA plus a hash of model configuration and prompt versions |"
- docs/design/observability-contract.md:88: "| WF-13 | Deploy to Railway (R-40) | runtime-operation | Railway build, app start-up | `deploy_id` (Railway deployment) + git SHA; `agent_version` |"
- Note: no source names the computing module or the Railway commit variable (searched: agent_version, RAILWAY_GIT, git SHA).

---

## AEA-50 gap note: slice-plan dependencies added in 7b (AEA-19, AEA-23)

Item (docs/plans/tickets/AEA-50.md:110): "**Added in 7b (real dependencies missing from the slice-plan row; orchestrator to confirm):** AEA-19 (the Langfuse project-key check AC-6 drives) and AEA-23 (`create_app()` lifespan and the async `/healthz` AC-5 and AC-10 drive)."

- docs/design/code-design.md:268: "│   ├── app.py                                   create_app; lifespan; one 422 handler; async /healthz       A8   2"
- docs/design/code-design.md:147: "3. **`/healthz` is `async def` and reads an in-memory heartbeat**, never the pool or SQLite"
- Note: no source names AEA-19 or AEA-23 or the slice-plan row (searched: AEA-19, AEA-23, project-key, create_app). The code-design area row (A8) is the only nearby placement.

---

## AEA-54: path of the deployment guide

Item (docs/plans/tickets/AEA-54.md:27): "**File:** `needs-decision: path of the deployment guide` (no source names one; recommended `docs/deployment-guide.md`, beside the technical documentation of AEA-07)."

- SUBMISSION.md:36: "| D-5 | Deployment guide | Portal | "Deployment Guide" | — | not started |"
- docs/prd/inno-aea-callcenter-interview.md:894-895: "- Decision: Deferred to the deployment guide (D-5) and DO-1: single environment, redeploy of the previous Railway deployment."
- Note: the deliverable is named; no source names a file path (searched: deployment guide, deployment-guide).

---

## AEA-55 ND-55a: "UI verify again" runs with fake models or live Sonnet and Jev

Item (docs/plans/tickets/AEA-55.md:112): "Does "UI verify again" run the backend with the scripted fake models (no spend ...) or with live Sonnet and Jev (`gate::paid`, real answers, spend counted against the $30/day cap)?"

- docs/design/evaluation-plan.md:155: "tamper check compares them, a dry run on mocked responses comes first, and paid calls go through a spend ledger that"
- docs/design/key-metrics-registry.md:78: "| M-26 | Spend per day against the cap | cost | Stops runaway spend | Sum of model-call cost in the calendar day; eval and load runs included, since they share the cap |"
- docs/design/evaluation-plan.md:255: "| E-8 | The load harness drives 20 scripted dev conversations at once against the deployed app"
- Note: "UI verify again" was not found in these sources (searched: fake model, scripted, UI verify, gate::paid).

---

## AEA-55 ND-55b: where the second UX-5 report goes

Item (docs/plans/tickets/AEA-55.md:113): "Where does the second UX-5 report go? `docs/ux/05-verify/QA_REPORT.md` belongs to the UX track and tickets may not edit `docs/ux/**`."

- no source found (searched: QA_REPORT, 05-verify, ui-verify-again). docs/ux/05-verify is outside the listed source set.

---

## Excluded grep hits (matched gap/missing/conflict text but are not decision items)

- AEA-03.md:63, :123: "missing or unknown" (refusal rule); "a missing sentence is a small ticket" (process rule).
- AEA-07.md:46: "Known gaps and assumptions" (a section name in the document spec).
- AEA-08.md:87: "is missing or disagrees with" (restates a hard stop from new-project-zero-to-hero).
- AEA-24.md:71, :80: "Missing instrumentation" (DO-6 section name).
- AEA-50.md:66, :80, :94: "Missing instrumentation" (DO-6 section name, and a responsibilities list).
- AEA-50.md:115: "real dependencies missing" boilerplate for "Must not edit" (sits with the AEA-50 gap note above).
- AEA-56.md:48: "a missing `mhc_session`" (the status the OpenAPI names for an unsigned request).

## Counts

Entries listed: 28 (decision items, including 2 cross-references from AEA-03 and AEA-11, and the AEA-50 gap note).
With no source found at all: 4 (AEA-11 cross-ref; AEA-16 chunking method; AEA-50 ND-50c apps/web; AEA-55 ND-55b QA_REPORT).
Source names a deliverable but no path (partial): AEA-07, AEA-54. Source present but the ticket's quoted wording not found: AEA-06 #2 (SCREEN_SPECS sentence), AEA-25 #2 ("given to the reviewer" phrase), AEA-50 ND-50a (retry count), AEA-50 ND-50b ("15-minute" and "S-232").
