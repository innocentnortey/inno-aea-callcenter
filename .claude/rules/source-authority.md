# Source Authority and Data Discipline

Always loaded. Rewritten 2026-10-20 for the AEA **AI Call Center Agent** brief (the 2026-10-14
version covered Project 1's healthcare-company research and is archived with it). This project is
graded on judgment about messy data — the brief asks *"Did you look at what was actually in the
knowledge base and transcripts, or did you assume? Did you catch the traps?"* — so how sources and
data are labelled is the thing most likely to go wrong.

## Ranking

| Rank | Source | Where | Notes |
|---|---|---|---|
| ISSUED | The briefing: portal page (Part A) + PDF (Part B) | `docs/source/aea-call-center-briefing.md` (S-100, S-101) | What gets graded. Never edit it. Where the two parts disagree (deliverables: five vs three), satisfy both and note it. |
| ISSUED (pending) | Gauntlet staff answers | `Gauntlet AI/open-questions.md` | When one arrives, it outranks our assumptions. |
| ISSUED-DATA | Transcripts, knowledge base, scheduling DB | `docs/data/issued/meridian_dataset/` (S-102…S-105) | Issued, but explicitly not clean. Evidence of what the data contains, not of what is true. Never edit it; the agent writes to a copy of the DB. |
| CONTEXT-AEA | AEA's own web pages | `docs/source/source-register.md` | Framing only: what AEA publishes about itself. |
| DERIVED | Our analysis | `docs/analysis/`, `docs/data/`, `docs/design/` | Judgments. Never cite our own analysis as if it were an issued fact. |
| HISTORY | Project 1 archive | `docs/archive/project-1-onboarding/` | A different brief. Never a requirement. |

## Rules

1. **The company is synthetic.** "The industry does not matter; the exercise does." Requirements
   come from the briefing and the issued data, never from AEA's real portfolio. AEA context is for
   the two-layer framing only.
2. **Look at the data before deciding anything about it.** Call drivers come from the transcripts,
   not from what a call center "usually" gets. Chunking comes from what is actually in the
   knowledge base (tables, images, duplicates, outdated pages), not from a default.
3. **Record every trap you find.** A duplicated, contradictory or outdated knowledge-base passage,
   a transcript that doesn't fit any driver, a scheduling row that breaks the schema: each gets
   written down with its location and what the system does about it. Undocumented handling
   doesn't count as catching it.
4. **The newest source is not automatically right.** When two knowledge-base passages conflict,
   decide which wins and record the basis (date, version marker, policy owner). If you can't tell,
   the agent escalates instead of choosing.
5. **Numbers come from runs.** Containment, accuracy, escalation rate and retrieval metrics are
   reported only from a run on a stated test set, with the set's size and how it was built. A
   target (60–75%) is never presented as a result.
6. **The test set must reflect real calls.** Cases are drawn from, or traceable to, the issued
   transcripts. Synthetic cases are labelled as synthetic, with the assumption they encode
   (`synthetic-test-data.md`).
7. **A confident wrong answer is worse than a handoff.** When scope or evidence is unclear, the
   design default is escalation with context, and that default is tested.
8. **No real personal data.** Use only issued or synthetic caller data. Don't enrich transcripts
   with outside data about people.
9. **Each fact has one owner.** Link to it; don't restate it in a second file. The owner map is in
   `CLAUDE.md`.
