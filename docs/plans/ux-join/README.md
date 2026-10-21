# UX ↔ backend join plan

**Date:** 2026-10-21. **Status:** proposed. Nothing in `apps/web/**`, `docs/ux/**`, the tickets or the slice plan was edited.
**Why it exists:** Innocent asked us to "make sure our UX isn't out of line with these tickets". Three read-only audits compared
the UX-4 frontend (`apps/web`) with the backend's truth (the stage-7 contracts and the rewritten tickets):
[`audit-customer.md`](audit-customer.md), [`audit-staff.md`](audit-staff.md),
[`audit-shell-reads-build.md`](audit-shell-reads-build.md). This page turns their findings into one plan.
**Rules it applies:** [`integrated-journeys.md`](../../../.claude/rules/integrated-journeys.md) (journeys, levels, evidence) and
slice plan §0a (Amendment 1: journey map J-1…J-10, AEA-57…AEA-62, *Decisions taken while writing the journey specs*).

**The other files in this folder:**

| File | For | What it holds |
|---|---|---|
| [`FOR-UX-SESSION.md`](FOR-UX-SESSION.md) | The UX session (it has none of this context) | What the backend will do, what it needs from them and by when, the selector minimum, build recipe, real-backend mode, fixture rules, their high findings, what not to do |
| [`backend-amendments.md`](backend-amendments.md) | The pass that rewrites the ticket files | Copy-ready acceptance criteria per AEA ticket, the `[journey]` criterion for every build-loop ticket, the conventions sentence |
| [`decisions-for-innocent.md`](decisions-for-innocent.md) | Innocent | Six owner choices, story first, each with a **Decision needed:** line |
| `selectors.md` (not yet written) | AEA-58, AEA-62, AEA-55 | The UX session's selector contract; this plan asks for it |

**Count check.** The brief for this pass said 95 findings. The audits' rows add up to **94** (customer 32, staff 25, shell 37),
**18 high**. The customer audit's total line says 33, but its rows and its own H/M/L columns (3 + 12 + 17) give 32.

---

## What this looks like in practice (one example)

A reviewer is chatting as Omar. Riley (the demo representative) joins and writes "Hi Omar, I can look at the after-hours
charge with you." The reviewer presses reload.

- **The frontend** rebuilds the thread from `getChatThread`'s `turns` and reopens the event stream *after* the newest event.
- **The backend, as written today,** puts only customer messages and stored turn replies into `turns`
  (`stage7/web.md` §14). Riley's message, "Riley has joined" and even the greeting are not there.
- **The reviewer sees** their own messages and the assistant's replies, and none of Riley's words.

AEA-58's first browser journey already expects the greeting after a reload (its AC-3), so it would fail on day one. The fix is
backend-side: AEA-40's `SessionService.thread` returns the whole history (amendment AEA-40-1). That is the pattern of this
whole page: each finding gets one owner, one fix and the point on the timeline by which it must be closed.

---

## (a) Where the two tracks connect, in order

Two tracks run in parallel: the **UX session** finishes the frontend in `apps/web` (UX-4, then UX-5), and the **backend
build** runs the tickets in waves 0–6. They meet at these points. Each later point needs the earlier ones.

| # | Point | Who does what | "Done" means |
|---|---|---|---|
| P0 | **The tree is committed** (before wave 0 is dispatched) | Innocent says yes; the main session commits. Today `main` holds one commit (`ed4ca89`, the Project 1 snapshot) and **everything since is untracked**: not only `apps/` and `docs/ux/` but `docs/design/`, `docs/plans/` (tickets included), `src/`, `pyproject.toml`, `uv.lock` and most `.claude/` rules (`git status --short`, 2026-10-21). Build tickets run in worktrees cut from `main`, so they would see none of it | `git ls-files` lists `pyproject.toml`, `docs/ux/03-structure/ui-contracts.openapi.yaml`, `apps/web/package.json`, `apps/web/src/api/types.gen.ts` and `apps/web/src/api/contract.gen.json`; `dist/`, `node_modules/`, `var/` and `.env` are not tracked. Decision 3 |
| P1 | **UX-4 signed** (checklist §4b line "UX-4 prototype") | The UX session lands the items marked P1 in table (b): the selector contract `docs/plans/ux-join/selectors.md` with its attributes built, the build recipe, the high UX fixes, a first real-backend mode, the fixture dump. Innocent answers WEB-1 before this (Decision 1) and signs UX-4 | The checklist line carries `Innocent ✓ <date>`; on the committed tree `npm ci && npm run build && npm run check:dist` passes from `apps/web`; `selectors.md` exists; every P1 row in (b) is closed or carries Innocent's deferral. Lifts `gate::ux4` on AEA-49 and AEA-58 |
| P2 | **AEA-49 serves `dist`** (wave 2) | Backend: `web/frontend.py` mounts the build, SPA fallback, the public paths WEB-1 allows, cache headers and a 404 for a missing asset (amendments AEA-49-1, -2). Tested on a fixture `dist`, so it reads nothing UX-owned | AEA-49's criteria pass; its J-1 HTTP journey (AC-9) is recorded |
| P3 | **AEA-57 harness** (wave 2, in parallel with P2) | Backend: the real app on a disposable DB copy with the scripted model. J-1 runs in two stages (§0a): login, guard and resume steps from wave 2; the turn steps once AEA-51 lands the graph, reported *blocked* until then. No UX dependency | `docs/testing/journeys/<date>-AEA-57.md` at level `integrated with a scripted model` (API level) |
| P4 | **AEA-58 browser journeys** (wave 3; needs P1, P2, P3) | Backend: builds `dist` with the UX recipe, serves it through AEA-49, drives Chrome through the real login: J-1 (guard, sign-in, turn, reload) and J-9's rate-limited login. Selectors are transcribed from `selectors.md` into one module. **From here the selector contract is frozen**: a rename is announced in this folder first | AEA-58's record at level `integrated with a scripted model` (browser) |
| P5 | **AEA-62 browser legs** (wave 4; needs AEA-58, 51, 52) | Backend: the browser legs of J-2, J-3, J-6 and J-8 (§0a). These need the chat cards, "What's settled", the queue, the case view and the role panel, so the UX fixes on those surfaces (B1, B2, C1, C2, A-5, A2) must be in `dist` | AEA-62's record, one result per journey |
| P6 | **UX-5 signed** (checklist §4b gate) | The UX session writes the UX-5 suite in two modes (mock and real-backend), `TRACEABILITY.md`, `QA_REPORT.md`, and the report notes AEA-55 needs; runs real mode once against an AEA-58-style server. Innocent signs | Checklist gate `Innocent ✓ <date>`; every P6 row in (b) closed |
| P7 | **AEA-55 UI verify again** (wave 5; needs P5, P6) | Backend: the UX-5 suite through Prism in proxy mode against the real backend; it may change run configuration only, never screens. Innocent's ★ "UI verify again". Then AEA-56 deploys (wave 6) | AEA-55's criteria pass; the checklist §8 line signed |

**Critical path.** The slice plan's critical path is now AEA-02 → 10 → 29 → 51 → **62** → 55 → 56. AEA-62 needs AEA-58,
and AEA-58 needs UX-4 signed, so **UX-4 sign-off sits on the critical path from wave 3 onward**. If P1 slips past the end of
wave 2, the whole build waits.

---

## (b) Every finding, by owner

Audit IDs carry a prefix: **CU** customer, **ST** staff, **SH** shell, reads and build. "Close by" names the point in (a), or
"plan of AEA-nn" for a backend item that must be in the ticket text before that ticket's planner starts. Backend fixes are written
out as acceptance criteria in [`backend-amendments.md`](backend-amendments.md) under the id in the *Amendment* column.

**Counts:** UX session **63** (8 high) · AEA tickets **24** (7 high) · Innocent **7** (3 high) · total **94** (18 high).
Several UX rows are the same fix found twice (noted "= …"), so the UX session's distinct work items are fewer, about 52.

### Innocent (7)

| Audit id | Sev | Finding, in one line | Fix | Close by |
|---|---|---|---|---|
| CU C-1 | H | The login page cannot load its own script files if only `/login` is public | Answer WEB-1 (Decision 1); if B, the UX session builds a self-contained login page | Plan of AEA-49; P1 |
| SH C1 | H | = CU C-1 (WEB-1 still open; AEA-49 written for option A) | Same answer | Plan of AEA-49 |
| SH F1 | H | `apps/` and `docs/ux/` are untracked, so ticket worktrees see neither (the whole tree is, see P0) | Commit (Decision 3) | P0 |
| CU C-3 | M | A login rate limit reads as "wrong password"; two signed UX-3 documents disagree on the copy, and AEA-58 AC-6 tests one of them | Pick the copy (Decision 5); the UX session and AEA-58 follow | P1 |
| CU D-2 | M | The chat stream can answer a 410 the OpenAPI does not document | Keep the contract and have AEA-41 answer 404 (its ND-1), or add 410 (Decision 4); the UI half is UX's | Plan of AEA-41 |
| ST B5 | M | The case view replays old events onto a fresh snapshot (no `last_event_id` on `CaseDetail`) | Add `CaseDetail.events.last_event_id` to the OpenAPI, or filter on the client (Decision 2) | Plan of AEA-45 |
| CU C-4 | L | The login copy promises the README holds the login; whether it does is DAT-3 | Answer DAT-3 (already logged, not re-asked); the UX copy follows | P6 |

### AEA tickets (24)

| Audit id | Sev | Finding, in one line | Fix | Amendment | Close by |
|---|---|---|---|---|---|
| CU A-1 | H | Resume drops the greeting, staff messages, event lines and the shift-end card | `SessionService.thread` returns the whole history in time order | AEA-40-1 | Plan of AEA-40 (breaks AEA-58 AC-3 otherwise) |
| ST A1 | H | No backend rule produces `allowed_actions`; every staff button could be dead | AEA-29 computes it by lifecycle × role × live state, "listed ⇔ accepted"; AEA-45 passes it through; AEA-52 proves it per role | AEA-29-1, AEA-45-1, AEA-52-1 | Plan of AEA-29 |
| ST A2 | H | Display fields (`reason` text, `priority.word`, `due_label`, `age_label`, …, the `source_id` join key) have no producer rule | AEA-29 fixes each value against the OpenAPI example; J-6 asserts every brief chip resolves (AEA-52-5; AEA-62 AC-11 already does in the browser) | AEA-29-2, AEA-45-1, AEA-52-5 | Plan of AEA-29 |
| ST A4 | H | Do live actions bump the case version? Sources disagree; if they do, Riley conflicts with herself after hand back | Rule (i), from staff.md §5: live actions change no lifecycle or version and append no `case_changed`; fix AEA-52 AC-4 | AEA-46-1, AEA-29-4, AEA-52-2 | Plan of AEA-46 |
| ST E1 | H | No criterion proved the relayed customer message reaches the case stream | AEA-40 AC-11 now covers the append (rewrite of 08:18); add the payload-equals-CON-12 check and the J-7 step | AEA-40-5, AEA-52-3 | Plan of AEA-52 |
| SH A1 | H | `unit` and the scale of `value` exist only in examples; a wrong unit misreports silently | AEA-53 fixes `unit` ∈ {count, ms, share}, `share` 0–1; AEA-48's schema refuses anything else | AEA-53-1, AEA-48-1 | Plan of AEA-53 (and AEA-48) |
| SH F2 | H | `npm run build` reads the OpenAPI from outside `apps/web`; AEA-50 says its web stage reads `apps/web` only (DAT-21) | AEA-50 copies the spec to the same relative path and runs the UX recipe unchanged, with dev dependencies | AEA-50-1 | Plan of AEA-50 |
| CU A-2 | M | A "Talk to a person" turn is stored in a different shape; after reload its card may vanish | AEA-42 stores the outcome as is; AEA-40's `thread` maps it to a customer turn plus the handoff card | AEA-40-2, AEA-42-1 | Plans of AEA-40, AEA-42 |
| CU A-3 | M | Card `answered` is lost on reload, so old cards are tappable again | Recommended owner AEA-40: `thread` sets `answered` from the later turn that answered the card (engineering; UX fallback in FOR-UX-SESSION) | AEA-40-3 | Plan of AEA-40 |
| CU C-2 | M | The real login was never driven in a browser | Covered: AEA-58 AC-2…AC-6 sign in through SCR-12 with no dev parameters | — (present) | P4 |
| CU F-1 | M | The build needs the OpenAPI and dev dependencies; who adds the image stage was open | = SH F2 | AEA-50-1 | Plan of AEA-50 |
| ST A3 | M | The OpenAPI examples call the customer "You" on staff screens | On staff reads the customer speaker's `display_name` is null (the UI shows its kind label); never "You" | AEA-29-3, AEA-40-5 | Plan of AEA-29 |
| SH C4 | M | No cache policy; a missing asset is not specified as 404 | AEA-49: `no-cache` on `index.html` and fallbacks, `immutable` on `/assets/*`, 404 for a missing asset | AEA-49-1 | Plan of AEA-49 |
| SH J1 | M | Server-sent events through Prism proxy are unproven; a buffering proxy would hang both streams | AEA-55 probes first; if it hangs, the two stream paths bypass Prism in the run config, recorded | AEA-55-1 | Plan of AEA-55 |
| SH J2 | M | J-10's browser half had no runner in its wave | Resolved by §0a: J-10 is API-level (AEA-53 AC-9) plus the wave walkthrough; nothing to add | — (resolved) | — |
| SH S2 | M | `check:gen` runs in no gate, and the drift test covered `types.gen.ts` only | Covered: AEA-59 AC-9 (contract index) and AC-11 (types); P0 makes the files tracked | — (present) | P0 |
| CU A-6 | L | After a restart an inbox message shows dots but still reads `active` | AEA-27's `inbox` reports `expired` whenever it no longer holds the code; AEA-43 echoes it | AEA-27-1, AEA-43-1 | Plan of AEA-27 |
| CU A-7 | L | History wording differs from the live row ("[code entered]" vs "Code entered") | AEA-40 returns the live display texts for code, form and choice turns; UX agrees | AEA-40-4 | Plan of AEA-40 |
| ST A5 | L | Two 409 examples write timestamps with a space instead of `T` | Note only, in AEA-08's reconcile list; the OpenAPI is not edited | AEA-08-1 | AEA-08 |
| ST A7 | L | staff.md §8 gives `ClockAdvanced` a `date_label` the OpenAPI lacks | AEA-47 returns exactly the OpenAPI keys | AEA-47-1 | Plan of AEA-47 |
| SH B5 | L | The mock's supervisor and owner `SessionInfo` is invented; the real one is first seen late | J-8's browser leg asserts the header name and marked role for all four roles | AEA-62-1 | P5 |
| SH C6 | L | Under Prism proxy, a cookieless request may get Prism's own 401 body | AEA-55 probes it in its first run and records the result | AEA-55-1 | Plan of AEA-55 |
| SH C7 | L | Local runs need `MERIDIAN_COOKIE_SECURE=false` | Present in AEA-57; add to AEA-55's environment | AEA-55-1 | Plan of AEA-55 |
| SH G5 | L | The `[contract drift]` signal exists only in mock mode | AEA-55's report says so; Prism proxy's log (its AC-3) is the real check | AEA-55-1 | Plan of AEA-55 |

### UX session (63)

| Audit id | Sev | Finding, in one line | Fix | Close by |
|---|---|---|---|---|
| CU G-1 | H | Almost no stable hooks; journeys would key on copy | Publish `selectors.md` and add the attributes (FOR-UX-SESSION §3) | P1 |
| ST B1 | H | The role is read once; another tab's switch or a reset is never noticed | Re-read `getSession` on focus, on `visibilitychange` and on any `ROLE_NOT_ALLOWED`, then refetch | P1 |
| SH B1 | H | = ST B1 (and AEA-55 may not edit `src/`, so it must land before) | Same fix | P1 |
| ST B2 | H | Queue and case view swallow `ROLE_NOT_ALLOWED`; stale staff data stays up | On a 403 from a read, re-read the session and show the role panel with `reset = details.reason === "role_reset"` | P1 |
| ST C1 | H | "Claim and join" is shown to the supervisor, who cannot join | Render it only for the representative | P1 |
| ST C2 | H | The live reply box is active for the supervisor | Active only when `allowed_actions` has `send_live_message` | P1 |
| SH G1 | H | Every e2e test enters through `?signedin` / `?scenario`, so all of them are `mock-tested` only | A dual-mode UX-5 suite; mock-only tests tagged `@mock-only` | P6 |
| SH S3 | H | Nothing validates the TypeScript dev fixtures against the OpenAPI | A script that dumps every fixture, transform output and stream event to JSON for AEA-59 to validate read-only | Plan of AEA-59 (else AEA-59 adds it as a follow-up) |
| CU A-4 | M | "Try again" on a reloaded timeout notice resends a corrupted payload | Disable it on history entries (`live: false`) | P1 |
| CU A-5 | M | "What's settled" hides a cancellation; the "earlier" list is built by position | List visit actions' summaries when `visit` is null; exclude only the newest booked/moved action otherwise | P1 |
| CU B-1 | M | A re-tapped "Talk to a person" after a lost response never draws the card | Keep the pending `turn_id` until a 2xx; on `already_open` with no card in the thread, render `res.block` | P1 |
| CU D-1 | M | A 400 on a turn is shown as retryable | `retryable: false` for 400; no Try again | P1 |
| CU G-2 | M | Only SCR-1 has `data-screen` | `data-screen="SCR-n"` on all twelve | P1 |
| CU G-3 | M | The Playwright runners differ | Runner decided: AEA-58 is pytest-playwright. The UX side adds a real-backend project for UX-5 and AEA-55 | P6 |
| ST B3 | M | The mock cannot show B1, B2 or C1 | Dev role in `localStorage`; keep `role_reset` until a switch; refuse per-action roles | P1 |
| ST B4 | M | `controller_changed` updates the controller but never the live state | Set `state` from the event, or reload on an event this view did not cause | P6 |
| ST B6 | M | A non-401 failure of the first `getSession` signs the reviewer out | Only 401 signs out; other failures show "Try again" | P1 |
| SH C3 | M | = ST B6 | Same fix | P1 |
| ST C3 | M | Real mode exists but no staff state is reachable without dev forcing | Write J-6, J-7, J-8 as product-driven steps; point `E2E_BASE_URL` at the served build | P4 |
| ST E2 | M | The client reconnects after `demo_reset` and can stream a re-seeded case into the old view | On `demo_reset`, stop the stream and offer Reload | P6 |
| ST E3 | M | A 403 on the case stream stops it silently | Report 403 as its own status; re-read the session | P6 |
| ST G1 | M | = CU G-1 for staff screens (live state, owner, conflict, role panel, …) | Staff rows of the selector contract | P1 |
| SH A2 | M | `Measure.kind` is ignored; only the first tile shows "Estimate" | Tag from `kind === "estimate"` on tiles and rows | P4 |
| SH A3 | M | SCR-11 aligns measures by `id` alone; ids repeat | Key rows by `id` + `label` (AEA-53-2 makes that pair unique) | P4 |
| SH A4 | M | SCR-10's empty state is guessed from every health tile | Key it on the volume tile, by the id AEA-53 lists (AEA-53-3) | P4 |
| SH B2 | M | "Cap reached" is computed in the browser | Drive the tag from the `spend_cap_reached` alert state | P4 |
| SH B3 | M | Real time and demo time sit side by side without labels | Label wall-clock times "(real time)"; correct SCREEN_SPECS SCR-10 R1 through the UX track | P4 |
| SH C2 | M | `favicon.svg` sits outside `/assets/` (= CU C-5) | Import it so Vite hashes it under `/assets/`, or inline it | P1 |
| SH D1 | M | No error boundary anywhere (= CU C-6) | A root `errorElement` with reload; one reload on a chunk-load error | P1 |
| SH F3 | M | `check:dist` is a denylist and not chained to the build | `postbuild: check:dist`; fail if any `src/dev/` module is in the build manifest | P1 |
| SH G2 | M | Ports and origin are hard-coded | `E2E_TARGET`/`E2E_BASE_URL`; servers only in mock mode; paths relative to `baseURL` | P6 |
| SH G3 | M | The sweep writes screenshots under `docs/ux/**` | `SHOTS_DIR` from the environment | P6 |
| SH G4 | M | No hooks to find a value by its field (= CU G-1 for read pages) | `data-state`, `data-measure`, `data-field` on SCR-9/10/11 | P1 |
| CU A-8 | L | `ChatThread` has no `limits`; the UI caches them | Accept; note only (adding it is an OpenAPI change, not recommended) | P6 |
| CU B-2 | L | SCR-1 stops polling clock and staffing after the chat ends | Fall back to polling when the stream is not open | P6 |
| CU B-3 | L | Sign out keeps the stored thread id | `clearThread()` on sign out | P6 |
| CU B-4 | L | Other tabs keep the old role label after a reset | Re-read on `demo_reset` and on focus (with ST B1) | P6 |
| CU C-5 | L | = SH C2 | — | P1 |
| CU C-6 | L | = SH D1 | — | P1 |
| CU D-3 | L | `saveFollowUp` 409 has two causes, one message | Branch on `details.state` | P6 |
| CU D-4 | L | The RATE_LIMITED hold time is a guess | Accept; note only | P6 |
| CU E-1 | L | No idle watchdog on the chat stream | Reconnect after 45 s with no bytes | P1 |
| CU E-2 | L | A replayed `shift_ended` can regress "What's settled" | Keep the newer `settled`, or re-read the thread after a replay | P6 |
| CU F-2 | L | OpenAPI request examples (synthetic name, phone, a code) ship in `dist` | Split a runtime index from a dev-only examples index; add a `check:dist` needle | P1 |
| CU F-3 | L | A dev hook is read in production | Read `__mhcDevRoutes` only under `MODE === "mock"` | P1 |
| CU F-4 | L | `dist/` is older than the sources | Rebuild and rerun `check:dist` at sign-off | P1 |
| CU G-4 | L | Entry ids embed turn UUIDs | Keep; document the pattern in `selectors.md` | P1 |
| ST A6 | L | The assign dialog writes its own success line | Show the server's `result_line` | P6 |
| ST C4 | L | 503 `RESET_IN_PROGRESS` on role switch or clock advance shows a generic failure | Say "The demo is resetting…" and wait `retry_after_ms` | P6 |
| ST D1 | L | `NOT_LIVE` `not_waiting` reads as "This chat has ended." | Its own line with Reload | P6 |
| ST D2 | L | No client check before a send or a flag | Disable blank sends, `maxLength` 2,000, flag target required | P6 |
| ST F1 | L | = CU F-2 | — | P1 |
| ST F2 | L | Test fixtures outside `src/dev` could be imported by app code | Lint rule `no-restricted-imports`, or a `check:dist` needle per fixture | P6 |
| SH A5 | L | A null numerator renders "0 of N" | Render "—" | P6 |
| SH A6 | L | SCR-11 sums transcript and synthetic counts in the browser | Record it in the UX-5 report as an allowed display sum | P6 |
| SH B4 | L | SCR-11's stale line checks one run only | Compare each run with `current_agent_version` | P6 |
| SH C5 | L | = CU F-3 | — | P1 |
| SH D2 | L | Empty alerts list shows a bare heading | "No alerts configured" | P6 |
| SH D3 | L | SCR-10 empty: spec says "—", UI shows "0" | Align (UX track) | P6 |
| SH D4 | L | Some read states exist only as client transforms of examples | For each state, `selectors.md` names how the real backend reaches it (seed, action, or "mock only") | P4 |
| SH F4 | L | No `engines` field or `.nvmrc` | Add `engines.node`; AEA-50 pins the image to it | P1 |
| SH F5 | L | The production tab title carries internal screen ids | "Monitoring · Meridian"; tests read `data-screen` | P6 |
| SH J3 | L | AEA-58 (Python) and AEA-55 (TypeScript) share only selectors and login steps | Keep `selectors.md` runner-neutral; write the sign-in steps down, not only in code | P1 |

---

## (c) What each journey needs from the UX session, and what happens if it is late

Every journey has an **API leg** (backend only, through AEA-57's harness) and, for some, a **browser leg** (the production
build in Chrome through the real login). The API legs need nothing from the UX session. The browser legs need three things
from it: **selectors** (`selectors.md`, FOR-UX-SESSION §3), the **build recipe** (§4) and a **real-backend mode** with no dev
parameters (§5), plus the UX fixes on the surfaces the leg walks through.

| Journey | API leg (no UX dependency) | Browser leg | Needs from the UX session | Fixes that must be in `dist` |
|---|---|---|---|---|
| J-1 login → turn → reload | AEA-57 (wave 2; turn steps after AEA-51) | AEA-58 (wave 3) | SCR-12 form and message hooks; SCR-1 root state, thread id, entries; build recipe | WEB-1 answer (and the standalone login page if B); CU C-5 favicon; ST B6 |
| J-2 grounded answers | AEA-51 | AEA-62 (wave 4) | Reply block type and source chip hooks | — |
| J-3 booking and follow-up | AEA-51 | AEA-62 | SCR-2 inbox message id and status; card id and answered state; "What's settled" visit status | CU A-5, CU A-4 (and CU A-3's fallback if AEA-40 does not take it) |
| J-4 fee-bearing change | AEA-51 | wave walkthrough only | Handoff card and request reference | — |
| J-5 safety | AEA-51 | wave walkthrough only | Block type of the first reply | — |
| J-6 escalation → queue → case | AEA-52 | AEA-62 | Queue row names; case root lifecycle and version; brief headings; source cards; promise status | ST C1, ST B2 |
| J-7 live takeover | AEA-52 | wave walkthrough only | Live box mode and controller; message speaker; event lines | ST C2, ST B4, ST E2 |
| J-8 roles and session | AEA-52 | AEA-62 (AEA-58 covers sign-out) | Role switch; role panel with its reason; `data-screen` | ST B1, ST B2, ST B3, ST E3 |
| J-9 empty, timeout, busy, limited | AEA-51 | AEA-58 (rate-limited login), walkthrough for the rest | Notice codes; pending phase; composer lock | CU D-1, CU A-4, Decision 5 |
| J-10 read pages | AEA-53 | wave walkthrough only | `data-state`, `data-measure`, `data-field` | SH A2, A3, A4, B2, B3 |

**If the UX session is late.** AEA-58 cannot start: it carries `gate::ux4`. Then:

- **The journey stays "integrated with a scripted model" at the API level only.** Its evidence record says exactly that:
  *Level:* `integrated with a scripted model` (API level); *Blocked by:* UX-4 sign-off (or "selector contract", or "build
  recipe"). No record claims a browser result, and a browser claim without a record is read as `mock-tested`
  (integrated-journeys §4).
- **The wave walkthrough** for the affected journeys records `NOT_RUN` with the same *Blocked by*, instead of walking the Prism
  mock and calling it integrated.
- **The critical path moves.** AEA-62 and AEA-55 wait for AEA-58, and AEA-56 waits for both. A late UX-4 delays the deploy
  day for day.
- **A selector missing from `selectors.md`** does not block a whole journey. The AEA-58 or AEA-62 planner records
  `blocked-on UX selector <state>` for that step only, and the rest of the leg runs. It never invents a copy-text selector.

---

## (d) Risks

1. **Untracked tree vs ticket worktrees (high).** The audit saw `?? apps/` and `?? docs/ux/`. The real state is wider: only the
   Project 1 snapshot is committed. A worktree cut from `main` has no `pyproject.toml`, no contracts, no tickets and no OpenAPI,
   so AEA-01 could not even start, AEA-23's `openapi_check` has no file to read, and AEA-59's drift test has no `apps/web`.
   Two smaller points: the UX session keeps editing `apps/web` in the primary checkout, so after the commit its later work is
   committed by it (with Innocent's yes) and merges are never done with `git add -A` (ticket conventions); and the GitLab
   `main` starts with Innocent's README commit, so the first push builds on it, no force push (`project-provenance.md`).
   *Mitigation:* Decision 3, before wave 0 is dispatched.
2. **Dev-only sign-in makes every UX test `mock-tested` (high).** The UX suites sign in with `?signedin=1&role=…` and enter states
   with `?scenario=…`. Against the real server none of that exists, so not one UX test so far has passed the real login gate,
   the HttpOnly cookie, the 303 redirect or a cross-tab role change: the Riverside failure in its exact form. *Mitigation:* AEA-58
   proves the guard and the login first (its AC-2 even checks that `?signedin=1&role=owner` is redirected); the UX-5 suite gains a
   real-backend mode with sign-in through SCR-12 and `@mock-only` tags (SH G1, P6); AEA-55 records `@mock-only` tests as
   `NOT_RUN`, never as passed.
3. **The build reads the OpenAPI from outside `apps/web` (high).** `prebuild` regenerates the types and contract index from
   `../../docs/ux/03-structure/ui-contracts.openapi.yaml`, and `tsc -b` type-checks tests, so the build needs dev dependencies.
   AEA-50's text ("reading `apps/web` only", DAT-21) would fail. *Recommended:* AEA-50 copies that one file into the web stage at
   the same relative path and runs the UX recipe unchanged (`npm ci && npm run build && npm run check:dist`, no `--omit=dev`),
   amendment AEA-50-1. The slice plan row's "reading only" (the stage never edits `apps/web`) stays true. If the UX session later
   adds a `build:dist` script that skips regeneration, AEA-50 can switch to it; nothing waits on that. This is engineering, not
   an owner choice.
4. **Two signed UX documents disagree with each other or with the backend.** SCREEN_SPECS N-28 vs UI_CONTRACTS CON-22 on the
   throttle copy (Decision 5); SCREEN_SPECS SCR-1 "the chat resumes" after a new sign-in vs `owned_thread`'s 404 (Decision 6).
   A test written against one of them fails against the other. *Mitigation:* the decisions, then one line in each spec through
   the UX track.
5. **Tickets are being rewritten while this was written.** AEA-52, 53, 57, 58, 59, 60 and 61 changed between 08:17 and 08:23.
   *Mitigation:* every amendment uses `AC-<next>` and names the criterion it extends or replaces by content, not only by number;
   the applying pass re-reads each ticket first.
6. **Server-sent events through Prism proxy (SH J1).** If Prism buffers the never-ending stream, AEA-55's rerun hangs.
   *Mitigation:* AEA-55-1 probes first and routes the two stream paths around Prism in the run configuration if needed.
7. **UX-4 sign-off is on the critical path from wave 3** (see (a)). *Mitigation:* the P1 list is short and ordered in
   FOR-UX-SESSION §2; anything not on it waits for UX-5.
