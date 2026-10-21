# inno-aea-callcenter

AEA Investors hiring-partner project, via Gauntlet AI: **AEA FDE Challenge — AI Call Center Agent**.

A services company's call center can't keep up with its call volume. The job is to act as a
Forward Deployed Engineer:

1. Find out from the call transcripts why customers actually call.
2. Build an agent that answers the top three reasons from the company's knowledge base (RAG).
3. Have it book appointments against a scheduling database.
4. Hand everything else to a human with enough context to continue.
5. Prove it with a test set built from real calls. The target is to resolve 60–75% of calls with
   no human involved.
6. Deploy it at a public URL with monitoring and a feedback loop.

Voice is extra credit.

- **Brief:** [`docs/source/aea-call-center-briefing.md`](docs/source/aea-call-center-briefing.md)
  (portal page + PDF, word-for-word; original PDF beside it)
- **Status:** [`PROJECT-CHECKLIST.md`](PROJECT-CHECKLIST.md) — zero-to-hero light, Stage 1.
  Data received 2026-10-20 ([`docs/data/issued/`](docs/data/issued/README.md)).
- **Deliverables and dates:** [`SUBMISSION.md`](SUBMISSION.md)
- **Working in this repo:** [`CLAUDE.md`](CLAUDE.md) and the [router](.claude/README.md)

No code yet. How to run it and the containment numbers will be added here once they exist; the
brief requires both in this README.

## History

The repo began on 2026-10-14 as `inno-aea-onboarding` for AEA's earlier *Project 1: Onboarding
Assistant* brief. That research is frozen in
[`docs/archive/project-1-onboarding/`](docs/archive/project-1-onboarding/README.md), and the
whole pre-pivot tree is tagged `project-1-onboarding-snapshot`.
