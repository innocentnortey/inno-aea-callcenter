# Resume note — inno-aea-callcenter

**Updated:** 2026-10-21 (Stage 5 closed after SP-1), Mac working copy. **Product stage:** see [`PROJECT-CHECKLIST.md`](../../PROJECT-CHECKLIST.md)
(re-initialized 2026-10-20; the checklist shows the current gate). **Context maturity:** [ICM checklist](icm-progress.md).

## UX track update (2026-10-21, VPS)

UX-4 is signed (Innocent ✓ 2026-10-21): `apps/web/` is the real frontend, mock-only. **Next on the UX track: UX-5** (`TRACEABILITY.md`, Playwright + axe, Lighthouse, `QA_REPORT.md`); the sweep in `apps/web/tests/e2e/` is a start. Open: review-page decisions D-1…D-9 (not answered by the sign-off). No backend exists yet; real-backend verification and the combined chat → booking → handoff journey are listed in `docs/ux/04-prototype/INTEGRATION_HANDOFF.md`. Stage 7 may run in parallel; it must not build `web/templates` or `web/static` and must treat the OpenAPI file as read-only.

## Where we are

The repo was re-initialized to zero-to-hero 1.9.0 after the brief changed from Project 1 (onboarding)
to the AI Call Center Agent. Stage 0 was redone (principles refreshed, four rules added,
`icm-project` 1.5.0 context system). Stage 1 has two artifacts: sources converted and the
[brief audit](../../docs/analysis/2026-10-20-brief-audit.md). The
[handoff product direction](../../docs/analysis/2026-10-20-human-handoff-product-direction.md) is
input to the PRD, not a requirement.

## Latest work

[`docs/data/handoff-information-inventory.md`](../../docs/data/handoff-information-inventory.md): all 420 calls classified
(37 categories, 11 families; scripts in `docs/data/scripts/`, per-call table `docs/data/handoff-inventory-call-map.csv`),
sources inventoried, handoff payload and snapshot-vs-link proposed. It is DERIVED discovery, **not** the Stage 2 gate
(no samples, selection matrix or worked pairs yet) and approves no scope. Corrections to the audit and direction note's
keyword counts are recorded in its §10.2 (neither document edited).

[`docs/analysis/2026-10-20-meridian-company-service-profile.md`](../../docs/analysis/2026-10-20-meridian-company-service-profile.md):
company and service-context profile for later UX/UI work (outside sources S-170…S-180 added to the register). Reference
only; its brand directions A–C are exploratory and its §8 decisions are open.

[`docs/analysis/2026-10-20-human-handoff-consolidated-direction.md`](../../docs/analysis/2026-10-20-human-handoff-consolidated-direction.md):
decision-ready replacement for the original direction's §5 (C1 human access, C2 triage brief, C3 ownership, C4 sources,
C5 outcomes; proposed validation spike, not an SP-N). Decisions recorded later the same day (see below).

## Open choices (owners, not copied)

All product decisions are made (Innocent, 2026-10-20, three rounds); the table is the
[consolidated direction §11](../../docs/analysis/2026-10-20-human-handoff-consolidated-direction.md). **Do not re-ask any of them.**
Remaining:
- Meridian's real emergency number is needed before real use; the demo uses the placeholder (512) 555-0199.
- Partner deadline (GQ-20) unconfirmed; **internal target Wed 2026-10-21 06:00 CT** (`SUBMISSION.md`).
- Delegated to Claude: handoff lanes (after Stage 2) and demo default limits.
- Known accepted risk: the issued dataset goes into a **public** repository without a licence (audit L-8, Q-1).

## Next action

Stage 2 artifacts exist:
- samples;
- `docs/data/README.md` (the matrix);
- `docs/data/worked-pairs.md` (WP-1…WP-8);
- the page `docs/artifacts/2026-10-20-data-reality.html`.

**Stage 2 gate signed (Innocent ✓ 2026-10-20).** His WP-3 answer narrowed the urgent path: the emergency number and a
P1 case run only when the customer says someone is in danger because of no heat, no cooling or a leak (consolidated
§9.1, PRD R-8). WP-2: explain invoice lines as billed. WP-6: nothing beyond the KB.

**Stage 3 gate signed (Innocent ✓ 2026-10-20).** Register `docs/design/hard-problems.md`; page
`docs/artifacts/2026-10-20-hard-problems.html`. Choices:
- HP-1: his two-layer design plus turn-to-turn context (PRD §6.1, R-45);
- HP-2: C, with false alarms ≤ 10% (R-47);
- HP-3: no fee-bearing reschedule or cancel by the AI; a staff request instead (R-21, R-22). Roadmap now 77.9%, and
  22.1% with people;
- HP-4: B (R-46);
- SP-1 (turn latency and cost) approved for Stage 5.

**Stage 4 gate signed (Innocent ✓ 2026-10-20): PRD 0.4 approved.** Interview `docs/prd/inno-aea-callcenter-interview.md`
(completion gate holds); research `docs/research/2026-10-20-vendor-and-framework-facts.md`. Answers since the Stage 3 close:
- 10× written scale path;
- alerts on the page plus a restarting health check;
- traces in the VPS Langfuse v4 (localhost:3100; the Railway app needs a public route at deploy, with Innocent's yes);
- dev and sealed held-out split;
- Sonnet in every role by default; SP-1 compares Terra, Gemini Flash and Jev;
- a $30/day model cap.

**The fork:** the UX track runs in session `aea-call-center-ux-stages` (Innocent started it early). It was told PRD 0.4
reopens its UX-1. **This session takes the System track:** §5 spike SP-1 (latency, cost and correctness of the two-layer
turn), then §6 design. **Stage 5 closed (2026-10-21).** SP-1 ran on the VPS: mix **B** chosen (Jev plans and classifies, Sonnet 5.5 writes);
latency line **p95 ≤ 12.5 s at 20 at once** (measured 10.2 s); cost about $0.016 per conversation; 0 hard-gate failures in
190 conversations. Carried into Stage 6:
- the actions-across-turns fix (R-45);
- stating the 12-month minimum;
- keeping the Sonnet call count down for the 429 acceleration limit;
- Jev's unstated retention as an accepted known limit;
- Stage 9 re-measures against 12.5 s.

**Stage 6 closed (Innocent ✓ 2026-10-21):** system design approved; DO-1…DO-7 in `docs/design/`; DO-4 agrees with the signed UX-3 contracts (22 CONs). **Working copy moved to the VPS 2026-10-21.** **Next:** §7 tickets (the join of both tracks; the scope cut line is the first question there) and UX-4 (prototype), both on the VPS.

**Parked code (set aside 2026-10-21, Innocent "d2 set aside"; now `docs/parked/2026-10-21-first-attempt/`, reference only, never imported):** (original note:) `pyproject.toml`, `src/meridian/`, `data/kb_transcriptions/` and `var/` were
written 19:25–19:40 CT before the shortcut was withdrawn. They are untouched, uncommitted, and wait for the §8 build
stage. Innocent decides whether they are kept. `.env` holds the model keys (git-ignored).

**Uncommitted:** everything since snapshot `ed4ca89`. Commit only when Innocent asks.

## UX track (started 2026-10-20 ~21:05 CT, beside Stage 4)

Innocent: "while i settle things with aea investors stage 4 lets start the ux stages". A separate session runs the
Stage 4 interview (`docs/prd/inno-aea-callcenter-interview.md`); the UX session does not edit PRD files.
- **UX-1 closed** (Claude, no sign-off, standing policy) on PRD v0.2: `docs/ux/01-planning/`, page
  `docs/artifacts/2026-10-20-ux-planning.html`. **If Stage 4 changes the PRD, UX-1 reopens.**
- **Fork:** the System track (§5 SP-1 → §6) needs its own session; Innocent opens it.
- **UX-2 in progress:** directions (A1 Work order recommended, A2 Route sheet, A3 Dispatcher's log) in
  `docs/design/DESIGN-DIRECTIONS.md`; behaviour findings in `docs/ux/02-concepts/REFERENCES.md`; concepts C2 chat + S2
  case view recommended in `CONCEPTS.md`; clickable A1/A2 direction prototypes in `docs/artifacts/2026-10-20-direction-*.html`.
  **UX-2 reopened:** A2 was chosen, then replaced by A3 ("A1 and A2 were very similar"); then an A4 Account statement was
  requested. A3 prototype and A4 look sheet are built; **UX-2 signed 2026-10-21: A5 Service desk (light first), C2, S2.** **UX-3 signed by Innocent 2026-10-21** (page `docs/artifacts/2026-10-21-ux-structure.html`); contracts handed to the System track. R-48 demo login + role switch added (UX-1 re-closed). **Next: UX-4 on the VPS,** the real frontend on a Prism mock of the OpenAPI (it must add the login, the role switch, TURN_TIMEOUT/BUSY cards and follow design.md's mint rule, which the A5 choice prototype predates). **Paused for the move to the VPS.** C2 + S2 stand. UX-3: IA.md and
  SCREEN_SPECS.md written (N-1…N-27 contract needs); `design.md` waits for the pick (A2 draft in `docs/design/_superseded/`);
  CON cards + OpenAPI on hold until Innocent says to restart them.
- Carry to UX-3: the safety card keeps Meridian's words exactly (numbered layout only); the stack question (PRD §6.2
  server-rendered vs the pipeline's React default); demo bar and staffing banner never use warning styling.
- **Split (Innocent, 2026-10-20):** System track (SP-1, then §6) runs on the VPS copy
  `claude-vultr:/home/linuxuser/workspaces/inno-aea-callcenter`; the UX track stays on this Mac copy. Ownership:
  `docs/analysis/spikes/HANDOFF-SP1-VPS.md` (Mac: `docs/ux/**`, the ux-planning page and `_build`, the CONs; VPS:
  `docs/analysis/spikes/**`, `spikes/sp1/**`, later `docs/design/system-design.md`). Shared files (PRD, checklist, this
  note, source register, hard-problems.md) are copied by hand, never automatically.
- **Update (late 2026-10-20):** Stage 6 (System track) now runs on the **Mac** in the planning session, not the VPS. It owns
  `docs/design/system-design.md`, `readiness-report.md`, `evaluation-plan.md`, `observability-contract.md`,
  `key-metrics-registry.md`, later `code-design.md` and `docs/design/contracts/` (DO-4, starting from the draft CONs).
  The UX session owns `docs/ux/**`, `docs/design/DESIGN-DIRECTIONS.md`, `docs/design/references/`, `docs/design/design.md`
  and `docs/design/_superseded/`. N-26's per-turn deadline and error code come from §6 once Innocent confirms.

## Journey protection (2026-10-21, Riverside lesson)

- **What changed.** New rule `.claude/rules/integrated-journeys.md`:
  - browser → real server → a disposable DB copy, with guards on and a scripted model;
  - journeys check what the user sees and what was stored;
  - contract and prompt ↔ consumer checks;
  - live smoke;
  - evidence records with three levels.

  The project copy of `build-loop-test-scope.md` was re-copied from the workspace original. Its *AEA addition* puts
  journeys in the merge gate. Checklist §8 has three new unticked lines.
- **Executable today: nothing.** `tests/` and `eval/` are empty. `apps/web`'s Playwright suite runs only on Prism with
  dev-only sign-in, so it counts as `mock-tested`.
- **Waits for:**
  - AEA-57 and AEA-59 (wave 2);
  - AEA-58 and AEA-60 (wave 3). Their rows come from the slice-plan amendment.
  - Browser journeys also wait on AEA-49, which waits on the UX-4 sign-off. UX-5 and AEA-55 stay the visual and
    accessibility gate.

## Stage 7 (VPS session, started 2026-10-21 ~01:00 CT)

Started before UX-5 by Innocent's decision (checklist *Skips*). **7a draft:** `docs/plans/slice-plan.md` (57 tickets, 9 waves). **Waiting on Innocent:** sign-off of 7a, which tickets are `risk::security`, and the cut line against the 06:00 CT target (slice-plan §5). Nothing published; 7b–7d not started. UX-4 owns `apps/web/**`; this session touches `src/`, `tests/`, `eval/`, `data/`, `pyproject.toml`, §7–§8 lines only.

## Stage 7 closed (2026-10-21, Innocent: D-1 yes, D-2 set aside, D-3 sign-off)

62 tickets published as GitLab issues #1–#62 (project 2318; issue number = ticket number). Local `main` holds the whole tree
(`ca9ab5c`, then a small docs commit); **nothing is pushed**: the first push must merge GitLab's README commit
(`--allow-unrelated-histories`, keep our README, no force). Parked first-attempt code is reference-only at
`docs/parked/2026-10-21-first-attempt/`. **Next:** Stage 8, waves 0–1 (AEA-01…25) with the prompt in
`docs/plans/BUILD-PROMPT-waves-0-1.md`. Open decisions D-4…D-15 are in `docs/plans/stage7-signoff.md` (tickets are built on the
recommended option). The UX session takes `docs/plans/ux-join/FOR-UX-SESSION.md`.

## Stage 8: AEA-07 landed (2026-10-21)

`docs/technical-documentation.md` (D-4) is drafted: 13 sections, every number either measured on the issued data or `pending`
(chunk count: AEA-16; eval numbers and test-results link: Stage 9; URL: AEA-56). `SUBMISSION.md` D-4 reads *drafted, numbers
pending Stage 9*. **Next action for its owners:** AEA-16 replaces the chunk-count line in section 5; AEA-24 and Stage 9 replace
the `pending: Stage 9` lines in sections 1, 5, 8 and 10; AEA-25 (README) and AEA-54 (deployment guide) link to it; whoever
records Innocent's answers on DAT-1, DAT-2, DAT-3, DAT-4, WEB-1, CAS-16 and GRC-3 updates section 12 and the section each names.
Progress per ticket is in `.claude/state/build-ledger.md`.

## Stage 8: AEA-08 landed (2026-10-21)

DO-3 (`docs/design/code-design.md`) is at **revision 3**: it carries the slice plan's three deviations (AEA-10 writes every DDL
file and owns `repos_cases.py`; cross-ticket reads and reset clearing live in `repos_core`; one route file and one schema file per
ticket), the modules the Stage 7 addenda added, and a recounted module total (103). The area map (with a *Tickets* column),
`api-con-mapping.md`, DO-4 and `system-design.md` follow it; every area-map row is still *planned*. **Next action for
the build tickets:** each changes only its own area-map row (planned → actual + commit). The stale lines in the UX-owned
documents are listed on issue #8 for the UX session; Innocent's two open items from the UX join (decisions 5 and 6) are still his.

## Stage 8: AEA-25 landed (2026-10-21)

The root `README.md` is the reviewer's front door: eight sections (What this is, Try it, Results, How to run it locally, What is in the
repository, Monitoring and the feedback loop, Documents, History). Every result reads `pending: Stage 9`; the demo login is "provided
with the submission" (DAT-3 option B); held-out keys are described as kept outside the repository (DAT-2 option B). `SUBMISSION.md` D-3
reads *run instructions written; containment pending Stage 9*. **Next action for the owners:** each ticket replaces only its own
`pending:` line: AEA-02 (`.env.example`, the env-names line), AEA-16 (ingest), AEA-23 (start command), AEA-24 (eval commands),
AEA-49/55 (screens), AEA-50 (Docker), AEA-54 (deployment guide link), AEA-56 (URL), Stage 9 (results, test-results link).
