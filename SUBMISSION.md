# SUBMISSION — AEA Investors, Project 1: AI-Powered Onboarding Assistant

**Owner of:**
- deliverables, and the evidence that each one is done;
- dates, keeping **confirmed partner deadlines** separate from **our internal targets**.

Requirements come from the [issued brief](docs/source/aea-proj1-onboarding-assistant.md),
§Submission Requirements and §Evaluation Rubric. Opened 2026-10-14. Nothing has been built yet;
every row is `not started`.

## Dates

| Date | What | Kind | Source |
|---|---|---|---|
| 3 days | Brief timebox ("Timebox: 3 days · Format: take-home assessment") | **Partner (brief)** | Brief header |
| **Unknown** | Partner submission deadline: due before the interview, or a fixed portal deadline? | **Partner, unconfirmed** | GQ-20 in `Gauntlet AI/open-questions.md` |
| Thu 2026-10-22 | AEA interview (virtual) | Partner schedule, as recorded in Gauntlet notes on 2026-10-13. Re-confirm on the portal. | `Gauntlet AI/artifacts/2026-10-13-hiring-partner-project-choice-and-deadlines.md` §1 |
| Wed 2026-10-14 | Research, brief audit and PRD decisions | **Internal target** | `Gauntlet AI/artifacts/2026-10-13-partner-projects-todo.md` |
| Thu 10-15 → Sat 10-17 | Build | **Internal target** | same |
| **Sat 2026-10-17, 22:00 CT** | Submit (Sunday 10-18 until noon is buffer) | **Internal target, not a partner deadline** | same |

⚠️ **Schedule pressure:** the research phase now continues before the PRD, so the internal build
window (Thu–Sat) is at risk. Re-plan the internal dates once research ends. Staff answers to GQ-20
decide how much room really exists.

## Deliverables (brief §Submission Requirements)

| # | Deliverable | Brief wording | Evidence (path / URL) | Status |
|---|---|---|---|---|
| D-1 | Repository with README and `AI_USAGE.md` | "GitHub repository (with README + `AI_USAGE.md`)" | GitHub mirror needs Innocent's yes (`.claude/rules/project-provenance.md`) | not started |
| D-2 | Seed script, fixtures, synthetic OCR golden set, `.env.example` | "so the app runs and is gradeable from a clean checkout with no real PII" | — | not started |
| D-3 | Grader quick-start in the README | run app, seed, tests and AI eval "in minutes": setup, env vars, seed command, demo credentials, test command | — | not started |
| D-4 | Deployed application URL | "Deployed application URL" | — (Railway default) | not started |
| D-5 | Documentation | "Documentation" | — | not started |
| D-6 | Video demo | shows "the chatbot flow, image-to-text data entry with confirmation, a booking, and supportive-content surfacing" | — | not started |

## Requirements graders will look for that produce artifacts

| # | Item | Brief section | Evidence | Status |
|---|---|---|---|---|
| R-1 | `AI_USAGE.md`: tools, LLM and OCR engines and versions, material prompts and config | AI Usage Disclosure | — | not started |
| R-2 | Eval harness (e.g. `rake ai:eval`) printing a scorecard: OCR ≥ 90% field accuracy on 30 synthetic documents; every intent handled | AI Metrics & Test Method | — | not started |
| R-3 | k6 script committed; p95 results at 20 VUs for 60 s (chat < 3 s, OCR < 8 s, booking < 1 s) | Performance Benchmarks | — | not started |
| R-4 | Uptime evidence ≥ 99% over the review window | Performance Benchmarks | — | not started |
| R-5 | Health-check endpoint reporting DB, OCR and LLM reachability | Code Quality | — | not started |
| R-6 | CI running tests and linters on every push; ≥ 80% coverage on core logic | Code Quality | — | not started |
| R-7 | Regulatory note: which regime applies to the assumed domain, and how the design supports it | Security, Privacy & Compliance | — (healthcare niche → HIPAA analysis, RQ-20) | not started |

## Rubric (pass ≥ 70 of 100)

Core flows 30 · AI quality 20 · Security, privacy & compliance 20 · Code quality & architecture 15
· Performance 10 · Docs, AI disclosure & demo 5. The rubric levels are in the brief.

## Hiring-partner extras (our rule, not the brief's)

| Item | Path | Status |
|---|---|---|
| Two-layer framing, metrics tree, demo script | `docs/delivery/YYYY-MM-DD-angle-and-demo-framing.md` | not started |
| Brief audit (traps and how each was handled), part of the submission story | `docs/analysis/YYYY-MM-DD-brief-audit.md` | not started |
| Interview answer table | `docs/delivery/` | not started |
