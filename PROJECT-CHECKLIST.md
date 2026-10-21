# Project Checklist — inno-aea-callcenter

Sequence: `zero-to-hero` **v1.9.0** (template file still reads v1.6.0; Stage 0 follows `ARTIFACT-MAP.md` §0, incl. the *Build loop* set) (`Nortorious-Technologies/.claude/skills/zero-to-hero/`).
Artifact paths: that skill's `ARTIFACT-MAP.md` (§ numbers below match).

| Field | Value |
|---|---|
| Project | inno-aea-callcenter — AEA Investors, *AEA FDE Challenge: AI Call Center Agent* |
| Kind | hiring partner (AEA Investors, via Gauntlet AI) |
| Mode | light (2–3 day brief timebox) |
| Started | 2026-10-14 as `inno-aea-onboarding`; **re-initialized 2026-10-20** for the call-center brief (issued 2026-10-19). The 2026-10-14 checklist is at tag `project-1-onboarding-snapshot` |
| Deadline / internal cutoff | partner deadline **unconfirmed** (GQ-20); AEA interview Thu 2026-10-22 / **internal target Wed 2026-10-21 06:00 CT** (Innocent, 2026-10-20). See `SUBMISSION.md` |
| Layout substitutions | GitLab rule carried as short `.claude/rules/project-provenance.md` · issued data in `docs/data/issued/` (read-only) · dev log central in `Gauntlet AI/devlogs/aea-callcenter/` · Project 1 history in `docs/archive/project-1-onboarding/` |
| Context system | [ICM progress checklist](.claude/state/icm-progress.md) — tracks `.claude/` maturity; its rows are not copied here |
| Setup profile | [`.claude/reference/setup-profile.md`](.claude/reference/setup-profile.md) — owners, locations, adopted rules |

**How to use.** Tick an item when its artifact exists at the mapped path. A gate line is passed
only with evidence, and a ★ gate only with `Innocent ✓ YYYY-MM-DD`. Up to the fork, the first
unticked gate is where the project is; after it there is one current gate per track (headings marked
**UX track** and **System track**), and §7 waits for both. A stage skipped goes under *Skips* with its reason.

**Ownership after the fork (two sessions):** the UX session ticks the §4b rows and owns the contract
files (`docs/ux/03-structure/UI_CONTRACTS.md`, the OpenAPI); the System session ticks §5–§6 rows and
requests contract changes rather than editing them. Whoever reaches §7 first waits for the other's gate.

---

## 0 · Scaffold  (§0)
- [x] `PROJECT-CHECKLIST.md` (this file) filled in — 2026-10-20 (fresh from the template)
- [x] `CLAUDE.md` entry point (+ `AGENTS.md` if Codex works here) — rebuilt 2026-10-20 from `icm-project`'s entry template
- [x] Principles pack, both halves: `Gauntlet AI/principles/` → `docs/principles/` (incl. `system-design.md`), and rules → `.claude/rules/` with a provenance line each: general (incl. `system-design-conversation`, `system-design-questioning`, `problem-framing`, `business-metrics`) · Gauntlet policy · hiring partner · legacy (OpenEMR only) · **build loop** (`build-loop-test-scope`) — 2026-10-20: `docs/principles/` GP-1–GP-144 (17 files, identical to originals); rules incl. the four new ones; dispositions in the setup profile; legacy excluded
- [x] Context system bootstrapped by **invoking** `icm-project` (Phases 1 and 3; version recorded in `icm-progress.md`): `CLAUDE.md` from its entry template, `.claude/README.md` router, `rules/context-maintenance.md`, dev-log home, `.claude/state/icm-progress.md`; `CLAUDE.md` and the router both link the ICM checklist — 2026-10-20, `icm-project` 1.5.0 invoked (Phases 1 and 3); dev-log home central
- [ ] Remote and host set per policy (Gauntlet: GitLab `origin`, Railway) — *local git only (snapshot `ed4ca89`); GitLab project not created (Innocent); Railway not set up*
- [x] `SUBMISSION.md` opened (Gauntlet) — 2026-10-20, call-center deliverables (portal five + PDF three)
- **Gate:** ☑ pack present, checklist filled, `icm-progress.md` exists and is linked from `CLAUDE.md`, `check_context.py` reports no FAIL — 2026-10-20 (checker: "ok all"; remote/host item still open, it does not block Stage 1)

## 1 · Frame  (§1)
- [x] Sources converted and ranked in `docs/source/` — 2026-10-20: briefing (portal + PDF) S-100/S-101; issued data S-102…S-105; register
- [x] Brief audit: traps, real problem, real guideline — `docs/analysis/2026-10-20-brief-audit.md` (2026-10-20); DEC-1…DEC-5 decided by Innocent 2026-10-20 (status: consolidated handoff direction §11)
  - *Input for the items below (not a template item):* `docs/analysis/2026-10-20-human-handoff-product-direction.md` — ranked handoff features, ideation only
- [x] Problem behind the brief: why-chain, assumptions marked, each metric's hop chain to money, north star named (GP-120 – GP-130) — 2026-10-20, audit § *The problem behind this brief*
- [x] Metrics chosen: health vs value groups, leading + lagging pair per branch, decision line / denominator / baseline / aspiration / hard gate per metric (GP-131 – GP-144) — 2026-10-20, `docs/delivery/2026-10-20-angle-and-demo-framing.md` §2; "our targets" await Innocent's sign-off at the gate
- [x] Two-layer success framing + metrics tree — 2026-10-20, `docs/delivery/2026-10-20-angle-and-demo-framing.md` §1–§3
- [x] PRD draft — `docs/prd/inno-aea-callcenter-prd.md` (0.1 at this tick; now 0.3, 2026-10-20; reviewed against the audit, profile and consolidated direction, review log §11)
- [x] Stage 1 **visual** review page — `docs/artifacts/2026-10-20-inno-aea-callcenter-prd.html` (rebuilt ~19:55 CT with all seven Markdown sources and the agent flow; check: 0 fails, 0 warnings; diagrams inspected at 1280 px, layout at 500 px), built per spec: built after the Markdown (problem, journey, metrics chain, scope and cuts, evidence limits, approval request); `check_review_page.py` passes; inspected at laptop and phone width; linked from `.claude/README.md`
- **Gate:** ☑ audit + framing signed off — Innocent ✓ 2026-10-20 ("yes to all": scope, targets, foundation answers; the bundled stage-shortcut item was withdrawn the same day, see Skips note)

## 2 · Data reality ★  (§2)
- [x] Samples in `docs/data/samples/` (full 20–50 · light ~10) — 2026-10-20: 14 (10 transcripts, 3 KB items incl. the PNG, 1 DB extract)
- [x] Selection matrix: every source, every type, the strange ones — `docs/data/README.md` (2026-10-20; new data findings D-11…D-13)
- [x] Worked pairs `WP-1…` in `docs/data/worked-pairs.md` (full 5–10 · light 3), each marked easy/hard and sure/uncertain — 2026-10-20: WP-1…WP-8; WP-2, WP-3, WP-6 uncertain
- [x] Synthetic stand-ins labelled with their assumption — 2026-10-20: WP-2, WP-3, WP-4, WP-8 keep the transcript's words with a DB record substituted (README)
- [x] Stage 2 **visual** review page — `docs/artifacts/2026-10-20-data-reality.html` (check: 0 fails, 0 warnings; inspected at 1280 and 500 px) (coverage matrix + side-by-side worked pairs), built after both Markdown files; check passes; inspected at both widths; linked from `.claude/README.md`
- **Gate:** ☑ every core workflow has pairs; every uncertain pair checked — Innocent ✓ 2026-10-20 (WP-2, WP-3, WP-6 answered; WP-3 narrowed OD-4 (ii) / R-8)

## 3 · Hard problems ★  (§3)
- [x] Register `docs/design/hard-problems.md`: HP-1 orchestration + one card per hard problem + *Handled by default* list (2026-10-20; light mode: 4 cards)
- [x] Every `hard` worked pair maps to a card (WP-2 → HP-3, HP-4; WP-3 → HP-2, HP-3; WP-4 → HP-3; WP-6 → HP-2; WP-8 → HP-4)
- [x] Each card: evidence pairs, why hard, options with diagrams, recommendation, principles, success measure
- [x] `docs/principles/system-design.md` questions walked (register's last section); open ones are cards or interview options (none new; GP-112 and GP-110's timing points go to Stage 6)
- [x] Stage 3 **visual** review page — `docs/artifacts/2026-10-20-hard-problems.html` (check: 0 fails, 0 warnings; inspected at 1280 and 500 px, light and dark), built after the register; linked from `.claude/README.md`
- **Gate:** ☑ Innocent has worked through the page — Innocent ✓ 2026-10-20 (HP-1 his two-layer design + turn-to-turn context, R-45; HP-2 C with false alarms ≤ 10%, R-47; HP-3 no fee-bearing change or cancel by the AI, R-21/R-22; HP-4 B, R-46; SP-1 approved for Stage 5)

## 4 · Interview ★  (§4)
- [x] `prd-interview` run *after* §3, fed the register (page choices recorded, not re-asked) — `docs/prd/inno-aea-callcenter-interview.md`, 2026-10-20; 46 answers carried, batch 1 (Q-029) answered
- [x] Every HP choice in the decision record (consolidated §11 *Stage 3 choices*; PRD §10/§11; register HP-1…HP-4)
- **Gate:** ☑ PRD approved — Innocent ✓ 2026-10-20 (PRD 0.4; interview `docs/prd/inno-aea-callcenter-interview.md`, completion gate holds)

## 4b · UX-1 user stories ★  (§4b) — the fork; starts once the PRD is approved
*Via the `ux-pipeline` (UX-1); projects outside it use `ARTIFACT-MAP.md` §4b's list.*
> **Early start (Innocent, 2026-10-20 ~21:05 CT):** "while i settle things with aea investors stage 4 lets start the ux stages". UX-1 is drafted on **PRD v0.2 before the §4 gate**; it is an overlap, not a skip (§4 still runs in full). Any PRD change from Stage 4 reopens UX-1 and everything after it.
- [x] User stories `US-1…` (`docs/ux/01-planning/USER_STORIES.md`): As a <who> I need <what> so that <why>; each links its PRD requirement, WP-N and screen; every core flow covered — 2026-10-20: US-1…US-27 across five users; 45 requirements in scope (R-42, R-43 have no screen)
- [x] Flows with a draft `CON-N` on every data step (`USER_FLOWS.md`) and a sitemap (`SITEMAP.md`); `trace_check --upto FLOW` passes — 2026-10-20: 7 journeys, FLOW-1…FLOW-12, error-branch table, CON-1…CON-20 (drafts), SCR-1…SCR-11; `trace_check` 0 fails at `--upto FLOW`, `SCR` and `CON`
- [x] UX-1 review page `docs/artifacts/2026-10-20-ux-planning.html` (journeys, all 12 flows, sitemap, coverage grids, draft CON list; `check_review_page.py` 0 fails, 1 word-count warning from required diagram text; inspected 1280/500, light and dark). Rebuild: `python3 docs/artifacts/_build/ux-planning/gen_ux1.py .` (refuses to build over a changed source until the diff is read)
- **Gate:** ☑ UX-1 done-when holds and the page passes — Claude, 2026-10-20, no sign-off (standing policy, `ux-pipeline` phases.md UX-1). **Reopened again 2026-10-21** for PRD R-48 (one demo login gates the whole deployment; one-click role switch; Innocent): adds US-28, SCR-12 login, SCR-4 as the role switch, CON-22; **re-closed 2026-10-21 (Claude, no sign-off):** trace_check 0 fails (46 reqs, US=28, FLOW=12, SCR=12, CON=22), page rebuilt (0 fails). Earlier: **reopened and re-closed the same night** for PRD v0.4 (Stage 4 gate): R-35 (alerts on the page, health-check restart), R-36 (traces stay on the VPS), R-38 (dev and sealed held-out splits) applied to US-27, FLOW-11, SCR-10, SCR-11, CON-19, CON-20; trace check 0 fails; page rebuilt (0 fails)

> **▶ FORK — open a second session for the System track now (§5 spikes → §6 design).**
> Launch it on the same machine or VPS as this project's working copy, on the same model as this session
> (`~/.claude/rules/match-model-on-vps.md`). It reads first: the PRD, `docs/ux/01-planning/USER_STORIES.md`,
> the draft CONs in `USER_FLOWS.md`, `docs/design/hard-problems.md`, `docs/data/worked-pairs.md`.
> Its first gate is §5's. This session continues with the UX track below.

## 4b · UX/UI ★  (§4b) — UX track: UX-2 → UX-5
- [x] UX-2 concepts: Dribbble texture directions, behaviour research on live products with captured images (`docs/ux/02-concepts/`, `docs/design/DESIGN-DIRECTIONS.md`), a direction chosen — Innocent ✓ 2026-10-20 ("lets go with A2 light mode and yeah you have my approval"): ~~D1 = A2 Route sheet~~ **D1 changed the same night to A3 Dispatcher's log** (Innocent, ~23:05 CT: "ill be honest i actually didnt like either of the uis you showed me A1 and A2 were very similar i want to go with A3 its nicer on the eyes"); light mode first (carried over, assumption); D2 = C2 and D3 = S2 unchanged. A3 had no built screens, so an A3 prototype is built for him to confirm. 12-hour times stay a condition. **Gate reopened ~23:20 CT:** he asked for an A4 ("utility professional but soft on the eyes"); A4 Account statement shown as a quick look sheet (`docs/artifacts/2026-10-20-a4-look-sheet.html`); A3 built (`docs/artifacts/2026-10-20-direction-A3-dispatchers-log.html`). **Then** he said he doesn't like the colours so far and pointed at Dribbble's "Kirridesk: AI customer service with reply regeneration" ("more stuff like this"): **A5 Service desk** look sheet `docs/artifacts/2026-10-20-a5-look-sheet.html`. **Narrowed (Innocent, ~00:00 CT):** "okay so drop everything except for A5 thats really goot lets do one more … https://dribbble.com/shots/27664920-Customer-Service-Workspace the issue will be turning it into a chatbot look". **A1–A4 dropped; A5 kept; A6 requested** from the "Customer Service Workspace" shot (look sheet with a chatbot translation). **Picked: A5 Service desk — Innocent ✓ 2026-10-21 ("alright we're going with A5, use parallelization as much as possible to finish (use sonnet)")**; C2 + S2 unchanged; light first
  - *Work done 2026-10-20 (history; gate passed 2026-10-21 on A5):* directions A1/A2/A3 (`docs/design/DESIGN-DIRECTIONS.md`, 15 credited Dribbble shots); behaviour research R1–R4, 19 findings (`docs/ux/02-concepts/REFERENCES.md`); concepts C1/C2, S1/S2 (`CONCEPTS.md`); clickable A1 and A2 prototypes (`docs/artifacts/2026-10-20-direction-A1-work-order.html`, `…-A2-route-sheet.html`); wireframes `docs/ux/02-concepts/wireframes/`; review page `docs/artifacts/2026-10-20-ux-concepts.html` (check 0 fails, 0 warnings). Decided: **A5 Service desk** (light first; picked 2026-10-21) + C2 + S2; the history of A1–A6 is in the line above
- [x] UX-3 structure: IA, screen specs with every state, `docs/design/design.md` (UI-2 template), UI contracts signed (CON cards + OpenAPI; lints, mocks); `trace_check --upto CON` passes — Innocent ✓ 2026-10-21 ("i approve you can stop here for now soon we will switch to the vps")
  - *Built and signed 2026-10-21:* `docs/ux/03-structure/IA.md`, `SCREEN_SPECS.md` (12 screens × 8 states, 82 real), `docs/design/design.md` (A5, 179 tokens, AA both themes), `UI_CONTRACTS.md` + `ui-contracts.openapi.yaml` (CON-1…CON-22, 30 operations; redocly 0 errors; Prism smoke test passed; all 22 agree with §6 DO-4, UXR-1…27 closed); A5 prototype `docs/artifacts/2026-10-21-direction-A5-service-desk.html`; review page `docs/artifacts/2026-10-21-ux-structure.html` (0 fails)
- [x] UX-4 prototype in the project's **real frontend folder** on the Prism mock (mock-only machinery in a dev-only layer; types generated from the OpenAPI) — Innocent ✓ 2026-10-21 ("yes you have my sign off")
  - *Built 2026-10-21:* `apps/web/` (React 19, Vite, TypeScript, Tailwind, shadcn/ui); Prism 4019, Vite 5184; plan `docs/ux/04-prototype/PROTOTYPE_PLAN.md`; review page `docs/artifacts/2026-10-21-ux-prototype.html`. Checks (orchestrator rerun): lint, typecheck, 2,614 unit tests, build with no dev layer in dist, sweep of every scenario with axe at 1280/390 (desktop 494 passed, phone 257 passed, 0 failed). **All mock-only; no real backend exists.** Integration dependencies and unverified behaviour: `docs/ux/04-prototype/INTEGRATION_HANDOFF.md`. The nine review-page decision cards (D-1…D-9) were not answered by this sign-off; they stay open.
- [~] UX-5 verify (first run): **skipped by Innocent 2026-10-21** ("skip it all we've done enough testing"; see Skips). Not done: `TRACEABILITY.md` (`trace_check.py`), Lighthouse, `QA_REPORT.md`. Done anyway as part of UX-4: Playwright + axe sweep of every scenario at 1280/390, light and dark (mock-only). Second run ("UI verify again", §8) is NOT skipped.
- **Gate:** ☐ UX-5 signed off (closes the UX track) — Innocent ✓ ____

## 5 · Spikes  (§5) — System track
- [x] `SP-N` record for every card not yet `chosen`: brief + pass line first, frozen scoring harness, options built **in parallel by fan-out agents**, harness re-run by the orchestrator on each branch (`references/spikes.md`) — SP-1 `docs/analysis/spikes/SP-1-two-layer-turn-latency-cost.md`, run on the VPS 2026-10-20/21; harness digest `41c46ad927b3d6ca` unchanged across runs; build `b030228` (planner → implementer); $3.94 of the $10 cap; branches kept as `archive/spike/SP-1-*` (also fetched to the Mac)
- [x] Innocent has read each SP result — Innocent ✓ 2026-10-21: chose model mix **B** (Jev plans and classifies, Sonnet writes) and a latency line of **p95 ≤ 12.5 s at 20 at once** (measured 10.2 s); "we reached a verdict … we are confident"
- [x] Any spike result that changes what a screen needs raised with the UX session as a contract change — 2026-10-21: the waiting state for replies up to about 12.5 s, and completed actions read from conversation state (R-45), sent to `aea-call-center-ux-stages`
- **Gate:** ☑ no HP card is `open` — 2026-10-21: HP-1 `proven (SP-1)` for B; HP-2, HP-3, HP-4 chosen (Innocent ✓ 2026-10-20)

## 6 · Design  (§6) — System track
- [x] **Foundation questions answered by Innocent before DO-1** (`.claude/rules/system-design-questioning.md`): SD-3.1 load target + scale path, SD-3.4 peak/concurrency, SD-7.2 failure to survive, SD-1.6 spend ceiling, SD-1.9 hardest uncertainty. Each recorded with date and his words in the readiness report and the PRD decision table; none filled by a test load, default or public count — 2026-10-20/21: PRD §10 (SD-3.1 with the 10× path, SD-3.4, SD-7.2, SD-1.6 at $30/day, SD-1.9), interview Q-029/Q-061, readiness report
- [x] `system-design-readiness` READY — `docs/design/readiness-report.md`, 2026-10-21: 0 Missing (58 Found/Decided, 1 Assumed SD-7.3, 1 N/A); register holds at the readiness gate
- [x] DO-1…DO-7 written at their mapped locations; DO-4 starts from the UI contracts (draft CONs, then the UX-3-signed set) — 2026-10-21: `docs/design/` (system-design, code-design, contracts/, evaluation-plan, observability-contract, key-metrics-registry); DO-4 reconciled: 21/21 CONs agree with the UX-3 specified set (UXR-1…26 adopted); metz review PASS
- [x] Code design recorded: `.claude/reference/area-map.md` with planned paths labelled planned; router rows added; ICM "code design" row updated with evidence — 2026-10-21: area map from DO-3 (all paths planned), router rows per area, ICM row established
- [x] Entry rebuilt: `icm-project` Phase 3 re-run so `CLAUDE.md` and the router follow the entry template against the area map; fresh-context walkthrough done and its ICM row verified; `check_context.py` reports no FAIL — 2026-10-21: CLAUDE.md rebuilt (70 lines, 6.4 KB); walkthrough verified; check_context no FAIL
- [x] DO-5 eval plan: worked pairs as the first dev set, HP success measures as criteria, error-analysis-first rule — `docs/design/evaluation-plan.md` (WP-1…WP-8 + WP-4 fee-free as dev set; HP criteria; error-analysis-first; EVQ-1 = A split)
- [x] Stage 6 visual review page `docs/artifacts/YYYY-MM-DD-system-design.html`: a story-first study guide with every DO-1/DO-2 finding (`check_review_page.py` passes; inspected at laptop and phone width) — `docs/artifacts/2026-10-21-system-design.html` (check 0 fails; inspected at 1280 and 500 px, light and dark; reviewed and approved by Innocent 2026-10-21)
- [x] Questions raised while designing: each new choice is an `SDQ-N` (asked, or drawn as a labelled proposal with a `data-ask` card); any answer the numbers undercut was put back to Innocent, not changed silently; pre-gate sweep leaves no foundation item proposed or defaulted — 2026-10-21: SDQ-1…10 and EVQ-1 answered by Innocent (SDQ-1 changed to 60 s); undercut answers (Q-054 split) re-asked, not changed silently; no foundation item proposed or defaulted
- **Gate:** ☑ `design_outputs.py check … --gate tickets` passes; DO-4 agrees with the signed contracts; Innocent reviewed DO-1/DO-2 and the current Stage 6 page ✓ 2026-10-21 ("yeah i approve") (closes the System track)
  - 2026-10-21: `design_outputs.py --gate tickets` passes (all seven outputs `ready`); metz review PASS. **Innocent's call:** the UXR-27 login change ("that shouldn't affect us finishing the system design gate") does not hold this gate. DO-4 agrees with the UX-3 specified set on 18/21 CONs; CON-7, CON-9 and CON-10 follow UXR-27 and are re-checked at the start of §7. *(Same day: UXR-27 adopted; all 22 CONs now agree.)* Waiting only on Innocent's review of DO-1/DO-2 and the Stage 6 page.

## 7 · Tickets — four passes ★  (§7) — the join
- [ ] Both tracks closed: the UX-track gate (UX-5) and the §6 gate are ticked
- [x] 7a Slice plan `docs/plans/slice-plan.md` — Innocent ✓ 2026-10-21 ("you have my permission … we're just going to build"; then "i approve lets move on"). **Recut the same day on Opus with the `to-tickets` skill at his instruction:** 56 tickets, 6 waves (9/16/24/4/2/1), critical path 6, 50 build-loop / 4 direct / 2 human, 7 `risk::security`; parallelism audit and collision map in the plan **Updated 2026-10-21 (later): 62 tickets, waves 0–6 (9/16/26/6/3/1/1), 56 build-loop / 4 direct / 2 human, critical path 7 waves, after the journey-protection amendment (slice plan §0a) and the UX↔backend join (`docs/plans/ux-join/`). Innocent ✓ 2026-10-21 ("d3 you have my sign off", on `docs/plans/stage7-signoff.md`).**
- [x] 7b Spec one wave at a time; each issue opens with its user story (US-N), has an example pair (WP-N), its HP link and (UI work) its screen — all 62 specs `docs/plans/tickets/AEA-01…62.md` (written on Opus, amended for the residual rulings, join audits and one `[journey]` AC each). Innocent ✓ 2026-10-21 (D-3).
- [x] 7c Coverage audit clean — `docs/plans/coverage-audit.md`: 173 requirements, 491 matrix rows; checker 338 → 15 problems. **Not literally clean:** 15 known gaps are recorded in its *Findings* table (8 depend on ruling D-9, 6 on D-10, 1 checker quirk). Innocent ✓ 2026-10-21 (D-3, signed off with the gaps listed); D-9 and D-10 still open.
- [x] 7d Published to GitLab, waves labelled — 62 issues #1–#62 on `innocentnortey/inno-aea-callcenter` (project 2318, public) 2026-10-21; issue number = ticket number; labels `wave::0…6`, `lane::*`, `risk::security` (17), `gate::human/ux4/ux5/live/paid`; blockers as `relates_to` links plus the *Blocked by* section in each body. Authorised by Innocent's sign-off (D-3).
- **Gate:** ☐ all four passes done

## 8 · Build  (§8)
- [ ] Frontend: one integration step per contract, pointing the prototype at the real backend once it passes its contract tests against the same OpenAPI
- [ ] Each ticket's WP-N written as its first failing test before implementation
- [ ] Each slice reconciles `.claude/` in the same change: area map (planned → actual), router rows, rule `paths:`, and ICM rows (scaffold, routes verified) with dated evidence
- [ ] Review gates per ticket; seam audit per wave
- [ ] Journey harness exists and runs in the merge gate: affected journeys at ticket merge, all at wave merge and before deploy (AEA-57; rules `integrated-journeys.md`, `build-loop-test-scope.md` *AEA addition*) — evidence: `docs/testing/journeys/YYYY-MM-DD-AEA-57.md`
- [ ] Per-wave browser walkthrough recorded on the integrated branch, production build, normal login (from AEA-58) — evidence: `docs/testing/journeys/YYYY-MM-DD-wave-N-walkthrough.md`, one per wave
- [ ] Live smoke run recorded through the real app: dev cases only, inside $30/day, failures, versions, traces and cost (AEA-60; compatibility only, not a quality number) — evidence: `docs/testing/journeys/YYYY-MM-DD-live-smoke-N.md`
- [ ] UI verify again: the UX-5 suite reruns against the real backend (Prism in proxy mode) — Innocent ✓ ____
- **Gate:** ☐ waves merged, seam audits clean, area map matches the checkout, UI verify again signed

## 9 · Experiment ★  (§9)
- [ ] Kickoff page generated from code (flow, prompts with versions, approach, failure types)
- [ ] Error-analysis round: ~20 traces, first failure each, `FT-N` taxonomy, models × failures table — Innocent ✓ ____
- [ ] Every `XP-N` targets one `FT-N`, one change, scored on the frozen set
- **Gate:** ☐ no tuning change without a named failure type

## 10 · Ship & defend  (§10)
- [ ] `SUBMISSION.md` walked; every row's evidence at the expected path
- [ ] Demo script (two-layer order) and interview prep
- [ ] Demo decision inventory (`docs/delivery/YYYY-MM-DD-demo-decision-inventory.md`) built from dev logs, decision records and research; video = product under 5 min, then decisions (`.claude/rules/hiring-partner-framing.md` → *Demo video*)
- [ ] ICM progress checklist reconciled: no row left provisional without a named reason
- [ ] Retro written; lessons fed back to `Gauntlet AI/principles/` and `zero-to-hero`
- **Gate:** ☐ shipped — Innocent ✓ ____

---

## Skips

| Stage | Reason | Decided by | Date |
|---|---|---|---|
| §7 precondition (UX-5 signed before 7a) | Stage 7 builds the backend; every UI contract (CON-1…CON-22, `ui-contracts.openapi.yaml`) is already signed at UX-3. UX-4 (prototype, `apps/web/`) runs in a parallel session. **Cost:** a contract change found in the build reopens UX-3 and breaks UX-4's pinned types, so the build stops and asks instead of editing. Page-rendering is not ticketed (UX-4 owns it). Publishing and §8 UI integration still wait for UX-5. | Innocent ("Stage 7 may start before the UX track closes") | 2026-10-21 |
| UX-5 first run (`TRACEABILITY.md`, Lighthouse, `QA_REPORT.md`) | Enough testing already done: UX-4 sweep (494 desktop / 257 phone browser runs with axe, 0 failed), 2,614 unit tests, code review. **Cost:** no traceability matrix, so a must-have requirement with no test is not flagged; no performance baseline; no consolidated QA report. The §8 "UI verify again" run is unaffected. | Innocent ("skip it all we've dont enough testing") | 2026-10-21 |

*2026-10-20: seven skip rows (§2–§7) were added from a bundled "yes to all" and removed the same day at Innocent's question; no stage is skipped. Rule: one skip, one yes.*

## ID registers (quick index)

| Prefix | Where | Count |
|---|---|---|
| WP | `docs/data/worked-pairs.md` | 8 |
| HP | `docs/design/hard-problems.md` | 4 |
| US | `docs/ux/01-planning/USER_STORIES.md` (or `docs/prd/user-stories.md`) | 27 |
| CON | `docs/ux/03-structure/UI_CONTRACTS.md` (drafts in `docs/ux/01-planning/USER_FLOWS.md` until UX-3) | 20 draft |
| SP | `docs/analysis/spikes/` | |
| FT | `docs/testing/error-analysis/` | |
| XP | `docs/testing/experiments/` | |
