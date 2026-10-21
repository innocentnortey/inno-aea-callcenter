# 7b decisions: data (DAT)

**Date:** 2026-10-21. **Tickets:** AEA-03, 04, 06, 07, 08, 09, 11, 16, 24, 25, 33, 50, 54, 55, 56.
**Inputs:** each ticket's `needs-decision` and contract-gap lines; the [evidence sweep](data-evidence.md) (quotes
re-checked in the sources; two of its "not found" notes were wrong, see *Contradictions*); the slice plan; DO-1…DO-7; the
PRD; Railway's docs read today. **Signatures:** [`docs/design/contracts/stage7/data.md`](../../design/contracts/stage7/data.md).

**Counts:** 28 items. Settled by a source: 8. Engineering: 16 (5 of them [A] defaults, each with its measurement). For
Innocent: 4 (below).

**One measurement made for this log [M].** Parked heading-aware chunker over the issued KB (61 chunks, 60 current),
`bge-small-en-v1.5` from the cached model in `var/fastembed/`, cosine top-1 scores: 12 in-corpus questions scored
**0.616–0.842**; 8 off-corpus questions scored **0.399–0.649**; US-7's own example ("How long have you been in
business?") scored **0.563**. Script: `/tmp/dat-measure/floor.py` (scratch, not committed). Used by DAT-11 and DAT-17.

---

## For Innocent

### DAT-1 · How much name and address masking is enough before text goes to Jev and Langfuse

**The story.** The system design promises that Jev (the planner, reached through OpenRouter) never sees a customer's
name or street address, and that traces in your Langfuse are masked the same way. AEA-04 builds the one redaction
function that keeps that promise. Card numbers, codes, phones, emails and IDs have fixed shapes, so patterns catch them
every time. Names don't: "my name is Omar Patel" is easy, but "Omar here, my AC died" or "my mother Jane is 88" has no
shape a pattern can rely on. The good news is that the main place a name and address arrive, the locate step, uses the
form payload, and that never reaches a model at all (api-con-mapping §0). What's left is a name typed loosely in chat.
Data is fictional, but a member of the public trying the demo could type a real one.

**Option A: introduction patterns, and write the limit down (recommended).** "My name is…", "this is…", "I'm…" plus a
street-address pattern (number, street name, suffix). DO-6 gets one line saying loose names in free chat may reach Jev
(under `data_collection: deny`) and your own Langfuse. No extra work; no new dependency.
**Option B: A, plus the located customer's own values.** Once a customer is located, their name and street address are
masked wherever they appear. Catches "Omar here" after locate; not third parties ("my mother Jane"). Half a day: it
changes the gateway's interface (AEA-20) as well as AEA-04.
**Option C: a named-entity model (Presidio or spaCy).** Catches most names. Adds a 50–500 MB model to an image on a disk
that is 87% full, adds latency to every turn, and still misses some.
*Recommended: A,* because the form channel already keeps the reviewer's locate details away from every model, and B or
C can be added later without changing anyone's tests except AEA-04's and AEA-20's.

**Decision needed:** Is pattern-based name and address masking with the limit written down (A) acceptable, or should we
add the located customer's values (B) or a name-recognition model (C)?

### DAT-2 · Where the sealed held-out answer key lives until it is scored

**The story.** The README number comes only from the held-out split, and the evaluation plan says build agents must
never see its answer key: "the key sits in a directory their prompts and permissions exclude, and its SHA-256 is
recorded here at sealing" (evaluation-plan.md *Who may read what*). Today nothing excludes anything. The repo is public
(R-42), every build agent works inside it, and a `grep -r` over `eval/` from any agent's shell would print the key, even
with a Read deny rule. Someone also has to write the key, and that writer has necessarily read it. If a build agent
reads the key and a fix follows, the split stops being held-out and the README number is no longer honest.

**Option A: key in `eval/cases/heldout/`, plus a deny rule.** You add a deny rule for that folder to the project's Claude
settings; the AEA-06 agent writes and seals it and takes no later build ticket; its hash goes into DO-5. Simple, but
shell commands bypass the deny rule.
**Option B: key outside the repo until scoring, then committed (recommended).** The scripts (customer turns) stay in
`eval/cases/heldout/`; the answer keys go to a folder outside the workspace (for example
`/home/linuxuser/.meridian-sealed/heldout/`) with a deny rule on that path; the hash goes into DO-5 at sealing; after the
E-4 run the keys are copied into the repo, so reviewers can audit them and the hash proves nothing changed. Same writer
rule as A. About 20 minutes more than A; needs a backup copy of the folder.
**Option C: you write or seal the held-out keys yourself.** Strongest separation; costs you roughly an hour of labelling.
*Recommended: B,* because it is the only option where an accidental search by a build agent finds nothing, and it still
ends with the keys public.

**Decision needed:** Where should the held-out answer key live until it is scored: in the repo with a deny rule (A),
outside the repo until scoring (B), or written by you (C)?

### DAT-3 · Whether the README holds the demo password

**The story.** You decided (R-48) that one demo login gates the whole app and that it is "given to the reviewer in the
README", to keep things easy for the reviewer. You also decided (R-42) that the repo is public. Together, anyone who
finds the repo can sign in, chat, press reset in the middle of a reviewer's session and spend model budget. The $30/day
cap still stops spending, but once it trips, new chats hand off for the rest of the day, which is what a reviewer would
then see.

**Option A: the README holds the username and password, as R-48 says.** Easiest for the reviewer; the login guards
nothing from the public.
**Option B: the README says where the login is given (the submission form or notes), and the values go only there
(recommended).** One extra step for the reviewer; the public can't sign in. You check whether the portal's submission
form has a notes field.
**Option C: A now, and change the password after grading.** Same exposure during the grading window, which is when it
matters.
*Recommended: B,* falling back to A if the portal has nowhere private to put it.

**Decision needed:** Should the README hold the demo login values (A), point to the submission form where they are given
(B), or hold them until grading ends (C)?

### DAT-4 · Opening the trace route, and on which hostname

**The story.** SDQ-3 decided the method: a TLS reverse proxy on a VPS hostname that exposes only Langfuse's ingestion
path, with the UI kept on localhost. Turning it on is your yes (Q-062). AEA-09 found ports 80 and 443 on the VPS already
held by a process it couldn't name, so the proxy has to go through whatever owns them, and the hostname has to be a name
under a domain you control. If you say no, the deployed app runs with trace export off, the monitoring page says so,
and VPS eval runs still trace locally.

**Option A: yes, on a subdomain you name (recommended).** You run `sudo ss -ltnp 'sport = :443'`, create the DNS record;
Claude posts the path-restricted proxy configuration for that server, citing Langfuse v4's documentation.
**Option B: no route.** Nothing is exposed; deployed turns have no traces (M-29 reads `off`). Because every turn then
records `trace_export = off`, the deployed monitoring page shows the `trace_export_failed` alert firing for as long as
the app runs (DO-6 :237; cases.md §8). *Changed at merge 2026-10-21: MC-24 added this consequence; not a new decision.*
*Recommended: A,* because a reviewer's live session is then traceable, which answers the brief's "would the business
know if it broke".

**Decision needed:** Do you open the ingestion-only Langfuse route (A, and which hostname), or keep it closed (B)?

---

## All items

Labels: **Source** settled by a document · **Eng** [Decided §7, engineering] · **Eng [A]** engineering default, replaced
by the measurement named · **Innocent** above.

| ID | Question | Raised by | Resolution | Basis | Text the ticket carries |
|---|---|---|---|---|---|
| DAT-1 | How names and street addresses are found in free text | AEA-04 ND-1 | **Innocent** (rec. A: introduction patterns + street-address pattern; limit recorded in DO-6) | DO-1 §3.2 (Jev sees names replaced); api-con-mapping §0 (form never reaches a model) | AEA-04 ND-1: "`needs-decision` → DAT-1 (Innocent). Build introduction and street-address patterns now (they are in every option); AC-2's name cases use introductions only until DAT-1 is answered." |
| DAT-2 | How the held-out key is kept from build agents | AEA-06 ND-1; AEA-24 item 7 | **Innocent** (rec. B: keys outside the repo until E-4, deny rule, isolated writer, hash in DO-5) | evaluation-plan.md:121; R-42 | AEA-06 ND-1: "→ DAT-2 (Innocent). Write scripts and keys as separate files (`<id>.case.json`, `<id>.key.json`, contract §5) so any option works; no held-out key file is written until DAT-2 is answered." AEA-24: "`--heldout-key-dir PATH` selects where keys are read (contract §6)." |
| DAT-3 | README holds the login, or says where it is given | AEA-25 (both lines) | **Innocent** (rec. B) | PRD R-48 vs R-42; slice plan §5 Q-4 | AEA-25: "Login location → DAT-3 (Innocent). Until answered the README says 'the demo login is provided with the submission' and holds no value (AC-4)." |
| DAT-4 | Which VPS hostname carries the Langfuse route | AEA-09 step 5 | **Innocent** (rec. A); method already SDQ-3 | system-design.md SDQ-3, §10; slice plan §5 Q-3 | AEA-09 step 5: "Hostname and yes/no → DAT-4 (Innocent)." |
| DAT-5 | Does SONNET mask contact details | AEA-04 ND-2 | **Source:** yes. SONNET masks cards, codes, emails, street addresses, and phones to `[phone ending NN]`; keeps names, customer and invoice IDs, account facts | system-design.md §3.2 Anthropic row ("full phone, email and street address (masked hints only)") and §10 *What each vendor sees*; DO-4 §5's comment is the incomplete one | AEA-04 table row SONNET: "Replaces: card-like numbers, codes, emails, street addresses; phones to their last two digits. Leaves: names, `MHC-`/`INV-` IDs, account facts. Source: system design §3.2, §10 (DAT-5)." Add AC: `::test_sonnet_masks_contact_keeps_ids`. AC-10's DO-6 line records it. |
| DAT-6 | Which wording `must_say` uses where a worked pair and SCREEN_SPECS differ | AEA-06 ND-2; AEA-03 (two cross-refs) | **Source:** SCREEN_SPECS wording, i.e. exactly what `policy/texts.py` sends | api-con-mapping.md:83 UXR-18 "Settled: UX owns customer copy"; api-con-mapping §0 *Fixed texts*; DO-5 *Expected-answer authority* (promise row: "exact strings"); SCREEN_SPECS.md:28, :144–145, :153 | AEA-06 ND-2: "Settled (DAT-6): `must_say` items quote SCREEN_SPECS copy notes word for word, source `SCREEN_SPECS SCR-n`; the worked pair stays the source of *what* is said." AEA-03 lines 32 and 104: "…the eval uses the same SCREEN_SPECS wording (DAT-6)." |
| DAT-7 | Path of the technical documentation | AEA-07 | **Source:** `docs/technical-documentation.md` | slice plan §5 Q-1 | AEA-07 **File:** "`docs/technical-documentation.md` (slice plan §5 Q-1)." |
| DAT-8 | Path of the deployment guide | AEA-54 | **Source:** `docs/deployment-guide.md` | slice plan §5 Q-1 | AEA-54 **File:** "`docs/deployment-guide.md` (slice plan §5 Q-1)." |
| DAT-9 | Exact env variable names | AEA-09 step 6 | **Eng, cross-topic:** `config.py` `Settings` (AEA-02) fixes them; AEA-09 copies them. Recommended names in contract §9 item 1 | slice plan §1 row AEA-02 and §2 ("Settings moved into 02"); AEA-19 already uses `LANGFUSE_PUBLIC_KEY`/`_SECRET_KEY`/`_BASE_URL` | AEA-09 step 6: "Names: as AEA-02's `Settings` declares them (expected: contract stage7/data.md §9 item 1). Step 6 waits for AEA-02's merge, not AEA-01's." *Changed at merge 2026-10-21: MC-21: the list adds `LANGFUSE_PROJECT_ID` after `LANGFUSE_BASE_URL`; `config.py` owner confirmed AEA-02. Web's four `MERIDIAN_*` deploy values are listed in contract §7 (DAT-29).* |
| DAT-10 | Where `temp_sqlite()` lives | AEA-11 cross-ref | **Source:** `tests/fixtures/sqlite.py`, owned by AEA-10 | slice plan §3 row `tests/fakes/…` | AEA-11 line 43: "`temp_sqlite()` is AEA-10's, in `tests/fixtures/sqlite.py` (slice plan §3)." |
| DAT-11 | Chunking method | AEA-16 ND-1 | **Eng [A]:** heading-aware split (heading path = `section`; sections over 1,100 characters cut at paragraphs into ~900; no overlap); CSV one row per chunk; PDF and TXT by paragraph groups; PNG via its transcription. Constants in `retrieval/settings.py` | Rule `source-authority` 2 ("Chunking comes from what is actually in the knowledge base … not from a default"). Data: every KB file is ≤ 2.1 KB with 1–8 headings, so a ~500-token split would make most files one chunk and lose section citations (R-11). [M] 61 chunks from this method; the 12 in-corpus questions scored 0.616–0.842 top-1. Replaced by E-2 hit @3 | AEA-16 ND-1: "Settled (DAT-11): heading-aware split per `retrieval/settings.py` (contract §3); values [A] until the first E-2 run. AEA-07 documents it." Owns: add `retrieval/settings.py`. |
| DAT-12 | Where the WF-14 `ingest_run` record lives | AEA-16 ND-2; AEA-50 ND-50d | **Eng:** `ingest_run.json` beside the index in the image; no DB row | The image build cannot write the volume (DO-1 §9); no reader of a row exists (CON-19/CON-20 carry no ingest field); DO-6 *Storage* lists eval and deploy records in SQLite, not ingest runs; one index per image, so the file is tied to its deployment | AEA-16 ND-2 and AEA-50 ND-50d: "Settled (DAT-12): `ingest_run.json` in the index directory (contract §3); CAP-9 reads it from the image." |
| DAT-13 | How `internal/agent_discretion_notes.md` reaches staff | AEA-16 ND-3 | **Eng:** AEA-16 writes `staff_notes.json` (passages with ID, version, hash), never embedded; `load_staff_guidance()` reads it. When it is attached to a case is the cases topic's | DO-4 §7 (heading 3/7, `source.kind = "lookup_log"`); system-design §10 *Staff-only text*; code-design §7 R-10 row | AEA-16 ND-3: "Settled (DAT-13): `staff_notes.json` + `load_staff_guidance` (contract §3); attaching it to a brief is AEA-29's (contract §9 item 4). AC-2 unchanged: the file is in no customer index." *Changed at merge 2026-10-21: MC-26: `StaffGuidance` lives in `retrieval/manifest.py` (no numpy or fastembed import); `load_staff_guidance` stays in `retrieval/ingest.py`.* |
| DAT-14 | How eval results reach the tables CON-20 reads on Railway | AEA-24 ND-1 | **Eng:** the harness writes `eval/reports/<run_id>.json` (contract §6, with a precomputed OpenAPI `EvalRun` summary); the report is committed and baked into the image; an idempotent start-up loader (cases topic) upserts it into `95_ops`. SCR-11 updates on the next deploy | DO-6 *Storage* (eval runs in SQLite; reports in the public repo); DO-2 §A.5 ("`eval/` output written by the harness"); AEA-24 AC-12 (HTTP-only, no app import); no OpenAPI operation accepts results, and adding one is a contract change | AEA-24 ND-1: "Settled (DAT-14): write `eval/reports/<run_id>.json` per contract §6; the loader is the cases topic's (contract §9 item 3)." AEA-50: "Image copies `eval/reports/`." |
| DAT-15 | Header names for the eval key, `run_id`, eval/load | AEA-24 ND-2 | **Eng, cross-topic:** web (AEA-23 middleware) names them; suggestion `X-Meridian-Eval-Key`, `X-Meridian-Run-Id`, `X-Meridian-Run-Tag` | DO-6 *Correlation*; topic ownership (middleware is web's) | AEA-24 ND-2: "Use AEA-23's header names (WEB decision); AC-1's stub asserts them." *Settled at merge 2026-10-21: web WEB-7 adopted the suggested names (web.md §4); contract §6 now names them.* |
| DAT-16 | The judge's own spend cap | AEA-24 ND-3 | **Eng [A]:** `HarnessLedger` cap $5 per Chicago day for judge calls, plus a preflight that reads CON-19 `spend.today_cents` and refuses a paid run when today + estimate + judge cap would pass the $30 cap | DO-5 *Scoring* ("stops at its cap") and *Spend for repeats* (~$4 per full eval [C]); $30/day decided (Q-061) and shared by eval traffic; this partitions the decided cap and spends nothing new. Replaced by the first E-1 run's measured judge spend | AEA-24 ND-3: "Settled (DAT-16): judge ledger cap $5/day [A] and the CON-19 preflight (contract §6); AC-13 tests both." |
| DAT-17 | `k` and the relevance floor | AEA-33 ND-1 | **Eng [A]:** `SEARCH_K = 3`, `MIN_SCORE = 0.60` (cosine). AEA-06 adds about 5 labelled synthetic off-corpus retrieval queries (`expect_below_floor`) so E-2 can tune the floor | [M] above: 0.60 keeps all 12 in-corpus questions (lowest 0.616) and refuses US-7's example (0.563) and 5 of 8 off-corpus questions; the two ranges overlap, so the floor alone can't refuse every off-corpus question and R-13's "answer only from passages" plus the R-46 fact check still carry that. k = 3 matches E-2 @3 and fits 3 × 1,100 characters in the 4,000-character tool output. Retrieval rule 4 and its review checklist. Replaced by the first E-2 run | AEA-33 ND-1: "Settled (DAT-17): k = 3, floor 0.60 [A] from `retrieval/settings.py`; the first E-2 run sets the floor (hit @3 with no floor, plus off-corpus below-floor rate)." AEA-06 step 4: "plus about 5 off-corpus queries with `expect_below_floor: true`, labelled synthetic." |
| DAT-18 | Is the duct-cleaning stub indexed | AEA-33 ND-2 | **Source:** never indexed. "Do you do duct cleaning?" is answered from `services/service_catalog.md` ("not offered") | PRD R-10 ("Stub, not answered from"), PRD §4.3a row *What Meridian does, and doesn't*; AEA-16 AC-2 (stub never indexed). The file reads only "TODO — Marcy to write up partner referral process." | AEA-33 ND-2: "Settled (DAT-18): not indexed (R-10; AEA-16 AC-2)." |
| DAT-19 | Railway restart retry count | AEA-50 ND-50a | **Eng [A]:** `ON_FAILURE`, `restartPolicyMaxRetries: 10` | docs.railway.com/deployments/restart-policy, read 2026-10-21: "The default is `On Failure` with a maximum of 10 restarts"; paid plans may set any number. Revisit with M-28 | AEA-50 ND-50a: "Settled (DAT-19): ON_FAILURE, 10 retries [A] (Railway default, docs read 2026-10-21); AC-11 checks both values." AEA-54 documents it. |
| DAT-20 | Is S-232 enough for a 65 s turn | AEA-50 ND-50b | **Eng [A]:** accept S-232 (15-minute platform limit); add no slow endpoint. Replaced if AEA-56's smoke or the Stage 9 load run logs any proxy 502/504 on a turn under 900 s | source-register.md S-232 (Railway staff answers, COMMUNITY); code-design §2.3 rule 7 keeps [A] with S-232 cited; a deliberately slow route is attack surface | AEA-50 ND-50b: "Settled (DAT-20): accept S-232 [A]; no live 65 s hold; AC-12 as written." |
| DAT-21 | Which issue adds the `apps/web` build stage | AEA-50 ND-50c | **Source:** AEA-50. The stage runs only when `apps/web/package.json` exists | slice plan §1 row AEA-50 ("a stage that runs `apps/web`'s own build when present, reading only") | AEA-50 ND-50c: "Settled (DAT-21): this issue, conditional stage (contract §7)." |
| DAT-22 | Which module computes `agent_version`, from what | AEA-50 ND-50e | **Eng:** `scripts/agent_version.py` (AEA-50) at container start: SHA from `RAILWAY_GIT_COMMIT_SHA`, else the `BUILD_SHA` file the deploy step writes, plus a hash of the role → model map and the prompt and text source files; exported as `MERIDIAN_AGENT_VERSION`, read via `Settings` | DO-6 *Correlation* (SHA + model config + prompt versions); Railway variables reference (read 2026-10-21: `RAILWAY_GIT_COMMIT_SHA` = "the commit that triggered the deployment", so it is empty for `railway up`, AEA-09 step 2); `.git/` is excluded from the build context (AEA-50 AC-3) | AEA-50 ND-50e: "Settled (DAT-22): `scripts/agent_version.py` + start command (contract §7); needs `Settings.agent_version` (contract §9 item 1b)." AEA-54/56: "Before `railway up`: `git rev-parse HEAD > BUILD_SHA`." |
| DAT-23 | Confirm AEA-19 and AEA-23 as AEA-50 blockers | AEA-50 gap note | **Source:** already in the slice plan row | slice plan §1 row AEA-50 lists "16, 31, 32, 33, 19, 23" | AEA-50 *Blocked by*: drop "orchestrator to confirm"; cite the slice-plan row. |
| DAT-24 | UI verify again with fake or live models | AEA-55 ND-55a | **Eng:** the automated suite (AC-3, AC-4, AC-7…AC-9) runs on the scripted fakes; Innocent's walkthrough (AC-10) runs on live Sonnet and Jev, marked `live`, under the $30 cap (about 20 turns ≈ $0.30 at SP-1's $0.016 per conversation [C]) | Conventions: no paid model in a default test; the walkthrough asks free questions fakes can't answer; spend within the decided cap | AEA-55 ND-55a: "Settled (DAT-24): fakes for the suite; live models for the AC-10 walkthrough only (`live`, `gate::paid`)." |
| DAT-25 | Where the second UX-5 report goes | AEA-55 ND-55b | **Eng:** `docs/testing/ui-verify-again.md`, linked from checklist §8 | Tickets may not edit `docs/ux/**`; DO-5 already uses `docs/testing/` | AEA-55 ND-55b: "Settled (DAT-25): `docs/testing/ui-verify-again.md`." |
| DAT-26 | E-2 needs a `RetrievalIndex`, but the harness imports no app code | AEA-24 suite 4 vs AC-12 (found here) | **Eng:** `eval/run_retrieval.py` (outside `eval/harness/`) builds `FastembedIndex` and passes it to `run_retrieval_suite`, which takes a structural `SearchesPassages` | AEA-24 AC-12, suite 4; DO-4 §13 | AEA-24 suite 4: "Entry `python -m eval.run_retrieval --index-dir PATH` (contract §6); AC-12's scan covers `eval/harness/` only." |
| DAT-27 | One case-file format both AEA-06 and AEA-24 build against | AEA-06 ("written down once"); AEA-24 *Blocked by* | **Eng:** contract §5 (JSON, script and key in separate files, `case.schema.json`) | DO-5 *What every case file records*; AEA-06 *Every case file records* | AEA-06 and AEA-24: "Case format: contract stage7/data.md §5." AEA-24 drops "if AEA-06's format differs … `blocked-on AEA-06`". |
| DAT-28 | Placeholder tokens and the SONNET/TRACE phone hint | AEA-04 ("exact form is the planner's") | **Eng:** the per-kind tokens in contract §1 | Several tickets assert on them (AEA-35 AC-9, AEA-51 CAP-1); workspace rule `context-management-multi-turn` 5 | AEA-04: "Placeholders: contract stage7/data.md §1." |
| DAT-29 | Cross-topic requests to data not covered by a merge-clash row (added at merge 2026-10-21) | staff.md cross-topic DAT; graph-nodes.md cross-topic 5; web.md cross-topic DAT (AEA-50/54/56); graph-tools.md C-6 | **Eng:** (a) `policy/texts.py` `live` group carries the four OpenAPI representative event lines, OpenAPI `{name}` = placeholder `rep_name`; (b) `booking.urgent_note` text for the urgent burning-ruled-out booking; (c) Railway variables add `MERIDIAN_COOKIE_SECURE`, `MERIDIAN_TRUST_PROXY_HEADERS`, `MERIDIAN_REQUIRE_FRONTEND` (all `true`) and `MERIDIAN_WEB_DIST_DIR=/app/apps/web/dist`; (d) AEA-33 exposes `knowledge_tools(retrieval)` instead of a self-registering `KB_SEARCH`; (e) AEA-55 checks the `wrong_role` → re-read `getSession` behaviour against the real API; (f) *added at final xref 2026-10-21:* the `identity` group carries graph-tools C-5's two CON-6 inbox bodies, `INBOX_CODE_BODY` / `INBOX_CODE_GONE`, placeholder `digits` | OpenAPI `EvRepresentativeJoined`/`EvAiPaused`/`EvAiResumed`/`EvChatClosed`; graph-nodes §6; web WEB-30, WEB-32; graph-tools GRT-1; staff STF-19 | AEA-03: "Adds the `live` event lines (OpenAPI `Ev*` examples, `rep_name`), `booking.urgent_note` and the two `identity.inbox_code_*` bodies (contract §2, DAT-29)." AEA-54/56: "Railway variables per contract §7 (DAT-29)." AEA-33: "Expose `knowledge_tools(retrieval)` per contract §4; no `register_` hunk (GRT-1, DAT-29)." AEA-55: "Check `wrong_role` → re-read `getSession` on the real API (STF-19, DAT-29)." |
| DAT-30 | `SearchesPassages.search` returned `Any` (signature-check pass, 2026-10-21) | `signature_check.py`: "a bare Any says nothing a test can check" | Read-only structural Protocols `PassageLike` (`file`, `section`, `version_label`, `score`) and `SearchResultLike` (`passages`, `below_floor`) in `eval/harness/retrieval.py`; `search` returns `SearchResultLike`. `FastembedIndex` and `RetrievalResult` satisfy them without the harness importing app code. Contract §6. | Engineering. AEA-24 AC-12 (harness imports nothing from `src/meridian/`); DO-4 §13 `RetrievalResult` / `Passage` fields; DAT-26. | AEA-24: "`SearchesPassages.search -> SearchResultLike` (DAT-30); the type check proves `FastembedIndex` satisfies it." |
| DAT-31 | Where WF-10's "client-side turn timings" record is stored (signature-check pass) | `signature_check.py`: "client_side_turn_timings (required by WF-10): no table or file named"; DO-6 WF-10 | One JSON line per CON-2 call in `eval/reports/<run_id>.client_side_turn_timings.jsonl` (`ClientTurnTiming`: ids, conversation and turn index, `sent_at` UTC, `first_byte_ms`, `total_ms`, `http_status`, `outcome`, `notice_code`), committed beside the run's report; the report summary computes p50/p95/max. Joins the server `turn` rows on `turn_id`. Contract §6. | Engineering. DO-6 WF-10 *Required records*; reports are public and committed (§6); M-23…M-25. | AEA-24: "The `load` suite writes `<run_id>.client_side_turn_timings.jsonl` rows as data.md §6 (DAT-31)." |
| DAT-32 | `FixedClock` (DO-3 §4.2 `Clock` test implementation) had no signed class (signature-check pass) | `signature_check.py`: "adapter FixedClock: no class or Protocol in DO-4" | `tests/fakes/clock.py`: `FixedClock(at=WORKED_PAIRS_NOW)` implements `Clock`; `now()` constant; `advanced(by) -> FixedClock` returns a new clock; a naive or non-Chicago `at` is a `ValueError`. Contract §8a. | **Source** for the default: worked-pairs header "Friday 2026-10-16, 10:00" (AEA-11 AC-6; cases.md `DEMO_START`). Engineering for `advanced` (AEA-29 AC-9 builds clocks before and after a due time). | AEA-11: "`FixedClock` exactly as data.md §8a (DAT-32)." |

---

## Contradictions found between sources

1. **DO-4 §5 vs DO-1 §3.2/§10** on what Anthropic sees: DO-4's comment masks cards and codes only; DO-1 says full
   phone, email and street address never cross. DO-1 wins (DAT-5); DO-4's comment needs one line (AEA-08's kind of fix).
2. **PRD R-48 vs R-42:** the login is "given to the reviewer in the README", and the README is public (DAT-3).
3. **Worked pairs WP-4, WP-5, WP-6 vs SCREEN_SPECS** on three fixed sentences (DAT-6; UXR-18 settles it).
4. **Slice plan §5 Q-2 and AEA-01's ticket vs slice plan §1/§2** on who owns `config.py`: Q-2 and AEA-01 say AEA-01;
   §1 row AEA-02 and §2 say AEA-02. The orchestrator settles it; DAT-9 follows the owner. *Settled at merge
   2026-10-21 (MC-21): AEA-02.*
5. **AEA-50's gap note vs the slice plan:** the note says AEA-19 and AEA-23 are missing from the row; the row lists both
   (DAT-23).
6. **Evidence sweep errors (not source conflicts):** the DO-5 phrase "sits in a directory their prompts and permissions
   exclude" exists (evaluation-plan.md:121), and the SCREEN_SPECS fee sentence exists (SCREEN_SPECS.md:28, :153).
7. **Retrieval observation for E-2 (not a contradiction):** in the [M] run, "Do you service Manor?" ranked
   `faq/customer_faq.md` first, not `policies/service_area.md`. Flagged for the first E-2 run, not changed here.

---

## Merge changes (2026-10-21)

Applied to [`stage7/data.md`](../../design/contracts/stage7/data.md) from [merge-clashes.md](merge-clashes.md). No
earlier row was deleted; affected rows carry a dated note.

| MC | What changed in the contract |
|---|---|
| MC-19 | §7: `scripts/reset.py` calls `reset(<wall now>, request_id=<new UUID4>, session_id=None, role=None)` with its own `ResetGate`; stopped service only; live path CON-9. Signature owner: cases.md §7. |
| MC-20 | §6 `EvalRunRecord` times are UTC; §7 script's `now` is `datetime.now(UTC)`. |
| MC-21 | §9 item 1 adds `LANGFUSE_PROJECT_ID`; `config.py` is AEA-02's (DAT-9, contradiction 4). |
| MC-23 | §1 adds `Redactor = Callable[[str, RedactionProfile], Redacted]` and the container binding for staff's `redact_store`. |
| MC-24 | DAT-4 option B states the `trace_export_failed` alert consequence. |
| MC-26 | §3: `StaffGuidance` in `retrieval/manifest.py` (DAT-13). |
| MC-28 | §9 item 8: AEA-11 fakes build `ProviderCall`, `InMemoryTraceSink` yields `SpanHandle`. |

Cross-topic items 2–5 in contract §9 are now marked settled by the owners' decisions (WEB-7, CAS-27, CAS-33, GRT-1);
the remaining additions are DAT-29.

## Residual pass (2026-10-21)

Closed in [`residuals-web.md`](residuals-web.md): `render` gains the `amount` placeholder and `policy/texts.py` the one
money formatter `format_usd(cents)` (R-W-7, answering AEA-03's needs-decision); `TextId.PERSON_REQUEST_LABEL` ("Talk to
a person") for the reloaded CON-4 row (R-W-6). Header names for the eval key and run id re-checked: unchanged (R-W-20).
