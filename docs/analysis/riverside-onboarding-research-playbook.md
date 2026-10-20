# Riverside Onboarding Research Playbook

**Reconstructed from the AEA onboarding research · written 2026-10-15 · writer: Claude Code (Sonnet 5.5)**

**Status of this file:** a playbook only. **No Riverside research, scaffold, theme choice, dashboard or approval has happened.** The AEA project (`inno-aea-onboarding`) is untouched and remains the historical evidence. The AEA assignment is changing; those changes are not yet known and are not reflected here (see §0.6).

**What this file is for.** A fresh Claude session, with no memory of the conversation that produced this, can pick it up, find the first unticked box in §0.4, and run the next stage using the "ready-to-use instruction" inside that stage.

---

## 0. How to use this file

### 0.1 Reading order for a fresh session

1. This file, §0 (rules, labels, paths, progress), then the stage you are on in Part 3.
2. The Riverside project's own `CLAUDE.md`, `.claude/README.md` and `RESEARCH-PROGRESS.md` once Stage 2 has created them.
3. Parts 4 and 5 when a stage tells you to. Part 1 is background, not instructions.

### 0.2 Evidence labels used in this playbook

Every claim about the AEA process carries one of these. They are the main thing to keep straight.

| Label | Meaning |
|---|---|
| **[D] Documented** | An artifact or run log says this happened. The source is cited. |
| **[I] Inferred** | I deduced it from file contents, cross-references or file timestamps. Nothing states it. Treat as likely, not certain. |
| **[V] Verified now** | I re-checked it read-only on 2026-10-15 while writing this (re-ran a script, recomputed a number, opened a raw file). |
| **[U] Unavailable** | The raw evidence, prompt or script is not in the repo. I did not reconstruct it. |
| **[R] Recommended** | An improvement for the next run. It did **not** happen in AEA. |

Where a sentence has no label inside Part 1, it is [D] and the citation next to it is the source.

### 0.3 Configurable paths and values

Nothing below is chosen yet. Fill the right-hand column at Stage 1 or 2, and copy it into the Riverside project's `RESEARCH-PROGRESS.md`.

| Placeholder | Meaning | Value |
|---|---|---|
| `{WS}` | Command-center folder | `/Users/innocentnortey/Desktop/Nortorious-Technologies` |
| `{AEA}` | Historical evidence project (read-only for this work) | `{WS}/inno-aea-onboarding` |
| `{GAUNTLET}` | Gauntlet AI workspace (briefs, open questions, dev logs) | `{WS}/Gauntlet AI` |
| `{PLAYBOOK}` | This file | `{AEA}/docs/analysis/riverside-onboarding-research-playbook.md` |
| `{PROJECT}` | The new Riverside research project | **not chosen** (convention suggests `{WS}/inno-riverside-onboarding/`; Innocent decides at Stage 2) |
| `{PARTNER}` | Partner to research | The Riverside Company (legal: Riverside Partners L.L.C.) — **confirm at Stage 1** |
| `{THEME}` | The onboarding theme chosen at Stage 4 | **not chosen** |
| `{DEVLOG}` | Run-log folder | `{GAUNTLET}/devlogs/<project-folder-name>/` (the AEA convention; create at Stage 2) |
| `{DATE}` | Today's date, America/Chicago | set per session |

### 0.4 Progress and resumption

**Resume protocol.** (1) Open `RESEARCH-PROGRESS.md` in `{PROJECT}` (before Stage 2 exists, use the Stage 1 record below). (2) The first stage with an unticked box is where the work is. (3) Re-read that stage's "Inputs" and confirm each exists before acting. (4) Do the stage. (5) Tick boxes only with evidence at the stated output path. (6) A ★ decision box is ticked only with `Innocent ✓ YYYY-MM-DD` — never on Claude's say-so. (7) Write one dev-log entry per coherent wave (contract: `{AEA}/.claude/reference/dev-log.md`).

**Copy this block into `{PROJECT}/RESEARCH-PROGRESS.md` at Stage 2.** Until then, tick it here.

| # | Stage | Started | Outputs written | Completion checks passed | Decision recorded |
|---|---|---|---|---|---|
| 1 | Confirm partner, brief, requirements, objectives, unknowns | [ ] | [ ] | [ ] | [ ] D-1 ★ |
| 2 | Scaffold the research project | [ ] | [ ] | [ ] | [ ] D-2 ★ |
| 3 | Inventory the portfolio, screen, group by workflow | [ ] | [ ] | [ ] | [ ] D-3 |
| 4 | Compare themes; recommend | [ ] | [ ] | [ ] | [ ] D-4 ★ |
| 5 | Select cohort, roles, sampling; adapt the template | [ ] | [ ] | [ ] | [ ] D-5 ★ |
| 6 | Company sites, published steps, documents, tools | [ ] | [ ] | [ ] | — |
| 7 | Customer-review evidence | [ ] | [ ] | [ ] | [ ] D-7 (sources and sample sizes, before collecting) |
| 8 | Reference journeys and guidance | [ ] | [ ] | [ ] | — |
| 9 | Synthesis: comparison, friction, core, variations, hypotheses, scenarios | [ ] | [ ] | [ ] | [ ] D-9 ★ (scope boundaries) |
| 10 | Brief audit and reconciliation | [ ] | [ ] | [ ] | — |
| 11 | Candidate inventory, baseline, parked, rank, shortlist | [ ] | [ ] | [ ] | [ ] D-11 ★ (rubric approval before scoring) |
| 12 | Audit evidence chains and consistency | [ ] | [ ] | [ ] | — |
| 13 | Generate and verify the dashboard | [ ] | [ ] | [ ] | — |
| 14 | Record Innocent's choices; hand off | [ ] | [ ] | [ ] | [ ] D-14 ★ (selections) · [ ] research-complete call (his alone) |

**Stage 1 record (the only state this file holds before the project exists).** Fill in at Stage 1.

| Field | Value |
|---|---|
| Partner display name on the portal | |
| Legal entity per first-party disclosure; URL; date read; passage | |
| Riverside brief path / SHA-256 / bytes / date received | observed 2026-10-15 during preparation, **to be confirmed at Stage 1**: `{GAUNTLET}/artifacts/2026-10-13-partner-briefs/riverside-onboarding-assistant.md` · `5a15efa2087dc00f390042aed3eaac8ceb4e368d83ad083fa3c00f2698946be7` · 13,916 bytes · LF line endings · file dated 2026-10-13 23:21 |
| AEA brief SHA-256 (matches the AEA source register) | `0de4e06ea72524b1725af63fdd48a3fb364712d16c21f79c9b1d8e49a0011331` · 14,344 bytes · CRLF |
| Newer Riverside brief on the portal? (Innocent to check) | |
| AEA assignment changes received? date / file | |
| Portfolio page URL(s) and entry count (structure only) | |
| `{PROJECT}` path and name chosen | |

### 0.5 Hard boundaries (apply to every stage)

These come from `{AEA}/.claude/rules/source-authority.md`, `{AEA}/.claude/rules/html-files-not-artifacts.md`, the root `{WS}/CLAUDE.md` and the root rule `{WS}/.claude/rules/new-project-zero-to-hero.md`. A fresh session must obey them without being reminded.

1. **Research phase only.** No PRD, application design, tickets or product code until Innocent says research is done. The dashboard is a decision aid, not evidence that anything was built.
2. **No commit, push, publish or outreach** unless Innocent asks. No company, partner or Gauntlet-staff contact.
3. **Issued briefs are never edited.** New versions get a new dated file and a new source-register row.
4. **Synthetic data only.** No real personal data in samples, scenarios or fixtures.
5. **HTML is a local file** (`docs/artifacts/…`). Never the Artifact tool, never a share link.
6. **Public sources only; view-only on forms.** Never submit a form, create an account, upload a file or message anyone. Never enter real data.
7. **No process is killed that Innocent did not name** (`~/.claude/rules/confirm-before-killing-processes.md`). In AEA the Chrome DevTools MCP was blocked by an open Chrome profile; it was left alone and another driver was used.
8. **Innocent's ★ decisions are his.** Claude presents options (a recommendation first, 2–4 concrete options) and waits.
9. **Model matching on the VPS.** If any stage is delegated to a session on the VPS, use the same model as this session (`~/.claude/rules/match-model-on-vps.md`).

### 0.6 Pending input and playbook maintenance

- **AEA assignment changes** — not yet supplied. When they arrive, add a dated entry to the table below and re-check Stage 1 (brief diff), Stage 10 (audit) and Part 2 (what transfers). Do not edit the AEA project's research conclusions.

| Date | Change received | Effect on this playbook |
|---|---|---|
| | | |

- **Version:** 1.0, 2026-10-15. Change this file by appending a dated line here; do not rewrite history.

---

# Part 1 · What we actually did in AEA

## 1.1 Method and limits of this reconstruction

I read the instruction files first (`{AEA}/AGENTS.md`, `CLAUDE.md`, `.claude/README.md`, `.claude/rules/source-authority.md`, `.claude/rules/hiring-partner-framing.md`, `.claude/rules/project-provenance.md`, `.claude/rules/synthetic-test-data.md`, `.claude/reference/dev-log.md`). I then read the checklist, README, SUBMISSION, source register, issued brief, portfolio inventory, fit review, AEA context, the research-template, the report and both annexes, the superseded checklist (banner and structure), the review report, the journey baseline, the pitfalls synthesis, the matrix, the dashboard source, the brief audit (structure and the T1–T12 rows), research questions, the company profiles (Commonwealth in full, others by structure), all 11 dev-log runs, the two upstream Gauntlet documents, and both partner briefs. I also read the raw review JSON for four listings, the page cache for the pages the three traces cite, and the two scripts in the repo.

**What I could not see [U]:**

- **Innocent's own prompts.** Every run log paraphrases what he asked. The original messages are not in the repo. The 40% / 20% instruction exists only as the Codex run's "proposed interpretation" (§1.4.9).
- **The Claude prompt Codex wrote for the matrix** (`review-synthesis-and-selection-handoff-codex-01.md` says it "prepared" it; the text is not saved).
- **The inventory script.** `docs/evidence/2026-10-14-aea-portfolio-inventory.json` is the output; whatever fetched 118 profiles is not saved.
- **The Google review extraction run.** The extractor exists, but in the user-scope skill, not the project (`~/.claude/skills/google-reviews/scripts/extract-reviews.js`; the skill's `SKILL.md` records the selectors and gotchas). The raw JSON outputs are in the project, git-ignored.
- **The quote-verification script and the dashboard-parity script.** Both are described in run logs ("a script compared every review quotation with the raw extracts"; "a script confirmed all 19 IDs, ranks, scores…"). Neither was saved.
- **The sub-agent's 14-page re-read on 2026-10-14**, and any browser screenshots or console output from the dashboard checks.
- **The AdaCare scheduler re-read (S-83).** The cached page text from the first pass shows an *empty frame* [V]. The later view-only re-read that showed New Patient Visit slots exists only as text in the source register and one run log. No screenshot or DOM text was cached.
- **A formal record of the niche decision.** The checklist has no decision row for "healthcare / patient intake". The fit review calls it a "research recommendation"; later files call it "chosen".

## 1.2 Reconstructed chronology

All times America/Chicago. "mtime" = file modification time on disk; it shows the *last edit*, so it can only support an inference.

| When | Step | Artifact(s) | Writer | Basis |
|---|---|---|---|---|
| 2026-10-13 | Briefs arrive through the Gauntlet portal. Companion research chooses AEA Project 1 over Project 2 and finds both onboarding briefs are *general* "sensitive-service onboarding" | `{GAUNTLET}/artifacts/2026-10-13-hiring-partner-project-choice-and-deadlines.md` §0–§2; `…-partner-projects-todo.md` | Claude | [D] |
| 2026-10-14 | **Portfolio screen.** 118 AEA portfolio profiles read; 56 current/active kept; nine workflow groups; representative flows researched; cohort proposed | companion doc §0.1; `docs/evidence/2026-10-14-aea-portfolio-inventory.json` | Claude | [D] |
| 2026-10-14 | **Project created.** Brief copied unchanged (SHA-256 recorded), inventory byte-copied, source register S-1…S-35, AEA context, five company profiles, fit review, RQ-1…28, checklist, SUBMISSION, principles pack. A sub-agent re-read 14 company pages | `…/2026-10-14-project-initialization-claude-01.md` | Claude (Opus 5.5) | [D] |
| 2026-10-14 | **Brief audit.** T1–T13 reviewed against primary sources; T14–T23 added; S-36…S-62; RQ-29…36. Then a **consistency pass** C1–C11 (+RQ-37), then verbatim-quote anchors added to every C and T row | `docs/analysis/2026-10-14-brief-audit.md`; two Codex run logs | Codex | [D] |
| 2026-10-15, morning | The research template `docs/aea-portfolio-research.md` is in place (mtime 11:21). **First pass**: a configuration checklist and review report for five companies, then reviews redone from Google's review dialogs (raw JSON mtimes 11:33–11:40; extractor 11:45; `themes.py` 12:13; `fetch.py` 12:04) | `…/2026-10-15-onboarding-research-claude-01.md` | Claude (Haiku 5.5) | [D] for the pass; times [I] |
| 2026-10-15 | **Rejected and corrected.** Innocent judged the first pass "a checklist of outstanding work, not the requested report"; several factual errors were found and confirmed. A **completion pass** then read ~100 first-party pages (S-64…S-107), rewrote all five profiles, wrote the 12-section report plus Annex 1 and Annex 2, added RQ-38…43, and made every review quotation exact | same log; `docs/analysis/2026-10-15-onboarding-research-report.md` | Claude (Opus 5.5) | [D] |
| 2026-10-15 | **Redirect.** Innocent moved the work away from "evaluating public contact forms as complete onboarding products". Codex wrote the **journey baseline** from professional guidance (S-108…S-121, RQ-44…46) | `…/patient-journey-baseline-codex-01.md`; `docs/analysis/…-patient-journeys-and-onboarding-baseline.md` | Codex | [D]; its position after the report [I] (it refers to "the existing research report") |
| 2026-10-15 | **Review interpretation + handoff.** Codex saved the **pitfalls synthesis** and prepared the prompt for the matrix | `…/review-synthesis-and-selection-handoff-codex-01.md`; `…-review-pitfalls-and-solution-opportunities.md` | Codex | [D] |
| 2026-10-15 | **Matrix written** by a separate Claude session: M-01…M-15, SOL-001…019, P-01…11, rubric, shortlist of 8, eight evidence cards | `…/solution-selection-claude-02.md`; `docs/analysis/…-solution-selection-and-evidence-matrix.md` | Claude (Opus 5.5) | [D] |
| 2026-10-15 | **Reconciliation.** A third Claude session found the matrix "written minutes earlier by another session", continued it without changing IDs/ranks/scores, rechecked the AdaCare scheduler, added review §7 (patient status), tool-job labels, section citations in place of 71 line citations, and an evidence-correction ripple through report, profiles, register, annexes, RQs | `…/research-reconciliation-claude-03.md` | Claude (Opus 5.5) | [D] |
| 2026-10-15 | **Dashboard** built from the reconciled artifacts and browser-checked (mtime 20:54, after the matrix's 18:32) | `…/selection-dashboard-claude-04.md`; `docs/artifacts/2026-10-15-solution-selection-dashboard.html` | Claude (Opus 5.5) | [D]; times [I] |
| 2026-10-15 | Riverside identity correction (GQ-19 closed) and the prompt that produced this playbook | `…/riverside-identity-codex-01.md`; `…/riverside-process-prompt-codex-02.md` | Codex | [D] |

**Order in one line:** brief and portfolio → profiles → audit (in parallel) → first pass → rejection → corrected deep pass → reference baseline → review interpretation → candidates and ranking → reconciliation → dashboard.

## 1.3 Differences from the five-step recollection

Your five steps are right as a skeleton. The artifacts show these additions and corrections:

1. **A source-and-provenance layer sat under everything.** The brief was copied unchanged with a SHA-256; every fact has an `S-N` in a register with an authority label and a read date; raw page text and raw reviews are cached locally and git-ignored. (`docs/source/source-register.md`)
2. **The brief audit ran in parallel and fed the candidate stage.** It produced T1–T23 (risks) and C1–C11 (the brief's internal contradictions) with verbatim quotes. The mandatory baseline M-01…M-15 in the matrix is built from the brief; the audit owns the risks attached to them.
3. **Portfolio screening came *before* the repo existed**, in the Gauntlet companion document, and the theme comparison was qualitative and written once (no scoring, no decision record).
4. **The first company-research pass failed and was redone.** The correction loop is a core part of the process, not an accident: the second pass is where facts, quotes and denominators were made exact.
5. **Customer reviews and reference journeys were not in the original research prompt.** The template (`docs/aea-portfolio-research.md`) says "use the referenced websites as the primary sources". Reviews were added at Innocent's request; the reference-journey step came from his redirect away from treating public forms as the whole onboarding.
6. **A reconciliation pass sat between synthesis and dashboard.** It changed labels, citations and caveats across about ten files without changing any ID, score or rank.
7. **Candidates came from several places, not only from reviews:** the report's gaps G1–G9 and its §12 recommendations, the journey baseline's candidate-baseline table, the review pitfalls table, and the brief's own stretch items. The matrix records no generation log [I].
8. **Mandatory, discretionary and parked are three different classes**, and the percentages apply only to the discretionary pool.
9. **Unresolved scope decisions were carried, not resolved.** RQ-44 (optional clinical-adjacent context) and RQ-45 (where intake ends; new versus established customers) were still open at the end, which left a parked idea (P-01, P-11) and several demo scenarios "not demo-ready".
10. **The dashboard was transcribed by hand into the HTML file.** There is no generator and no saved parity script (§5.2).

## 1.4 How each part of the process worked

### 1.4.1 Inventory, screening and grouping by workflow

- **[D] What was read.** All 118 profiles linked from AEA's public portfolio directory (S-6): name, group, status, description, company website. (`docs/analysis/portfolio-fit-review.md` §3; `docs/evidence/…inventory.json` → `method`.)
- **[D] The record.** Each company has `name, source_url, group, investment_date, status, industry, location, summary, company_website, screening_disposition`; the 56 eligible ones also have `screening_cluster`.
- **[D] The screening rule.** Eligible = status "Current" or "Active" under an AEA investment group. Excluded: realized investments; "AEA Elevate Team Prior Experience" listings; private-debt borrowers were not treated as reachable operating companies. "Current" is a *website label*: it does not establish control, procurement access or permission to deploy. (`company-research/aea-investors.md` §2.)
- **[V] The denominators reconcile.** 118 = 56 eligible (55 Current + 1 Active) + 55 realized + 7 team-prior-experience (3 Current + 4 realized). I recounted this from the JSON.
- **[D] Grouping.** Nine groups by *workflow*, not by AEA's industry labels: patient-facing clinic and dental platforms 4 · complex rehabilitation and mobility 1 · veterinary 1 · recruitment and staffing 3 · home/property/facilities 8 · logistics 4 · business technology and outsourced services 6 · consumer/retail/hospitality 7 · industrial 22.
- **[D] Depth.** The groups that looked plausible got representative service flows read on company websites (S-25…S-35: NES Fircroft, RED Global, Bespoke, 50 Floor, Window Nation, Mark Spain, BMS CAT, Montway, Magna5, AmeriVet). The 29 consumer and industrial listings were **not** investigated for internal workflows; the fit review says so and warns this is "not proof that no onboarding opportunity exists".
- **[U]** The tool that produced the inventory. **[R]** Save the script, the date and a page cache of the directory.

### 1.4.2 Comparing themes

- **[D] Criteria, in priority order** (`portfolio-fit-review.md` §4): (1) natural fit with all four required flows, where collecting name/DOB/address serves a real purpose; (2) connection to the brief's business problem (a person completes registration and reaches a next step); (3) reuse across current platforms and their locations; (4) a coherent three-day demonstrator that includes the edge cases; (5) evidence quality (first-party published steps; missing evidence stays unknown).
- **[D] Method.** One table of groups with "evidence and fit" and a one-line judgment. **No numeric scores.** The rankings are described as "reasoned product-fit judgments", not measured ROI or demand.
- **[D] Result.** Patient-facing care platforms = the only group where the complete combination fits (document-heavy personal intake, a real appointment as next step, anxious users). Staffing = strongest alternative; its paperwork peaks *after* placement.
- **[D] Limitations recorded:** directory may be stale; no proprietary data; published pages are not practice; variation inside platforms under-sampled; rankings by one reviewer in one day.
- **[I] What was missing:** a formal decision record and a "what would change this recommendation" line. **[R]** Add both (Stage 4).

### 1.4.3 Choosing the cohort and each company's role

- **[D]** Four directly relevant platforms plus one adjacent: Commonwealth Pain & Spine (**anchor**), American Dental Companies (**second configuration**), Metro Vein Centers (**reuse and benchmarking**), American Oncology Network (**fourth core platform**), Numotion (**adjacent**). Roles are in `portfolio-fit-review.md` §7. After the full five-platform comparison the roles were re-affirmed (report §1 "Anchor reassessment"): Commonwealth has the richest published intake requirements, an explicit measurable access promise, 33 offices behind one form and one fax line; Metro Vein is the light-front-door benchmark; FOH is the long-packet example that "should not lead a demo".
- **[D] Counting rule:** platforms are counted, not practices. A practice or branch is a possible reuse site, not an extra investment.
- **[D] Practice examples:** AdaCare (Meridian, ID) for ADC because it is listed on ADC's partner page; Florida Oncology & Hematology (FOH) for AON because AON's own practice page links it. Commonwealth got two offices for reviews (Louisville South and Elizabethtown).
- **[I] No written rule says *why* those practices were chosen** beyond first-party linkage and visible intake evidence. **[R]** Record the practice-selection rule (Stage 5).

### 1.4.4 Collecting company information, existing tools and documents

- **[D] Frame.** The research template `docs/aea-portfolio-research.md` has Parts 1–10 and a required 12-section report order. Its research standards: websites as primary sources, cite URLs, date every assessment, never fabricate volumes/conversion/availability/integrations, never submit appointments or forms.
- **[D] Sources.** About 100 first-party pages and documents, registered S-64…S-106 (plus the earlier S-10…S-23). The page cache (`docs/evidence/raw-page-text/`, 280 files [V]) was built with `fetch.py` (curl, then pandoc for HTML or pdftotext for PDF, one `.txt` and one `.links` file per URL, with the fetch date in the header [V]).
- **[D] Obstacles handled:** Commonwealth's site sits behind a Cloudflare check, so it was read through the `stealth-chrome` browser session; forms were **viewed only**; scanned PDF pages were read visually (page images are in the cache); the AdaCare booking widget did not render in the first fetch.
- **[D] Profile structure** (`company-research/*.md`): *Verified public facts* → *Our interpretation (inference)* → *What we must not assume* → *Open questions* (linked to RQ-N).
- **[D] Existing tools.** Every platform publishes digital tools (request form, virtual agent, portal, scheduler, chatbot, app). Reconciliation added a four-job taxonomy so a tool is never read as proof of a gap: **contact capture · scheduling · administrative onboarding · ongoing coordination** (clinical assessment is never the product's job). (`journeys-and-baseline.md` "What a published tool can and cannot establish".)
- **[D] Corrections found after the first pass** (report §1 key finding 5): Commonwealth has 33 offices in 7 states (not "20 cities in 3 states"); the SSN in the referral packet is the *referring provider's* field, not a patient field; the FAQ publishes self-pay (uninsured only), a $50 late-cancel fee and three phrasings of a scheduling aim; Numotion's documentation step is 2–4 weeks.

### 1.4.5 Collecting and interpreting customer reviews

- **[D] Method** (review report "How to read this evidence"; skill `google-reviews`): Google search → business card → review count → review dialog, sorted **Lowest** and **Newest**; full text, stars, relative date and owner-reply flag extracted by script; **reviewer names not extracted**. Sample sizes: Lowest 40–80, Newest 40–80 per listing (AdaCare: all 43 loaded, lowest first); small listings (AdaCare, FOH, Metro Vein, Numotion) captured the whole low tail; large Commonwealth listings captured only part ("Low tail captured? Partly").
- **[D] One location per listing.** Commonwealth Louisville South ("Shively" on Google), Commonwealth Elizabethtown, AdaCare Meridian, Metro Vein Queens–Forest Hills, FOH Naples, Numotion Nashville branch (LaVergne). Rule: a review describes that office, never the network.
- **[D] Counting.** Themes are keyword-coded by `themes.py`. Denominator per sample = reviews at ≤3★ **with text**, de-duplicated on (stars, date, first 80 characters). Lowest and Newest counts are **never added** (they overlap). Counts are indicators, not rates. **[V] I re-ran `python3 -I themes.py` on the raw folder; every count in review report §6 reproduced** (e.g. Louisville South 10/58 callbacks, Metro Vein 13/33 waiting, Numotion 10/27 lead time, FOH 3/6 callbacks).
- **[D] Quotation rules.** Exact text with "[…]" for omissions and "[name]" for removed names; identifiable health narratives paraphrased without quote marks; Google machine translations labelled. Quotes were checked against raw by script [U].
- **[D] Not used as evidence:** Google AI Overview summaries; Indeed/Glassdoor employee-rating snippets (both were in the first version and removed because they were not read at source).
- **[D] Patient-status labelling (review report §7)** was added in reconciliation *after* the candidates were already scored: each cited complaint is tagged new / established / unclear, journey stage, and "direct / indirect / uncertain" as onboarding evidence. This materially narrowed the evidence: several Commonwealth complaints concern established patients between procedures.
- **[D] Positives were kept** (AdaCare reminder calls, Commonwealth explanations, Numotion technicians) and carried into the pitfalls document as "behaviours to preserve".
- **[V] Two limits I found in the data.** (a) FOH's lowest sample includes a **1★ review whose text is positive** ("Always timely and professional !"); it is counted inside the denominator of 6 and the report does not mention the star–text mismatch. (b) A Lowest-sorted sample structurally over-represents complaints; the only positive/neutral slice is Newest (plus AdaCare's full set). **[R]** flag star–text mismatches and add a balanced sample (Stage 7).

### 1.4.6 Reference journeys and professional guidance

- **[D] Why.** Public contact forms show only the entry point and company implementation is unknown. A reference model from guidance lets a company be compared with *good practice* without claiming access to its private workflow.
- **[D] What was produced** (`…-patient-journeys-and-onboarding-baseline.md`): an evidence-category table (what each source establishes and cannot); an 8-stage **common first-visit journey** (derived, not observed) with patient need / administrative work / assistant role / what stays with humans; five service-specific reference sequences; 13 **candidate baseline** rows each with "what to check in a demonstration"; a clinical-information boundary; privacy and financial distinctions; three synthetic evaluation situations.
- **[D] Sources** S-108…S-121: AMA pre-registration and sample forms, ADA, AHRQ tools 4/9/11/21, W3C WAI forms, HHS Notice of Privacy Practices, CMS Good Faith Estimate, two peer organisations (MSK, Cleveland Clinic) and Metro Vein's own "what to expect" page. Labelled PROFESSIONAL-GUIDANCE, PRIMARY-GUIDANCE or CONTEXT-PEER. Two sources that returned 404 or an inconsistent redirect were **excluded and noted**.
- **[D] It created RQ-44…46** — the three scope questions that stayed open.

### 1.4.7 From findings to problems, opportunities and candidates

- **[D] Chain on paper.** Review report (§1–§5, patient status §7) + published requirements → **pitfalls table** (five pitfalls: nobody owns the next action · patients cannot see status · submitted information does not carry through · scheduling expectations break down · automation becomes another obstacle) → the four patient questions (*Was my information received? What is missing? Who handles the next action? What happens next?*) → report gaps G1–G9 and §12 recommendations → matrix candidates. The report's §9 maps each gap to SOL IDs (e.g. "G1 → SOL-001, SOL-006").
- **[D] What the reviews support less directly** was written down and became parked ideas: long-form abandonment (little direct evidence), office waits and staffing (P-08), treatment outcomes, equipment repair (P-03), ongoing care (P-11), vendor fault.
- **[I] Where the 19 candidates came from.** No generation log exists. Cross-reading shows: SOL-001…004, 006, 007, 008 from G1–G6 and pitfalls; SOL-005, 009 from G4/G7 and the baseline; SOL-010, 011, 012, 014, 016, 017, 018 from the baseline's candidate-baseline table and company pages; SOL-013 and 019 from brief stretch items #5 and #7; SOL-015 from the cohort/reuse strategy. **[R]** keep a harvest log (§3 Stage 11).

### 1.4.8 Mandatory requirements, discretionary options, parked ideas

- **[D] Mandatory baseline M-01…M-15** — taken from the issued brief's sections (core flows, edge cases, security, performance, metrics/evals, code quality, submission, regulatory note). Your selection "cannot remove them". Two project rules also always apply: synthetic data only; the administrative-only boundary (no diagnosis, urgency triage, treatment recommendation, insurance approval, coverage promise or referral bypass).
- **[D] Discretionary candidates SOL-001…019** — anything beyond the mandatory floor. Typed **Complete** (a behaviour that solves a problem alone) or **Supporting** (makes another candidate or a mandatory feature better).
- **[D] Parked P-01…P-11** — not ranked, not in the denominator. They fall into five kinds: *unresolved scope decision* (P-01 clinical context → RQ-44; P-11 ongoing care → RQ-45) · *unsupported by evidence* (P-02 sentiment tone; P-06 provider matching; P-07 duplicate-record flag) · *out of scope* (P-03 Numotion tracker; P-08 in-office waits) · *no access* (P-04 live integrations; P-05 real-calendar booking) · *prohibited by rule* (P-09 triage/eligibility/referral bypass; P-10 replacing an existing tool).
- **[D] Overlap with mandatory** is noted on the candidate (SOL-004 builds on M-02/M-05; SOL-007 and SOL-006 extend M-03; SOL-014 overlaps M-04; SOL-010 extends M-05; SOL-003 is "partly implied" by M-01).

### 1.4.9 De-duplication, ranking, shortlist and selection

- **[D] De-duplication.** "Overlapping ideas merged; nothing split to reach a round number." The pool was therefore **19**.
- **[D] Rubric** (matrix §3): six criteria scored 1–5 — E evidence (weight 20), P problem importance (20), F fit with brief and administrative scope (20), D demonstrable in the timebox with synthetic data (15), R reuse across portfolio companies (15), I low effort and dependency (10). **Score = Σ(weight × score ÷ 5), maximum 100.** [V] I recomputed all 19 scores from the table: 0 mismatches; scores are non-increasing in rank order.
- **[D] Evidence scale E:** 5 = direct attributed reports at ≥2 platforms plus published workflow · 4 = direct reports at one platform, or a published requirement at ≥3 platforms, plus guidance · 3 = published workflow or guidance with indirect/single reports · 2 = derived from the brief or our analysis only · 1 = speculative.
- **[D] Tie-breaks**, applied after scoring and each stated once: SOL-005 over SOL-011 (83 each) on brief fit; SOL-006 over SOL-014 (82 each) because it is a complete solution with stronger problem evidence while SOL-014 mainly feeds M-04; SOL-008 over SOL-018 on evidence; SOL-009 over SOL-012 on evidence and importance; SOL-013 over SOL-017 as a brief stretch item. **[D] Sensitivity:** the cut at ranks 8/9 is "a tie broken by judgement".
- **[D] Percentages.** Shortlist ≈40% × 19 = 7.6 → **8**. Selections for Innocent ≈20% × 19 = 3.8 → **4**. Both are rounded to the nearest whole number and apply to **the same 19-candidate discretionary pool**, excluding the 15 mandatory and 11 parked. **[I]** The 40%/20% came from Innocent through the Codex handoff ("proposed interpretation: rank the discretionary candidate set, shortlist roughly 40%, and reserve roughly 20% of that original set for Innocent to choose; required brief capabilities stay outside the discretionary cut"); his original wording is [U].
- **[D] Shortlist cards** (ranks 1–8 only) carry the full chain; ranks 9–19 have inventory rows only. Each card ends with *Reason to choose / Reason to defer / Selection ☐ (Innocent)*. A table separates **problem confidence** from **solution confidence** for each shortlisted candidate.
- **[D] Preparation for selection:** dependency notes (SOL-001 and SOL-006 need SOL-002; SOL-003 needs a staff view; SOL-007 and SOL-006 extend M-03; SOL-011 needs somewhere to send an estimate request; SOL-013 needs SOL-012), combination notes, interview explanations written in "research tense", an **evidence-status ledger** (inspired → proposed → selected → implemented → demonstrated → validated, all "pending"), a blank selection area (§6), and the single decision: "which four of these eight go into scope, given that SOL-001 and SOL-006 each bring SOL-002 with them?"
- **[V] Weakness: E was not re-scored after review §7.** The reconciliation log says "No ID, score, rank or shortlist membership changed" and lowered only the *stated problem confidence* for SOL-003. SOL-001's E=5 ("direct reports at ≥2 platforms") still stands although its review support is "mostly established patients". Whether that would change a rank is untested.

### 1.4.10 Contradictions and evidence weaknesses, and how they were reconciled

| Problem found | How it was handled | Where |
|---|---|---|
| First-pass factual errors (office count, SSN, fees, Numotion step) | Re-read first-party pages; corrected in the owner files; superseded checklist given a banner and kept as history | report §1 finding 5; checklist banner |
| Review quotes tidied or with inserted words; "seven reviews name AI"; Lowest and Newest mixed; a listing name that differed from the company's | Exact quotes, "6 AI + 1 robot", per-sample denominators, "Shively = Louisville South" | review report "Revision notes" |
| AI Overview and employee ratings used as evidence | Removed | same |
| "Did not render" AdaCare widget vs Innocent's own walkthrough | View-only DevTools recheck; both readings kept with dates | S-83; reconciliation log |
| Tool presence treated as a gap | Four-job taxonomy; "tool presence is not complete onboarding"; "gap" redefined as *difference from the reference baseline or a reported problem* | report front matter and §9; baseline |
| Complaints counted as onboarding evidence although many were about established patients | Review §7 status table; confidence lowered on SOL-003; caveats in SOL-001/006 | review §7; matrix |
| Annex excludes medical history; report §7 and four demo scenarios collect it | Flagged "⚑ RQ-44" everywhere; conservative default stays; scenarios "not demo-ready"; **left unresolved** | annex; blueprint; P-01 |
| 71 line-number citations would go stale | Replaced by section citations | matrix revision log |
| Dashboard still shows line numbers | **Not reconciled** — see §5.2 | dashboard |
| Riverside identity assumed to be the Boston firm | Corrected from first-party disclosures; GQ-19 closed | `{GAUNTLET}/open-questions.md`; register S-63 |

### 1.4.11 How the dashboard was assembled and checked

- **[D]** One self-contained HTML file with embedded CSS and JS, no network assets or tracking, opened from `file://`. Its six views and every capability are in Part 5.
- **[D] Source.** "Transcribed from the reconciled selection matrix, the review report (including §7), the journey baseline, the profiles and the source register." The data are inline JavaScript constants (`C`, `CARDS`, `MANDATORY`, `PARKED`, `DEPS`, `SOURCES`, …). **[V] No generator, parser or parity script exists in the repo.**
- **[D] Checks run** (log `selection-dashboard-claude-04`): rendering and no JS errors; all filters; journey-stage linking; detail dialog focus; three-way compare; selection count, over-target message and dependency warnings; localStorage persistence across reload and the blocked-storage fallback; Markdown and JSON export (including notes); the audit ledger keeping "recorded: pending" separate from browser drafts; narrow width ≥500px without horizontal scroll; contrast ≥4.5:1 text and ≥4:1 controls in both themes (computed); a script confirming the 19 IDs, ranks, scores and rubric criteria match the matrix and that zero selections are recorded. Three defects were fixed during checking (a duplicated "Proposed" label, control-border contrast, an oversized selection tray on narrow screens).
- **[D] Not checked:** print layout; light-theme screenshots; 320–400px widths; the content of a downloaded file.
- **[V] What I found on 2026-10-15** (read-only): all 19 candidates' rank, six sub-scores and total match the matrix (0 differences); no external `<script>`/`<link>` tags; **but** the "Where this card lives" citations use line numbers that are **two lines stale** (e.g. SOL-001 → line 223, actual heading at 225; the audit cards cite "§5 … 496", actual 498) even though the matrix itself was moved to section citations because lines drift; and the ledger's "Selected by Innocent (recorded)" cell is hard-coded "pending", so recording a choice requires regenerating the page. Also, the dashboard file was last modified at 20:54, about two and a half hours after its run log was last written (18:32); the log does not say what changed afterwards [U]. What I checked is the file as it stands.

## 1.5 Artifact dependency map

```
                 ┌────────────── Gauntlet portal briefs (AEA Proj 1 · Riverside · Proj 2) ───────────────┐
                 │                                                                                       │
        docs/source/aea-proj1…md  (unchanged, SHA-256 in register S-1)                                  │
                 │                                                                                       │
     ┌───────────┼────────────────────────────┐                                                          │
     │           │                            │                                                          │
     ▼           ▼                            ▼                                                          │
 brief audit   M-01…M-15 (matrix §1)     research-questions RQ-N ◄── every stage adds                    │
 T1–T23 / C1–C11  (mandatory baseline)       ▲                                                           │
 + S-36…S-62      │                          │                                                           │
     │            │                          │                                                           │
     │   AEA portfolio page (S-6) ─► inventory.json (118 → 56 → 9 workflow groups)                       │
     │            │                          │                                                           │
     │            │             Gauntlet companion doc §0.1 ─► portfolio-fit-review.md + aea-investors.md │
     │            │                          │  (criteria · comparison · cohort roles)                   │
     │            │                          ▼                                                           │
     │            │        company sites ─► raw-page-text cache ─► company-research/<co>.md (5 profiles) │
     │            │        (S-10…S-23, S-64…S-106)                           │                           │
     │            │                                                          ▼                           │
     │            │   docs/aea-portfolio-research.md (template, Parts 1–10) ─► onboarding-research-report│
     │            │                                                          (12 sections) + Annex 1 + 2 │
     │            │                                                          │  G1–G9, §12 recs          │
     │            │   Google review dialogs ─► raw-google-reviews/*.json ─► themes.py ─► review report    │
     │            │   (S-77…S-107)                                          (§0–§7 incl. patient status)  │
     │            │   guidance (S-108…S-121) ─► journeys-and-onboarding-baseline                          │
     │            │                                       │                    │                          │
     │            │                                       └──► review pitfalls synthesis ◄────────────────┘
     │            ▼                                                            │
     └──────► solution-selection-and-evidence-matrix  (M · SOL · P · rubric · scores · 8 cards · ledger · §6 selection)
                                     │   (authoritative; fed by profiles, register, RQs, report, baseline, pitfalls, review report)
                                     ▼
                  solution-selection-dashboard.html  (hand-transcribed copy; reads nothing at runtime)
                                     ▼
                  browser-local draft selections ──(manual)──► matrix §6 + ledger  (the record)
```

| Document | Fed by | Feeds | Owner of |
|---|---|---|---|
| `docs/source/…brief.md` + register | portal, Gauntlet copy | audit, matrix M-list | requirements (ISSUED), source IDs, review dates |
| `…inventory.json` | AEA portfolio page | fit review, AEA context | the 118 records and screening disposition |
| `portfolio-fit-review.md` | companion §0.1, inventory | cohort, profiles | industry comparison, criteria, recommendation |
| `company-research/<co>.md` | company sites, cache | report, matrix | per-company facts, inference, non-assumptions |
| `…onboarding-research-report.md` + annexes | template, profiles, reviews | pitfalls, matrix | company comparison, config spec, 15 synthetic scenarios |
| `…google-review-sentiment.md` | raw reviews, `themes.py` | pitfalls, matrix | review samples, excerpts, counts, patient status |
| `…journeys-and-onboarding-baseline.md` | guidance S-108…121 | pitfalls, matrix | reference journey and baseline |
| `…review-pitfalls-and-solution-opportunities.md` | review report, baseline | matrix | interpretation of reviews against the baseline |
| `2026-10-14-brief-audit.md` | brief, primary sources | matrix M-list notes, RQs | T1–T23, C1–C11 |
| `research-questions.md` | all | all | RQ-N |
| `…solution-selection-and-evidence-matrix.md` | all of the above | dashboard | M · SOL · P IDs, rubric, scores, shortlist, selection record |
| `…solution-selection-dashboard.html` | matrix (by hand) | Innocent's draft | nothing — a view |

## 1.6 Backward traces from three AEA candidates (plus one short)

Each trace goes **dashboard → matrix card → intermediate documents → source register → raw evidence**, and marks what I opened myself.

### Trace A — SOL-002 "Owned staff handoff queue" (rank 3, 89/100, E=5)

| Level | What it says | Where |
|---|---|---|
| Dashboard | Solutions → shortlist card → "Open evidence" dialog; `CARDS["SOL-002"]` | dashboard JS constants `C`, `CARDS` |
| Matrix | Card chain: Commonwealth and AON/FOH → Louisville South, Elizabethtown, Naples → request to first contact → unreturned calls and automation without a human → owned, ageing queue → every request visible and owned → SIM-CPS-2, SIM-FOH-2 → time to first human contact. Scores E5 P5 F4 D4 R5 I3 = 20+20+16+12+15+6 = **89** [V] | matrix §2 row, §3 scores, §4 card |
| Intermediate | "Callback and reach-a-person" counts: Louisville South 10/58, Elizabethtown 4/41, FOH 3/6, Numotion 3/27; two clear *new-patient* reports (a referred Commonwealth patient who waited two weeks for a call; an FOH new patient whose calls went unreturned) with §7 status "New patient" | review report §1 item 1, §4, §6, §7 |
| Reference baseline | Referral work has clear responsibilities and tracking (AHRQ Tool 21, S-114); recovery routes (W3C, S-116); "Keep referral work owned" | baseline "Candidate baseline"; register S-114, S-116 |
| Published fact | Commonwealth's "24/7 Virtual Agent" will "connect you with the appropriate member of your care team when needed" (S-66); FOH: "a Patient Services Specialist will contact you" (S-96) | `commonwealth-pain-spine.md` §1.1; `american-oncology-network.md` |
| Raw | [V] **Review:** `raw-google-reviews/…aon-foh-naples.json` → `lowest.reviews[]`: a 1★ "Edited 9 months ago" entry beginning "I tried to schedule a new patient appointment…". `themes.py` reproduces FOH callbacks 3 of 6. **Page text:** [V] `raw-page-text/cps/www-mypainsolution-com-about-complete-care.txt` (lines 38–39 contain the virtual-agent sentence) and `raw-page-text/foh/www-floridaonc-com-patient-referral.txt` (line 43 contains the Patient Services Specialist sentence) | raw folders |

**What this teaches.** (1) The top-3 rank rests on a *theme count* across mostly established patients plus only **two** clear new-patient reports; E=5 was assigned before the §7 status table existed and was not re-scored (§1.4.9). (2) Its real importance is structural: it is a prerequisite for SOL-001, -006, -009, -011 and half of -003, so a selection needs the dependency view, not just the rank. (3) The value is staff-side and depends on staffing the product cannot create; every card had to say so. (4) Reproducing the trace was cheap *because* each document names its source IDs and sections.

### Trace B — SOL-007 "Confirmation and visit-logistics package" (rank 2, 90/100, E=4)

| Level | What it says | Where |
|---|---|---|
| Matrix | Metro Vein Queens–Forest Hills → prepare for the visit → missing directions or instructions, changed times → a confirmation generated only from a stored booking. Scores E4 P4 F5 D5 R5 I4 = 16+16+20+15+15+8 = **90** [V] | §2, §3, §4 |
| Intermediate | Forest Hills reviews: changed or cancelled times (3 of 33 low-with-text), missing address/instructions (one 2★, "a year ago"), arrival-time mismatches; status "booked, did not attend; self-paying", logistics direct. Metro Vein "Reading": complaints are about *after* the request is captured, not evidence the chatbot or form fails | review report §3, §7 |
| Reference baseline | Appointment logistics are part of pre-registration (AMA, S-108); "Give appointment logistics" | baseline |
| Published fact | SMS reminders and reschedule-by-text exist (S-19, S-86); Forest Hills hours (S-90) | `metro-vein-centers.md` §1.2 |
| Raw | [V] `raw-google-reviews/…mvc-forest-hills.json` → `lowest.reviews[]` 2★ "a year ago": "…I supposed to receive email and text and I have to call 2 times for that… They did not gave me address or instructions…". [V] `raw-page-text/mvc/www-metroveincenters-com-faqs.txt` line 156 (reschedule by phone 866-715-9121 or "text us back at the same number you receive appointment reminders"); `…privacy-policy.txt` line 173 (chatbot for appointment requests, insurance verification, general inquiries) | raw folders |

**What this teaches.** The rank is driven by **D, R, F = 5/5/5** (demonstrable, reusable, on-brief), not by problem evidence, which the same document rates only "Medium" (problem confidence) with solution confidence "Medium-high". A reader who sees only "rank 2" would misread it; the dashboard therefore shows the six sub-scores beside the rank. Also: the complaint says *what* was missing, not *why*; the card says "cause is not established".

### Trace C — SOL-006 "Prerequisite-aware next step" (rank 8, 82/100, E=4)

| Level | What it says | Where |
|---|---|---|
| Matrix | Commonwealth, FOH, Numotion → arrange the next appointment → a coordination appointment as the bookable next step, never a referral bypass; **AdaCare as the no-prerequisite contrast**. Scores E4 P4 F5 D4 R4 I3 = 16+16+20+12+12+6 = **82**, tied with SOL-014 (82) and placed above it by a stated tie-break [V] | §2, §3, §4 |
| Intermediate | Authorisation not communicated / treatment not authorised on arrival — Louisville South about a year ago, Elizabethtown about 8 years ago, **both established patients' procedures** | review §1 item 4, §7 |
| Published fact | "Treatment for worker's compensation needs authorization before scheduling" (S-12); referral wording that conflicts between FAQ sections (profile §1.3); FOH entry "by physician's referral or transfer" (S-95); Numotion face-to-face physician visit and Letter of Medical Necessity (S-102) | profiles |
| Raw | [V] `raw-page-text/cps/www-mypainsolution-com-faq.txt` line 81 contains the workers' compensation sentence. **The AdaCare contrast has no raw cache [U]:** `raw-page-text/adacare/schedule-jarvisanalytics-com-frame-…10886.txt` is an *empty frame* (the first-pass fetch); the later view-only DevTools re-read that showed New Patient Visit slots for 19–26 Oct before any personal details exists only as register text (S-83) and the reconciliation log | raw folders |

**What this teaches.** (1) The finding that most changed the card — "the rule must be configurable per company and appointment type, including *no prerequisite*" — depends on evidence that was never captured as a file. **Every interactive check needs a saved screenshot or DOM text.** (2) The shortlist boundary was decided by a judged tie at 82 (§1.4.9). (3) Its review support concerns established patients; the card says so, and the problem/solution confidence table rates solution confidence "Medium-low".

### Trace D (short) — SOL-004 "Insurance capture with OCR and confirmation" (rank 4, 87/100, E=4)

The problem evidence is a **published requirement at all five platforms** (request form insurer + member ID, S-75; Numotion primary/secondary and MBI, S-102; AdaCare two dental insurances, S-82; FOH insurance with policyholder, S-98), not reviews. The only review item is *indirect* (an established patient's insurance update not available at check-in) and the card says so. This is what E=4 means under the scale: "a published requirement at three or more platforms, plus guidance". **Teaching:** a candidate can be strong on published requirements and weak on reported pain; both must be shown separately, and the dashboard's "Evidence type" line does that.

**Across the four traces.** The chain survives only because three habits held: every fact carries an `S-N` plus a section; every review claim carries its sample and its status label; every card states what is *not* established. Where a link broke (Trace C's AdaCare contrast; Trace A's un-rescored E), the cause was something that happened outside a saved file.

## 1.7 Iterations, corrections and unresolved decisions (consolidated)

**Iterations that changed the result:** first pass rejected → corrected deep pass; "tools are not gaps" reframing; patient-status labelling; three-baselines separation (reference practice, company current state, measured performance); AdaCare recheck; line-citation → section-citation switch.

**Still unresolved at the end of AEA's run:**

- **Selections:** none recorded. The ledger is "pending" for all eight shortlisted candidates.
- **RQ-44** (optional clinical-adjacent context) and **RQ-45** (where intake ends; established customers) — Innocent's decisions; they keep P-01, P-11 and four demo scenarios in limbo.
- **Research sign-off:** not given. No PRD, framing/metrics-tree document (`docs/delivery/…`) or interview answer table exists.
- **Partner questions:** GQ-18 (one build for two partners) and GQ-20 (deadline) open; GQ-19 resolved.
- **Company discovery questions** RQ-38…43 and the measured baselines RQ-2/3 — unknown for every company.
- **Recommended-but-not-done:** a decision record for the niche; re-scoring E after §7; saved parity and quote-check scripts; a dashboard whose citations do not drift.

---

# Part 2 · What transfers to Riverside

## 2.1 Reusable as-is (methods, templates, evidence rules, dashboard behaviour)

| Item | AEA source | Why it transfers | Note |
|---|---|---|---|
| Source ranking and authority labels (ISSUED → CONTEXT → DERIVED, plus EVIDENCE, PROFESSIONAL-GUIDANCE, PRIMARY-LAW/GUIDANCE/VENDOR, CONTEXT-PEER) | `.claude/rules/source-authority.md`; register header | Independent of industry | Rewrite the rule file for Riverside; keep the structure |
| `S-N` source register: ID · source · authority · **date actually read** · supports; "never silently overwrite an old reading" | `docs/source/source-register.md` | Makes every claim traceable | |
| Brief handling: unchanged copy, SHA-256, provenance row | register "Provenance of the issued brief" | Both partners issue briefs | |
| Verified / inference / not-assumed / open-question profile structure | `company-research/*.md` | Works for any company | |
| Page cache with fetch date, final URL and links list | `docs/evidence/raw-page-text/fetch.py` | Keeps claims re-checkable | Save as a project script; AEA's copy is a working but informal tool |
| View-only rule for forms; never submit | research template Part 3; register note | Ethics and safety | |
| Review protocol: location-level, sort modes, denominators, no reviewer names, git-ignored raw files, exact quotes, keyword coding with a saved script, patient-status labelling | review report; `themes.py`; skill `google-reviews` | Applies wherever there are public reviews | Source platform depends on theme (§Stage 7) |
| Three baselines kept apart: reference practice · company current state · measured performance (unknown) | pitfalls; matrix header | The central honesty device | |
| "A tool's existence is not a gap"; four tool jobs | baseline | Prevents wrongful "you're broken" framing | Redefine the jobs for the theme |
| Brief audit format: T (risk, with primary source) and C (internal contradiction with verbatim excerpt and section anchor) | `2026-10-14-brief-audit.md` | The briefs are ~95% identical | Re-verify each source and quote (§Stage 10) |
| Mandatory baseline vs discretionary candidates vs parked ideas | matrix §1–§2 | Keeps the brief's floor out of the selection | |
| Weighted rubric, formula, E scale, deterministic tie-breaks, sensitivity note | matrix §3 | Transparent ranking | Parameters adapt (Part 4) |
| Evidence cards with a fixed chain, problem vs solution confidence, reasons to choose/defer | matrix §3–§4 | Auditable selection | Chain extended in Part 4 |
| Evidence-status ledger and "claim-growth ladder" | matrix §5 | Prevents overclaiming in interviews | |
| Dashboard behaviours (Part 5) | dashboard HTML | A decision aid, not a source of truth | Regenerate from Riverside data |
| Dev-log contract, one file per run, four fields | `.claude/reference/dev-log.md` | Resumability | |
| Ripple reconciliation (fix the owner, then dependents, log it) | reconciliation run | Prevents contradictions | Formalised in Part 3 |
| `PROJECT-CHECKLIST.md` from `zero-to-hero`, light mode | root `.claude/skills/zero-to-hero/` | Required for any new coding repo | |

## 2.2 Needs adaptation after the theme is chosen

| Element | AEA form | What to decide for Riverside |
|---|---|---|
| Theme comparison criteria and their order | five criteria, qualitative | Confirm against Riverside's brief and add domain-risk load and review-source availability |
| Workflow groups | nine groups by customer-facing workflow | Define "onboarding" for the theme: who registers, what is collected, what is the next step |
| Cohort size and roles | 4 core + 1 adjacent; anchor / second configuration / benchmark / fourth / adjacent | Size from evidence; roles from what each company can teach |
| Practice/branch rule | one example per platform, two for the anchor | Written rule for choosing the location(s) |
| Review sources | Google review dialogs | Choose by theme (Stage 7, decision D-7) |
| Reference guidance | AMA, ADA, AHRQ, W3C, HHS, CMS | Find the theme's own authorities; W3C form guidance probably still applies |
| Journey stage names | find/request · record · arrange · packet · prepare · arrive · consult · leave | Replace with the theme's real stages; keep "arrive and reconcile" if there is an in-person step |
| Tool-job taxonomy | contact capture · scheduling · administrative onboarding · ongoing coordination | Re-check each job exists in the theme |
| Domain boundary | administrative only; never diagnose, triage, approve insurance, bypass a referral | Write the theme's equivalent: what the assistant never decides (Part 4.7) |
| Rubric criterion D | "demonstrable in the 3-day timebox" | Re-read the Riverside timebox before using it |
| Rubric criterion R | "applies to all five platforms" | Re-express as a share of the cohort |
| Synthetic scenario names | `SIM-CPS-1` | `SIM-<company>-n`; keep "obviously synthetic" |
| Regulatory note | HIPAA | Whatever regime the chosen theme actually triggers; the brief makes it conditional |
| Persistent rules in `.claude/rules/` | `source-authority.md` names AEA, Elevate, patients | Rewrite with Riverside's identity and the theme; keep the numbered-rule format |

## 2.3 AEA-specific — do **not** carry over; research again

| Category | Do not carry over |
|---|---|
| **Domain** | Healthcare as the answer; "patient" language; HIPAA as the assumed regime; the administrative-only wording unless the chosen theme is healthcare (then carry the safeguards — §4.7) |
| **Cohort** | Commonwealth, American Dental Companies/AdaCare, Metro Vein, American Oncology Network/FOH, Numotion; the "four platforms plus one adjacent" count |
| **Counts and groupings** | 118 profiles, 56 eligible, 55 realized, 7 team-prior-experience; the nine groups |
| **Company facts** | Offices, fees, hours, forms, tools, scheduling aims, the S-10…S-107 register entries |
| **Review evidence** | Every review sample, quote, count, rating and theme table |
| **Candidates** | The 19 SOL candidates, 15 M items, 11 P items, their scores, ranks, the shortlist of 8, the selection target of 4, the dependency list, the tie-breaks (all are *examples* of the method) |
| **Open questions** | RQ-1…46 contents (the *kinds* of question transfer) |
| **Risks** | T1–T23 and C1–C11 contents (candidates to re-verify, not conclusions) |
| **Stack and vendors** | AEA's mandated Rails + Next.js, Render/Railway + Supabase, Groq/Gemini/Ollama; the vendor-terms findings (S-36…S-45) |
| **Timebox and dates** | 3-day timebox, internal target 2026-10-17 22:00 CT, interview 2026-10-22, deadline GQ-20 |
| **Decisions** | The niche choice, RQ-44/45 positions, the GQ-18/19/20 statuses |
| **Strategy** | AEA strategies (Middle Market, Enterprise, Elevate, Private Debt), the Head of AI Solutions inference |

## 2.4 Assumptions in the original research template that need correction

Source: `{AEA}/docs/aea-portfolio-research.md` (Parts 1–10, 12-section report). It is a good frame; these assumptions are not safe to copy. Create a Riverside copy at Stage 5 with these fixed and leave the AEA file unchanged.

| # | Template wording / assumption | Problem | Correction for Riverside |
|---|---|---|---|
| 1 | "analyze the healthcare company website(s) **provided earlier in this conversation**" | Depends on hidden context | List companies and URLs in a file the prompt cites |
| 2 | "I am building general-purpose healthcare onboarding software… configure **my existing software**… I am not building a custom application from scratch" | **No product exists.** This is research for a proposed assistant; it also says "software" is configurable and has integrations | State "a proposed onboarding assistant, to be specified later". Never imply built software, configuration capability or integrations |
| 3 | Role panel: healthcare CEO, healthcare operations consultant, healthcare growth strategist | Domain-bound; invites role-play authority | Use lenses appropriate to the theme (customer operations, UX/accessibility, privacy, product) and say they are lenses, not credentials |
| 4 | Intro: "what appears to be **missing**, how my product could **create additional value**" | Presumes gaps and failure | Apply source-authority rule 5; define "gap" as a difference from the reference baseline or a reported problem (AEA report §9) |
| 5 | Part 5 "Clinically appropriate service opportunities", "legitimate additional revenue" | Collides with the administrative-only boundary; became unresolved RQ-44 in AEA | In a non-clinical theme, drop; in healthcare, decide the boundary *before* writing the part (Stage 9, D-9) |
| 6 | Part 6 "clinician-approved urgency screening or escalation" | Implies the product does triage | Replace with "company-published emergency notice plus staff routing", as AEA did, or the theme's equivalent |
| 7 | Part 7 "Compare … with a proposed onboarding experience using my software" | Compares a real company with an imagined product | Compare with the **reference baseline**; keep the four evidence classes (Verified / Not publicly established / Inferred / Proposed) |
| 8 | Part 8 revenue/ROI with "illustrative calculations" | Easy to read as findings | Label every number illustrative; list baselines to obtain; add "no measured baseline exists" |
| 9 | Part 9 scenario 3 "reveals other potentially relevant care needs requiring professional review" | Same boundary issue; four AEA scenarios stayed "not demo-ready" | Keep only if D-9 allows; otherwise replace with a different obstacle |
| 10 | Research standard 1: "Use the referenced websites as the primary sources" and nothing about reviews, reference journeys or the brief | **Three evidence layers added later by hand** | Add explicit steps for reviews (Stage 7), reference practice (Stage 8) and the brief audit (Stage 10) |
| 11 | "Include the date of the website assessment" | One date per report hides per-page dates | Record date read per source (register) and fetch date per cached page |
| 12 | Closing deliverable "What I Need to Configure This Company in My Onboarding Software" | Reads as product configuration planning | Rename "Configuration-relevant facts (research only, not a product design)" |
| 13 | "patient", "clinician", "provider" throughout | Vocabulary assumes healthcare | Use neutral terms in the template (customer/applicant, staff, service) and translate per theme |
| 14 | Template does not forbid account creation, uploads or contact; it forbids "submit actual appointments, patient information, medical forms, or inquiries" | Incomplete | Add: no accounts, no uploads, no messages, no real data |

## 2.5 The two briefs, compared (done now, from local files)

Files: `{GAUNTLET}/artifacts/2026-10-13-partner-briefs/riverside-onboarding-assistant.md` and `aea-proj1-onboarding-assistant.md`. The AEA original in `{AEA}/docs/source/` is **byte-identical** to the Gauntlet copy (`cmp` [V]) and matches the SHA-256 in the AEA register. The two briefs differ in line endings (AEA CRLF, Riverside LF), so a plain `diff` looks like a total rewrite; a diff with carriage returns stripped shows four real differences [V]:

| Area | AEA Project 1 | Riverside |
|---|---|---|
| Tech stack intro | "Concrete free-tier defaults; substitution allowed if justified and benchmarks met." | "Candidates pick their own languages, frontend, and hosting, and briefly justify the choice in the README; benchmarks must still be met." |
| Required stack | Required: Ruby on Rails (API) + Next.js (React/TypeScript) | None required |
| LLM | Groq free tier, Gemini free tier or Ollama; Claude or OpenAI optional | **Claude (Anthropic API) suggested**; Groq, Gemini, Ollama, OpenAI acceptable if justified |
| Cloud platforms | Render or Railway + Supabase (Postgres + Auth) | Not specified |
| Model/data boundary | Prefer local OCR and a self-hosted or free-tier LLM; disclose any cloud API; avoid sending raw ID images | **Same, plus:** "Candidates using the Claude API must document exactly which PII fields are sent to it and keep that to the minimum needed" |

**Identical in both:** target industry ("Sensitive-service onboarding"), timebox and tier, problem statement, business context, illustrative metrics, the four core flows with acceptance criteria, stretch items, the six edge cases, performance targets and k6 load, AI metrics (30-document OCR golden set, ≥90%, intent coverage), security/privacy bullets and the conditional regulatory note, code-quality section, AI-usage disclosure, submission requirements and the 100-point rubric (pass ≥ 70).

**What transfers, and what each difference forces:**

- The whole **Requirements baseline (M-list)** transfers in structure and nearly in content; rewrite it from the Riverside text, not from the AEA matrix.
- The **brief audit's C-register** (internal contradictions) applies to both because the text is identical, but each quote and section anchor must be re-verified against the Riverside file. T-register items about vendors (Gemini, Groq, Supabase, Render, Railway) apply to AEA's named stack and need re-assessment: Riverside's different stack choice and **Claude suggestion** add new items (Anthropic's terms for the data sent, the PII-field disclosure Riverside requires, any use of a hosted LLM with sensitive data). The older vendor findings were read on 2026-10-14; documentation changes, so re-read before reuse.
- The **rubric, thresholds, edge cases and performance targets** are shared, so Stage 11's "mandatory" floor will look much the same.
- **GQ-18** (may one build serve both partners?) is a staff question, not ours; the AEA changes may alter it.
- **Do not treat the two briefs as the same document** in the register: Riverside gets its own `S-1` row, hash and provenance, and its own copy in `docs/source/`.

## 2.6 Partner identity and the early portfolio check

**Provenance in the repo.** The portal card is titled "Riverside Partners LLC" and links to `riversidecompany.com` (screenshot supplied by Innocent on 2026-10-14; the image itself is [U]). The Riverside Company's own regulatory disclosures and privacy policy name **Riverside Partners L.L.C.** as doing business as **The Riverside Company**; this closed GQ-19 on 2026-10-15 (`{GAUNTLET}/open-questions.md` GQ-19; AEA register **S-63**; companion doc §0). The **Boston** Riverside Partners rebranded to **RS2 Healthcare Partners** (announcement 2026-05-11, per the companion doc) and is a *separate firm*; do not use its healthcare-only focus or portfolio. The exact legal entity on any eventual employment contract is a narrower question.

**Portal claims that are not verified facts:** majority ownership in "nearly 30 companies, including 10 software companies" and the aim to "accelerate AI adoption, create AI use cases and embed AI into portfolio-company products/services". These describe the recruiting scope; the real portfolio page may list a different set. The companion doc also records seven industry specializations from Riverside's industries page (business services, consumer, education, franchising, healthcare, software, manufacturing); it was **not re-read** in AEA.

**Early execution check (Stage 1, before any portfolio work):** re-read the first-party disclosure, confirm the domain, find the portfolio directory, and record its structure (is it complete? does it separate current from realized? does it offer filters?). Only the structure is recorded at Stage 1; the inventory itself is Stage 3. If anything contradicts the identity above, **stop and ask Innocent** (D-1).

---

# Part 3 · The forward execution process

## 3.0 Overview, adjustments and rules that apply to every stage

**Stage order and the reasons it differs slightly from the 14-step list in the request.** The stage numbers are kept so Innocent's list still maps one-to-one. These adjustments are evidence-based:

| Adjustment | Evidence from AEA | Effect |
|---|---|---|
| Draft the mandatory baseline (M-list) at Stage 1, finalise at 11 | In AEA the M-list appeared only in the matrix, yet the theme criteria already used "the four required flows" | Criteria at Stage 4 cite a real list |
| Start the brief audit (Stage 10) as soon as Stage 2 ends, in parallel | Codex ran the audit on 2026-10-14 while research proceeded; the audit is mostly theme-independent | Saves time; reopen after D-4 for theme-specific regimes |
| Begin reference guidance (Stage 8) right after D-4; finish after Stage 6 | The baseline was written after the report and then forced a reconciliation | Fewer rewrites |
| Move the scope-boundary decisions (AEA's RQ-44/45) to Stage 9 (D-9) | They stayed open to the end and left P-01, P-11 and four scenarios unusable | Resolved before scoring |
| Add an explicit rubric approval (D-11) before scoring | The rubric and tie-breaks were chosen by the author and shown afterwards | Innocent sees weights before they move a rank |
| Adapt the research template at Stage 5, not 6 | The template's assumptions were fixed by hand later (§2.4) | Corrected on day one |
| Freeze candidate data before building the dashboard (Stage 12 → 13) | The dashboard was transcribed while the matrix still moved (stale line numbers) | Dashboard built from audited data |

**Parallelism map.**

```
1 ─► 2 ─┬─► 3 ─► 4★ ─► 5★ ─┬─► 6 ─┐
        │                   ├─► 7 ─┤
        │                   └─► 8 ─┴─► 9★ ─► 11★(rubric) ─► 12 ─► 13 ─► 14★
        └─► 10a (audit: theme-independent part) ───────────────► 10b (after D-4/D-9) ─┘
```

- **Run together:** 6, 7 and 8 per company (one worker per company; reviews one browser tab at a time); 10a with 3–9; per-group screening inside Stage 3.
- **Must revisit after later findings:** Stage 5 if Stage 6 disqualifies a company; Stage 9 and 11 when Stage 7 changes a problem's evidence status (re-score E); Stage 10b after D-4 and D-9; Stage 12 → earlier stages for any failed chain; Stage 13 after any matrix change.

**Common rules for all stages**

- **Fact owners.** Each fact lives in exactly one file (the owner map you write in Stage 2). Link; do not copy.
- **Ripple rule.** When a fact changes: (1) fix the owner; (2) grep the whole project for the old value; (3) update dependents; (4) add a dated line to the document's revision notes and the dev log; (5) re-run any affected count or score; (6) mark the dashboard stale (Stage 13).
- **Dev log.** One entry per coherent wave in `{DEVLOG}`, with Changed / Why / Checked / Remaining. Name what *actually* happened (proposed, approved, implemented, verified).
- **A common preamble** for every ready-to-use instruction (write it once at the top of each prompt):

```text
You are continuing the Riverside onboarding research. Read, in order:
1. {PLAYBOOK} (copy at {PROJECT}/docs/analysis/research-playbook.md after Stage 2): §0.5 boundaries, then the stage named below.
2. {PROJECT}/CLAUDE.md, {PROJECT}/.claude/README.md, {PROJECT}/RESEARCH-PROGRESS.md (once they exist).
Research phase only: no PRD, design, tickets or code; no commit, push, publish or contact; synthetic data only;
HTML is a local file, never an Artifact. Innocent's ★ decisions are his — present options and wait.
Cite every fact with an S-N and read date. Label claims Verified / Reported / Not publicly established / Inferred / Proposed / Simulated.
End with a dev-log entry and an updated progress file.
```

---

## Stage 1 · Confirm partner identity, brief version, requirements, business objectives and unknowns

**Purpose.** Be sure the right firm is researched and the right, current brief is the target; capture what the partner measures; list what the brief does not say.

**Inputs and prerequisites.** Riverside brief (path in §0.4); AEA brief; `{GAUNTLET}/artifacts/2026-10-13-hiring-partner-project-choice-and-deadlines.md` §0 and `open-questions.md` GQ-18/19/20; AEA register S-63; the portal card details; the AEA-assignment changes when Innocent supplies them. Prerequisite: none (read-only). **Do not create the project folder yet.**

**Concrete actions.**
- [ ] Hash both briefs again; compare with §0.4; if the portal shows a newer Riverside brief, Innocent supplies the file as a *new dated copy* (never overwrite).
- [ ] Re-read Riverside's regulatory disclosures and privacy policy; record URL, date read and the passage naming Riverside Partners L.L.C. d/b/a The Riverside Company. Confirm the domain and that RS2/Boston is excluded.
- [ ] Find the portfolio directory (URL, whether it is complete/filterable, whether current and realized are separated, entry count). Do **not** inventory companies yet.
- [ ] Extract the requirements into a draft **M-list** (one row per requirement; brief section; short verbatim excerpt; section anchor). Pull every business-context and impact-metric sentence into a draft **metrics tree** (north star → revenue → leading indicator → health metrics), each with the brief's own words.
- [ ] Build the **AEA–Riverside difference table** (start from §2.5); add any AEA-assignment changes.
- [ ] List **unknowns**: hiring team, deadline (GQ-20), shared submission (GQ-18), domain, timebox, what Riverside measures. Mark which are staff questions (Innocent asks) and which are public-research questions.
- [ ] Record interview/deadline facts as **partner** vs **internal**, never merged.

**Expected outputs and ownership.** The Stage 1 record in §0.4. After Stage 2, copied into: `docs/source/source-register.md` (S-1 provenance, S-2 disclosure), `docs/analysis/requirements-baseline.md` (**owner of M-NN**, draft), `docs/analysis/research-questions.md` (RQ-1…), the progress file.

**Required evidence and citation fields.** Brief: path, SHA-256, bytes, date received, portal date if known. Each requirement: M-ID · brief section · excerpt · anchor. Identity: URL · date read · passage · authority label (first-party company disclosure). Every unknown: RQ-N · who can close it.

**Completion checks.** Both hashes recorded and compared; every brief section appears in the M-list or is marked "not a requirement"; each business metric sentence appears once in the metrics tree; the difference table covers Tech Stack, LLM, Cloud, Model/data boundary and anything new; identity statement has a first-party passage; no company researched.

**Decisions Innocent makes — D-1 ★.** (a) Confirm the partner is The Riverside Company; (b) confirm the brief version to use; (c) whether to start now or wait for the AEA changes; (d) any portal facts only he can see.

**Claude may continue?** Continue through reading, hashing, diffing and drafting. **Wait** for D-1 if the identity or brief version is ambiguous, or if the AEA changes arrive mid-stage.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 1 of {PLAYBOOK}. Do not create {PROJECT}. Hash the Riverside and AEA briefs and compare with §0.4.
Re-read The Riverside Company's regulatory disclosures; record URL, date and passage. Find the portfolio directory
structure only (no company research). Draft the M-list, the metrics tree, the AEA–Riverside difference table and
the unknowns list. Write results into the §0.4 Stage 1 record and a draft requirements note I can paste into the
project at Stage 2. Then stop and ask me D-1.
```

---

## Stage 2 · Scaffold the research project

**Purpose.** Create the project with the right instructions, ownership map, evidence tracking and stage gates before any research.

**Inputs and prerequisites.** D-1 passed; project location chosen. This is a new coding repo under the root rule `{WS}/.claude/rules/new-project-zero-to-hero.md`, which makes the `zero-to-hero` Stage 0 the first action. **Hard stop: no design docs, tickets or feature code before `PROJECT-CHECKLIST.md` exists.** The user-scope hook `~/.claude/hooks/zero-to-hero-guard.py` injects Stage 0 when a new repo or `CLAUDE.md` appears.

**Concrete actions.**
- [ ] Create `{PROJECT}`; copy `PROJECT-CHECKLIST.md` from `{WS}/.claude/skills/zero-to-hero/templates/`; fill in project, kind (hiring partner), mode (light), started date, deadline fields as "unconfirmed".
- [ ] Write `CLAUDE.md` and `AGENTS.md` (entry points), `README.md`, `SUBMISSION.md`, and `.claude/README.md` (router: task → files to load).
- [ ] Copy **both halves of the principles pack**: rules into `.claude/rules/` (`agent-architecture`, `agent-tools`, `retrieval-and-context`, `verification-evals-observability`, `safe-validation-errors`, `synthetic-test-data`, `design-doc-defense` with scope line adapted, `system-design-conversation`, `gauntlet-hosting-default`, `html-files-not-artifacts` with location adapted, `hiring-partner-framing`, `project-provenance`) **and** `{GAUNTLET}/principles/` into `docs/principles/` (the rules cite GP IDs that live only there). Skip `legacy-integration-constraints` (OpenEMR only). Each copied rule starts with a provenance line.
- [ ] Write the project-specific `source-authority.md` (ranking table, numbered rules; Riverside identity; "a portfolio listing is not control"; "count companies, not locations"; the theme's decision boundary once chosen).
- [ ] Write the **owner map** ("Where facts live") in `CLAUDE.md`, one owner per fact (Appendix B).
- [ ] Create the folders in Appendix B; `.gitignore` for `docs/evidence/raw-reviews/` and `docs/evidence/raw-page-text/` (raw reviews contain reviewers' words and sometimes health or financial details).
- [ ] Copy the brief(s) unchanged into `docs/source/`; create the source register with the Stage 1 rows; create the RQ register and the ID-prefix registry.
- [ ] Copy §0.4 into `RESEARCH-PROGRESS.md`; copy this playbook to `docs/analysis/research-playbook.md` (keep the AEA copy).
- [ ] Add the project row to `{WS}/CLAUDE.md`'s index (required by the zero-to-hero rule). Create `{DEVLOG}`.
- [ ] `git init` locally only if Innocent says so. **No remote, no commit unless asked.** GitLab `origin` is created by Innocent, not Claude.

**Expected outputs and ownership.** The tree in Appendix B. Owners: `CLAUDE.md` (owner map), `PROJECT-CHECKLIST.md` (stage and gates), `SUBMISSION.md` (deliverables, dates), `docs/source/` (briefs, register), `RESEARCH-PROGRESS.md` (this playbook's state).

**Required evidence and citation fields.** Every copied rule: provenance line. Every `docs/principles` copy: source path and date.

**Completion checks.** `docs/principles/system-design.md` exists; checklist filled; owner map has no fact with two owners; `.gitignore` covers raw folders; brief copy hash equals the Stage 1 record; no research content yet; the AEA project is unchanged.

**Decisions Innocent makes — D-2 ★.** Project name and location; whether to `git init` now; whether Riverside gets its own dev-log folder (recommended); that nothing is committed.

**Claude may continue?** **Wait** for D-2 (location/name). After D-2, continue to the end of the stage, then stop for a progress report.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 2 of {PLAYBOOK}. Use the project location and name Innocent gave: {PROJECT}.
Follow zero-to-hero Stage 0 and the root new-project rule: PROJECT-CHECKLIST.md first, then CLAUDE.md/AGENTS.md,
both halves of the principles pack, project-specific source-authority.md, the owner map, folders, .gitignore,
unchanged brief copy with hash, source register, RQ register, RESEARCH-PROGRESS.md (copy §0.4), playbook copy,
dev-log folder and the root index row. No research, no commit, no remote. Report the tree and what is unticked.
```

---

## Stage 3 · Inventory the portfolio, document screening coverage and exclusions, group by shared onboarding themes

**Purpose.** Account for every company Riverside publicly lists, decide which are eligible, and group them by **shared onboarding workflow or customer problem** (not by Riverside's industry labels).

**Inputs and prerequisites.** Stage 2 done; portfolio URL from Stage 1; AEA method (§1.4.1) as the pattern.

**Concrete actions.**
- [ ] Define "eligible" in writing before screening (AEA: current/active label; exclude realized, team-prior-experience and non-operating relationships). Record that a public listing is not control, access or permission to deploy. Decide, and record, how "current" is determined on Riverside's site.
- [ ] Capture the directory page(s) in the page cache with date; enumerate every profile (name, profile URL, status label, investment date if shown, industry label, location, description, company website). Save the exact method or script.
- [ ] **Reconcile counts:** total = eligible + each excluded category. The sum must equal the directory's own number, or the gap is explained.
- [ ] For each eligible company, read the description and open the company site far enough to see **its customer entry path** (sign up / apply / book / quote / open an account / onboard a client). Record: who is onboarded, what is collected, what the next step is, and what documents are involved. If it cannot be seen, record "not established".
- [ ] Group by workflow: name each group by that workflow and write a one-paragraph **workflow card** (who, what is collected, what documents, what next step, why it might or might not suit the brief). Keep a group for "no visible onboarding workflow".
- [ ] For plausible groups read **representative service flows** on company websites and register them (AEA: S-25…S-35). Record coverage: how many companies per group were opened vs read from the description only.
- [ ] Sub-agent fan-out is fine (one per group or alphabetical chunk), followed by a single reconciliation pass.

**Expected outputs and ownership.** `docs/evidence/<date>-riverside-portfolio-inventory.json` (owner of the records and screening disposition); `docs/analysis/company-research/riverside.md` (firm context and counts; owner of portfolio counts); screening notes in `docs/analysis/portfolio-screening.md` (owner of method, exclusions, coverage); workflow cards inside it.

**Required evidence and citation fields.** Per company: name · source URL · status label · company website · screening disposition · workflow group · coverage depth (`description only` / `site opened` / `flow read`) · S-N for any page read · date read. Per exclusion: rule and count.

**Completion checks.** Counts reconcile; every eligible company has a group and a coverage depth; every exclusion has a stated rule; the inventory JSON validates and cites the directory; nothing says "no fit" where the truth is "not investigated"; a limits paragraph (stale directory; stakes unknown) exists.

**Decisions Innocent makes — D-3.** Accept the eligibility rule, the exclusions and the grouping scheme (or change them). Not a ★ gate; may be taken together with D-4.

**Claude may continue?** Continue into the Stage 4 draft, marking it provisional. Do not choose a theme.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 3 of {PLAYBOOK} for {PARTNER}. State the eligibility rule first. Cache the portfolio directory,
build the inventory JSON, reconcile counts to the directory's total, read each eligible company's customer entry
path, group by shared onboarding workflow with a workflow card per group, and record coverage depth for every
company. Use sub-agents per group if helpful, then reconcile. Do not choose a theme. Report counts, groups, and
what was not investigated.
```

---

## Stage 4 · Compare themes and present a recommendation

**Purpose.** Compare the workflow groups against the brief and recommend which theme the onboarding assistant should be researched around.

**Inputs and prerequisites.** Stage 3 outputs; the M-list and metrics tree; AEA criteria (§1.4.2); D-3 (or provisional).

**Concrete actions.**
- [ ] Fix the criteria **before** judging, in this order unless Innocent changes it: (1) fit with all required flows, with a real purpose for each collected field; (2) connection to the brief's business problem; (3) reuse across companies/locations; (4) a coherent demonstrator under the timebox and with the edge cases; (5) evidence quality; plus (6) domain-risk load and (7) availability of review evidence. State what a strong and weak score looks like for each.
- [ ] Judge each group with evidence cited; use 1–5 scores **and** a sentence, with weights set before scoring [R].
- [ ] Say what would **change** the recommendation; name the runner-up and why it lost; record limitations as in AEA.
- [ ] Present 2–4 concrete options with a recommendation first (single topic, no blank questions). Options may include "two themes", "general theme with a thin domain example", or "a group needing more screening".

**Expected outputs and ownership.** `docs/analysis/portfolio-fit-review.md` (owner of comparison, criteria, recommendation and limitations); a short options note in the chat or a Markdown file for the decision.

**Required evidence and citation fields.** Per judgment: group · criterion · score · evidence S-N or inventory reference · "Verified / Inferred". No criterion judged without a cited basis.

**Completion checks.** Every group appears; every score has a basis; runner-up and "what would change this" present; limitations stated; the recommendation is labelled a *research choice, not an approved PRD*.

**Decisions Innocent makes — D-4 ★.** Which theme (or none yet). Record as `Innocent ✓ date` in the checklist and progress file.

**Claude may continue?** **Wait.** Do not start Stage 5 until D-4 is recorded.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 4 of {PLAYBOOK}. Fix the criteria and weights first, then judge every workflow group with cited evidence.
Write docs/analysis/portfolio-fit-review.md. Present 2–4 options with a recommendation first, the runner-up, what would
change the answer, and the limitations. Stop and wait for my decision D-4. Do not begin Stage 5.
```

---

## Stage 5 · Select the company cohort with roles and sampling boundaries

**Purpose.** Choose which companies to research in depth, give each a defensible role, and fix exactly what will and will not be sampled. Adapt the research template for the theme.

**Inputs and prerequisites.** D-4 recorded; the chosen group's companies; AEA roles (§1.4.3).

**Concrete actions.**
- [ ] List every candidate company in the theme and what evidence is expected for each.
- [ ] Choose a cohort size from evidence, not from AEA's five. Assign each company a **role** with a reason (anchor / second configuration / benchmark / adjacent / other) and what could disqualify it.
- [ ] Count **platforms or companies**, not locations. Write the **location/branch selection rule** (for example: linked from the company's own page; has visible onboarding evidence; has enough public reviews).
- [ ] Set **sampling boundaries** per company: pages read, depth, how many locations, which review sources and sort modes, sample sizes, time window, and what is explicitly out of sample.
- [ ] Create the **Riverside research template** by copying `{AEA}/docs/aea-portfolio-research.md` and applying §2.4. Keep the original unchanged.
- [ ] Seed each `company-research/<company>.md` with role, sampling plan and empty Verified / Inference / Not-assumed / Open-questions sections.

**Expected outputs and ownership.** `portfolio-fit-review.md` §cohort and roles (owner); `docs/research-template.md` (owner of the research frame); `docs/analysis/company-research/<company>.md` skeletons (owners of per-company facts).

**Required evidence and citation fields.** Per company: role · reason · evidence expected · disqualifier · locations (with rule) · pages/sources in scope · sample sizes · S-N of the AEA/Riverside listing page. Template: list of corrections applied (§2.4 row numbers).

**Completion checks.** Roles unique and justified; counts are of companies; location rule is written; every boundary has a number; template shows all 14 corrections; no company is researched yet beyond the listing.

**Decisions Innocent makes — D-5 ★.** Cohort, roles, sampling boundaries and the corrected template.

**Claude may continue?** **Wait** for D-5.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 5 of {PLAYBOOK} for theme {THEME}. Propose a cohort sized from evidence, each company with a role,
reason and disqualifier; write the location selection rule and per-company sampling boundaries with numbers.
Create docs/research-template.md from {AEA}/docs/aea-portfolio-research.md applying playbook §2.4 (leave the AEA file alone).
Seed company-research skeletons. Present the cohort as options with a recommendation first, then wait for D-5.
```

---

## Stage 6 · Research company websites, published onboarding steps, documents and existing tools

**Purpose.** Establish what each company publishes about how a new customer starts, what they must provide, how they book or proceed, what tools exist, and what promises are made.

**Inputs and prerequisites.** D-5; skeleton profiles; research template; page cache tool.

**Concrete actions** (one worker per company is fine).
- [ ] Cache each page and document (HTML → text; PDF → text and the PDF; scanned pages → read visually and keep page images). Record URL, final URL, status, fetch date. Save the fetch script in the project.
- [ ] Capture the **entry path**: how a person finds out they are in the right place, requests care/service/an account, what personal, financial and document information is requested, which forms/portals/third-party tools appear, what is promised about timing, what happens after.
- [ ] **View-only on interactive tools**: record what is visible before any personal data is asked; **save a screenshot or DOM text** for every interactive check (AEA lost this for the AdaCare scheduler). Never submit, upload or create an account.
- [ ] Classify every published tool by **job** (adapt the AEA four: contact capture · scheduling or next step · administrative onboarding · ongoing coordination). Write "exists" only; do not infer failure or integration.
- [ ] Record **published promises, fees and policies** as quotes with exact wording (AEA found three phrasings of one scheduling aim) and note conflicts between pages.
- [ ] Count footprints with the method stated (machine count vs company statement; the AEA ADC counts differed by two).
- [ ] If a site blocks automated reading (a bot check), apply `~/.claude/rules/anti-bot-tooling.md`: use the ordinary-fingerprint driver (`stealth-chrome`), **view only**, and do not solve interactive puzzles on Innocent's behalf. The AEA Commonwealth site needed this.
- [ ] Write each profile: Verified public facts · Our interpretation · What we must not assume · Open questions (new RQ-N).
- [ ] Register every source in the S-N register; correct the register if a later reading differs (new date, never overwrite).

**Expected outputs and ownership.** `docs/evidence/raw-page-text/<co>/…` (cache, git-ignored); `company-research/<company>.md` (owner of company facts); register rows; RQ additions.

**Required evidence and citation fields.** Each fact: S-N · URL · date read · scope (company-wide, or one location) · exact quote or passage anchor · label. Each tool: name · job · where seen · "documented / viewed / not tested".

**Completion checks.** A script or reviewer confirms every quotation in profiles appears in the cache; every number reproducible from the cache; each profile has all four sections; every "not publicly established" lists the pages looked at; location evidence is labelled as that location's; no form was submitted.

**Decisions Innocent makes.** None unless blocked (login wall, challenge, consent screen, paywall). Blockers are reported with what was attempted.

**Claude may continue?** Continue. Stop and report on a blocker, or after 2–3 failed attempts at the same page.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 6 of {PLAYBOOK} for the approved cohort in {PROJECT}/docs/analysis/portfolio-fit-review.md.
One worker per company. Cache pages with dates; view forms and tools only (save a screenshot or DOM text of every
interactive check); classify every tool by job; quote promises exactly; write each profile in the four-section form;
register all sources. Verify every quotation against the cache. Report blockers, do not work around consent or login walls.
```

---

## Stage 7 · Collect and analyze relevant customer-review evidence

**Purpose.** Capture attributed customer experience at the sampled locations, without turning it into rates, causes or network-wide claims.

**Inputs and prerequisites.** Cohort and locations (D-5); Stage 6 started (needed to know which location is which company page); review-source decision.

**Concrete actions.**
- [ ] **Decide the sources and sample sizes before collecting (D-7).** AEA used Google review dialogs because the cohort was clinics. Choose by theme (for example Google Business for local sites; app stores, G2/Capterra or Trustpilot for software or financial products). Record why, and what each source cannot show.
- [ ] Collect by script, one browser tab at a time (a Google bot check appeared when five tabs were opened together). Sort modes: **Lowest** and **Newest**, plus a balanced slice (Highest or random) [R] so positives are not an afterthought.
- [ ] Do **not** extract reviewer names. Save raw JSON per listing: `place`, `read` date, sort, count, star counts, reviews (`stars`, `date`, `owner_replied`, `text`). Git-ignore the folder.
- [ ] Record for each sample: listing name → company location mapping; rating and review count at read time; sort; number loaded; whether the **low tail was fully captured**; overlap between samples; owner-reply counts; solicited-review signature (many 5★ in a week with owner replies).
- [ ] Code themes with a **saved script** (adapt `themes.py`): denominator = ≤3★ with text, de-duplicated on stars + date + first 80 characters; never add overlapping samples; counts are indicators. **Flag star–text mismatches** (AEA's FOH sample had a 1★ with positive text) and leave them out of the denominator or footnote them [R].
- [ ] Label **each cited review**: customer status (new / established / unclear), journey stage, whether it is direct, indirect or uncertain onboarding evidence, relative age at read. Separate first-time onboarding from ongoing service.
- [ ] Preserve positive reviews as "behaviours to preserve".
- [ ] Quote exactly with "[…]" and "[name]"; paraphrase identifiable personal, health or financial narratives; mark machine translations. **Verify every quote against raw with a saved script** [R].
- [ ] Do **not** use AI summaries, employee ratings, or reviews of other businesses.

**Expected outputs and ownership.** `docs/evidence/raw-reviews/*.json` (git-ignored); `scripts/themes.py` and `scripts/verify_quotes.py` (project); `docs/analysis/<date>-review-evidence.md` (owner of samples, excerpts, counts, status labels).

**Required evidence and citation fields.** Per excerpt: S-N (listing) · location · stars · relative date at read · sample (Lowest / Newest / …) · customer status · journey stage · use-as-evidence (direct / indirect / uncertain) · exact text or paraphrase flag.

**Completion checks.** Re-running the theme script reproduces every published count; the quote script passes; every denominator is stated; no reviewer name appears; star–text mismatches are handled; the status table covers every cited review; limits section states that reviews are one person's report, not prevalence.

**Decisions Innocent makes — D-7.** Review sources and sample sizes (before collection).

**Claude may continue?** Continue after D-7. Stop on a bot check that needs a human.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 7 of {PLAYBOOK}. First confirm D-7 (sources and sample sizes). Then collect reviews for the sampled
locations one tab at a time, without reviewer names, saving raw JSON (git-ignored). Code themes with a saved script,
flag star–text mismatches, label every cited review by customer status, journey stage and evidence use, keep positives,
verify every quote against raw with a saved script, and write the review-evidence document with exact denominators.
Do not claim prevalence, cause, or network-wide patterns.
```

---

## Stage 8 · Research reference onboarding journeys and applicable guidance

**Purpose.** Build a reference model of what good onboarding looks like for the theme, from authoritative guidance and published peer journeys, so companies are compared with good practice rather than with an assumption.

**Inputs and prerequisites.** D-4 (theme); Stage 6 profiles (to map stages); AEA baseline structure (§1.4.6).

**Concrete actions.**
- [ ] Find the theme's authorities: professional associations, regulators, standards bodies, accessibility guidance, and published peer journeys. Open each source; record the exact passage and scope. Label each PROFESSIONAL-GUIDANCE / PRIMARY-GUIDANCE / PRIMARY-LAW / PRIMARY-VENDOR / CONTEXT-PEER.
- [ ] Exclude and **note** sources that 404, redirect inconsistently or cannot be opened.
- [ ] Write: an evidence-category table (what each source type establishes and cannot); a **common journey** table (stage · customer needs · administrative work · assistant's possible role · what stays with humans); service-specific reference sequences; a **candidate-baseline** table, each row with source and "what to check in a demonstration"; the **boundary** section (what the assistant never decides); privacy and cost distinctions that matter for the theme; three synthetic evaluation situations.
- [ ] State that timing is flexible and that guidance is not a mandate.
- [ ] Open RQ-N for decisions this exposes (AEA: RQ-44 context, RQ-45 completion, RQ-46 notices).

**Expected outputs and ownership.** `docs/analysis/<date>-journeys-and-onboarding-baseline.md` (owner of the reference journey and baseline); register rows.

**Required evidence and citation fields.** Per baseline row: S-N · authority label · passage and scope · "recommended practice, not a requirement" · demonstration check.

**Completion checks.** Every baseline row has a source; guidance is never presented as a company's practice; peer examples are marked CONTEXT-PEER; excluded sources are listed; the boundary section agrees with `source-authority.md`.

**Decisions Innocent makes.** None here; the boundary decisions are D-9.

**Claude may continue?** Continue.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 8 of {PLAYBOOK} for theme {THEME}. Find and open the theme's authoritative guidance and published peer journeys.
Write the reference-baseline document: evidence-category table, common journey table, service-specific sequences,
candidate-baseline table with demonstration checks, boundary section, and three synthetic situations. Register every
source with authority and read date; list sources excluded and why. Do not describe any company's private workflow.
```

---

## Stage 9 · Synthesise the company comparison, friction patterns, reusable core, variations, business hypotheses and synthetic scenarios

**Purpose.** Turn evidence into an honest comparison and a set of hypotheses without claiming gaps, measurements or ROI that the evidence does not support.

**Inputs and prerequisites.** Stages 6, 7, 8 complete or reconciled; corrected research template.

**Concrete actions.**
- [ ] Write the report in the template's order, applying §2.4. Parts: company intelligence · services and pathways · positioning and promises · current journey · friction · opportunity matrix (only as allowed by D-9) · configuration-relevant facts (annex) · gap and business-impact matrix · revenue hypotheses · synthetic scenarios (annex) · unknowns · recommendations · closing checklist.
- [ ] Define "gap" in the document: a **difference from the reference baseline or a reported problem**, never a proven deficiency. Keep **three baselines apart**: reference practice, company current state, measured performance (unknown unless a company supplies it).
- [ ] Interpret reviews in a **pitfalls document**: pitfalls table (what reviewers reported and where · baseline expectation · possible response · what would need to be proved), positives to preserve, what reviews support less directly, the patient/customer questions the product must answer.
- [ ] State the **reusable core** versus **company variation** (configuration) versus **not portable by configuration**.
- [ ] Write **business hypotheses** as hypotheses with the chain of cause and effect, the metric, and the baseline needed; illustrative numbers labelled illustrative.
- [ ] Write **synthetic scenarios** (`SIM-<company>-n`), clearly fictional, mapped to published facts and marked as simulated.
- [ ] Raise the **scope-boundary questions as options** (AEA's RQ-44/45 analogues): what optional context, if any, may be collected; where intake starts and ends; whether established customers or ongoing service are in scope; what counts as "complete".

**Expected outputs and ownership.** `<date>-onboarding-research-report.md` + annexes (owner of the comparison, configuration facts, scenarios); `<date>-review-pitfalls-and-solution-opportunities.md` (owner of the review interpretation); RQ updates.

**Required evidence and citation fields.** Every finding: label (Verified / Reported / Not publicly established / Inferred / Proposed / Simulated) · S-N or section of the owner document. Each hypothesis: mechanism · metric · baseline required · owner of the baseline.

**Completion checks.** No claim of deficiency, integration or ROI without a Verified basis; every "Reported" cites the status label; the gap definition and three baselines appear; scenarios are synthetic; every template requirement is mapped in an audit appendix with an honest status ("covered with public evidence", not "complete").

**Decisions Innocent makes — D-9 ★.** The scope-boundary questions above, as options with a recommendation.

**Claude may continue?** Continue drafting. **Wait** for D-9 before finalising scenarios or anything the boundary affects.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 9 of {PLAYBOOK}. Using the Stage 6–8 outputs and docs/research-template.md, write the research report,
configuration annex, synthetic scenarios and the review pitfalls document. Define "gap" and keep the three baselines apart.
Raise the scope-boundary questions as options with a recommendation first (D-9) and do not finalise scenarios until I answer.
```

---

## Stage 10 · Audit the brief and reconcile evidence, contradictions and open questions

**Purpose.** Find where the brief asks for something risky or self-contradictory, and make every document agree with every other.

**Inputs and prerequisites.** **10a** (brief audit) can begin after Stage 2. **10b** (reconcile) follows Stages 7–9 and D-4/D-9.

**Concrete actions.**
- [ ] **10a. Audit.** Start from the AEA audit as a *list of candidate issues only*. Re-read the Riverside brief; for each T item re-open the primary source, record the date read, and keep, narrow or drop it. Add Riverside-specific items: Anthropic's terms for data sent to a hosted model, the PII-field disclosure the brief requires, free choice of stack, any regime the chosen theme triggers. Write **C items** with verbatim excerpts and section anchors; separate direct contradictions from ambiguities and conditional tensions. State the "real problem" in the partner's own metric and the "real guideline" from primary sources.
- [ ] **10b. Reconcile.** Build a contradictions table across all documents: claim · where · where else · resolution · owner · date. Recheck every superseded claim; add "superseded" banners; apply the ripple rule. Re-open any claim whose sample, date or scope has changed. Update RQs: closed, partly answered, new.
- [ ] Record which audit decisions belong to the PRD, not to research.

**Expected outputs and ownership.** `<date>-brief-audit.md` (owner of T and C); a reconciliation log in the dev log and the contradictions table in the audit or a separate `reconciliation-log.md`; `research-questions.md`.

**Required evidence and citation fields.** T: priority · brief anchor + excerpt · finding · primary source (S-N) + passage · conditional/confirmed/narrowed · proposed response · evidence to close. C: paired excerpts · consequence · proposed reading · clarification question.

**Completion checks.** Every T/C cites the Riverside brief text; every external source re-read with a date; no T presented as an implemented defect; each contradiction has an owner and resolution; counts of T/C/RQ are unique and consistent across files; the brief hash still matches.

**Decisions Innocent makes.** None for research; PRD decisions listed for later.

**Claude may continue?** Continue.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 10 of {PLAYBOOK}. 10a: re-audit the Riverside brief using the AEA audit only as candidate issues; re-open every
primary source; add Riverside-specific items (hosted-model data terms, the PII-field disclosure, stack choice, theme regime).
10b: build a contradictions table across all project documents, apply the ripple rule, add superseded banners, update RQs.
Verify T/C/RQ/S counts and the brief hash.
```

---

## Stage 11 · Generate the complete candidate inventory, mandatory baseline, parked ideas, ranking and shortlist

**Purpose.** Produce the auditable set Innocent will choose from.

**Inputs and prerequisites.** Stages 9–10; the M-list from Stage 1/2; D-9.

**Concrete actions.**
- [ ] Finalise the **mandatory baseline** (M-NN) from the Riverside brief; note project rules that always apply.
- [ ] **Harvest** candidates from every source (report gaps and recommendations, baseline candidate table, pitfalls, brief stretch items, company-published ideas); keep a **harvest log** (candidate → origin) [R].
- [ ] Normalise each candidate: ID · name · type (Complete / Supporting) · job · specific problem · company/location examples · evidence strength E · expected value (hypothesis) · effort and dependency.
- [ ] **De-duplicate** by merging overlaps; never split to reach a round number; keep a merge log.
- [ ] **Park** with a kind and a reason: unresolved scope decision · unsupported by evidence · out of scope · no access · prohibited by rule. Parked ideas are not in the denominator.
- [ ] **Propose the rubric and selection parameters** (Part 4.5) and **stop for D-11** before scoring: criteria, weights, E scale, denominator definition, rounding rule, tie-break order, whether Supporting candidates are in the pool.
- [ ] After approval: score every candidate with a **one-line rationale per cell** [R]; compute with a saved script; apply tie-breaks; run a **sensitivity check** (rank change when a weight moves ±5, or when E is re-scored from the status labels) [R].
- [ ] Shortlist the top `round(0.40 × N)`; compute the selection target `round(0.20 × N)` from the **same N**. Show exact and rounded values.
- [ ] Write an **evidence card** for each shortlisted candidate (Part 4.6); a problem-confidence vs solution-confidence table; tradeoffs; dependencies; combination notes; interview explanations in research tense; the evidence-status ledger (all "pending"); a **blank** selection area.

**Expected outputs and ownership.** `<date>-solution-selection-and-evidence-matrix.md` (owner of M · SOL · P IDs, rubric, scores, shortlist, cards, selection record); `requirements-baseline.md` links to it or owns M-NN (one owner only).

**Required evidence and citation fields.** Part 4.6 for every card; for every score cell a rationale; for every parked idea kind + reason + RQ/rule link.

**Completion checks.** N, shortlist and target arithmetic reproduced by script; rubric weights sum to 100; scores recompute; ranks non-increasing; every card has every chain link; no selection recorded; the three baselines are labelled.

**Decisions Innocent makes — D-11 ★.** Rubric, weights, E scale, denominator, rounding, tie-break order, pool rules — **before scoring**. A later optional review of the shortlist.

**Claude may continue?** Continue to the rubric proposal, then **wait** for D-11. After approval, continue to the matrix.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 11 of {PLAYBOOK}. Finalise the mandatory baseline, harvest and normalise candidates with a harvest log and merge log,
and propose parked ideas. Then STOP and present the rubric parameters (criteria, weights, E scale, denominator, rounding, tie-break order,
pool rules) for my approval (D-11). After approval, score with one-line rationales, compute by script, apply tie-breaks, run a sensitivity check,
build the shortlist and evidence cards, ledger and a blank selection area. Do not record any selection.
```

---

## Stage 12 · Audit evidence chains and document consistency

**Purpose.** Prove that every shortlisted card can be walked back to evidence and that no document contradicts another before a dashboard freezes the data.

**Inputs and prerequisites.** Stage 11 done. **Use an independent reviewer** (a different session or a sub-agent that did not write the matrix) [R]. In AEA the author audited the author.

**Concrete actions.**
- [ ] For each shortlisted card, walk the chain link by link (Part 4.6) and fill an audit table (✓ with source, or ✗ with a repair).
- [ ] Walk **three cards backwards to raw files** (like §1.6) and record what was opened.
- [ ] Mechanical checks by script: IDs unique; every `S-N` is registered; every `RQ-N` exists; local links resolve; section anchors exist; counts and denominators agree across files; scores recompute; brief hash unchanged; no reviewer or staff names; no real personal data; every quote matches raw.
- [ ] Check labels: every review claim has a status label; every benefit is a hypothesis; every "gap" follows the definition; no existing tool is described as a failure.
- [ ] Repair findings in the **owner**, then dependents (ripple rule); log.

**Expected outputs and ownership.** An appendix "Evidence-chain audit" in the matrix; `scripts/audit_*.py`; a dev-log entry; list of repairs.

**Required evidence and citation fields.** Audit table rows: candidate · each chain link · source · result · repair.

**Completion checks.** Zero ✗ remaining or each recorded as a known gap; script outputs saved; the independent reviewer's name/model recorded.

**Decisions Innocent makes.** None.

**Claude may continue?** Continue.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 12 of {PLAYBOOK} as an independent reviewer of the Stage 11 matrix (you did not write it). Walk each shortlisted card
through the evidence chain and three cards back to raw files. Run the mechanical checks by saved script. Repair findings in the owner
documents first, then dependents. Add the audit appendix and a dev-log entry. Report what remains uncertain.
```

---

## Stage 13 · Generate and verify the local HTML dashboard

**Purpose.** Give Innocent one place to inspect evidence, compare options and draft a selection. It is a decision aid; the matrix remains the record.

**Inputs and prerequisites.** Stage 12 complete; matrix frozen; Part 5 spec.

**Concrete actions.**
- [ ] Build `docs/artifacts/<date>-solution-selection-dashboard.html` as one self-contained file: `<!doctype html>`, `lang`, charset, viewport, `<title>`, inline CSS/JS, light and dark themes, a skip link, no network assets. **Local file; never the Artifact tool.**
- [ ] Generate the data from the matrix with a script where possible (Part 5.3); otherwise transcribe and add a **parity script**.
- [ ] Implement every capability in Part 5.1.
- [ ] Run the verification matrix in Part 5.4 and fix defects; record each check as completed, partial or not done.
- [ ] Link the dashboard from the matrix header with the line "browser selections are drafts; §6 and the ledger are the record".

**Expected outputs and ownership.** The HTML; `scripts/build_dashboard.py` (if used); `scripts/check_dashboard_parity.py`; verification results in the dev log and the matrix header.

**Required evidence and citation fields.** Every source link `S-N` with URL and read date; local locations as **section** citations, not line numbers.

**Completion checks.** Part 5.4 table with no unexplained "not done"; parity script passes; storage key is project-specific; exports contain drafts only; no external requests; opens from `file://`.

**Decisions Innocent makes.** None yet; he reviews the dashboard next.

**Claude may continue?** Continue, then report the path and `open "<path>"` command.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 13 of {PLAYBOOK} using Part 5. Build the self-contained local dashboard from the frozen matrix (script-generated data
plus a parity script). Implement every listed capability, then run and record the full verification matrix, fixing defects.
Do not use the Artifact tool. Report the absolute path, how to open it, and every check that was completed, partial or not done.
```

---

## Stage 14 · Record Innocent's choices and unresolved dependencies, then hand off

**Purpose.** Turn his selection into a recorded decision without inventing any, and hand off for the "is research done?" call.

**Inputs and prerequisites.** Stage 13; Innocent has inspected the dashboard.

**Concrete actions.**
- [ ] Innocent chooses (about `round(0.20 × N)` candidates; the percentage is an aid, not a limit). He may export the draft (Markdown/JSON) or state the IDs.
- [ ] Record **only** what he states, in the matrix selection area and ledger "Selected by Innocent" with the date; keep Implemented / Demonstrated / Validated as "pending".
- [ ] List **unresolved dependencies** (for example a candidate that needs another not chosen) as information, and ask — do not add the companion silently.
- [ ] List open decisions and RQs that remain; update `PROJECT-CHECKLIST.md` research lines (not the gate).
- [ ] Regenerate the dashboard so its "recorded" column matches the matrix, then re-run the parity script.
- [ ] Write the **handoff note**: what is decided, what is open, risks, and the single next decision — *is research complete?* Innocent alone says so; only then may a PRD/framing document begin.
- [ ] Dev-log entry; progress file updated.

**Expected outputs and ownership.** Matrix §selection + ledger (owner of the record); handoff note in the dev log; checklist rows; regenerated dashboard.

**Required evidence and citation fields.** Each recorded choice: ID · date · "Innocent ✓" · source (dashboard export file name or chat date).

**Completion checks.** No selection exists that he did not state; dashboard ledger equals matrix; dependency list present; no PRD, design, tickets or code were started.

**Decisions Innocent makes — D-14 ★.** The selections; which dependencies to accept; whether the research is complete.

**Claude may continue?** **Wait** for his selections and the completion call.

**Ready-to-use instruction.**

```text
[common preamble]
Execute Stage 14 of {PLAYBOOK}. Here are my selections: <IDs, or the exported draft file>. Record exactly these in the matrix selection area
and ledger with today's date; do not add or infer others. List unresolved dependencies and open decisions as information and ask about each.
Regenerate the dashboard and re-run the parity script. Write the handoff note and dev-log entry. Do not start a PRD, design, tickets or code.
```

---

# Part 4 · Evidence and selection standards

## 4.1 The seven kinds of statement, and what each may establish

Every sentence in a research file is one of these. A reader must be able to tell which.

| Kind | AEA label / authority | Example (AEA) | May establish | May **not** establish |
|---|---|---|---|---|
| **Issued requirement** | ISSUED; "M-NN" | "≥ 90% field-level OCR accuracy on 30 labeled documents" (brief, AI Metrics) | What gets graded | That a company needs the feature |
| **Published fact** | CONTEXT-AEA / CONTEXT-CO; "Verified" | Commonwealth FAQ: "Treatment for worker's compensation needs authorization before scheduling" (S-12) | What an organisation *publishes*, for that page and entity | How it operates internally; that it applies network-wide; that it works |
| **Attributed review experience** | EVIDENCE; "Reported" | A 2★ Forest Hills review: expected email/text and directions did not arrive (S-91) | That one person reported this at that location on that date | Frequency, technical cause, a vendor, a network pattern |
| **Professional / regulatory guidance** | PROFESSIONAL-/PRIMARY-GUIDANCE, PRIMARY-LAW, PRIMARY-VENDOR | AHRQ Tool 21: referral responsibilities and tracking (S-114) | A *reference baseline* | That a company falls short; a legal duty in a particular deployment |
| **Inference** | "Inferred" | "The complaints are about what happens after the request is captured" | A hypothesis, with what it rests on | Anything a reader should rely on without validation |
| **Proposal** | "Proposed" | "A confirmation generated only from a stored booking" (SOL-007) | What we would build or test | That it works, or that anyone asked for it |
| **Unknown** | "Not publicly established" + RQ-N | Who owns new-patient intake follow-up (RQ-4) | That we looked and did not find it | That it does not exist |

A **synthetic** scenario or number is a seventh-and-a-half category: always labelled "Simulated", never shown as company data.

## 4.2 Citation fields

**For every fact** in a profile, report or card:

| Field | Rule |
|---|---|
| Source ID `S-N` | Resolves in the register |
| URL | Live URL; Google review dialogs have no stable URL, so cite the search route and say so |
| Date read | The date *this fact* was read, not the report date |
| Scope | Company-wide, platform, or a **named location** |
| Anchor | A short exact quote, or the page section/PDF page |
| Label | Verified / Reported / Not publicly established / Inferred / Proposed / Simulated |
| Cache path | Local file for the page text (git-ignored), when one exists |

**For every review excerpt**, add: stars · relative age at read · sample (Lowest / Newest / …) · customer status (new / established / unclear) · journey stage · evidence use (direct / indirect / uncertain).

**For local cross-references** use document + section name (not line numbers). AEA replaced 71 line citations because lines drift, but the dashboard kept its own and they went stale (§1.4.11).

## 4.3 Disciplines carried forward, with the rule and how to apply it

| # | Discipline | Rule | How it looked in AEA | Apply to Riverside |
|---|---|---|---|---|
| 1 | Separate the seven kinds of statement | §4.1 | Verified / Reported / Not publicly established / Inferred / Proposed / Simulated labels in every table | Use the same labels in templates; reject unlabeled claims at Stage 12 |
| 2 | Reference practice ≠ current state ≠ measured performance | Three baselines, kept apart in every card | "Three meanings of baseline" block at the top of the matrix | Same block in the Riverside matrix; "Measured baseline: unknown" until a company supplies data |
| 3 | Count platforms, not locations | A branch is a reuse site, not an extra company | "four platforms plus one adjacent"; AdaCare ≠ ADC | Count companies (or the theme's equivalent), not offices, branches or sites |
| 4 | A public listing ≠ control, access or deployment permission | "Current" is a website label; it can be a minority stake | Fit review §9, AEA context §2 | Same for Riverside's portfolio page; never say "Riverside can roll this into X" |
| 5 | An existing tool ≠ a gap | Present tools by job; complement, don't replace | Four-job table; P-10 | Same. A form, portal or chatbot is a system to learn from |
| 6 | Reviews: location, date, sample, overlap, status, stage; first-time ≠ ongoing | Review §0, §7 | Louisville South vs Elizabethtown; "established" tags | Same fields (Stage 7) |
| 7 | Keep positives | Positive reviews are behaviours to preserve | Reminder calls, clinician explanations | Collect a balanced sample; record strengths in the pitfalls document |
| 8 | No prevalence, no technical cause from selected reviews | "Indicators, not rates"; "cause not established" | Six "AI" reviews + one "robot" ≠ a vendor | State it in every card |
| 9 | Benefits and ROI are hypotheses until measured | Mechanism + metric + baseline needed | "illustrative"; "no performance chart is shown because no performance data exists" | Same; claim-growth ladder (§4.8) |
| 10 | Domain boundary adapted to the theme | Say what the assistant never decides | Administrative only; no triage, no coverage approval, no referral bypass | §4.7 |
| 11 | Synthetic personal data only | Obviously fictional; reproducible | `SIM-CPS-1 "Avery Testcase"`; no real ID layout (RQ-17) | §4.9 |
| 12 | One owner per fact | Link, do not copy | Owner table in `CLAUDE.md` | Appendix B |
| 13 | Never edit an issued document | New dated copy + register row | Brief SHA-256 | Same for Riverside's brief |

## 4.4 Review evidence standard (summary; the procedure is Stage 7)

Source and platform · listing → company-location mapping · rating and count at read · sort modes and sample sizes · whether the low tail was fully captured · overlap between samples · owner-reply counts · extraction method and script version · denominator rule · keyword-coding script · patient/customer status table · exact-quote rule · privacy rule (no names; raw files git-ignored; paraphrase identifiable narratives) · explicit non-uses (AI summaries, employee ratings) · star–text mismatch handling [R] · balanced sample [R].

## 4.5 The weighted rubric, formula, tie-breaks, dependencies and percentages

### AEA's rubric (matrix §3) — historical, reusable as a default

| Criterion | Weight | What a 5 meant in AEA |
|---|---|---|
| **E** Evidence strength and directness | 20 | Direct reports at ≥2 platforms plus published workflow |
| **P** Importance of the problem | 20 | Blocks or delays a first visit, or damages trust |
| **F** Fit with the brief and the scope boundary | 20 | Serves a brief requirement or stated problem; no clinical judgement |
| **D** Demonstrable within the timebox with synthetic data | 15 | Clear pass/fail demo, little extra infrastructure |
| **R** Reuse across portfolio companies | 15 | Applies to all five platforms |
| **I** Low effort and low integration/operational dependency | 10 | Small build; no company systems or new staff process |

**Formula.** `Score = Σ (weight × score ÷ 5)`, scores 1–5, maximum 100. [V] I recomputed all 19 AEA scores from the table with this formula: 0 differences. Example: SOL-001 = 20·5/5 + 20·5/5 + 20·5/5 + 15·4/5 + 15·5/5 + 10·3/5 = 20+20+20+12+15+6 = **93**. The result is "a research judgement, not measured ROI".

**Evidence scale E (AEA):** 5 direct attributed reports at ≥2 platforms plus a published workflow · 4 direct reports at one platform, or a published requirement at ≥3 platforms, plus guidance · 3 published workflow or guidance with indirect/single reports · 2 derived from the brief or our analysis only · 1 speculative. **Adapt** the wording to "customer/company/platform" and to the theme's review availability; re-state it before scoring.

**Rank order.** Descending score. Ties are broken by the rule in force *before* the cut is made.

### AEA's tie-breaks (matrix §3), shown so the pattern is visible

| Tie | Broken by |
|---|---|
| SOL-005 over SOL-011 (83) | Fit with the brief (F 5 vs 4) |
| SOL-006 over SOL-014 (82) | A complete solution with stronger problem evidence (E 4 vs 3); SOL-014 mainly supplies content to a mandatory item |
| SOL-008 over SOL-018 (76) | Evidence |
| SOL-009 over SOL-012 (75) | Evidence and importance |
| SOL-013 over SOL-017 (63) | A brief stretch item |

These were applied **after** scoring and differ by pair. The cut at 8/9 was a tie "broken by judgement". **[R] For Riverside, fix the order before scoring (D-11)**: for example (1) higher E, (2) higher F, (3) higher P, (4) lower effort; and state what happens if a tie still straddles the cut: either include both (the shortlist grows by one) or keep the lower-effort one and record the other as the "closest excluded candidate".

### Dependencies

AEA wrote each dependency once in the matrix (§2 "Dependencies to check") and again as machine rules in the dashboard (`DEPS`): `SOL-001 → SOL-002` · `SOL-006 → SOL-002` · `SOL-011 → SOL-002` · `SOL-003 → SOL-002 or SOL-018` · `SOL-008 → SOL-007` · `SOL-013 → SOL-012` · `SOL-009 → SOL-002`. Also "builds on / extends" a mandatory item (`MAND_NOTES`) and overlap notes (`OVERLAPS`). A selection that picks a dependent without its companion is **flagged, not corrected**; the companion counts as part of the pick (information only). **[R]** Keep these in one machine-readable block in the matrix so the dashboard can read them.

### The 40% / 20% defaults, with explicit denominators and rounding

| Quantity | AEA value | Rule |
|---|---|---|
| **Denominator N** | **19** | Eligible discretionary candidates only. Excludes the 15 mandatory items and the 11 parked ideas. The AEA matrix says "overlapping ideas merged; nothing split to reach a round number" |
| **Shortlist** | **8** | `40% × 19 = 7.6 → rounded to the nearest whole number = 8` |
| **Selections reserved for Innocent** | **4** | `20% × 19 = 3.8 → 4`, taken from **the same N** (not from the shortlist's 8) |
| Parked | 11 | Not ranked, not counted |

**Reusable defaults for Riverside [R]:**

- `shortlist = round_half_up(0.40 × N)`; `selection target = round_half_up(0.20 × N)`; show both the exact value and the rounded value in the document. At these two percentages an exact half can never occur for integer N (it would need `4N` odd), but the rule must still be written because another percentage might be chosen.
- Add bounds so tiny pools do not collapse: for example `shortlist ≥ 3` and `shortlist ≤ N`. State them in D-11 rather than discovering them.
- The **pool definition** (what counts as eligible) is part of D-11: are "Supporting" candidates in? (AEA: yes, six of 19 were Supporting.) Do candidates that merely extend a mandatory item stay in? (AEA: yes, with a note.)
- The target is a decision aid. AEA's dashboard states "you are N over the approximate target; that is allowed".
- **Do not force Riverside to 19, 8 or 4.** If the evidence yields 11 defensible candidates, the numbers are 4 and 2.
- State where selections come from. AEA's matrix §6 offered only the eight shortlisted candidates, but its dashboard allowed any of the 19 to be drafted. Choose one rule and make the matrix and dashboard agree.

## 4.6 The evidence chain every shortlisted candidate must contain

```
Partner/platform → company or location → onboarding stage → reference practice →
published or reported current state → problem → proposed capability → mechanism →
dependencies → synthetic pass/fail demonstration → business metric → remaining uncertainty
```

AEA's card used a nine-link chain (`AEA platform → practice/branch → journey stage → reference baseline → evidenced problem → proposed solution → improvement mechanism → proof → outcome to measure`). The requested chain adds **dependencies** and **remaining uncertainty** as links; AEA's cards held them as separate bullets ("Dependencies and limits", "Reason to defer"). Use this template and fill every field or write "none found".

| Field | Content | Source rule |
|---|---|---|
| **ID · name · rank · score · E** | | matrix |
| **Type · job** | Complete / Supporting; the job it addresses | |
| **1 Partner / platform** | Listing + `S-N` (public listing only; no control claim) | Part 4.3 #4 |
| **2 Company or location** | The named office, branch or site; first-party link | scope rule |
| **3 Onboarding stage** | A stage of the reference journey | Stage 8 doc, by section |
| **4 Reference practice** | Guidance and `S-N`; "does not show the company falls short" | PROFESSIONAL/PRIMARY label |
| **5 Published or reported current state** | Published fact(s) with `S-N` and date; attributed review(s) with status label; "cause not established" | §4.2 |
| **6 Problem** | One sentence, plus a concrete example | |
| **7 Proposed capability** | What a customer and staff would experience (**Proposed**, not built) | |
| **8 Mechanism** | Why it could address the problem | |
| **9 Dependencies** | Candidates and mandatory items it needs; unknown ownership/rules (RQ-N) | |
| **10 Synthetic pass/fail demonstration** | Scenario ID + numbered pass conditions, including negative conditions (e.g. "never shows 'approved'") | |
| **11 Business metric** | Synthetic metric; company metric; **measured baseline: unknown (RQ-N)** | |
| **12 Remaining uncertainty** | What is unproven; reason to choose; reason to defer | |
| **Problem confidence** | High / Medium / Low, with the evidence that sets it | **kept separate** |
| **Solution confidence** | High / Medium / Low, with the evidence that sets it | **kept separate** |
| **Selection** | `☐ (Innocent)` — blank | |

**Keep problem confidence separate from solution confidence.** AEA's table shows why: SOL-004's data are certainly required (high) but typing them is only a thinly reported pain (low-medium) while OCR accuracy is testable (solution medium-high). Never merge them into one adjective.

## 4.7 Domain boundaries for the chosen theme

Write the boundary as numbered rules in the project's `source-authority.md` at D-4/D-9. Pattern from AEA: *the product never makes a determination that belongs to a qualified human or institution; a completed intake summary is a record of what was said, not a decision.* Examples of the pattern (replace with the theme's real equivalents):

- **Healthcare (if chosen):** carry forward the **administrative-only** safeguards: no diagnosis, urgency triage, treatment recommendation, insurance approval, coverage promise or referral bypass; booking respects prerequisites; clinical questionnaires stay with the care team; any optional patient-reported context is allowed only under an explicitly agreed collection policy (AEA's unresolved RQ-44).
- **Another regulated theme:** list the decisions the assistant must never make (eligibility, approval, identity verification outcome, pricing/quote commitments, legal or tax advice, a right-to-work or credit determination, etc.), what stays with staff, and which conditional regime the brief names. Do not assert a regime's specifics from memory; cite a primary source at Stage 10.
- **All themes:** no hallucinated commitments; "received", "reviewed" and "approved" are separate states; every automated path has a human route; messages never promise a time or outcome the company has not set.

## 4.8 The claim-growth ladder

Use the matrix ledger's columns. A claim may sit on only one rung at a time and moves up only with a dated record.

`Inspired by evidence → Proposed → Selected by Innocent → Implemented → Demonstrated with synthetic data → Validated in a real company workflow`

During research: "a public report or published requirement inspired a capability meant to address a particular failure mode". After a build: describe only the behaviour built and demonstrated. Claim a company improvement only with company-level measurement. A synthetic demonstration cannot establish a real company's revenue or completion improvement.

## 4.9 Synthetic data rules

From `.claude/rules/synthetic-test-data.md` (GP-34…37): demo data only; draw the facts in code with fixed seeds and let a model write around them; generate through the production schema; vary along one named dimension at a time; break known-good cases deliberately and label what the system should do; reproducible from a script and seed. For research documents: scenario names `SIM-<company>-n`, obviously fictional names, no real ID layout or security features (RQ-17), and every scenario marked **Simulated**. A public demo can still receive real information if it accepts unrestricted uploads or chat; a warning cannot enforce the boundary (brief audit, "Scope and evidence").

---

# Part 5 · Dashboard reproduction and verification

## 5.1 Capabilities to reproduce (what the AEA dashboard does)

The AEA file is one self-contained page (≈1,000 lines, 138 KB [V]) with six views reached by hash links (`#overview`, `#journeys`, `#solutions`, `#compare`, `#audit`, `#sources`).

| View | Capabilities |
|---|---|
| **Overview** | Business problem and the patient questions; proposed value as hypothesis with "measured baseline: unknown" and **no performance chart** because none exists; mandatory-vs-discretionary explainer; KPI tiles (N, shortlist, target, draft count); ranked shortlist list; current draft selections vs "recorded in the source: none"; unresolved decisions |
| **Patient journeys** | Stage buttons for the reference journey; a panel per stage with the issues, evidence and related candidates; lane labels (administrative · clinical · coordination); per-company reference journeys |
| **Solutions** | Filters (company, journey stage, evidence strength, onboarding vs coordination, effort/dependency, selection state) with a live count that says "ranks never change when you filter"; ranked shortlist cards (rank, score, E, type, scope, effort, six sub-scores, problem/where/value/dependency, "Open evidence", "Select (draft)"); a **full inventory table of all 19**; a **mandatory baseline** list (cannot be deselected); a **parked ideas** table; a "how the score is calculated" explainer with weights, the E scale and tie-breaks |
| **Evidence cards** | A modal detail with: the chain; the problem and a concrete example; portfolio connection; practice/branch; reference baseline; company and review evidence tagged by kind (Published fact / Attributed review / Positive review / General guidance / Inference / Proposed / Synthetic); proposed behaviour and mechanism; value and business mechanism (hypothesis); problem vs solution confidence; the synthetic demonstration with pass conditions; metric and measured baseline; dependencies, limits and open RQs; reason to choose / defer; where the card lives. Ranks without a full card show the inventory row and say so |
| **Compare & select** | Draft selection with count and target; **combination check** (dependency warnings, covered dependencies, "builds on mandatory work", overlaps, open questions attached to the selection); one note field per selected candidate; **export** (Markdown, JSON, "show text to copy", clear); **side-by-side comparison** of two or three candidates |
| **Interview & audit trail** | Research-tense explanation per candidate (what inspired it · portfolio example · meant to address · what would count as proof · what remains unproven); the **evidence-status ledger** with "recorded" separate from "draft in this browser" |
| **Sources** | Local documents with copyable paths; cited sources table with a filter box; every `S-N` linked with read date |
| **Cross-cutting** | Status banner "Draft decision aid — not a PRD, not scope approval, not research sign-off"; skip link; selection tray with progress bar and dependency warning; `prefers-color-scheme` dark theme; narrow-screen breakpoint at 720px; print stylesheet; reduced-motion handling; no network assets |

**Selection behaviours.**

- **Persistence:** `localStorage` key `aea-onboarding-selection-draft-v1` holding `{selected:[…], notes:{id:text}}`; read and write wrapped in try/catch; if storage is blocked the page says so and tells the user to download or copy before leaving. **[R]** Use a project-specific key for Riverside.
- **Export schema** (`exportData()`): `{exported (ISO time), status:"DRAFT — not recorded in the repository; not scope approval", pool:19, target:4, rounding:"20% × 19 = 3.8 → 4", selected:[{id,name,rank,score,note}], unresolvedDependencies:[…], source:"docs/analysis/…matrix.md"}`. The Markdown export lists `- [x] **ID name** (rank, score)` with notes, then "Unresolved dependencies", then "Mandatory baseline M-01…M-15 is always in scope and is not part of this selection". Files: `aea-solution-selection-draft.md` / `.json`.
- **Browser selections are drafts.** The matrix selection area and ledger are the record. The export panel says so.

## 5.2 How the content is embedded, and what owns it

- **[V] Embedded as inline JavaScript constants**, not read at runtime: `DOCS` (document names, paths, what each owns) · `SOURCES` (48 `S-N` rows [V] with URL, authority, read date, supports) · `COMPANIES`, `STAGES`, `ISSUES` (journey) · `MANDATORY` (M-01…15) · `PARKED` (P-01…11) · `C` (19 candidates: id, name, type, job, scope, rank, score, six sub-scores, E, companies, stages, effort, problem, where, value, dependency, line) · `CARDS` (the 8 evidence cards as structured objects) · `DEPS`, `MAND_NOTES`, `OVERLAPS`, `UNRESOLVED` · `POOL=19`, `TARGET=4`.
- **[V] There is no generator, parser or build script in the repo**, and no saved parity script. The data were transcribed from the matrix and other documents (dev log: "transcribed from the reconciled selection matrix, the review report (including §7), the journey baseline, the profiles and the source register").
- **Ownership.** The **Markdown matrix is authoritative** for IDs, ranks, scores, cards, dependencies and the selection record; the other documents own the facts the cards cite. The dashboard owns nothing. The matrix header says: "If this file changes, regenerate or re-check the dashboard."
- **[V] Drift found.** (a) "Where this card lives" line numbers are two lines stale; (b) the ledger "Selected by Innocent (recorded)" is hard-coded "pending"; (c) AEA/healthcare wording is also hard-coded in the rendering code (for example the headings "Portfolio connection (AEA listing)" and "Patient and business value", and "What the patient and staff would experience"), so reuse needs code edits as well as new data.
- **Alternative to a hand-copied page [R]:** keep the matrix Markdown authoritative and **generate** the data block from it. Its tables (inventory, scores, mandatory, parked) and cards (consistent `- **Chain:**`, `- **Problem:**` … bullets) are regular enough to parse. Emit `dashboard-data.json`, template it into the HTML, and run a parity script every time. Put all domain words and organisation names in the data block, not in code.

## 5.3 Reproduction specification for Riverside

1. **Inputs:** the frozen Riverside matrix and its audit (Stage 12). Output: `docs/artifacts/<date>-solution-selection-dashboard.html`.
2. **Data block fields:** exactly the constants listed in §5.2, plus a `ledger` array and `pool/target/rounding` from the matrix.
3. **Behaviours:** all of §5.1. Drop the AEA-specific view contents (journey ISSUES, company journeys) and rebuild them from Riverside's Stage 8/9 documents.
4. **Never** include real personal data, reviewer names, or a network call. **Never** publish; the page is a local file.
5. **Accessibility baseline:** semantic landmarks, a skip link, labelled controls, `aria-live` for counts and warnings, a modal with focus management (focus moves in, and returns to the opener on close), status never by colour alone, contrast ≥4.5:1 for text and ≥3:1 (aim 4:1) for controls in both themes, reduced-motion respected.
6. **Layout:** works from 320px; no horizontal page scroll; the selection tray cannot cover content on small screens.
7. **After any matrix change:** rebuild, run the parity script, re-run the interaction checks that touch the changed content, log it.

## 5.4 Verification matrix: AEA status and what to do next time

"Completed in AEA" = the dev log `2026-10-15-selection-dashboard-claude-04.md` says so. "[V]" = I checked it myself on 2026-10-15.

| Check | AEA status | Needed next time |
|---|---|---|
| **Content parity** — IDs, ranks, six sub-scores, totals, rubric criteria equal the matrix; zero selections recorded | **Completed** by an unsaved script. [V] I re-ran an equivalent comparison: 19/19 match | Save `check_dashboard_parity.py`; also compare `MANDATORY` (15), `PARKED` (11), `DEPS` against the matrix and each card's fields |
| **Calculations** — score formula; shortlist and target arithmetic; selection count and over-target text | **Completed** (selection and message); [V] formula recomputed; no script for rounding | Script the formula and `round_half_up` |
| **Citations / "where this lives"** | **Not checked.** [V] Line numbers are two lines stale | Use section anchors only; check every anchor exists |
| **Links** — external `S-N` links; local paths | External links `target=_blank rel=noopener`; local paths are copy-text. **Link resolution was not recorded as checked** | Script: each `S-N` in the data exists in the register; HEAD-check external URLs and record failures; every local path exists |
| **Interaction** — filters, stage linking, detail dialog focus return, three-way compare, dependency warnings | **Completed** (browser: `stealth-chrome` against `file://`; Chrome DevTools MCP unavailable because another Chrome held the profile) | Repeat with a saved checklist; record the browser and version |
| **Accessibility** | Contrast computed (all text ≥4.5:1; controls ≥4:1; both themes). Dialog focus verified. **No keyboard-only walk-through, no screen-reader pass recorded** | Keyboard-only run-through of every control; an automated audit (axe or Lighthouse); a screen-reader spot check |
| **Narrow screen** | Checked at ≥500px (the browser's minimum window): no horizontal scroll; the tray was fixed | Emulate 320, 360, 400px and landscape; record |
| **Persistence** | **Completed**: survives reload; blocked-storage fallback message shown | Also test a second tab, clearing storage, and a stale key from a previous version |
| **Export contents** | Buttons exercised. **A saved file was not inspected** | Open the downloaded `.md` and `.json`; check IDs, notes, `unresolvedDependencies`, status line, and that no personal data appears |
| **Draft vs recorded** | **Completed**: the ledger keeps "recorded: pending" separate from "draft in this browser" | After Stage 14, check the recorded column equals the matrix |
| **Print layout** | **Not checked** (CSS exists) | Print-preview PDF; inspect |
| **Light theme** | Contrast computed; **no visual check** | Screenshot both themes at three widths |
| **Reduced motion** | CSS exists; not tested | Toggle the OS setting |
| **No network assets / no JS errors** | No JS errors **completed**. [V] No external `<script>`/`<link>` | Console must be clean; block network and reload |
| **Privacy** | Not recorded | Search the HTML for reviewer names and personal data; check quotes are exact or paraphrased |
| **Opens by double-click** | Tested via `file://` | Record the OS/browser |

**Rule:** a check not listed as completed is reported as "not done", never as passed.

---

# Appendices

## Appendix A · Evidence inspected for this playbook

Paths relative to `{AEA}` unless stated. All read on 2026-10-15; nothing was modified.

| Group | Files |
|---|---|
| Instructions and rules | `AGENTS.md` · `CLAUDE.md` · `.claude/README.md` · `.claude/rules/source-authority.md` · `hiring-partner-framing.md` · `project-provenance.md` · `synthetic-test-data.md` · `html-files-not-artifacts.md` · `.claude/reference/dev-log.md`; root `{WS}/CLAUDE.md`, `{WS}/.claude/rules/new-project-zero-to-hero.md`, `{WS}/.claude/skills/zero-to-hero/` (`SKILL.md`, `ARTIFACT-MAP.md`); user rules `confirm-before-killing-processes.md`, `anti-bot-tooling.md`, `match-model-on-vps.md`; skill `google-reviews` |
| Brief, provenance, status | `docs/source/aea-proj1-onboarding-assistant.md` · `docs/source/source-register.md` · `PROJECT-CHECKLIST.md` · `SUBMISSION.md` · `README.md` · `docs/analysis/2026-10-14-brief-audit.md` |
| Portfolio and fit | `docs/evidence/2026-10-14-aea-portfolio-inventory.json` · `docs/analysis/portfolio-fit-review.md` · `docs/analysis/company-research/aea-investors.md` and the five company profiles |
| Research frame and synthesis | `docs/aea-portfolio-research.md` (template) · `…-onboarding-research-report.md` · `…-configuration-specification.md` (Annex 1) · `…-demo-blueprint.md` (Annex 2) · `…-onboarding-configuration-checklist.md` (superseded first pass) |
| Reviews | `…-google-review-sentiment.md` · `docs/evidence/raw-google-reviews/*.json` (opened: FOH Naples, Metro Vein Forest Hills; scripted: all) · `docs/evidence/raw-google-reviews/scripts/themes.py` (re-run) · `docs/evidence/raw-page-text/` (280 files; opened the ones cited in §1.6) · `raw-page-text/fetch.py` |
| Reference and interpretation | `…-patient-journeys-and-onboarding-baseline.md` · `…-review-pitfalls-and-solution-opportunities.md` |
| Selection and dashboard | `…-solution-selection-and-evidence-matrix.md` (all sections) · `docs/artifacts/2026-10-15-solution-selection-dashboard.html` (structure, data, logic) · `docs/analysis/research-questions.md` |
| Dev logs | `{GAUNTLET}/devlogs/aea-onboarding/` — all 11 runs, 2026-10-14 and 2026-10-15 |
| Upstream | `{GAUNTLET}/artifacts/2026-10-13-hiring-partner-project-choice-and-deadlines.md` (§0, §0.1, §1) · `…-partner-projects-todo.md` (pipeline, Project 1) · `…/2026-10-13-partner-briefs/` (Riverside and AEA briefs; Project 2 not needed) · `{GAUNTLET}/open-questions.md` (GQ-18/19/20) |

**Not available [U]** — repeated from §1.1 so it is next to the evidence list: Innocent's original prompts; Codex's prompt for the matrix; the portfolio-inventory script; the review extraction run; the quote-verification and dashboard-parity scripts; the 14-page sub-agent re-read; dashboard test screenshots/console output; any raw capture of the AdaCare scheduler re-read (S-83); the portal screenshot of the Riverside card; a decision record for the niche.

**Checks I ran myself [V]:** inventory count reconciliation (118 = 56 + 55 + 7) · `themes.py` re-run (reproduces review report §6) · rubric recomputation for all 19 candidates (0 differences; non-increasing in rank) · dashboard vs matrix comparison of 19 ranks and six sub-scores (0 differences) · counts of M (15), P (11), SOL (19) · `cmp` of the AEA brief against the Gauntlet copy (identical) and the SHA-256 of both briefs · normalised diff of the two briefs (four differences) · raw-file spot checks for Traces A–C · dashboard `SOURCES` row count (48) and absence of external script/link tags.

## Appendix B · Riverside project layout, owner map and ID registry (a starting point; adjust at Stage 2)

```
{PROJECT}/
├── README.md · CLAUDE.md · AGENTS.md          entry points (CLAUDE.md holds the owner map)
├── PROJECT-CHECKLIST.md                         zero-to-hero stages and gates (owns stage)
├── RESEARCH-PROGRESS.md                         this playbook's state (§0.4 copy)
├── SUBMISSION.md                                deliverables and dates (owns dates)
├── .gitignore                                   raw-reviews/ and raw-page-text/ at least
├── .claude/ README.md · rules/ · reference/dev-log.md
├── scripts/                                     themes, verify_quotes, score, audit_*, build_dashboard, check_dashboard_parity
└── docs/
    ├── source/        riverside brief (unchanged) · aea brief (reference copy) · source-register.md
    ├── evidence/      <date>-riverside-portfolio-inventory.json · raw-reviews/ · raw-page-text/
    ├── analysis/      research-playbook.md · requirements-baseline.md · portfolio-screening.md · portfolio-fit-review.md
    │                  company-research/<company>.md · <date>-onboarding-research-report.md (+ annexes)
    │                  <date>-review-evidence.md · <date>-journeys-and-onboarding-baseline.md
    │                  <date>-review-pitfalls-and-solution-opportunities.md · <date>-brief-audit.md
    │                  <date>-solution-selection-and-evidence-matrix.md · research-questions.md
    ├── artifacts/     <date>-solution-selection-dashboard.html
    ├── principles/    copy of Gauntlet AI/principles/
    └── research-template.md                     corrected copy of the AEA template
{DEVLOG}/                                         one file per run: YYYY-MM-DD-<topic>-<writer>-NN.md
```

**Owner map to write into `CLAUDE.md` (one owner per fact):**

| Fact | Owner |
|---|---|
| Requirements, rubric, metrics (ISSUED) | `docs/source/<riverside brief>` |
| M-NN mandatory baseline | `docs/analysis/requirements-baseline.md` (the matrix links to it) |
| Sources, authority, read dates | `docs/source/source-register.md` |
| Firm context and portfolio counts | `docs/analysis/company-research/riverside.md` |
| Screening method, exclusions, coverage | `docs/analysis/portfolio-screening.md` |
| Theme comparison and recommendation, cohort and roles | `docs/analysis/portfolio-fit-review.md` |
| Per-company evidence | `docs/analysis/company-research/<company>.md` |
| Company comparison, configuration facts, synthetic scenarios | the research report and annexes |
| Review samples, excerpts, counts, status | the review-evidence document |
| Reference journey and baseline | the journeys-and-baseline document |
| Review interpretation | the pitfalls document |
| T and C | the brief audit |
| SOL, P IDs, rubric, scores, shortlist, selection record | the matrix |
| Unknowns (RQ) | `research-questions.md` |
| Stage and gates | `PROJECT-CHECKLIST.md` |
| Deliverables and dates | `SUBMISSION.md` |
| Progress through this playbook | `RESEARCH-PROGRESS.md` |
| Work history | `{DEVLOG}` |

**ID prefixes.** `S-N` source · `RQ-N` research question · `GQ-N` partner/staff question (owned by `{GAUNTLET}/open-questions.md`) · `T-N` / `C-N` audit risks and contradictions · `M-NN` mandatory baseline · `SOL-NNN` discretionary candidate · `P-NN` parked idea · `SIM-<co>-n` synthetic scenario · `D-N` decision gates in this playbook. IDs are stable and never reused. When citing an AEA ID from Riverside files, write it as `AEA:SOL-006` so it cannot be mistaken for a Riverside ID.

## Appendix C · Templates

**C1 · Source-register row**

```
| S-NN | <title> — <URL> | <AUTHORITY LABEL> | <date actually read> ✓ | <one line: what it supports; scope: company-wide / location X> |
```

**C2 · Decision record** (append to the progress file and the checklist; `Innocent ✓` only with his words)

```
D-N · <stage> · <question> · options offered: <a / b / c> · recommendation: <x> · Innocent chose: <…> · Innocent ✓ <date> · consequences: <…>
```

**C3 · Company profile skeleton**

```
# <Company> — <role>
Role in this project · Sources read (dates) · AEA/Riverside listing table (status, group, date, location, description, site)
## 1. Verified public facts   (1.1 footprint, services, people · 1.2 how a new customer starts · 1.3 money and policies · 1.4 stated timing commitments · 1.5 preparation · 1.6 positioning)
## 2. Our interpretation (inference — not company statements)
## 3. What we must not assume
## 4. Open questions   (RQ-N)
```

**C4 · Review sample record** (raw JSON header)

```
{"place": "<listing — city, state (platform; rating, count)>", "read": "YYYY-MM-DD",
 "lowest": {"sort":"Lowest","n":60,"sample_star_counts":[…],"reviews":[{"stars":n,"date":"N months ago","owner_replied":bool,"text":"…"}]},
 "newest": {…}}
```

**C5 · Candidate inventory row**

```
| ID · name | Type · job | Specific problem | Company/location examples | E | Expected value (hypothesis) | Effort · dependency | Rank · status |
```

**C6 · Evidence card** — the table in §4.6.

**C7 · Contradictions-table row (Stage 10b)**

```
| claim | file A (section) | file B (section) | resolution | owner file | date | ripple done? |
```

**C8 · Dev-log entry** (contract: `{AEA}/.claude/reference/dev-log.md`)

```
## <milestone>
- **Changed:** <what, with paths>
- **Why:** <the reason, in Innocent's terms>
- **Checked:** <what was run or opened, and the result; failures included>
- **Remaining:** <what is open; "None for this change" when true>
```

**C9 · Rubric configuration block** (to approve at D-11 before scoring)

```
Pool: <rule> → N = <n>   Mandatory excluded: <count>   Parked excluded: <count>
Criteria and weights: E <w> · P <w> · F <w> · D <w> · R <w> · I <w>   (sum 100)
E scale: <5…1 definitions>   Formula: Σ(weight × score ÷ 5)
Rounding: round_half_up; shortlist = <0.40 × N = x → y>; selection target = <0.20 × N = x → y>; bounds: <min/max>
Tie-break order: <1, 2, 3, 4>   If still tied at the cut: <include both / keep lower effort and record the other as closest excluded>
Selection pool: <shortlist only | any candidate>
```

## Appendix D · Readiness check of this playbook (run 2026-10-15, after writing)

| Check | Result |
|---|---|
| All 14 stages contain: purpose · inputs/prerequisites · concrete actions (checkboxes) · outputs and ownership · evidence/citation fields · completion checks · decisions · continue-or-wait · ready-to-use instruction | **Pass** (scripted: 14 of 14, one instruction block each) |
| Every `{AEA}`, `{GAUNTLET}` and repo-relative path cited as existing resolves | **Pass**: 32 literal paths cited exist; the 5 that do not are **files the Riverside project will create** (`company-research/riverside.md`, `portfolio-screening.md`, `requirements-baseline.md`, `research-playbook.md`, `research-template.md`). Paths containing placeholders such as `<date>` or `<company>` were not tested |
| Placeholders used: `{WS} {AEA} {GAUNTLET} {PLAYBOOK} {PROJECT} {PARTNER} {THEME} {DEVLOG} {DATE}`; each defined in §0.3 | **Pass** |
| No reviewer, doctor or staff names; review text appears only as short exact fragments already present in the repo's review report | **Pass** (searched) |
| Both briefs and the AEA project unchanged | **Pass** (hashes re-checked at the end; no AEA file was edited; the only file added there is this playbook) |
| A fresh session can start with only this file | **Pass by design**: §0 gives rules, labels, paths, progress and the resume protocol; each stage names its inputs, outputs, checks and a prompt; Part 1 explains why |
| What is **not** tested | No stage has been executed. The [R] items (script-generated dashboard data, independent Stage 12 reviewer, balanced review sample, pre-registered tie-break order) have not been tried. The AEA-assignment changes may require edits to Part 2 |
