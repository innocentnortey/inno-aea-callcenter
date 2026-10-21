> **Provenance:** copy of `Gauntlet AI/.claude/rules/hiring-partner-framing.md` (zero-to-hero principles pack), copied 2026-10-20 (re-copied: original changed since 2026-10-14). Change the original first, then re-copy. *Demo video* section copied from the original 2026-10-20.

# Hiring-Partner Projects Are Presented in Two Layers of Success

Project-wide; applies to every hiring-partner project (Equinox, Cerbo, and the ones that follow),
**not** to Gauntlet's internal weekly builds. Recorded 2026-10-10 at Innocent's instruction.

**The rule.** Every hiring-partner project is framed, built, demoed and defended as two layers:

1. **The project's problem** — what the brief asks us to build, and what makes that correct.
2. **The business value that made the project exist** — why the partner wrote the brief, in the
   brief's own words, and the metrics the company will measure success by.

The write-up, the demo video and the interview answers all open with layer 2, prove layer 1, and
close by showing how the system drives layer 2. Never present the build as a feature list.

**Why.** Every cohort member gets the same brief, and partner briefs are deliberately small, so
judgment and framing are the differentiators. Innocent's edge is business-oriented and
teaching-focused: naming the partner's success metric before the partner does, and explaining how
the system moves it in plain words, is the angle nobody else's slice will have.

**How to apply, per project.**

- At intake, pull every sentence in the brief about business context and impact metrics into a
  **metrics tree**: north star → revenue → leading indicator → the health metrics that make those
  believable. For each: why the partner cares (quote), how the system produces it (field, account,
  query), and the caveat we state.
- Give the tree a **surface in the product** when the brief allows it (a Success or metrics page
  read from stored data, never recomputed), and a section in the technical doc.
- Write the **demo script** in this order: problem in the partner's words → what success means
  (two layers) → the flow, narrated by the thing the partner cares about → the success surface →
  decisions, cuts, candour. The video's time split and where its decisions come from are in
  *Demo video* below.
- Prepare **interview answers** in the same two-layer shape, one table, in `docs/delivery/`.
- Every "sauce" option must pass the project's brief-conformance check and name the brief sentence
  it serves; optional items are cut before any required deliverable slips.

**Where it lives.** `docs/delivery/YYYY-MM-DD-angle-and-demo-framing.md` in the project repo.
First instance: `../inno-cerbo/docs/delivery/2026-10-10-angle-and-demo-framing.md`.

## Demo video: the product first, then the decisions behind it (2026-10-20)

Recorded 2026-10-20 at Innocent's instruction, for **Riverside Onboarding, HouseAccount and the
AEA call center** (the three projects in flight then): the demo video "should talk about the
different decisions that I made in the construction of everything", and its narration should be
built from the dev logs and the research, covering the major pillars and the notable business and
technical decisions.

**What it means in practice.** The video has two jobs, in priority order:

1. **Show the product working.** This comes first, is never cut to make room for anything else,
   and stays **under 5 minutes**.
2. **Explain the decisions that shaped it.** The time left inside the partner's limit goes to
   the major pillars and the notable decisions: business decisions (who the user is, which
   metric matters, what was cut and why), technical decisions (architecture, models, data
   boundary, hosting) and research findings that changed the plan.

**How the time splits** depends on what the brief allows:

| The brief says | Split |
|---|---|
| A limit of 5 minutes or less (AEA: "a 3 to 4 minute voiceover … Design reasoning, not a feature tour") | No separate decisions segment. Each demo step is narrated with the decision behind it ("it escalates here because…"), and the brief's own required topics come first. |
| A limit above 5 minutes | Demo under 5 minutes, then a decisions segment that uses what is left. |
| No limit (Riverside, HouseAccount, as of 2026-10-20) | Demo under 5 minutes, then a decisions segment of **up to 5 minutes** (total ≤ 10), unless Innocent sets another length. |

**Where the decisions come from: the record, not memory.** Before any narration is written, build
a **decision inventory** at `docs/delivery/YYYY-MM-DD-demo-decision-inventory.md` by reading, in
this order:

1. the project's dev logs (`.claude/reference/dev-log.md`, `docs/devlog/`);
2. its decision records: the PRD's decision and status tables (D-N, PD-N, HP-N), `decision-record.md`,
   the system-design decisions, spike records (SP-N);
3. its research: the brief audit, research reports, solution-selection matrices, review pages;
4. the angle-and-demo-framing doc and `SUBMISSION.md`.

One row per decision or pillar: **what was decided, the alternative rejected, why (basis), the
source path, its status (decided / proposed / assumption), its type (business / technical /
research), and the demo moment it attaches to.** Rank the rows: the decisions a reviewer would
probe first (the brief's traps, the data boundary, the metric, the biggest cut) go to the top.
Then fit the top rows into the time the table above allows. The rest go to interview prep.

**Rules for the narration.**

- Every decision spoken in the video cites an inventory row; the row cites its source. Nothing is
  narrated from recollection.
- Only **decided** items are stated as decisions. Proposed items and assumptions are said as such
  ("we assumed…, and we'd confirm it by…"), per memory `decisions-must-be-defensible`.
- Each decision is told in the interview shape: the choice, the alternative rejected, the evidence,
  the limit.
- The product demo is never trimmed to fit more decisions; decisions are trimmed instead.

## Interview-preparation route (2026-10-17)

Before drafting hiring-partner interview answers, mentor-review packets, or personal positioning,
read [`prep/2026-10-17-hiring-partner-interview-feedback.md`](../../../Gauntlet%20AI/prep/2026-10-17-hiring-partner-interview-feedback.md).
It records the Peak6 feedback as relayed to Innocent, Derek's and Byron's responses, Ash's
technical-fit guidance, the SDLC mapping, Selph technical-story candidates, and the mentor-review
questions. Use the current project documentation to verify any implementation or outcome claim.

The two layers of success remain the project and demo frame. In a live interview, establish the
business problem briefly, then spend most of the answer on **Innocent's architecture, technical
decision, rejected alternative, verification, and limit**. This applies Ash's feedback without
losing the business-ROI thread that makes the engineering relevant.
