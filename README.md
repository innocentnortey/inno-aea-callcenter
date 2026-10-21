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

## What this is

Meridian Home Comfort is a fictional Austin heating, cooling and plumbing company whose phone lines are overloaded. This
repository is a chat agent that takes the calls people should not have to wait for, and hands the rest to a person with
the context already written down.

- **Competency 1, knowledge answers.** Membership, billing and warranty questions are answered from Meridian's messy
  knowledge base (RAG: the agent looks up the relevant passages first, then answers only from them).
- **Competency 2, booking.** Repair visits are booked against a mock scheduling database. The agent works on a *copy* of
  the issued database and never writes the issued file.
- **Escalation.** Anything else, anything unsafe, and anything the customer wants a person for goes to staff with a handoff
  brief. A confident wrong answer is treated as worse than a handoff.

The brief asks for a call-center agent that resolves 60-75% of calls without a human. That range is **the brief's
target**, not a result of ours; see Results.

- **Brief:** [`docs/source/aea-call-center-briefing.md`](docs/source/aea-call-center-briefing.md)
  (portal page + PDF, word-for-word; original PDF beside it)
- **Status:** [`PROJECT-CHECKLIST.md`](PROJECT-CHECKLIST.md). Issued data:
  [`docs/data/issued/`](docs/data/issued/README.md).
- **Deliverables and dates:** [`SUBMISSION.md`](SUBMISSION.md)
- **Working in this repo:** [`CLAUDE.md`](CLAUDE.md) and the [router](.claude/README.md)

## Try it

- **Deployed URL:** `pending: AEA-56`
- **Demo login (R-48).** One username and password gate every page except the login screen and `/healthz`. The demo login
  is provided with the submission.
- After signing in, a visible control switches between the customer view and the staff roles (representative, supervisor,
  owner) with no second password. Reset sits behind the same login.
- **What to try:** a membership, billing or warranty question; booking a repair; "talk to a person"; a safety phrase
  (for example, saying there is a gas smell); then the staff console and the monitoring page.

## Results

No number below is claimed before a run. Each line will read "n of N on <split>, run <id>, <date>" when the Stage 9 run
fills it.

| Measure | Result |
|---|---|
| In-scope correct resolution on the sealed held-out split (M-1, the headline number) | `pending: Stage 9` |
| Containment (M-5), shown as coverage x resolution | `pending: Stage 9` |
| Accuracy on handled call drivers | `pending: Stage 9` |
| Escalation rate on out-of-scope cases (M-19) | `pending: Stage 9` |
| Retrieval hit rate @3 (M-6) | `pending: Stage 9` |

The brief's target is 60-75% containment. It is the target, not a measurement.

- Test results (D-6): `pending: Stage 9`
- How the measures are defined and run: [`docs/technical-documentation.md`](docs/technical-documentation.md)

## How to run it locally

Prerequisites: Python 3.12 (`requires-python = ">=3.12,<3.13"` in `pyproject.toml`) and [`uv`](https://docs.astral.sh/uv/).

1. **Install:** `uv sync`
2. **Configure:** copy `.env.example` to `.env` and fill the names below (`pending: AEA-02` rewrites `.env.example` to
   this list; until then the names come from the design contract, `docs/design/contracts/stage7/graph-core.md` section 12).
   Values are never committed.
   - Required: `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `MERIDIAN_DEMO_USERNAME`, `MERIDIAN_DEMO_PASSWORD`,
     `MERIDIAN_SESSION_SECRET`
   - Optional: `MERIDIAN_EVAL_KEY`, and `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`,
     `LANGFUSE_PROJECT_ID`. Without all four Langfuse values, trace export is off.
3. **Start the app:** `pending: AEA-23` (the command for `create_app` in `src/meridian/web/app.py`). Run one worker.
   Never use port 4019 or 5184; the UX prototype holds them. On first boot the app copies the issued scheduling database
   into a working copy under `MERIDIAN_DATA_DIR` (default `var/`) and never writes the issued file (R-19).
4. **Build the local knowledge index:** `pending: AEA-16`. It will be
   `python -m meridian.retrieval.ingest --kb-dir PATH --transcriptions-dir PATH --out-dir PATH`, writing to
   `MERIDIAN_INDEX_DIR` (default `var/index`).
5. **Tests, lint and types:**
   - `uv run pytest` (the default run excludes the `live` marker, so it makes no paid model call)
   - `uv run ruff check src tests eval` and `uv run ruff format --check src tests eval`
   - `uv run mypy`
6. **Evaluation:** `pending: AEA-24`. It will be
   `python -m eval.harness run --suite worked-pairs|e2e|load --split dev --base-url URL` and
   `python -m eval.run_retrieval --index-dir PATH`. The held-out split is sealed and scored only at Stage 9.
7. **React screens (`apps/web`):** `pending: AEA-49/AEA-55`
8. **Docker:** `pending: AEA-50`

## What is in the repository

```
src/meridian/         the service: domain, policy, privacy, gates, services, agent, adapters, retrieval, web
eval/cases/{dev,heldout,retrieval}/   test cases built from the issued calls
eval/harness/         the scoring harness
eval/reports/         scored runs
tests/                unit, integration, contract, graph, and tests/journeys/ (end-to-end journeys)
apps/web/             the React screens (the UX prototype, mock-backed until wired)
docs/                 brief, data, PRD, design, delivery
Dockerfile, railway.json, scripts/    deployment
```

- Layers, owners and the full module list: [area map](.claude/reference/area-map.md).
- The issued dataset sits at `docs/data/issued/meridian_dataset/`. It is included under R-42: the repository is public and
  the licence risk is accepted (audit L-8).
- **Held-out answer keys** are kept outside the repository until the held-out run, then committed with their hash (DAT-2,
  open: built on option B).
- Some of these paths arrive with later tickets and do not exist yet.

## Monitoring and the feedback loop

- **The monitoring page** shows conversation volume and handoffs by reason, containment and escalations, failures per 100
  turns, latency, spend against the daily cap, unowned and overdue cases, health-check restarts, and trace export status.
  It reads stored data and never recomputes it.
- **Feedback loop (R-37).** Staff flag a wrong answer, a wrong brief or a wrong escalation. A flag goes to a review list.
  **Nothing changes the knowledge base, the prompts or the eval set automatically.**
- **From flag to fix.** A person reviews the flagged item, then the fix is a new dev case, a knowledge-base change or a
  prompt change, and the affected cases are re-scored before the change ships.
- Full description: [`docs/technical-documentation.md`](docs/technical-documentation.md), section 9.

## Documents

- Technical documentation: [`docs/technical-documentation.md`](docs/technical-documentation.md)
- Deployment guide: [`docs/deployment-guide.md`](docs/deployment-guide.md) (live URL `pending: AEA-56`)
- Test results: `pending: Stage 9`
- Submission checklist: [`SUBMISSION.md`](SUBMISSION.md)
- The brief: [`docs/source/aea-call-center-briefing.md`](docs/source/aea-call-center-briefing.md)

## History

The repo began on 2026-10-14 as `inno-aea-onboarding` for AEA's earlier *Project 1: Onboarding
Assistant* brief. That research is frozen in
[`docs/archive/project-1-onboarding/`](docs/archive/project-1-onboarding/README.md), and the
whole pre-pivot tree is tagged `project-1-onboarding-snapshot`.
