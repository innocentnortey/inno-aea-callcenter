# inno-aea-onboarding — AI Onboarding Assistant for AEA Investors

**What this is:** Innocent Nortey's hiring-partner project for **AEA Investors** (via Gauntlet AI),
built against AEA's *Project 1: AI-Powered Onboarding Assistant* brief.

**Where it stands (2026-10-15):** **research phase.** The repo holds research context and
documentation only. There is no PRD, no design and no code yet, by choice: more research comes
before the PRD.

---

## The problem, in one example

A new patient is referred to a pain clinic. To be seen, they must:
- send demographics, insurance and a referral;
- bring a valid photo ID;
- arrive early to fill in paperwork;
- wait while staff check referral and coverage.

Each step means retyping details already printed on a document, and wondering what is still missing.

The assistant we are researching would turn that into one guided flow:

1. **Chat intake.** The person answers a short conversational intake.
2. **Photo instead of typing.** They photograph their ID. Name, date of birth and address are
   extracted and shown back for confirmation or editing.
3. **A readiness summary.** The person sees what is complete and what is missing.
4. **The right next step.** They book a first visit, or a staff intake call if a prerequisite is
   still pending.
5. **Help at friction points.** Help content appears where people tend to get stuck.

**Working product concept** (initial framing, not an approved PRD or a validated customer need):

> Help a prospective patient complete administrative intake, confirm information extracted from a
> document, understand missing requirements, and book an appropriate next step with less
> repetitive entry and uncertainty.

## The niche and why

- **The brief targets general sensitive-service onboarding.** Healthcare is allowed, not required.
- **We compared AEA's whole public portfolio across industries:**
  - 118 profiles;
  - 56 current or active listings, which are website labels, not proof of control or access.
- **Chosen first niche: administrative patient intake across multiple practices.** The product
  core stays reusable.
- **Why healthcare:** it is the only group where document-heavy personal intake, appointment
  booking and supportive guidance all fit naturally.
- **Strongest non-healthcare alternative:** staffing.
- **The cohort is four directly relevant platforms plus one adjacent opportunity:**
  - Commonwealth Pain & Spine (anchor)
  - American Dental Companies (second configuration)
  - Metro Vein Centers (reuse and benchmarking)
  - American Oncology Network (fourth core platform)
  - Numotion (adjacent)

Riverside's portal partner identity is [The Riverside Company](https://www.riversidecompany.com/regulatory-disclosures), whose legal name is Riverside Partners L.L.C. (GQ-19 resolved). Whether one build may be submitted to both partners remains GQ-18; Riverside does not drive this AEA research framing.

## Document map

| Question | Read |
|---|---|
| What did AEA actually ask for? | [Issued brief](docs/source/aea-proj1-onboarding-assistant.md) (unchanged copy) |
| What legal, ethical, engineering and consistency issues did we find? | [Brief audit](docs/analysis/2026-10-14-brief-audit.md) (T1–T23; C1–C11, sources and proposed responses) |
| Where does each fact come from, and how strong is it? | [Source register](docs/source/source-register.md) |
| Who is AEA, and which parts of its portfolio matter? | [AEA Investors](docs/analysis/company-research/aea-investors.md) |
| Why patient intake, and what else was considered? | [Portfolio fit review](docs/analysis/portfolio-fit-review.md) |
| What do we know about each company? | [Commonwealth Pain & Spine](docs/analysis/company-research/commonwealth-pain-spine.md) · [American Dental Companies](docs/analysis/company-research/american-dental-companies.md) · [Metro Vein Centers](docs/analysis/company-research/metro-vein-centers.md) · [American Oncology Network](docs/analysis/company-research/american-oncology-network.md) · [Numotion](docs/analysis/company-research/numotion.md) |
| What do the five companies publish, and how do they compare? | [Onboarding research report](docs/analysis/2026-10-15-onboarding-research-report.md) with its [configuration annex](docs/analysis/2026-10-15-configuration-specification.md) and [demo blueprint](docs/analysis/2026-10-15-demo-blueprint.md) |
| What does a good onboarding journey look like? | [Patient journeys and onboarding baseline](docs/analysis/2026-10-15-patient-journeys-and-onboarding-baseline.md) |
| What do patients report? | [Google review evidence](docs/analysis/2026-10-15-google-review-sentiment.md) · [review pitfalls synthesis](docs/analysis/2026-10-15-review-pitfalls-and-solution-opportunities.md) |
| Which solutions could we build, and which will Innocent choose? | [Solution selection matrix](docs/analysis/2026-10-15-solution-selection-and-evidence-matrix.md) (selection pending) |
| What don't we know yet? | [Research questions](docs/analysis/research-questions.md) (RQ-1…RQ-46) |
| What must we hand in, and when? | [SUBMISSION.md](SUBMISSION.md) |
| Which stage is the project at? | [PROJECT-CHECKLIST.md](PROJECT-CHECKLIST.md) |
| Raw portfolio data | [Inventory JSON](docs/evidence/2026-10-14-aea-portfolio-inventory.json) |

## Next research steps

1. **Close the workflow questions for the anchor.** Find out:
   - which fields and documents are required before which appointment (RQ-6);
   - who verifies referral and coverage (RQ-7);
   - what a patient may self-book (RQ-8);
   - what Commonwealth's existing request form does (RQ-28).
2. **Sample variation inside a platform.** Read several more American Dental Companies practices,
   and a second AON practice (RQ-9, RQ-11).
3. **Identify existing systems** (practice management, EHR, scheduling, CRM) and where a completed
   intake record would land (RQ-18, RQ-25).
4. **Resolve the audit decisions.** The [brief audit](docs/analysis/2026-10-14-brief-audit.md)
   reviews T1–T13 and adds T14–T23, with source evidence, proposed responses and closure checks.
   Jurisdiction, provider choice, crisis protocol and implementation evidence remain open.
5. **After Innocent says research is done,** frame the two layers of success and draft the PRD. The data-reality, hard-problems and
   interview stages follow `zero-to-hero` (see the checklist).

## Status of setup

- Local git only. There is no commit and no remote yet. The GitLab project is Innocent's to create;
  the GitHub mirror needs his yes.
- The work log is in `Gauntlet AI/devlogs/aea-onboarding/`.
