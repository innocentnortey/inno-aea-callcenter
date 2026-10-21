# Stage 7 sign-off: what is ready, and what only you can decide

**Date:** 2026-10-21. Written for Innocent. Nothing here is ticked, committed or published; those need your yes.

## Where Stage 7 stands

| Item | State |
|---|---|
| Tickets | **62** (56 build-loop, 4 direct, 2 human), `risk::security` on 17. Specs: `docs/plans/tickets/AEA-01…62.md` |
| Waves | 0 to 6; widest wave W2 (26 tickets); critical path 7 waves. Blocker graph reconciled with the slice plan: no cycles, no wave moved by the amendments |
| Journey protection (Riverside lesson) | In every build-loop ticket as one `[journey]` AC; rule `.claude/rules/integrated-journeys.md`; harness AEA-57, browser journeys AEA-58/62, live smoke AEA-61 (needs your spend line) |
| Coverage audit (7c) | 173 requirements; matrix filled (491 rows). Checker: **15 known problems left**, all explained in the audit's *Findings* table |
| UX join | `docs/plans/ux-join/`: 94 findings from three audits (63 for the UX session, 24 for backend tickets, 7 for you). `FOR-UX-SESSION.md` is the page to hand the UX session |
| Not yet done | 7d: labels and issues on GitLab project 2318. Waits for your sign-off below |

## Decisions that block starting wave 0

**D-1 · Commit the working tree to local `main`?** (recommended: yes, whole tree.) Worktrees are cut from `main`, which today has one commit; everything since is untracked, so build agents would see no contracts, tickets or OpenAPI. Explicit paths, never `git add -A`; `.env`, `var/`, `.venv/`, `node_modules/` are already ignored. A push is a separate yes (first push builds on your README commit, no force). Detail: `ux-join/decisions-for-innocent.md` §3.

**D-2 · The parked code (AEA-01 needs-decision).** `pyproject.toml` and `src/meridian/` already exist uncommitted from an earlier attempt. Keep them as the base for AEA-01, or move them aside so AEA-01 scaffolds fresh? Recommendation: set aside (a pointer note in AEA-01), since design changed (no templates, no jinja). Your call: **keep or set aside?**

**D-3 · Sign off the breakdown (7a/7b/7c):** the 62-ticket cut with the journey amendment (slice plan §0a), the specs, and the coverage audit with its 15 known gaps. Checklist ticks need your own "Innocent ✓".

## Decisions that can wait (each names the wave it first blocks)

| # | Decision | First blocks | Recommendation |
|---|---|---|---|
| D-4 | WEB-1: which files may load before the demo login | AEA-49 (W2) | A (works with the app as built) |
| D-5 | Add `CaseDetail.events.last_event_id` to the signed OpenAPI | AEA-45 (W2) | Add it |
| D-6 | A 410 on the chat stream for an ended chat | AEA-41 (W2) | No |
| D-7 | Login-throttle message (two signed specs disagree) | AEA-23/58 | Separate line |
| D-8 | After signing in again, resume the chat or start fresh? (R-W-12) | AEA-40/58 | Start fresh |
| D-9 | CON-4 ("talk to a person" button) builds no brief; drop WF-2 from R-28, M-11, M-12, DC-11, DC-13, NFR-1, NFR-5, or give it one | coverage only | Drop WF-2 (matches the signed web design) |
| D-10 | Stage 9 (real eval and load runs) has no ticket; harness proves each measure, thresholds are measured later | coverage only | Treat as Stage 9 work, not a ticket now |
| D-11 | R-36 ("never store a code, card or contact value"): keep "all workflows" or narrow to the 10 that handle one (part 2 proposal, applied in the audit as a proposal) | coverage only | Narrow |
| D-12 | R-21 "supervisor alert at once" has no contract field for a P2 case booked more than 4 hours ahead | AEA-52 (W3) | Accept the limit; no contract change |
| D-13 | Wall-clock control for the journey harness (AEA-57 AC-17): no contract gives it | AEA-57 (W2) | Add a test-only seam in the settings overrides; needs your yes because it touches web.md §15 |
| D-14 | Earlier open items: DAT-1 (mask names before Jev/Langfuse), DAT-2 (held-out key custody), DAT-3 (demo password in public README), DAT-4 (Langfuse route), CAS-16, GRC-3 | W1 to W3 | in `docs/plans/7b-decisions/` |
| D-15 | Per-run spend statement for the live smoke (AEA-61) | AEA-61 (W4) | Set before wave 4 |

Engineering choices made without you (overrule any): the customer's speaker name on staff screens is "Customer" (staff.md §7), `HealthEvent`/`DeployRecord` get the DO-6 fields in cases.md, live actions do not change a case's version, and the deploy image copies the OpenAPI into the web stage.

## What happens after your yes

1. You answer D-1 to D-3 (the rest can follow). I commit, then create the labels and 62 issues on project 2318 (`env -u GITLAB_TOKEN glab`).
2. Wave 0 and 1 start together: 25 tickets, Opus planners then Sonnet implementers, frozen tests first on `risk::security` tickets, affected tests only, journey suite at merge.

## Decisions taken (Innocent, 2026-10-21: "ill take all your recommendations")

D-4 to D-15 are all decided as recommended: D-4 WEB-1 option A; D-5 add `CaseDetail.events.last_event_id` (the OpenAPI edit is made by the UX session, see `ux-join/FOR-UX-SESSION.md`); D-6 no 410 on the chat stream; D-7 a separate throttle message; D-8 start a fresh chat after signing in again; D-9 drop WF-2 from the seven requirements (audit updated); D-10 Stage 9 stays Stage 9 work (the seven eval gaps are accepted); D-11 narrow R-36 to the 10 workflows; D-12 accept the supervisor-alert limit, no contract change; D-13 add a test-only wall-clock override to `ContainerOverrides`; D-14 the DAT/CAS/GRC items stay on their recommended options; D-15 the spend line is still to be set before wave 4 (a statement, not a choice).
Applied: held amendments AEA-29-5, AEA-45-2, AEA-58-3, AEA-58-4, AEA-62-3; wall-clock seam in web.md §15, AEA-23, AEA-57. **Still needs Innocent:** only the AEA-61 spend line (before wave 4) and a yes to the UX session making the OpenAPI edit.
