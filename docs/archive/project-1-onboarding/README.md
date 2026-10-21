# Archive — AEA Project 1: AI-Powered Onboarding Assistant

**Frozen 2026-10-20.** This is the research done for AEA's first brief (an onboarding assistant;
our chosen niche was administrative patient intake at AEA's healthcare platforms). On 2026-10-19
AEA issued a different brief, the **AI Call Center Agent**
([`../../source/aea-call-center-briefing.md`](../../source/aea-call-center-briefing.md)), and the
repo was renamed `inno-aea-onboarding` → `inno-aea-callcenter`.

**Nothing here is live.** It is history: true when written, describing a brief we are no longer
building. Don't cite it as current requirements, and don't edit it. Fix the live docs instead.

## Layout

Mirrors the old `docs/` layout, so links between archived files still work:

| Path | What it was |
|---|---|
| `aea-portfolio-research.md` | Research prompt: healthcare company website analysis (Parts 1–10) |
| `source/aea-proj1-onboarding-assistant.md` | The Project 1 brief (ISSUED, unchanged) |
| `source/source-register.md` | Full Project 1 register, S-1…S-99 (AEA rows carried into the live register with the same IDs) |
| `analysis/` | Brief audit (T1–T23, C1–C11), research report and annexes, review sentiment, journeys, pitfalls, solution matrix (SOL-001…019), fit review, research questions (RQ-N) |
| `analysis/company-research/` | Profiles of the five healthcare platforms. AEA's own profile stayed live at `docs/analysis/aea-investors.md` |

## Links that point outside the archive

A few links target files that moved or were removed in the 2026-10-20 prune: the selection
dashboard HTML, `SUBMISSION.md`, the Project 1 `PROJECT-CHECKLIST.md`, `company-research/aea-investors.md`,
`../evidence/…json` (still live at `docs/evidence/`), and the raw review and page-text caches
(deleted; they were git-ignored). To see any of them as they were, check out the snapshot:

```bash
git show project-1-onboarding-snapshot:<old path>       # one file
git worktree add ../aea-p1-snapshot project-1-onboarding-snapshot   # the whole tree (remove after)
```

Also removed in the prune: `docs/analysis/riverside-onboarding-research-playbook.md`, a byte-identical
copy of `inno-riverside-onboarding/docs/analysis/research-playbook.md`, which owns it.
