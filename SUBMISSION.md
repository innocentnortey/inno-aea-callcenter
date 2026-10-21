# SUBMISSION — AEA Investors: AI Call Center Agent

**Owner of:**
- deliverables, and the evidence that each one is done;
- dates, keeping **confirmed partner deadlines** separate from **our internal targets**.

Requirements come from the [briefing](docs/source/aea-call-center-briefing.md): portal page
(Part A, §Required Deliverables) and PDF (Part B, §Deliverables). Opened for this brief
2026-10-20. Nothing has been built yet; every row is `not started`.

## Dates

| Date | What | Kind | Source |
|---|---|---|---|
| 2–3 days | Brief timebox ("Time Constraints: 2-3 days") | **Partner (brief)** | Briefing Part A |
| Mon 2026-10-19 | Call-center brief received (portal Version 1, last updated 10/16/2026) | Fact | Briefing header |
| **Unknown** | Partner submission deadline: before the interview, or a fixed portal deadline? | **Partner, unconfirmed** | GQ-20 in `Gauntlet AI/open-questions.md` |
| Thu 2026-10-22 | AEA interview | Partner schedule, per the 2026-10-16 sheet recorded in GQ-20. Re-confirm on the portal. | `Gauntlet AI/open-questions.md` GQ-20 |
| **Wed 2026-10-21, 06:00 CT** | Internal target: finish the build and submission | Internal (Innocent, 2026-10-20) | Set before GQ-20 is answered; the partner deadline is still unconfirmed |

The data arrived 2026-10-20 (`docs/data/issued/`). It fixes "today" as **2026-10-16**, and its
appointment slots run three weeks from then. The reviewer will test bookings against the same
database.

## Deliverables

The portal and PDF list different deliverables. Each row names which source asks for it; both
lists are satisfied.

| # | Deliverable | Asked by | Brief wording | Evidence (path / URL) | Status |
|---|---|---|---|---|---|
| D-1 | Deployed URL: interactive web app | PDF 1 · portal FR-6 | "a live web app the reviewer can interact with directly. They will ask their own questions and try to break it" | — | not started |
| D-2 | Walkthrough / demo video, 3–4 min voiceover | PDF 2 · portal "Demo Video" | "how you found the call drivers, why you chose your chunking and retrieval approach, how escalation works, and what your eval numbers say. Design reasoning, not a feature tour." | — | not started |
| D-3 | Source repository: code + eval set + README | PDF 3 · portal "Source Code" | "a README that explains how to run it and what the containment numbers were" | — | not started |
| D-4 | Technical documentation | Portal | "Technical Documentation" (incl. discovery findings: drivers, method, scope choice — PDF goal 1) | — | not started |
| D-5 | Deployment guide | Portal | "Deployment Guide" | — | not started |
| D-6 | Test results | Portal | "Test Results": containment, accuracy on handled drivers, escalation rate, retrieval eval | — | not started |
| D-7 | *Extra credit:* voice interface (STT/TTS, turn-taking) | PDF · portal | "A working voice agent, even a rough one, is a strong signal." Optional. | — | not planned yet |

AI usage documentation: **not needed** (portal, "AI Usage Documentation: Not-needed").

## Required goals → where the evidence will live

| Goal (PDF) | Evidence | Status |
|---|---|---|
| 1 Discovery: top 4–5 drivers ranked by volume, scope decision | `docs/data/handoff-information-inventory.md` (all 420 calls classified), PRD §3 (scope) → D-4 | evidence exists; write-up into D-4 not started |
| 2 RAG over the KB for the top 3 drivers; retrieval evaluated on its own | retrieval eval report → D-6 | not started |
| 3 Scheduling: availability check, confirm or offer alternatives | demo path in D-1 | not started |
| 4 Escalation with handoff context; no guessing | escalation cases in the eval set → D-6 | not started |
| 5 Test set from transcripts; containment 60–75% target; accuracy; escalation rate | eval set in D-3, numbers in D-6 and README | not started |
| 6 Public interactive web app | D-1 | not started |
| 7 Monitoring (volume, containment, escalations, failures, latency) + feedback loop | dashboard in D-1, loop described in D-4 | not started |
