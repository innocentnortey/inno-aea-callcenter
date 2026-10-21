# UX-4 prototype · slice G5 (oversight and read screens: SCR-7, SCR-8, SCR-9, SCR-10, SCR-11)

> **Planner:** `fanout-planner` · **Date:** 2026-10-21 · **Project:** `/home/linuxuser/workspaces/inno-aea-callcenter` · **Implementer:** `fanout-implementer` (Sonnet) · **Readiness:** READY (see §9; two coordination requests in §8)
> **Lane / loop:** `lane::build-loop`, not `risk::security` (a mock-backed prototype; no auth logic is written here). Loop: implement (code **and** the tests named in §7) → affected tests → code review. No test-writer, no frozen tests, no security agent. No worked pair (WP-N): no model behaviour changes.
> **No git here for commits:** do not run `git commit` / `push` (Innocent has not asked).
> **Foundation status when this plan was written:** `docs/plans/fanout/2026-10-21-ux4/foundation.md` is being built; `apps/web/` already holds the API layer, `src/components/{ui,shared,shell}`, `src/state/{session,demoStatus}.tsx`, `src/test/*`, `src/routes.ts`, `src/screens/{matrix.ts,ScreenStub.tsx}`, the twelve stub screens, and the dev-layer stubs (`src/dev/scenarios/scr07.ts` … `scr11.ts`, `src/dev/reactions/scr07.ts` … `scr11.ts`). Every signature in §4 was copied from those files or from foundation §4. **Step 0 re-checks them; if one is missing or differs, stop and report (do not recreate foundation files).**

## 1. Goal and sources

Replace the five stub screens with the real screens, built only from the contract in `docs/ux/03-structure/ui-contracts.openapi.yaml`, and make **every spec'd state of each screen reachable** from the dev state switcher (scenarios) or a real interaction.

| Screen | Route | Allowed roles (`SCREENS`) | Contracts |
|---|---|---|---|
| SCR-7 Supervisor oversight | `/staff/oversight` | supervisor | CON-17 `getOversight`; CON-13 `applyCaseAction` (+ `getCase` for the version); CON-7 `setStaffing`; CON-8 `advanceDemoClock`; CON-16 count |
| SCR-8 Review list of flags | `/staff/flags` | representative, supervisor, owner | CON-16 `listFlags`, `reviewFlag` |
| SCR-9 Business-owner outcomes | `/staff/owner` | owner, supervisor | CON-18 `getOwnerMetrics`; CON-12 (links to SCR-6) |
| SCR-10 Monitoring | `/monitoring` | all four | CON-19 `getMonitoring` |
| SCR-11 Evaluation report | `/eval` | all four | CON-20 `getLatestEval` |

**Sources (all read for this plan; cite when in doubt):** `docs/ux/03-structure/SCREEN_SPECS.md` SCR-7 (lines 375-409), SCR-8 (411-441), SCR-9 (443-478), SCR-10 (480-512), SCR-11 (514-547), "Copy rules that apply on every screen" (19-31), "State matrix" (602-621), N-13, N-16, N-21…N-25; `IA.md` "Per screen" SCR-7…11 and "Layout breakpoints"; `UI_CONTRACTS.md` CON-7, CON-8, CON-16…CON-20, "Named errors", "Settled at §6"; the OpenAPI file operations `getOversight` (l.6364), `getOwnerMetrics` (6737), `getMonitoring` (6935), `getLatestEval` (7612), `listFlags` (6223), `reviewFlag` (6279), `applyCaseAction` (5475), `setStaffing` (3031), `advanceDemoClock` (3140), and schemas `Alert`, `Lane`, `OversightResponse`, `Measure`, `OwnerMetricsResponse`, `Tile`, `MonitorAlert`, `MonitoringResponse`, `EvalMeasure`, `EvalRun`, `EvalResponse`, `Flag`, `FlagsResponse`, `FlagReviewRequest`, `QueueRow`, `CaseActionRequest`; `docs/design/design.md` §3.2-3.3 (type), §4.5 (colour rules), §8.2 (buttons, fields, tags), §8.8 (queue rows, priority tags), §8.11 "Lanes, tables, numbers", §9.2, §10 (state copy), §11 (Do / Don't); `docs/design/key-metrics-registry.md` rows for volume, tool and model failure rate, latency, spend, live AI-resolved rate (definitions text, §5 Step 15); foundation plan §2.4, §4, §8.2, §8.3. The A5 reference `docs/artifacts/2026-10-21-direction-A5-service-desk.html` shows tags, hairline cards and queue rows only (it has no oversight, owner, monitoring or eval screens); `design.md` wins on any difference.

## 2. Boundary

### 2.1 Owned files (the implementer may create or edit only these; paths relative to `/home/linuxuser/workspaces/inno-aea-callcenter/`)

```
apps/web/src/screens/reads/                       (intra-group shared pieces; all new)
  ScreenTitle.tsx          format.ts   format.test.ts      useNow.ts       ReadError.tsx
  MetricTile.tsx           MetricTile.test.tsx
  MeasuresTable.tsx        MeasuresTable.test.tsx
  test/specExample.ts      test/mockDesktop.ts               (test-only helpers)
apps/web/src/screens/scr07/                       (Scr07.tsx and index.ts exist as stubs: replace Scr07.tsx, keep index.ts)
  Scr07.tsx  DemoControls.tsx  AlertList.tsx  Lane.tsx  AssignDialog.tsx  signature.ts  copy.ts
  Scr07.test.tsx  AssignDialog.test.tsx  signature.test.ts
apps/web/src/screens/scr08/
  Scr08.tsx  FlagsTable.tsx  useShownFlags.ts  Scr08.test.tsx  useShownFlags.test.ts
apps/web/src/screens/scr09/
  Scr09.tsx  OpenCases.tsx  basis.ts  Scr09.test.tsx  basis.test.ts
apps/web/src/screens/scr10/
  Scr10.tsx  AlertsList.tsx  SpendBar.tsx  definitions.ts  dataAge.ts  Scr10.test.tsx  SpendBar.test.tsx  dataAge.test.ts
apps/web/src/screens/scr11/
  Scr11.tsx  EvalMeasuresTable.tsx  evalRows.ts  Scr11.test.tsx  evalRows.test.ts
apps/web/src/dev/scenarios/scr07.ts scr08.ts scr09.ts scr10.ts scr11.ts      (exist as stubs: replace content)
apps/web/src/dev/scenarios/g5-transforms.ts  g5-transforms.test.ts            (new)
apps/web/src/dev/reactions/scr07.ts scr08.ts scr09.ts scr10.ts scr11.ts        (exist as stubs: replace content)
docs/ux/04-prototype/groups/g5-oversight-reads.md                              (new; §5 Step 17)
```

Each `index.ts` stays exactly `export { default } from "./ScrNN";` (the router lazy-loads `@/screens/<slug>`; do not change it).

### 2.2 Read-only shared surfaces (never edit)

`apps/web/src/api/**`, `src/components/**`, `src/state/**`, `src/styles/**`, `src/lib/**`, `src/routes.ts`, `src/router.tsx`, `src/screens/{matrix.ts,ScreenStub.tsx}`, `src/test/**`, `src/dev/{resolve,defaults,world,install,transport}.ts` and `src/dev/{scenarios/{index,types,matrix,shared},reactions/{index,shared},directors/**,stream/**}`, `package.json`, `vite.config.ts`, `eslint.config.js`, `tests/e2e/**`; `docs/ux/03-structure/**` (including the OpenAPI file), `docs/design/**`, `.claude/**`, `CLAUDE.md`, `PROJECT-CHECKLIST.md`, `docs/plans/**` (except this file is already written; do not edit it).

### 2.3 Other slices' files this slice must not touch (collision map)

| Owner | Files | Why it matters here |
|---|---|---|
| G4 | `src/screens/scr05/**`, `scr06/**`, `src/dev/{scenarios,reactions}/scr05.ts scr06.ts`, `src/dev/stream/case-scripts.ts` | SCR-7 and SCR-8 link to SCR-6. G5 only builds links (§8.1 request R-1) |
| G3 | `src/screens/scr02/**`, `scr03/**`, `scr04/**`, `scr12/**`, `scr03/Switch.tsx` | SCR-7 builds its own shift switch (foundation §8.3: default is "G5 builds its own wrapper") |
| G1/G2 | `src/screens/scr01/**` | none |
| Foundation | everything in §2.2 | A missing primitive is a *request* (§8.2), never an edit |

### 2.4 Do not

- Do not edit any foundation file. Do not run `npm install` or add a dependency.
- Do not call `fetch`, read `document.cookie`, or import anything from `src/dev/**` inside `src/screens/**` (the ESLint rules ban it). `src/dev/**` files may import from `src/screens/**` only types (they do not need to).
- Do not use red, orange, amber, hex values, `--color-safety`, Tailwind default palette names (`red-*`, `amber-*`, `orange-*`), 24-hour times, `uppercase` on anything holding a time or date, countdowns ("in 3 days"), outlined pills, coloured left borders, or a grid of identical tiles. Overdue / firing / errors are **words + icon + ink weight** (`Tag tone="strong"` with `IconClock` / `IconWarning`).
- Do not key any behaviour on a measure `id` (`M-3`, `E-1`…). The ids in the OpenAPI examples do not match `docs/design/key-metrics-registry.md` (§8.1 item 4). Key on the response **field name** (`in_scope_correct_resolution`, `promises_kept_on_time`, `handoffs`) or array position.
- Do not invent data a contract does not carry (no example numbers, names, counts or times in screens). Copy strings that the specs quote are allowed; strings this plan adds are listed in §5 and in the group file.
- Do not hand-write response bodies in app code. Mock bodies come from the OpenAPI examples through `OpForce.example` (+ `transform` only where §5 Step 14 lists one).
- Do not leave Prism or Vite running when you finish.

## 3. Requirements table

State columns use the eight standard states. "Scenario" ids are the ones in §5 Step 14. "Test" names are the vitest `it(...)` titles in §7.

### 3.1 SCR-7 Supervisor oversight

| # | Requirement (source) | How implemented | How verified |
|---|---|---|---|
| 7-01 | Route `/staff/oversight`; console header with role "Demo supervisor", nav Oversight · Review list · Queue, role switch and sign out (SCR-7 R1; F-10/F-12) | `Scr07.tsx`: `AppFrame variant="console"` → `ConsoleHeader` → `Main` → `ScreenTitle` → `RoleGate allow={["supervisor"]}`; body mounts only inside the gate | `Scr07.test.tsx` "customer role sees the role panel and makes no staff call" |
| 7-02 | R2 "Demo controls" strip: "Simulated shift: off / on" switch; "Advance simulated time" with "+1 hour", "+4 hours", "Next business morning (Mon 7:00 am)"; current demo time "Fri Oct 16 · 2:20 pm"; neutral, labelled "Demo" | `DemoControls.tsx` (Step 8) | `Scr07.test.tsx` "controls strip shows the switch, three advance buttons and the demo time" |
| 7-03 | R3 alerts, decision lines, newest first, polite on change | `AlertList.tsx`: sort by `at` descending; `<ul aria-live="polite">`; each line as given by `Alert.line`; a text button "Open case MHC-C-0008" when `case_ref` is set | `Scr07.test.tsx` "alerts newest first"; scenario `scr07.default` |
| 7-04 | R4 five lanes in fixed order P0 and P1 · Overdue · Due soon · Unowned · Stuck waiting, each count + rows (priority tag, reference, reason, owner, age, due, follow-up preference, "Assign"); `section` with `h2` including the count | `Lane.tsx` using shared `QueueRow` (`showStaffTags`, `onSelect` → `navigate(caseHref(ref))`) + age line + "Assign" button | `Scr07.test.tsx` "five lanes render in the fixed order with counts in the headings" |
| 7-05 | default: seeds MHC-C-0008 in "P0 and P1", MHC-C-0005 in "Overdue", MHC-C-0006 and MHC-C-0007 in "Unowned"; alert "P0 safety case MHC-C-0008 created at 2:16 pm, unowned. Assign it."; seeds carry "Demo seed" | `getOversight` example `SEEDED` (Prism default) | scenario `scr07.default`; test "seeded rows land in the spec'd lanes" |
| 7-06 | empty: all lanes empty → "Nothing urgent, unowned, due soon, overdue or stuck. Every case has an owner and is on time."; an empty lane stays and shows "None" under its header | `Scr07.tsx` + `Lane.tsx` | scenario `scr07.empty`; test "empty oversight keeps all five lanes and shows the sentence" |
| 7-07 | loading: controls and lane headers render; row skeletons | `Lane` with `loading` prop renders `Skeleton height={44} rows={2}` under the fixed lane titles (no count) | scenario `scr07.loading`; test "loading shows lane titles and skeletons" |
| 7-08 | error: "Oversight didn't load. Try again." | `ReadError` with retry; controls strip stays | scenario `scr07.error`; test "load failure shows the sentence and retries" |
| 7-09 | error: advance failed "The clock didn't move. Try again." | `DemoControls` result line | scenario `scr07.error-advance`; test "advance failure line" |
| 7-10 | error: assign without a reason "Add a reason to assign this case." | client check keeps "Assign" disabled until a reason is typed; a server 422 `REASON_REQUIRED` shows the same sentence under the reason field | scenario `scr07.error-reason`; `AssignDialog.test.tsx` "422 REASON_REQUIRED shows the sentence" |
| 7-11 | stale: refresh every 10 s and on focus; "Lanes updated." when the lanes changed since the last read; after an advance the lanes re-read at once | `useOp("getOversight", {}, { pollMs: 10000, refetchOnFocus: true })`; `signature.ts` + `StaleLine` | scenario `scr07.stale-lanes-updated`; `signature.test.ts`; test "a changed read shows Lanes updated" |
| 7-12 | success: advance → "Demo time is now Mon Oct 19 · 7:00 am. 1 case became overdue." and the case moves lanes | `DemoControls` `ResultLine` from the `ClockAdvanceResponse`; then `demo.refresh()` + oversight refetch | scenario `scr07.success-advanced`; test "advance success line" |
| 7-13 | success: shift ended with a customer waiting → alert "Simulated shift ended with 1 customer waiting. Their case now has the 1-business-day promise."; CON-7 line "Shift ended. 1 waiting customer now has the 1-business-day promise." | result line from `StaffingResponse.converted_cases`; the alert arrives with the re-read | scenario `scr07.success-shift-ended`; test "shift off with a waiting customer" |
| 7-14 | success: assigned → row shows the owner and leaves "Unowned" | `AssignDialog` success → close, `ResultLine`, quiet refetch | scenario `scr07.success-assigned`; test "assign sends the exact body and refetches" |
| 7-15 | success (Change priority P0-P4 with words, required reason) | same dialog, second mode | scenario `scr07.success-priority-changed`; test "change priority sends the exact body" |
| 7-16 | disabled: advance buttons and switch disabled while saving | `saving` flag from both `useAction`s | scenario `scr07.disabled-saving`; test "controls are disabled while a save is pending" |
| 7-17 | disabled: "Assign" disabled until a reason is typed | `AssignDialog` | test "Assign stays disabled until a reason is typed" |
| 7-18 | disabled: no back-in-time; the line "To go back to Fri Oct 16, reset the demo." | static hint line under the advance buttons (always shown) | scenario `scr07.disabled-no-back`; test in 7-02 |
| 7-19 | R5 live queue line while staffed: "2 customers waiting in chat." No estimate | shown only when `useDemoStatus().staffing.mode === "simulated_on_shift"`; "1 customer waiting in chat." / "No customers waiting in chat." | scenario `scr07.staffed-live-queue`; test "live queue line only while staffed" |
| 7-20 | R6 "Review list · 3 new flags" link to `/staff/flags` | `Link` | test "review list link shows the new-flag count" |
| 7-21 | Dialog is a native `<dialog>`, reason field `aria-required`; buttons ≥ 32 px (console) / 44 px phone | foundation `Dialog`; `Button density="console"`; `TextArea` with `aria-required="true"` | `AssignDialog.test.tsx` |
| 7-22 | 12-hour times everywhere; "Overdue" never red | shared `QueueRow`/`Time` | every screen test ends with `expectNo24HourTimes(container)` |

### 3.2 SCR-8 Review list of flags

| # | Requirement (source) | How implemented | How verified |
|---|---|---|---|
| 8-01 | Route `/staff/flags`; console header (role switch, sign out); R2 statement "Nothing on this list changes the knowledge base, prompts or tests. People decide each fix." | `Scr08.tsx` (`RoleGate allow={["representative","supervisor","owner"]}`) | `Scr08.test.tsx` "statement is shown" |
| 8-02 | R3 flags newest first: kind (Answer · Brief · Escalation), reason, case reference link, "Open the message" link, flagged by, when, status New / Reviewed, optional note; table with `th scope`, stacked rows on phones | `FlagsTable.tsx`; server order kept | `Scr08.test.tsx` "renders the flag row with all columns"; scenario `scr08.default` |
| 8-03 | empty: "No flags yet. Staff flag a wrong answer, a brief that left something out, or an escalation that wasn't needed, from any case." | `EmptyState` | scenario `scr08.empty`; test "empty list sentence" |
| 8-04 | loading: header and statement render; row skeletons | `Skeleton height={44} rows={4}` | scenario `scr08.loading` |
| 8-05 | error: "The review list didn't load. Try again." | `ReadError` | scenario `scr08.error`; test |
| 8-06 | stale: refresh on focus; "1 new flag since you opened this page. Show it." | `useShownFlags.ts` (Step 11) + `StaleLine` with action "Show it" | scenario `scr08.stale-new-flag`; `useShownFlags.test.ts` |
| 8-07 | success: "Marked reviewed." and the status word changes; optional note | inline editor → `reviewFlag` → patched row + `ResultLine` | scenario `scr08.success-reviewed`; test "mark reviewed with a note" |
| 8-08 | disabled: for the representative role "Mark reviewed" is disabled with "Supervisors mark flags reviewed." | `role !== "supervisor"` → disabled buttons + one `aria-describedby` hint | scenario `scr08.disabled-rep`; test "representative sees disabled buttons and the hint" |
| 8-09 | row actions have the reference in the accessible name: "Mark flag on MHC-C-0007 reviewed" | `aria-label` | test (same as 8-07) |
| 8-10 | `ROLE_NOT_ALLOWED` from `reviewFlag` → "Supervisors mark flags reviewed."; `FLAG_NOT_FOUND` after a reset | `reviewError()` mapping, Step 11 | scenarios `scr08.error-review-forbidden`, `scr08.error-flag-gone` |
| 8-11 | No word suggesting an automatic fix ("learned", "updated the model") | copy review | test "no automation words" (`not.toMatch(/learn|updated the model|fixed automatically/i)`) |

### 3.3 SCR-9 Business-owner outcomes

| # | Requirement (source) | How implemented | How verified |
|---|---|---|---|
| 9-01 | Route `/staff/owner`; role "Demo business owner"; supervisor may also open it (CON-18 access) | `RoleGate allow={["owner","supervisor"]}` | `Scr09.test.tsx` "customer sees the role panel" |
| 9-02 | R2 three headline tiles stacked: estimate "Estimate from live chats (no verified answers)" + link to the measured number on SCR-11, "n of N in-scope conversations"; "n of N promises due"; "n of N conversations"; rate large, denominator under it, "Open the cases" | `MetricTile` ×3 from fields `in_scope_correct_resolution`, `promises_kept_on_time`, `handoffs` | scenario `scr09.default`; test "three tiles with denominators" |
| 9-03 | R3 basis line "From stored conversations and cases, as of Fri Oct 16 · 2:20 pm (demo time). Includes 4 demo seed cases. These are not targets." | `basis.ts` `basisLine(data)` | `basis.test.ts` |
| 9-04 | R4 outcomes table (Resolved by the AI · Escalated, resolved by staff · Escalated, still open · Abandoned · Failed): count and share of N | `MeasuresTable` | test "outcomes table rows" |
| 9-05 | R5 handoffs by reason: reason, count, "Open the cases" | `MeasuresTable` | same |
| 9-06 | R6 missed promises: reference, due time, outcome | small table in `Scr09.tsx` | test "missed promises row" |
| 9-07 | R7 inline list of references with reason and status, each opening SCR-6; "Open the cases" expands in place; announces its count | `OpenCases.tsx`; `aria-expanded`; `useAnnounce()` "2 cases listed." | test "open the cases expands in place and announces the count" |
| 9-08 | R8 "System health is on the Monitoring page. Evaluation results are on the Evaluation page." with links to `/monitoring`, `/eval` | static, `Link`s | test |
| 9-09 | empty: "No outcomes yet. Numbers appear once conversations end. Nothing here is a target."; tiles show "—" with "0 conversations" | all-zero detection (Step 12) | scenario `scr09.empty`; test |
| 9-10 | loading: tile and table skeletons | | scenario `scr09.loading` |
| 9-11 | partial: a measure with no denominator shows "—" and the reason ("No promises are due yet.") while the others show numbers | per-measure `value === null` → "—" + `null_reason` | scenario `scr09.partial`; test |
| 9-12 | error: "Outcomes didn't load. Try again." | `ReadError` | scenario `scr09.error` |
| 9-13 | stale: "These numbers are as of 2:20 pm; the demo time is now Mon 7:00 am. Refresh." | `StaleLine` when demo clock is later than `as_of` by > 60 s; action "Refresh" → refetch | scenario `scr09.stale-clock-moved`; test |
| 9-14 | disabled: a number with a zero denominator is not a link: "No cases to open." | `MetricTile`/`MeasuresTable` render text instead of a button | scenario `scr09.disabled-zero-denominator`; test |
| 9-15 | seeds named; a handoff is never called containment; "Not a target" stays | copy in `basis.ts` and tile labels from the contract | tests (no "containment" in the page text: `not.toMatch(/containment/i)`) |
| 9-16 | each tile is a `section` with an `h2`; rates are text; tables with `th scope` | `MetricTile`, `MeasuresTable` | tests |

### 3.4 SCR-10 Monitoring

| # | Requirement (source) | How implemented | How verified |
|---|---|---|---|
| 10-01 | Route `/monitoring`, readable in any role; header "Monitoring · Is it running, and is it right?"; role switch and sign out | `Scr10.tsx`: `AppFrame variant="page"` → `DemoPageHeader title="Monitoring" subtitle="Is it running, and is it right?"` → `Main` → h1 "Monitoring" | `Scr10.test.tsx` "renders for the customer role" |
| 10-02 | data-age line "Updated 2:20 pm · redacted · traces are not shown here" | `Time format="point"` of `as_of` (wall-clock per CON-19 "Closed"; **no "(demo time)" suffix**, §8.1 item 3) | test "updated line" |
| 10-03 | R2 alerts: firing first, then quiet; each a decision line | `AlertsList.tsx`: `Tag tone="strong"` + `IconWarning` "Firing" (+ "since {time}") or plain `Tag` "Quiet"; line as given | scenarios `scr10.alerts-cap-and-latency`, `scr10.alert-zero-traffic`, `scr10.alert-failure-and-trace`; test "firing first" |
| 10-04 | R3 Health: volume (conversations, turns), failures (count and share), latency p50 and p95, spend today against the $30 cap, last health-check restart | `Card` "Health" with `CardRow`s from `health[]`, `spend`, `last_restart`, `trace_export` | test "health rows" |
| 10-05 | spend bar with the numbers in text | `SpendBar.tsx` | `SpendBar.test.tsx` |
| 10-06 | R4 Correctness in its own `section` apart from Health: containment **estimate** labelled so, with denominator; escalations by reason | separate `Card` with its own `h2` | test "health and correctness are separate sections" |
| 10-07 | R5 definitions of what each measure counts (static) | `definitions.ts` + `Disclosure` per measure group | test "definitions present" |
| 10-08 | empty: "No conversations since the last reset, so there is nothing to measure yet."; health tiles "—"; the restart line still shows | all-zero/null detection | scenario `scr10.empty`; test |
| 10-09 | loading: tile skeletons | | scenario `scr10.loading` |
| 10-10 | partial: latency "Not enough turns yet (fewer than 20)" while volume and spend show values | `null_reason` rendered in place of the value | scenario `scr10.partial-too-few-turns`; test |
| 10-11 | error: "Monitoring didn't load. Try again."; 503 `RESET_IN_PROGRESS` → "The demo is resetting. Try again in a few seconds." | `ReadError` | scenarios `scr10.error`, `scr10.error-resetting` |
| 10-12 | stale: auto-refresh every 30 s while visible; data older than 2 minutes: "This data is [n] minutes old." | `useOp(..., { pollMs: 30000 })` + `dataAge.ts` + `useNow(15000)` | scenario `scr10.stale-data-age`; `dataAge.test.ts` |
| 10-13 | a newly firing alert is announced politely; other refreshes are silent | `useAnnounce()` on set difference | test "announces a newly firing alert only" |
| 10-14 | no codes, no card-like numbers, no names, no trace links (R-36) | none rendered | test: container text has no `href` containing "trace" |
| 10-15 | one `h1`; groups are `section`s with `h2` "Health" and "Correctness" | | test |

### 3.5 SCR-11 Evaluation report

| # | Requirement (source) | How implemented | How verified |
|---|---|---|---|
| 11-01 | Route `/eval`, any role; header role switch and sign out; one `h1` | `DemoPageHeader title="Evaluation" subtitle="Latest run"` + h1 "Evaluation report" | `Scr11.test.tsx` |
| 11-02 | R1 headline: correct-resolution rate from the held-out split, "n of N held-out cases", "Held-out split: scored only, never tuned against.", run ID and date | `Scr11.tsx` from `headline` + `splits.held_out` | scenario `scr11.default`; test "headline" |
| 11-03 | R2 run identity: run ID, date, split sizes (dev, held-out), test-set size and mix summary (transcript-derived vs labelled synthetic) | `RunIdentity` block in `Scr11.tsx` | test "run identity" |
| 11-04 | R3 measures per split, each "n of N", caption naming the run, `th scope="col"`; Target only in its own column | `EvalMeasuresTable.tsx` + `evalRows.ts` | `evalRows.test.ts`; test "caption names the run" |
| 11-05 | R4 test-set mix by category; synthetic cases labelled with what they test | table in `Scr11.tsx` | test |
| 11-06 | R5 dev failures from the dev split only, redacted | list | test |
| 11-07 | empty: "No evaluation run yet. When one runs, its results appear here with their test set. No number is shown before then." | `EmptyState` | scenario `scr11.empty` |
| 11-08 | loading: skeletons | | scenario `scr11.loading` |
| 11-09 | partial: only a dev run: headline reads "No held-out run yet." and the dev column shows, labelled "Dev (we read and fixed these, so it overstates)" | `dev_label` from the response | scenario `scr11.partial-dev-only`; test |
| 11-10 | error: "The evaluation report didn't load. Try again." (+ `RESET_IN_PROGRESS`) | `ReadError` | scenarios `scr11.error`, `scr11.error-resetting` |
| 11-11 | stale: "This run used an earlier version of the agent ([run version]); the deployed version is [current]." | `StaleLine` | scenario `scr11.stale-run-version`; test |
| 11-12 | a target (60-75%, ≥ 90%) never appears as a result; dev numbers always carry the dev label | no target text anywhere except a Target column from `EvalMeasure.target` | test: BOTH_SPLITS page text has no "Target" column header; a fabricated target renders only in a column headed "Target" |

## 4. Shared code to use (copied from the current files)

### 4.1 Imports and signatures

```ts
// API (apps/web/src/api)
import { useOp, useAction } from "@/api/useOp";
//  useOp<K>(op, args: CallArgs<K> | null, opts?: { pollMs?: number; pauseWhenHidden?: boolean; refetchOnFocus?: boolean })
//    : { data: OkBody<K> | undefined; error: ApiError | undefined; status: "idle"|"loading"|"success"|"error"; isRefetching: boolean; refetch(): Promise<void> }
//    NOTE (read from useOp.ts): `data` is KEPT when a later refetch fails (status becomes "error" while data stays).
//    So "first load failed" is `data === undefined && error`, and "loading" is `data === undefined && !error`.
//  useAction<K>(op): { run(args?: CallArgs<K>): Promise<OkBody<K>>; pending: boolean; error: ApiError | undefined; data; reset() }  (run() rejects with ApiError)
import { refetchAll } from "@/api/refetch";
import { ApiError } from "@/api/errors";   // fields: status, code, body, details (Record|null), requestId, field; getters isUnauthenticated, isRoleNotAllowed
import type { components } from "@/api/types.gen";
// shell + shared components
import { AppFrame } from "@/components/shell/AppFrame";            // variant: "chat"|"console"|"page"|"auth"
import { ConsoleHeader, DemoPageHeader, Main } from "@/components/shell/chrome"; // DemoPageHeader({ title, subtitle?, showDemoBar? }), Main({ children, id?, className? })
import { RoleGate, RoleNotAllowedPanel } from "@/components/shell/RoleGate";     // RoleGate({ allow, children }); RoleNotAllowedPanel({ role, allow, reset? })
import { ErrorLine, EmptyState, StaleLine, ResultLine } from "@/components/shared/states";
//  ErrorLine({ message, onRetry? }) ; EmptyState({ title, body?, action? }) ; StaleLine({ children, actionLabel?, onAction? }) ; ResultLine({ children, id? })  (tabIndex -1, role="status")
import { QueueRow } from "@/components/shared/QueueRow";   // QueueRow({ row, selected?, showStaffTags?, onSelect?(reference), href? }) renders an <li>: put it inside a <ul>
import { PriorityTag } from "@/components/shared/PriorityTag";
import { RefChip } from "@/components/shared/RefChip";    // RefChip({ reference, copyable? })
import { Time } from "@/components/shared/Time";          // Time({ iso, format: "point"|"short"|"staff"|"day"|"sentence"|"clock", variant?, fallback?, className? })
import { Button, Card, CardHeader, CardBody, CardRow, Dialog, Disclosure, Field, TextArea, TextInput, Skeleton, Tag, IconClock, IconWarning, IconInfo, IconCheck, IconChevron } from "@/components/ui";
//  Button({ variant?: "primary"|"secondary"|"send"|"text"; density?: "chat"|"console"; loading?; icon?; ...native }) ; one primary per card/dialog
//  Card (section) ; CardHeader({ icon?, title, hint?, meta?, as?: "h2"|"h3"|"h4" }) ; CardBody ; CardRow({ label, hint?, mono?, children })
//  Dialog({ open, onClose, title, children, initialFocus?: "cancel"|"first", labelledBy?, className? })  (native <dialog>; its own <h2> shows `title`)
//  Field({ label, hint?, error?, children: ({ id, describedBy, invalid }) => ReactNode }) ; TextArea / TextInput({ invalid?, density?: "chat"|"console", ...native })
//  Disclosure({ summary, children, open?, onOpenChange?, className? }) (native <details>; content stays in the DOM when closed)
//  Skeleton({ height: number, width?, rows?, className? }) ; Tag({ tone?: "plain"|"strong"; icon? })
import { useAnnounce } from "@/components/ui/LiveRegion";  // (msg: string) => void
// state, routing, time
import { useSession } from "@/state/session";             // { status, session, role, ... }
import { useDemoStatus } from "@/state/demoStatus";       // { clock: DemoClock|null; staffing: Staffing|null; refresh(): Promise<void>; ... }
import { caseHref, screenById } from "@/routes";          // caseHref("MHC-C-0007") === "/staff/cases/MHC-C-0007"
import { Link, useNavigate } from "react-router";
import { formatClockLabel, formatTimePoint, formatStaffTime, formatDateTimeShort, formatDayLong } from "@/lib/time";
//  formatClockLabel(iso) -> "Fri Oct 16 · 2:20 pm" ; formatTimePoint -> "2:20 pm" ; formatStaffTime -> "Mon 7:00 am" ; formatDateTimeShort -> "Mon Oct 19 · 7:00 pm"
import { cn } from "@/lib/cx";
import { ROLE_LABEL, type Role } from "@/lib/roles";
// tests
import { renderWithProviders, shellTransport } from "@/test/render";   // renderWithProviders(ui, { route?, transport?, role? }) -> { router, ...RTL }
import { makeFakeTransport, jsonResponse } from "@/test/fakeTransport"; // makeFakeTransport((ctx, url, init) => Response); ctx = { op, method, path, body? }
import { expectNo24HourTimes } from "@/test/no24h";
import { CLOCK_START, STAFFING_ON, STAFFING_OFF } from "@/test/fixtures";
// dev layer types
import type { ScreenScenarios, Scenario, Reaction, OpForce } from "../scenarios/types";   // from src/dev/scenarios/*.ts and src/dev/reactions/*.ts
```
`shellTransport(role, extra?, seen?)` answers `getSession`, `getStaffing`, `getDemoClock`, `switchRole`, `logout` and 404s everything else; pass `extra: (op) => Response | undefined` to answer the screen's own ops. Build the test transport as `shellTransport(role, (op) => op === "getOversight" ? jsonResponse(200, body) : undefined, seenOps)`.

### 4.2 Contract shapes the screens use (verbatim from `types.gen.ts` / OpenAPI)

```ts
OversightResponse = { as_of; demo_now; staffing: Staffing; alerts: Alert[];
  lanes: { p0_p1: Lane; overdue: Lane; due_soon: Lane; unowned: Lane; stuck_waiting: Lane };
  live_queue_length: number; new_flags_count: number }
Alert = { type: "p0_p1_created"|"unowned"|"due_soon"|"overdue"|"stuck_waiting"|"shift_ended_with_queued"; case_ref: string|null; line: string; at: string }
Lane = { count: number; rows: QueueRow[] }      // QueueRow has age_label: string|null, owner: string|null, follow_up_short, seed, due_state ...
// advance:  advanceDemoClock  POST /api/demo/clock   body { step: "plus_1h"|"plus_4h"|"next_business_morning" }  -> { now, label, became_overdue }
// staffing: setStaffing       PUT  /api/demo/staffing body { mode: "nobody_online"|"simulated_on_shift" }         -> { mode, label, converted_cases }
// case:     getCase           GET  /api/staff/cases/{reference}  -> CaseDetail { case: CaseSummary { version: number, ... }, ... }
//           applyCaseAction   POST /api/staff/cases/{reference}/actions
CaseActionRequest = { action: "assign"|"change_priority"|...; expected_version: number; reason?: string|null; assignee?: "riley"|"supervisor"|null; priority?: "P0"|"P1"|"P2"|"P3"|"P4"|null; ... }
//   assign body:           { action: "assign", expected_version, assignee: "riley" | "supervisor", reason }
//   change priority body:  { action: "change_priority", expected_version, priority: "P0".."P4", reason }
//   409 VERSION_CONFLICT details { changed_by, changed_at, current_version } ; 422 REASON_REQUIRED field "reason"
// flags
FlagsResponse = { as_of; flags: Flag[] }
Flag = { flag_id; target: "answer"|"brief"|"escalation"; reason: string|null; case_ref; message_id: string|null; note: string|null;
         flagged_by; at; status: "new"|"reviewed"; reviewed_by: string|null; reviewed_note: string|null }
// reviewFlag  PATCH /api/staff/flags/{flag_id}  body { status: "reviewed", note?: string|null } -> Flag ; 403 ROLE_NOT_ALLOWED ; 404 FLAG_NOT_FOUND
// owner
Measure = { id; label; numerator: number|null; denominator: number|null; unit; value: number|null; null_reason: string|null; kind: "measured"|"estimate"; case_refs: string[] }
OwnerMetricsResponse = { as_of; seeds_included: boolean; seed_count: number; in_scope_correct_resolution: Measure;
  measured_north_star_link: { label: string; path: "/eval" }; promises_kept_on_time: Measure; handoffs: Measure;
  outcomes: Measure[]; handoffs_by_reason: Measure[]; missed_promises: { reference; due_at; outcome }[]; cases: { reference; reason; status }[] }
// monitoring
Tile = { id; label; value: number|null; unit: string; numerator: number|null; denominator: number|null; null_reason: string|null }   // unit seen: "count", "ms", "share"
MonitoringResponse = { as_of; demo_now; health: Tile[]; spend: { today_cents; cap_cents; day; resets_at };
  correctness: { containment_estimate: Tile; escalations_by_reason: Tile[] };
  alerts: MonitorAlert[]; alert_config; last_restart: { at; kind: "health_check" } | null; trace_export: string; redacted: true }
MonitorAlert = { type: "spend_cap_reached"|"p95_latency_over_12_5s"|"health_check_restart"|"zero_traffic"|"failure_rate_over_2pct"|"trace_export_failed"; state: "firing"|"quiet"; fired_at: string|null; decision_line: string }
// eval
EvalResponse = { splits: { dev: EvalRun|null; held_out: EvalRun|null }; headline: EvalMeasure|null; current_agent_version: string; dev_label: string }
EvalRun = { run_id; date: "YYYY-MM-DD"; agent_version; size; mix: { category; count; origin: "transcript"|"synthetic"; tests: string|null }[]; measures: EvalMeasure[]; dev_failures: { case_id; redacted_summary }[] }
EvalMeasure = { id; label; numerator; denominator; value; min: number|null; max: number|null; target: string|null }
```
Query/path argument shapes for `useOp` / `useAction`: no-parameter reads take `{}`; `getCase`: `{ path: { reference } }`; `applyCaseAction`: `{ path: { reference }, body }`; `reviewFlag`: `{ path: { flag_id }, body: { status: "reviewed", note } }`.

### 4.3 Named Prism examples (from `src/api/contract.gen.json`; the names are the only legal `example:` values)

| Operation | 2xx examples | Error examples |
|---|---|---|
| `getOversight` | `SEEDED`, `AFTER_ADVANCE`, `SHIFT_ENDED_WITH_WAITING`, `NOTHING_URGENT` | 401 `UNAUTHENTICATED`, 403 `ROLE_NOT_ALLOWED`, `ROLE_NOT_ALLOWED_ROLE_RESET` |
| `getStaffing` | `OFF`, `ON` | |
| `setStaffing` | `TURNED_ON`, `TURNED_OFF_WITH_WAITING` | 400 `VALIDATION_ERROR`, 503 `RESET_IN_PROGRESS` |
| `getDemoClock` | `START`, `ADVANCED` | 429 `REQUEST_RATE_LIMITED` |
| `advanceDemoClock` | `NEXT_MORNING`, `PLUS_1H` | 400 `VALIDATION_ERROR`, 403 `ROLE_NOT_ALLOWED`, 503 `RESET_IN_PROGRESS` |
| `getCase` | `DEFAULT` (MHC-C-0007, `version: 3`) … | 404 `CASE_NOT_FOUND` |
| `applyCaseAction` | `CLAIMED` (Prism default), `WAITING`, `RESOLVED`, `ASSIGNED`, `PRIORITY_CHANGED` | 409 `VERSION_CONFLICT`, `CASE_ALREADY_CLAIMED`, `NOT_ALLOWED_IN_STATE`; 422 `REASON_REQUIRED`, `WAKE_UP_REQUIRED`, `OUTCOME_REQUIRED` |
| `listFlags` | `THREE` (one flag: `flg-3`, MHC-C-0007, message `m-2`, status `new`), `EMPTY` | 403 `ROLE_NOT_ALLOWED` |
| `reviewFlag` | `REVIEWED` | 403 `ROLE_NOT_ALLOWED`, 404 `FLAG_NOT_FOUND` |
| `getOwnerMetrics` | `SEEDED`, `EMPTY` | 403 `ROLE_NOT_ALLOWED` |
| `getMonitoring` | `DEFAULT`, `FIRING`, `TOO_FEW_TURNS`, `EMPTY`, `ZERO_TRAFFIC_FIRING`, `FAILURE_AND_TRACE_FIRING` | 429 `REQUEST_RATE_LIMITED`, 503 `RESET_IN_PROGRESS` |
| `getLatestEval` | `BOTH_SPLITS`, `DEV_ONLY`, `STALE_RUN`, `NO_RUN` | 429 `REQUEST_RATE_LIMITED`, 503 `RESET_IN_PROGRESS` |

Mock facts that shape the design (all verified in `defaults.ts`, `world.ts`, `scenarios/types.ts`):
- With no force, `defaultExample` answers the **first** 2xx example: `advanceDemoClock` → `NEXT_MORNING` (even for "+1 hour"), `applyCaseAction` → `CLAIMED`, `setStaffing` → `TURNED_ON` (even when turning off). The screens therefore **build their result lines from the request and the typed response fields they need, never from the response's `label` / `result_line`** where those would be wrong in the mock; §5 says which.
- A force with a `transform` is **not persisted** across a page reload (`world.ts persistable()`); scenarios re-apply with `?scenario=<id>`. `setWorld({forces})` (what `ctx.setForce` does) **clears every sequence cursor**, so do not combine `sequence` forces with `setForce` reactions. This plan uses no `sequence`.
- Reactions run after the response is recorded and receive `ctx.response = { status, body }`, `ctx.request` (the request body), `ctx.world` (includes `scenarioId`), `ctx.setForce`, `ctx.refetch`.
- The shared reaction (foundation) already sets `world.staffing` from the `setStaffing` **request** body, so `getStaffing` (default `ON`/`OFF`) follows the switch.

## 5. Steps (build order; each step ends with a check)

Work in `apps/web/`. Run commands from `apps/web/`. Order matters: later steps import earlier ones.

### Step 0 · Preflight (no code)
1. `ls src/components/shared/QueueRow.tsx src/components/shared/states.tsx src/components/shared/Time.tsx src/components/shell/RoleGate.tsx src/components/shell/chrome.tsx src/state/session.tsx src/state/demoStatus.tsx src/test/render.tsx src/dev/scenarios/types.ts src/dev/reactions/scr07.ts` must list all ten. If any is missing, stop and report `BLOCKED-ON: foundation file X`.
2. `grep -n "export function useNow\|export function ScreenTitle" -r src` prints nothing (they are yours to create). `grep -c "" src/dev/scenarios/scr07.ts` prints 2 (stub).
3. `npx vitest run src/routes.test.ts src/screens/stubs.test.tsx` is green before you change anything (baseline for the files you will replace). If it is not green, report and continue only if the failure is not in your files.
**Check:** the three bullets hold.

### Step 1 · `src/screens/reads/format.ts` (+ `format.test.ts`) and `useNow.ts`
Pure helpers. Write exactly these exports:
```ts
export function pluralize(n: number, one: string, many: string): string;           // n === 1 ? one : many
export function formatShare(value: number | null): string;                          // null -> "—" (U+2014); else Math.round(value * 100) + "%"   0.75 -> "75%", 0.667 -> "67%", 0.294 -> "29%", 0 -> "0%"
export function formatCount(n: number | null): string;                              // null -> "—"; else String(n)
export function nOfN(numerator: number | null, denominator: number | null, noun: string): string; // "9 of 12 in-scope conversations"; if denominator is null: "—"; if denominator === 0: `0 ${noun}`
export function formatSeconds(ms: number | null): string;                           // null -> "—"; else (ms / 1000).toFixed(1) + " s"   4200 -> "4.2 s", 10200 -> "10.2 s", 13800 -> "13.8 s"
export function formatCents(cents: number): string;                                 // "$" + (cents / 100).toFixed(2)   612 -> "$6.12", 3000 -> "$30.00", 3012 -> "$30.12"
export function formatTileValue(t: { value: number | null; unit: string }): string; // unit "ms" -> formatSeconds; "share" -> formatShare; else formatCount (value as integer string)
export function dateOnlyToIso(date: string): string;                                // "2026-10-20" -> "2026-10-20T12:00:00-05:00" (noon keeps the Chicago date in both CDT and CST)
export function readErrorText(err: ApiError | undefined, didntLoad: string): string;
//   err?.code === "RESET_IN_PROGRESS" -> "The demo is resetting. Try again in a few seconds."
//   err?.code === "REQUEST_RATE_LIMITED" -> "Try again in a moment."
//   otherwise didntLoad
```
`useNow.ts`: `export function useNow(intervalMs: number): number` — `useState(() => Date.now())`, `useEffect` with `setInterval(() => setNow(Date.now()), intervalMs)` cleared on unmount. (The only `setInterval` in the slice; it is a UI clock, not a data poll.)
`format.test.ts`: the examples in the comments above as `expect(...).toBe(...)`, plus `readErrorText` for an `ApiError(503,"RESET_IN_PROGRESS",{})` and `ApiError(0,"NETWORK",null)`.
**Check:** `npx vitest run src/screens/reads/format.test.ts` green.

### Step 2 · `src/screens/reads/ScreenTitle.tsx`, `ReadError.tsx`
```tsx
export function ScreenTitle({ id, children }: { id: ScreenId; children: ReactNode }): JSX.Element
//  <h1 className="t-title">…</h1> where the content is <span className="sr-only">{id} · </span>{children}
//  and an effect sets document.title = `${id} · ${screenById(id).title} · Meridian`.
```
Why the `sr-only` prefix: foundation `stubs.test.tsx` and `tests/e2e/smoke.spec.ts` require the single `h1` to contain/start with `SCR-<n>`; this keeps them green with no foundation edit. The integrator can drop the prefix later by editing this one component (request R-3 in §8.2). Use `import type { ScreenId } from "@/routes"`.
```tsx
export function ReadError(props: { error: ApiError; role: Role | null; allow?: Role[]; didntLoad: string; onRetry(): void }): JSX.Element
//  error.isRoleNotAllowed && props.allow && props.role -> <RoleNotAllowedPanel role allow reset={error.details?.reason === "role_reset"} />
//  otherwise <ErrorLine message={readErrorText(error, didntLoad)} onRetry={onRetry} />
```
**Check:** `npm run typecheck` green.

### Step 3 · `src/screens/reads/MetricTile.tsx`, `MeasuresTable.tsx` (+ tests)
```tsx
export interface MetricTileProps {
  heading: string;                // the contract's measure label, used as given
  estimate?: boolean;             // true -> a plain Tag "Estimate" beside the heading
  value: string;                  // already formatted: "75%" or "—"
  denominatorLine: string;        // "9 of 12 in-scope conversations" or "0 promises due"
  reason?: string | null;         // measure.null_reason; rendered under the denominator when value is "—"
  extra?: ReactNode;              // e.g. the link to the Evaluation page
  caseRefs: string[]; denominator: number | null;
  open: boolean; onToggle(): void; panelId: string;
}
```
Structure: `<Card as section aria-labelledby={headingId}>` → `CardHeader as="h2"` (title = heading, meta = estimate Tag) → `CardBody`: the figure `<p className="t-time-hero">{value}</p>` (design.md §3.3: headline KPIs use the hero style), `<p className="text-ui text-text-muted">{denominatorLine}</p>`, reason line (`text-small text-text-muted`) when present, `extra`, then **either** `<Button variant="text" density="console" aria-expanded={open} aria-controls={panelId} onClick={onToggle}>Open the cases</Button>` when `(denominator ?? 0) > 0 && caseRefs.length > 0`, **or** `<p className="text-small text-text-muted">No cases to open.</p>`.
```tsx
export interface MeasuresTableProps {
  caption: string; firstColumn: string;          // e.g. "Outcome" / "Reason"
  rows: Measure[];                                // components["schemas"]["Measure"]
  noun: string;                                   // "conversations" | "handoffs"
  openKey: string | null; onOpen(key: string, measure: Measure): void; panelId: string;
}
```
Structure: `<table>` with `<caption className="sr-only">`, `<th scope="col">` headers `{firstColumn}`, "Count", "Share", and an unlabeled-visually (sr-only text "Cases") last column; one `<th scope="row">` per measure label; count cell `nOfN(numerator, denominator, noun)`; share cell `formatShare(value)` and, when `value === null`, the `null_reason`; action cell as in the tile (button `Open the cases` with `aria-label={`Open the cases for ${label}`}` or "No cases to open."). Row key = `${index}-${label}` (the contract repeats `M-15` as id for several rows; never key on id). Responsive: wrap the table in `<div className="overflow-x-auto">`.
Tests: `MetricTile.test.tsx` — "renders the figure, the denominator line and an Open the cases button", "a zero denominator renders No cases to open. and no button", "a null value shows the reason". `MeasuresTable.test.tsx` — "rows use th scope=row and the columns use th scope=col", "count is n of N and share is rounded", "a row with no case refs says No cases to open.".
**Check:** `npx vitest run src/screens/reads` green; `npm run lint` clean for the folder.

### Step 4 · `src/screens/reads/test/specExample.ts`, `mockDesktop.ts`
`specExample.ts` (test-only; reads the real OpenAPI examples so tests never hand-copy a body):
```ts
import specText from "../../../../../../docs/ux/03-structure/ui-contracts.openapi.yaml?raw";
import { parse } from "yaml";
import type { OkBody, OperationId } from "@/api/client";
export function specExample<K extends OperationId>(op: K, name: string, status = 200): OkBody<K> {
  // walk parse(specText).paths[*][method] for operationId === op; return structuredClone(
  //   operation.responses[String(status)].content["application/json"].examples[name].value )
  // throw new Error(`no example ${op}/${status}/${name}`) when missing
}
```
(`?raw` is typed by `vite/client`; `yaml` v2 keeps ISO timestamps as strings.) `mockDesktop.ts`: `export function mockDesktop(matches = true): void` using `vi.spyOn(window, "matchMedia").mockImplementation((q) => ({ matches, media: q, onchange: null, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent: () => false }) as MediaQueryList)`.
If the `?raw` import is refused by Vite for a path outside the project root, report it and fall back to a hand-copied typed literal for **only** the fields the tests assert (never edit `vite.config.ts`).
**Check:** a throw-away assertion in `format.test.ts`? No: verify in Step 5's first test (`specExample("getOversight","SEEDED").alerts[0].case_ref === "MHC-C-0008"`).

### Step 5 · SCR-7: `signature.ts`, `copy.ts`, `Lane.tsx`, `AlertList.tsx`
`copy.ts` exports string constants and tiny builders (so tests and components share the exact wording):
```ts
export const LANES = [
  { key: "p0_p1", title: "P0 and P1" }, { key: "overdue", title: "Overdue" }, { key: "due_soon", title: "Due soon" },
  { key: "unowned", title: "Unowned" }, { key: "stuck_waiting", title: "Stuck waiting" },
] as const;                                                         // fixed order (SCREEN_SPECS R4)
export const EMPTY_ALL = "Nothing urgent, unowned, due soon, overdue or stuck. Every case has an owner and is on time.";
export const NO_BACK = "To go back to Fri Oct 16, reset the demo.";   // spec string; the demo start date is fixed (R-3)
export const LOAD_ERROR = "Oversight didn't load. Try again.";
export const CLOCK_ERROR = "The clock didn't move. Try again.";
export const STAFFING_ERROR = "Staffing didn't change. Try again.";
export const REASON_MISSING = "Add a reason to assign this case.";
export const ADVANCE_STEPS = [
  { step: "plus_1h", label: "+1 hour" }, { step: "plus_4h", label: "+4 hours" },
  { step: "next_business_morning", label: "Next business morning (Mon 7:00 am)" },
] as const;
export function advanceLine(nowIso: string, becameOverdue: number): string;
//  `Demo time is now ${formatClockLabel(nowIso)}. ${overdueSentence(becameOverdue)}`   -> "Demo time is now Mon Oct 19 · 7:00 am. 1 case became overdue."
//  overdueSentence: 0 -> "No case became overdue."; 1 -> "1 case became overdue."; n -> `${n} cases became overdue.`
export function shiftLine(turnedOn: boolean, converted: number): string;
//  turnedOn -> "Simulated shift is on."; off & converted 0 -> "Simulated shift is off.";
//  off & 1 -> "Shift ended. 1 waiting customer now has the 1-business-day promise."; off & n>1 -> `Shift ended. ${n} waiting customers now have the 1-business-day promise.`
export function liveQueueLine(n: number): string;           // 0 "No customers waiting in chat." ; 1 "1 customer waiting in chat." ; n "n customers waiting in chat."
export function reviewListLine(newFlags: number): string;   // 0 "Review list · no new flags" ; 1 "Review list · 1 new flag" ; n "Review list · n new flags"
```
`signature.ts`: `export function oversightSignature(o: OversightResponse): string` = `JSON.stringify({ a: o.alerts.map(x => [x.type, x.case_ref, x.line]), l: LANES.map(({ key }) => [o.lanes[key].count, o.lanes[key].rows.map(r => [r.reference, r.owner, r.priority.level, r.due_state, r.lifecycle])]), q: o.live_queue_length, f: o.new_flags_count })`. It **excludes** `as_of`, `demo_now` and every `age_label` (they change on every read). `signature.test.ts`: "same read twice → equal", "SEEDED vs AFTER_ADVANCE → different" (uses `specExample`), "only as_of/age_label differ → equal".
`Lane.tsx`: `Lane({ title, lane, loading, onAssign(row), }: { title: string; lane?: Lane; loading?: boolean; onAssign(row: QueueRow): void })`:
- `<Card>` (a `section`; give it `aria-labelledby`), `CardHeader as="h2"` with `title={lane ? `${title} · ${lane.count}` : title}`.
- `loading` → `<Skeleton height={44} rows={2} />`. `lane.count === 0 / rows.length === 0` → `<p className="px-3 py-2 text-ui text-text-muted">None</p>`.
- rows: for each row a `div.flex` containing `<div className="min-w-0 flex-1"><ul><QueueRow row={row} showStaffTags onSelect={(ref) => navigate(caseHref(ref))} /></ul>{row.age_label ? <p className="px-[9px] text-time-meta text-text-muted">{row.age_label}</p> : null}</div>` and `<Button density="console" aria-label={`Assign ${row.reference}`} onClick={() => onAssign(row)}>Assign</Button>`. (One `ul` per row because `QueueRow` renders its own `li` and the Assign button must sit beside it.) Age text is the contract's `age_label` ("Open 4 min"), used as given.
`AlertList.tsx`: `AlertList({ alerts }: { alerts: Alert[] })` — sorts a copy by `at` descending (`Date.parse`), renders `<ul aria-live="polite" className="flex flex-col gap-2">`; each `li`: `<Tag tone="strong" icon={<IconInfo …/>}>` is **not** used; render `<span className="font-semibold">{alert.line}</span>` + `<Time iso={alert.at} format="point" variant="meta" />` + (when `case_ref`) `<Button variant="text" density="console" onClick={() => navigate(caseHref(ref))} aria-label={`Open case ${ref}`}>Open case</Button>`. Region heading: visually shown small `h2` "Alerts" (`t-card-title`). Render nothing when `alerts.length === 0`.
**Check:** `npx vitest run src/screens/scr07/signature.test.ts` green; `npm run typecheck`.

### Step 6 · SCR-7: `DemoControls.tsx`
```tsx
export interface DemoControlsProps { demoNow: string | null; onChanged(): Promise<void> }   // onChanged: refetch oversight + mark the next read "quiet"
```
Behaviour (numbered; the invariant each step protects is in brackets):
1. Read `const { staffing, clock, refresh } = useDemoStatus()`; `const advance = useAction("advanceDemoClock")`; `const shift = useAction("setStaffing")`. `saving = advance.pending || shift.pending`. [spec: controls disabled while saving]
2. Wrapper: `<section aria-label="Demo controls" className="rounded-card border border-border-hair bg-surface-well …">` with a visible label "Demo controls" and a plain `Tag` "Demo". Wrap the interior in `Disclosure` with `open={desktop}` where `desktop = useState(() => window.matchMedia("(min-width: 700px)").matches)[0]`; the summary reads `Demo controls · {formatClockLabel(time)}` (phone shows one line; content stays in the DOM, so tests need no click). Neutral surfaces only, no amber/red. [IA: strip collapses to one line on a phone]
3. Current demo time: `<p>Demo time: <time dateTime={t}>{formatClockLabel(t)}</time></p>` where `t = demoNow ?? clock?.now ?? null` (the lane read's `demo_now` first, because lane ages come from the same clock). [SCR-7 R2]
4. Shift switch (own wrapper, foundation §8.3): `<label className="inline-flex min-h-[var(--control-h-console)] items-center gap-2"><input type="checkbox" role="switch" aria-checked={checked} checked={checked} disabled={saving || staffing === null} onChange={…} /> <span>Simulated shift: {checked ? "on" : "off"}</span></label>`, `checked = pendingMode ? pendingMode === "simulated_on_shift" : staffing?.mode === "simulated_on_shift"` (`pendingMode` is a `useState` set while the request is in flight). While `staffing === null` show the hint "Checking…". On change: `const mode = e.target.checked ? "simulated_on_shift" : "nobody_online"`; `shift.run({ body: { mode } })`; on success `setResult(shiftLine(mode === "simulated_on_shift", res.converted_cases))` (**the requested mode decides the sentence, not `res.mode`**, because the mock answers `TURNED_ON` to everything), then `await refresh(); await onChanged();`; on failure `setResult(STAFFING_ERROR)` and `await refresh()` (so the switch snaps back to the true state). [CON-7; mock artefact]
5. Advance buttons: three `Button density="console"` from `ADVANCE_STEPS`, `disabled={saving}`. On click: `advance.run({ body: { step } })`; success → `setResult(advanceLine(res.now, res.became_overdue))`, `await refresh(); await onChanged();`; failure → `setResult(CLOCK_ERROR)`. [CON-8]
6. Hint line under the buttons, always: `NO_BACK` (`text-small text-text-muted`), and there is **no** back button. [SCR-7 disabled]
7. `<ResultLine id="demo-controls-result">{result}</ResultLine>` after the controls, rendered only when `result` is set (polite, `role="status"` comes from the component). Clear `result` when a new action starts.
8. Announce nothing extra (the `ResultLine` is the live region).
**Check:** covered by `Scr07.test.tsx` (Step 8). `npm run typecheck`.

### Step 7 · SCR-7: `AssignDialog.tsx`
```tsx
export interface AssignDialogProps { row: QueueRow | null; onClose(): void; onDone(line: string): Promise<void> }  // row null = closed
```
1. `open = row !== null`. When open fetch the version: `const detail = useOp("getCase", row ? { path: { reference: row.reference } } : null)`; `version = detail.data?.case.version`. [QueueRow carries no version; `expected_version` is required by `CaseActionRequest`; request R-4 in §8.2 asks for `version` on the lane row. Until then this is the one extra read.]
2. Local state: `mode: "assign" | "priority"` (default "assign"), `assignee: "riley" | "supervisor"` (default `"riley"`), `priority: "P0"|"P1"|"P2"|"P3"|"P4"` (default = the row's current `priority.level`), `reason: string`, `error: string | null`. Reset all when `row` changes (`useEffect` on `row?.reference`).
3. Dialog `title={`Assign or change priority · ${row.reference}`}` hmm: use `title={mode === "assign" ? `Assign ${ref}` : `Change priority of ${ref}`}`; `initialFocus="first"`. Content:
   - `fieldset` "What do you want to do?" with two native radios: "Assign to a person" / "Change priority" (visible `legend`).
   - assign: `fieldset` legend "Owner" with two native radios, labels exactly `Riley (demo)` (value `riley`) and `Demo supervisor` (value `supervisor`).
   - priority: `fieldset` legend "Priority" with five native radios labelled `P0 · Safety`, `P1 · Danger`, `P2 · Time-sensitive`, `P3 · Standard`, `P4 · Routine` (words from `components["schemas"]["Priority"]["word"]`).
   - `Field label="Reason" hint="Required."` with `TextArea density="console" aria-required="true" value onChange` and `error={error}` shown under it.
   - footer: secondary `Button data-dialog-cancel>Cancel</Button>` and one `Button variant="primary" loading={action.pending}>{mode === "assign" ? "Assign" : "Change priority"}</Button>`.
4. `canSubmit = reason.trim().length > 0 && version !== undefined && !action.pending`; the primary is `disabled={!canSubmit}`. While `version` is still loading show the hint "Loading the case…" (`text-small text-text-muted`); if `detail.error` show `ErrorLine message="Couldn't load this case. Try again." onRetry={detail.refetch}`. [7-17]
5. Submit: body = mode assign ? `{ action: "assign", expected_version: version, assignee, reason: reason.trim() }` : `{ action: "change_priority", expected_version: version, priority, reason: reason.trim() }`; `await action.run({ path: { reference: row.reference }, body })`.
6. Success: `const line = mode === "assign" ? `Assigned ${row.reference} to ${assignee === "riley" ? "Riley (demo)" : "Demo supervisor"}.` : `Priority of ${row.reference} changed to ${priority} · ${PRIORITY_WORD[priority]}.``; call `await onDone(line)` then `onClose()`. (Lines are built from the request; the mock's default `CLAIMED` response must not leak into the text.)
7. Errors from `action.run` (catch `ApiError`): `code === "REASON_REQUIRED"` → `setError(REASON_MISSING)`; `code === "VERSION_CONFLICT"` → `setError(`This case changed since you opened it (${d.changed_by} at ${formatStaffTime(d.changed_at)}). Reload to see it.`)` + show a text button "Reload" that calls `detail.refetch()` and clears the error (`d = err.details as { changed_by: string; changed_at: string }`; if `details` is null use "someone"); `isRoleNotAllowed` → "Assigning is for the demo supervisor."; `CASE_NOT_FOUND` → "That case isn't there any more. It may have been cleared by a demo reset."; anything else → "Couldn't save. Try again." Keep the dialog open on every error.
**Check:** `npm run typecheck`.

### Step 8 · SCR-7: `Scr07.tsx` and `Scr07.test.tsx`, `AssignDialog.test.tsx`
`Scr07.tsx` composition:
```tsx
export default function Scr07() {
  return (
    <AppFrame variant="console">
      <ConsoleHeader />
      <Main className="flex flex-col gap-4 p-4">
        <ScreenTitle id="SCR-7">Supervisor oversight</ScreenTitle>
        <RoleGate allow={["supervisor"]}><Oversight /></RoleGate>
      </Main>
    </AppFrame>
  );
}
```
`Oversight` (same file) steps:
1. `const { role } = useSession(); const { staffing } = useDemoStatus(); const res = useOp("getOversight", {}, { pollMs: 10_000, refetchOnFocus: true });` `const quiet = useRef(false); const lastSig = useRef<string | null>(null); const [updated, setUpdated] = useState(false);`
2. `useEffect` on `res.data`: if undefined return; `sig = oversightSignature(res.data)`; if `lastSig.current !== null && sig !== lastSig.current`: if `quiet.current` → leave `updated` false else `setUpdated(true)`; if `sig === lastSig.current` → `setUpdated(false)`; set `quiet.current = false`; `lastSig.current = sig`. [invariants: "Lanes updated." only for changes this tab did not cause; it clears at the next unchanged read]
3. `async function afterOwnChange() { quiet.current = true; await res.refetch(); }` passed to `DemoControls` (`onChanged`) and used by the dialog's `onDone`.
4. Render order inside `Oversight` (a `div.flex.flex-col.gap-4`): `DemoControls demoNow={res.data?.demo_now ?? null} onChanged={afterOwnChange}`; then, by data state:
   - `res.data === undefined && res.error` → `<ReadError error={res.error} role={role} allow={["supervisor"]} didntLoad={LOAD_ERROR} onRetry={() => void res.refetch()} />` and stop.
   - `res.data === undefined` (loading) → five `<Lane title loading />` in `LANES` order.
   - else: `{updated ? <StaleLine>Lanes updated.</StaleLine> : null}`; `<AlertList alerts={res.data.alerts} />`; if `allEmpty` (every lane `count === 0` **and** `alerts.length === 0`) `<p className="text-ui">{EMPTY_ALL}</p>`; `staffing?.mode === "simulated_on_shift"` → `<p className="text-ui">{liveQueueLine(res.data.live_queue_length)}</p>`; the five `Lane`s; the review-list link `<Link to="/staff/flags" className="…link-text">{reviewListLine(res.data.new_flags_count)}</Link>`.
   - a result line for assign/priority: `const [assignLine, setAssignLine] = useState("")` rendered as `<ResultLine>{assignLine}</ResultLine>` when set.
5. Dialog: `const [target, setTarget] = useState<QueueRow | null>(null)`; `<AssignDialog row={target} onClose={() => setTarget(null)} onDone={async (line) => { setAssignLine(line); await afterOwnChange(); }} />`; `Lane` `onAssign={setTarget}`.
6. When the poll fails but data exists (`res.error && res.data`) render nothing extra for SCR-7 (the lanes stay; the next read recovers).
Tests (`Scr07.test.tsx`, helper `transport(role, ops)` builds a `shellTransport(role, (op) => ops[op])` where `ops` maps operation → `() => Response`; bodies come from `specExample`; `mockDesktop()` in `beforeEach`; record `seen` op names). Titles:
- "customer role sees the role panel and makes no staff call": render at `/staff/oversight` with role customer; expect the sentence `You're acting as the customer. Switch to a staff role to see this.`; `seen` has no `getOversight`.
- "five lanes render in the fixed order with counts in the headings": h2 texts equal `["P0 and P1 · 1","Overdue · 1","Due soon · 0","Unowned · 2","Stuck waiting · 0"]` (the page also has h2 "Alerts"; filter by lane titles).
- "seeded rows land in the spec'd lanes": MHC-C-0008 in lane 1, MHC-C-0005 in lane 2, MHC-C-0006 and MHC-C-0007 in lane 4; "Demo seed" appears 4 times; the alert text `P0 safety case MHC-C-0008 created at 2:16 pm, unowned. Assign it.` is present; "Open 4 min" is present.
- "alerts newest first": render `AFTER_ADVANCE` modified with a second alert (spread the example, push `{ ...alert, line: "Older line.", at: "2026-10-16T08:00:00-05:00" }`) and assert order.
- "empty oversight keeps all five lanes and shows the sentence" (`NOTHING_URGENT`; five `None`).
- "loading shows lane titles and skeletons" (transport promise never resolves; `document.querySelectorAll("[data-skeleton]").length === 5` and the five titles without counts).
- "load failure shows the sentence and retries" (`jsonResponse(500, …)`? use a network-style failure: handler throws; or 503 with `{ error: { code: "X" } }`): `Oversight didn't load. Try again.`; click "Try again"; second call returns the body.
- "controls strip shows the switch, three advance buttons and the demo time": `getByRole("switch")`, buttons `+1 hour`, `+4 hours`, `Next business morning (Mon 7:00 am)`, text `Fri Oct 16 · 2:20 pm`, and `To go back to Fri Oct 16, reset the demo.`
- "advance success line": click the third button; `advanceDemoClock` answers `specExample("advanceDemoClock","NEXT_MORNING")`; expect `Demo time is now Mon Oct 19 · 7:00 am. 1 case became overdue.`; `seen` contains a second `getOversight`.
- "advance failure line": `advanceDemoClock` handler throws → `The clock didn't move. Try again.`
- "controls are disabled while a save is pending": the advance handler returns a promise you resolve later; while pending all three buttons and the switch are `disabled`.
- "shift off with a waiting customer": `getStaffing` first answers ON (`STAFFING_ON`), `setStaffing` answers `specExample("setStaffing","TURNED_OFF_WITH_WAITING")`; toggle the switch; expect `Shift ended. 1 waiting customer now has the 1-business-day promise.`
- "live queue line only while staffed": with staffing ON and `live_queue_length: 2` → `2 customers waiting in chat.`; with OFF the text is absent.
- "a changed read shows Lanes updated": use `vi.useFakeTimers()`; first read SEEDED, the poll (advance 10 s) returns AFTER_ADVANCE; expect `Lanes updated.`; third read AFTER_ADVANCE again → the line disappears.
- "review list link shows the new-flag count": `Review list · 3 new flags` with `href="/staff/flags"`.
- "row opens the case": click the MHC-C-0008 row button → `router.state.location.pathname === "/staff/cases/MHC-C-0008"`.
- "no 24-hour times": `expectNo24HourTimes(container)`.
`AssignDialog.test.tsx` titles (render `AssignDialog` inside `renderWithProviders` with `row` from `specExample("getOversight","SEEDED").lanes.unowned.rows[1]` (MHC-C-0007), `getCase` answering `specExample("getCase","DEFAULT")`):
- "Assign stays disabled until a reason is typed" (also disabled until `getCase` resolves).
- "assign sends the exact body and refetches": type `Billing dispute, Riley has the context`; click Assign; the recorded `applyCaseAction` body deep-equals `{ action: "assign", expected_version: 3, assignee: "riley", reason: "Billing dispute, Riley has the context" }`; path `/api/staff/cases/MHC-C-0007/actions`; `onDone` called with `Assigned MHC-C-0007 to Riley (demo).`; dialog closed.
- "change priority sends the exact body": choose "Change priority", pick `P2 · Time-sensitive`, reason `Customer reports a second invoice`; body `{ action: "change_priority", expected_version: 3, priority: "P2", reason: "Customer reports a second invoice" }`; `onDone` line `Priority of MHC-C-0007 changed to P2 · Time-sensitive.`
- "422 REASON_REQUIRED shows the sentence": server answers `jsonResponse(422, specExample-error)`; text `Add a reason to assign this case.` under the field; dialog stays open. (Build the 422 body inline as `{ error: { code: "REASON_REQUIRED", field: "reason", constraint: "required for release, assign and change_priority", details: null }, request_id: "req_8f2a41" }`.)
- "409 VERSION_CONFLICT shows who changed it and offers Reload": details `{ changed_by: "Demo supervisor", changed_at: "2026-10-16T14:31:00-05:00", current_version: 4 }` → text contains `This case changed since you opened it (Demo supervisor at Fri 2:31 pm). Reload to see it.` and a "Reload" button that triggers a second `getCase`.
**Check:** `npx vitest run src/screens/scr07 src/screens/reads` green; `npm run typecheck`; `npm run lint`.

### Step 9 · SCR-8: `useShownFlags.ts`
```ts
export function useShownFlags(flags: Flag[] | undefined): { shown: Flag[]; newCount: number; showNew(): void }
```
1. `const [shownIds, setShownIds] = useState<string[] | null>(null)`.
2. `useEffect`: when `flags` is defined and `shownIds === null`, `setShownIds(flags.map(f => f.flag_id))` (the first read is what "opened" means).
3. `shown = flags && shownIds ? flags.filter(f => shownIds.includes(f.flag_id)) : []` — server order kept; **status updates of already-shown flags flow through, additions are held back**; a flag the server dropped (reset) disappears.
4. `newCount = flags && shownIds ? flags.filter(f => !shownIds.includes(f.flag_id)).length : 0`.
5. `showNew = () => flags && setShownIds(flags.map(f => f.flag_id))`.
`useShownFlags.test.ts` (renderHook): "first read is shown, nothing is new", "a later added flag is counted, not shown", "showNew reveals it", "a status change on a shown flag appears without showNew", "a removed flag disappears".

### Step 10 · SCR-8: `FlagsTable.tsx`
```tsx
export interface FlagsTableProps {
  flags: Flag[]; canReview: boolean; hintId: string;
  editing: string | null; onEdit(flagId: string | null): void;
  onReview(flag: Flag, note: string | null): Promise<void>; pendingId: string | null; rowError: { id: string; message: string } | null;
}
```
- One `<table>` with `<caption className="sr-only">Flags, newest first</caption>`; header cells `th scope="col"`: Kind, Reason, Case, Flagged, Status, Action. Phone reflow: `thead` gets `max-[699px]:sr-only`; `tr` gets `max-[699px]:block max-[699px]:border-b …`; each `td` gets `max-[699px]:flex max-[699px]:justify-between` with a `data-label` pseudo label via an in-cell `<span className="min-[700px]:sr-only text-small text-text-muted">Kind</span>`. (jsdom ignores the media queries; tests assert content, not layout.)
- Cells: Kind → `KIND = { answer: "Answer", brief: "Brief", escalation: "Escalation" }[flag.target]`. Reason → `flag.reason ?? "No reason given."`, plus when `flag.note` is non-null a second line `Note: {note}` (`text-small text-text-muted`). Case → `<Link to={caseHref(flag.case_ref)} className="t-ref link-text">{flag.case_ref}</Link>` and, when `flag.message_id`, `<Link to={`${caseHref(flag.case_ref)}?tab=conversation&message=${encodeURIComponent(flag.message_id)}`}>Open the message</Link>` (request R-1: G4 reads `tab` and `message`; without it the link lands on the case view). Flagged → `{flagged_by}` + `<Time iso={flag.at} format="short" variant="meta" />`. Status → `<Tag tone={status === "new" ? "strong" : "plain"}>{status === "new" ? "New" : "Reviewed"}</Tag>` plus for reviewed `by {reviewed_by}` and `reviewed_note` when present.
- Action cell (new flags only): not editing → `<Button density="console" disabled={!canReview} aria-describedby={canReview ? undefined : hintId} aria-label={`Mark flag on ${flag.case_ref} reviewed`} onClick={() => onEdit(flag.flag_id)}>Mark reviewed</Button>`. Editing → `Field label="Note (optional)"` with `TextInput density="console"`, primary `Button density="console" loading={pendingId === flag.flag_id} aria-label={`Mark flag on ${flag.case_ref} reviewed`}>Mark reviewed` and secondary `Cancel`. `rowError` for this flag renders as `<p className="text-small">` under the controls (never red). Reviewed flags: no button.
**Check:** `npm run typecheck`.

### Step 11 · SCR-8: `Scr08.tsx`, `Scr08.test.tsx`
Composition as Scr07: `AppFrame variant="console"` → `ConsoleHeader` → `Main` → `ScreenTitle id="SCR-8"` "Review list of flags" → `RoleGate allow={["representative","supervisor","owner"]}` → `Flags`.
`Flags` steps:
1. `const { role } = useSession(); const announce = useAnnounce(); const res = useOp("listFlags", {}, { pollMs: 15_000, refetchOnFocus: true });` (the poll is this plan's addition so the "new flag" line can appear in the demo without a focus event; §8.1 item 6). `const { shown, newCount, showNew } = useShownFlags(res.data?.flags); const review = useAction("reviewFlag");` state: `editing`, `pendingId`, `rowError`, `patches: Record<string, Pick<Flag, "status"|"reviewed_by"|"reviewed_note">>`, `resultLine`.
2. `canReview = role === "supervisor"`; when `!canReview` show once, under the statement: `<p id="flags-hint" className="text-ui">Supervisors mark flags reviewed.</p>`.
3. Statement paragraph (always, even loading/error): `Nothing on this list changes the knowledge base, prompts or tests. People decide each fix.`
4. Body by data state: first-load error → `ReadError … didntLoad="The review list didn't load. Try again."`; loading → `Skeleton height={44} rows={4}`; `res.data.flags.length === 0 && shown.length === 0` → `EmptyState title="No flags yet." body="Staff flag a wrong answer, a brief that left something out, or an escalation that wasn't needed, from any case."` (render the title and body as one sentence in the DOM: title `No flags yet.` + body; the test matches the two parts); else `StaleLine` when `newCount > 0`: `` `${newCount} new ${pluralize(newCount,"flag","flags")} since you opened this page.` `` with `actionLabel={newCount === 1 ? "Show it" : "Show them"}` `onAction={showNew}` (full sentence reads "1 new flag since you opened this page. Show it."), then `FlagsTable flags={shown.map(f => ({ ...f, ...patches[f.flag_id] }))}`.
5. `onReview(flag, note)`: `setPendingId(flag.flag_id); setRowError(null)`; `await review.run({ path: { flag_id: flag.flag_id }, body: { status: "reviewed", note } })`; success → `setPatches(p => ({ ...p, [flag.flag_id]: { status: "reviewed", reviewed_by: r.reviewed_by, reviewed_note: r.reviewed_note } }))`, `setEditing(null)`, `setResultLine("Marked reviewed.")`, `announce("Marked reviewed.")`, focus the result line (`document.getElementById("flags-result")?.focus()`), `void res.refetch()`. Failure: `isRoleNotAllowed` → `{ id, message: "Supervisors mark flags reviewed." }`; `code === "FLAG_NOT_FOUND"` → `"That flag is gone. It may have been cleared by a demo reset."` and `void res.refetch()`; otherwise `"Couldn't mark it reviewed. Try again."`. `finally` `setPendingId(null)`. Result line: `<ResultLine id="flags-result">Marked reviewed.</ResultLine>`.
Tests (`Scr08.test.tsx`; bodies via `specExample("listFlags","THREE"|"EMPTY")`, `specExample("reviewFlag","REVIEWED")`): "statement is shown"; "renders the flag row with all columns" (Answer, `Quoted $144 as the after-hours fee`, `Note: Quoted $144 as the fee`, link `MHC-C-0007` → `/staff/cases/MHC-C-0007`, `Open the message` → `/staff/cases/MHC-C-0007?tab=conversation&message=m-2`, `Riley (demo)`, `New`); "empty list sentence"; "loading shows skeletons"; "load failure shows the sentence"; "representative sees disabled buttons and the hint" (role representative: `Mark flag on MHC-C-0007 reviewed` is disabled; text `Supervisors mark flags reviewed.`); "mark reviewed with a note" (supervisor: click, type `Fee schedule is right; answer fixed in review`, confirm; the `reviewFlag` request has path `/api/staff/flags/flg-3`, method PATCH, body `{ status: "reviewed", note: "Fee schedule is right; answer fixed in review" }`; text `Marked reviewed.`; the row shows `Reviewed`); "an empty note is sent as null"; "403 from reviewFlag shows Supervisors mark flags reviewed."; "a flag added by a later read is held back with Show it" (fake timers 15 s; second read has two flags; the line `1 new flag since you opened this page.` and button `Show it`; after click two rows); "owner can list but not review"; "no automation words" (`expect(container.textContent).not.toMatch(/learn|updated the model|fixed automatically/i)`); "no 24-hour times".
**Check:** `npx vitest run src/screens/scr08` green; `npm run typecheck`; `npm run lint`.

### Step 12 · SCR-9: `basis.ts`, `OpenCases.tsx`, `Scr09.tsx`, tests
`basis.ts`:
```ts
export function basisLine(d: Pick<OwnerMetricsResponse, "as_of" | "seeds_included" | "seed_count">): string;
//  `From stored conversations and cases, as of ${formatClockLabel(d.as_of)} (demo time). ${seedSentence} These are not targets.`
//  seedSentence: seeds_included ? `Includes ${n} demo seed ${pluralize(n,"case","cases")}.` : `Does not include the ${n} demo seed ${pluralize(n,"case","cases")}.`
//  -> "From stored conversations and cases, as of Fri Oct 16 · 2:20 pm (demo time). Includes 4 demo seed cases. These are not targets."
export function isEmptyOwner(d: OwnerMetricsResponse): boolean;      // [d.in_scope_correct_resolution, d.promises_kept_on_time, d.handoffs].every(m => (m.denominator ?? 0) === 0) && d.outcomes.length === 0
export function isStale(asOfIso: string, clockNowIso: string | null): boolean;   // clockNowIso !== null && Date.parse(clockNowIso) - Date.parse(asOfIso) > 60_000
```
`basis.test.ts`: the spec sentence for SEEDED; singular "1 demo seed case"; `seeds_included:false`; `isEmptyOwner` true for `EMPTY`, false for `SEEDED`; `isStale` true for as_of 14:20 vs now 07:00 on Oct 19, false when equal.
`OpenCases.tsx`: `OpenCases({ id, title, refs, cases }: { id: string; title: string; refs: string[]; cases: OwnerMetricsResponse["cases"] })` — `<section id aria-labelledby>` with `h3` `title` (e.g. `Cases behind "Handoffs"`), `<ul>`; each ref → `<li><Link to={caseHref(ref)} className="t-ref link-text">{ref}</Link>` + (when found in `cases` by `reference`) ` · {reason} · {status}` `</li>` (a ref missing from `cases` shows the reference only); an effect announces `` `${refs.length} ${pluralize(refs.length,"case","cases")} listed.` `` through `useAnnounce()` on mount.
`Scr09.tsx`: `AppFrame variant="console"` → `ConsoleHeader` → `Main` → `ScreenTitle id="SCR-9"` "Business-owner outcomes" → `RoleGate allow={["owner","supervisor"]}` → `Outcomes`. `Outcomes` steps:
1. `const { role } = useSession(); const { clock } = useDemoStatus(); const res = useOp("getOwnerMetrics", {}); const [open, setOpen] = useState<{ key: string; title: string; refs: string[] } | null>(null);` (no poll: the spec has no refresh interval; stale is driven by the demo clock).
2. Error/loading as before (`didntLoad="Outcomes didn't load. Try again."`; loading → three `Skeleton height={120}` and `Skeleton height={32} rows={5}`).
3. Data: `d = res.data`. `stale = isStale(d.as_of, clock?.now ?? null)` → `<StaleLine actionLabel="Refresh" onAction={() => void res.refetch()}>These numbers are as of {formatTimePoint(d.as_of)}; the demo time is now {formatStaffTime(clock.now)}.</StaleLine>`. Empty → `<EmptyState title="No outcomes yet." body="Numbers appear once conversations end. Nothing here is a target." />`.
4. Tiles, stacked in one column (`div.flex.flex-col.gap-3`), in this order, from **field names**:
   - `in_scope_correct_resolution`: `estimate`; `denominatorLine = nOfN(num, den, "in-scope conversations")`; `extra = <Link to={d.measured_north_star_link.path} className="…link-text">{d.measured_north_star_link.label}</Link>`.
   - `promises_kept_on_time`: noun `promises due`.
   - `handoffs`: noun `conversations`.
   `value = formatShare(m.value)`; `reason = m.value === null ? m.null_reason : null`; `open`/`onToggle`/`panelId="cases-panel"`: toggling sets `open` to `{ key: field, title: m.label, refs: m.case_refs }` (clicking the open one closes it).
5. R3 basis `<p className="text-ui">{basisLine(d)}</p>`.
6. R4 `Card` + `CardHeader as="h2" title="Outcomes"` + `MeasuresTable caption="Outcomes of stored conversations" firstColumn="Outcome" rows={d.outcomes} noun="conversations"`. R5 `Card` "Handoffs by reason" + `MeasuresTable firstColumn="Reason" rows={d.handoffs_by_reason} noun="handoffs"`. When `rows` is empty: `<p className="text-ui text-text-muted">None yet.</p>`.
7. R6 `Card` "Missed promises": if empty `None.`; else a table (`th scope`): Case (link), Due (`<Time iso format="short">`), Outcome (as given).
8. R7: `{open ? <OpenCases id="cases-panel" … key={open.key} /> : null}` placed right after the tiles. `MeasuresTable.onOpen(key, m)` sets `open` with `key = "o-" + index` / `"h-" + index`, `title = m.label`, `refs = m.case_refs`.
9. R8: `<p>System health is on the <Link to="/monitoring">Monitoring</Link> page. Evaluation results are on the <Link to="/eval">Evaluation</Link> page.</p>` (exact sentence parts as quoted in SCREEN_SPECS R8).
Tests (`Scr09.test.tsx`; `specExample("getOwnerMetrics","SEEDED"|"EMPTY")`; role owner; `getDemoClock` answers `CLOCK_START` unless noted): "customer sees the role panel"; "three tiles with denominators" (texts `75%`, `9 of 12 in-scope conversations`, `67%`, `2 of 3 promises due`, `29%`, `5 of 17 conversations`; headings: the three labels from the contract; the estimate label `Estimate from live chats (no verified answers)`; link text `The measured number is on the Evaluation page (latest held-out run).` → `/eval`); "basis line names the seeds and says not targets"; "outcomes table rows" (five rows; `9 of 17`, `53%`); "handoffs by reason rows" (Billing dispute `2 of 5`, 40%); "missed promises row" (MHC-C-0005, `Fri Oct 16 · 9:00 am`, `Open, overdue`); "open the cases expands in place and announces the count" (click the handoffs tile's button → list with MHC-C-0007 `Billing dispute` `Unassigned` and MHC-C-0008; live region has `2 cases listed.`); "the estimate tile has no case link when case_refs is empty" (`No cases to open.` present; the SEEDED estimate has `case_refs: []`); "empty shows the sentence and — tiles" (`No outcomes yet.`, three `—`, `0 in-scope conversations`, `0 promises due`, `0 conversations`); "partial shows — with its reason while the others show numbers" (modify SEEDED: `promises_kept_on_time = { ...m, numerator: 0, denominator: 0, value: null, null_reason: "No promises are due yet.", case_refs: [] }`; expect `—`, `No promises are due yet.`, `75%` still present); "stale line when the demo clock moved" (`getDemoClock` answers `specExample("getDemoClock","ADVANCED")`; expect `These numbers are as of 2:20 pm; the demo time is now Mon 7:00 am.` and button `Refresh` that triggers a second `getOwnerMetrics`); "error shows the sentence"; "no containment word" (`not.toMatch(/containment/i)`); "no 24-hour times".
**Check:** `npx vitest run src/screens/scr09 src/screens/reads` green; typecheck; lint.

### Step 13 · SCR-10: `dataAge.ts`, `SpendBar.tsx`, `definitions.ts`, `AlertsList.tsx`, `Scr10.tsx`
`dataAge.ts`:
```ts
export const STALE_AFTER_MS = 120_000;
export function dataAgeMinutes(asOfIso: string, nowMs: number): number;   // Math.floor((nowMs - Date.parse(asOfIso)) / 60_000), min 0
export function staleLine(asOfIso: string, nowMs: number): string | null; // null when nowMs - Date.parse(asOfIso) <= STALE_AFTER_MS; else `This data is ${n} ${n === 1 ? "minute" : "minutes"} old.`
```
`dataAge.test.ts`: "fresh data has no line", "exactly 2 minutes old has no line", "5 minutes → This data is 5 minutes old.", "a future as_of is 0 minutes and no line".
`SpendBar.tsx`: `SpendBar({ todayCents, capCents }: { todayCents: number; capCents: number })`: text `<p>{formatCents(todayCents)} of {formatCents(capCents)} daily cap</p>`; `<div aria-hidden="true" className="h-2 rounded-tag border border-border-hair bg-surface-well"><div className="h-full rounded-tag bg-text" style={{ width: `${pct}%` }} /></div>` with `pct = Math.min(100, Math.round(todayCents / capCents * 100))` (ink fill; **never emerald, never red**); when `todayCents >= capCents` add `<Tag tone="strong" icon={<IconWarning …/>}>Cap reached</Tag>`. A visually hidden sentence mirrors the numbers (`sr-only`: "Spend today $6.12 of the $30.00 daily cap, 20 percent."). `SpendBar.test.tsx`: "612 of 3000 → $6.12 of $30.00 and no Cap reached", "3012 of 3000 → bar clamps to 100% and Cap reached shows", "fill width is the rounded percent".
`definitions.ts` exports `DEFINITIONS: { heading: string; items: { term: string; text: string }[] }[]` — static copy derived from `docs/design/key-metrics-registry.md` (cite the registry row names in a file comment, not numbers):
- "Health": `Conversations` — "Live conversations started since the last reset. Tests and load runs are not counted."; `Turns` — "Customer messages the assistant replied to."; `Failures` — "Turns that ended in a handoff because of a model error, a tool error or a timeout, out of all turns. Retried rate-limit responses are counted apart."; `Latency p50 and p95` — "How long a customer waits for a reply, measured on live turns. p50 is the typical turn; p95 is the slowest 1 in 20. Shown once at least 20 turns exist."; `Spend today` — "Model-call cost since midnight Austin time, against the $30 daily cap. At the cap, new chats hand off and no model calls run until tomorrow."; `Last restart` — "The last time the health check restarted the service."; `Trace export` — "How many turns have had their trace sent. Traces themselves are never shown here."
- "Correctness": `Containment estimate` — "An estimate, not a measured number: live conversations that ended resolved by the assistant and were not flagged wrong by staff, out of live conversations on a handled topic. The measured number is on the Evaluation page."; `Escalations by reason` — "Conversations handed to a person, grouped by the reason on the case."
`AlertsList.tsx`: `AlertsList({ alerts }: { alerts: MonitorAlert[] })` — `[...alerts].sort((a, b) => Number(b.state === "firing") - Number(a.state === "firing"))` (stable: firing first, contract order kept inside each group). Each `li`: firing → `<Tag tone="strong" icon={<IconWarning …/>}>Firing</Tag>` + `<span className="font-semibold">{decision_line}</span>` + (when `fired_at`) `<span className="text-time-meta text-text-muted">since <Time iso={fired_at} format="point" variant="meta" /></span>`; quiet → `<Tag>Quiet</Tag>` + `<span className="text-text-muted">{decision_line}</span>`. `<ul>` inside `section aria-labelledby` with `h2` "Alerts".
`Scr10.tsx`: `AppFrame variant="page"` → `DemoPageHeader title="Monitoring" subtitle="Is it running, and is it right?"` → `Main className="flex flex-col gap-4 p-4"` → `ScreenTitle id="SCR-10"` "Monitoring" → `Monitor`. `Monitor` steps:
1. `const res = useOp("getMonitoring", {}, { pollMs: 30_000 }); const now = useNow(15_000); const announce = useAnnounce(); const prevFiring = useRef<Set<string> | null>(null);`
2. `useEffect` on `res.data`: `firing = new Set(data.alerts.filter(a => a.state === "firing").map(a => a.type))`; if `prevFiring.current !== null`, for each type in `firing` not in `prevFiring.current` call `announce(data.alerts.find(a => a.type === type)!.decision_line)`; then `prevFiring.current = firing`. [first read never announces; steady refreshes are silent]
3. Error with no data → `ReadError … didntLoad="Monitoring didn't load. Try again."` (no `allow`); loading → `Skeleton height={20}` data-age line + `Skeleton height={56} rows={6}`.
4. Data-age line (`<p className="text-ui text-text-muted">`): `` `Updated ${formatTimePoint(d.as_of)} · redacted · traces are not shown here` `` and, when `staleLine(d.as_of, now)` is non-null, a `StaleLine` with that text under it (polite).
5. Alerts `AlertsList`; then **Health** `Card` (`CardHeader as="h2" title="Health"`): one `CardRow` per `d.health` tile (`label` = tile label; value `formatTileValue(tile)` when `tile.value !== null`, else `—` with the row `hint = tile.null_reason`; `Failures`-style tiles with `numerator`/`denominator` add `hint` `` `${num} of ${den} turns` ``), then a `CardRow label="Spend today"` containing `SpendBar`, `CardRow label="Last health-check restart"` (value `<Time iso={d.last_restart.at} format="short" />` or `No restart recorded.` when null), `CardRow label="Trace export"` with `d.trace_export` verbatim. Then **Correctness** `Card` (`h2` "Correctness"): `CardRow` for `correctness.containment_estimate` (label as given; value `formatShare`; hint `nOfN(num, den, "live conversations")` or its `null_reason`; plus plain `Tag` "Estimate"), then `h3` "Escalations by reason" and one `CardRow` per tile (label, `formatCount(value)`), or `<p>No escalations since the last reset.</p>` when the list is empty. **Health and Correctness are two separate `Card`s; no row or tile mixes them (R-35).**
6. Empty (`d.health.every(t => t.value === 0 || t.value === null)`): above Health, `<p className="text-ui">No conversations since the last reset, so there is nothing to measure yet.</p>`; the rows still render ("—", reasons) and the restart row still shows.
7. Definitions (R5): `Disclosure summary="What each measure counts"` containing `DEFINITIONS` as `h3` + `dl`.
8. `trace_export` and everything else comes only from the response; render no `<a>` with an href containing "trace".
Tests (`Scr10.test.tsx`; role customer unless noted; `specExample("getMonitoring", …)`; `vi.useFakeTimers({ toFake: ["setTimeout","setInterval","Date"] })` with `vi.setSystemTime("2026-10-16T14:21:00-05:00")` for the age tests): "renders for the customer role" (one `h1`, role switch present, no RoleNotAllowed text); "updated line" (`Updated 2:20 pm · redacted · traces are not shown here`); "health rows" (`Conversations` 18, `Turns` 74, `Failures` with `1 of 74 turns`, `Latency p50` `4.2 s`, `Latency p95` `10.2 s`, `$6.12 of $30.00 daily cap`, restart `Thu Oct 15 · 10:41 pm`, `sent 70 of 74`); "health and correctness are separate sections" (two `section`s named Health / Correctness; the containment row is not inside the Health section); "firing first" (FIRING: the two firing lines precede the four quiet ones; `Cap reached` tag); "partial shows the reason in place of the value" (`TOO_FEW_TURNS`: `Not enough turns yet (fewer than 20)` twice; `18` still present); "empty shows the sentence" (`EMPTY`: the sentence, `No turns yet`, restart line present); "error shows the sentence" and "resetting shows the reset sentence" (503 `RESET_IN_PROGRESS`); "stale data line" (system time 2:25 pm vs `as_of` 2:20 pm → `This data is 5 minutes old.`; at 2:21 pm no line); "announces a newly firing alert only" (first read DEFAULT → nothing announced; poll at +30 s returns FIRING → the live region holds the spend-cap decision line; a further identical read announces nothing new); "definitions present"; "no trace links"; "no 24-hour times".
**Check:** `npx vitest run src/screens/scr10 src/screens/reads` green; typecheck; lint.

### Step 14 · SCR-11: `evalRows.ts`, `EvalMeasuresTable.tsx`, `Scr11.tsx`
`evalRows.ts`:
```ts
export interface EvalRow { id: string; label: string; heldOut: EvalMeasure | null; dev: EvalMeasure | null; target: string | null }
export function buildEvalRows(splits: EvalResponse["splits"]): EvalRow[];
//  union of measure ids across the two splits (ids are used ONLY to align the same measure across the two runs, never for behaviour);
//  order: first the held-out run's measures in their given order, then dev-only measures in their given order;
//  label from the held-out measure when present else the dev one; target = held-out.target ?? dev.target ?? null
export function hasTargets(rows: EvalRow[]): boolean;      // rows.some(r => r.target !== null)
export function formatRange(m: EvalMeasure): string | null; // min/max both non-null -> `Range over repeats: ${formatShare(min)} – ${formatShare(max)}` (en dash with spaces) else null
export function mixSummary(run: EvalRun): string;           // `${t} transcript-derived and ${s} labelled synthetic cases in the mix` (t, s = sums of mix[].count by origin)
```
`evalRows.test.ts` (`specExample("getLatestEval","BOTH_SPLITS")`): "rows start with the held-out measures in order, then dev-only ids", "E-1 appears once with both columns", "dev-only run gives rows with heldOut null", "NO_RUN gives no rows", "hasTargets false for the example and true when one target is set", "formatRange for the headline is `Range over repeats: 60% – 68%`", "mixSummary → `8 transcript-derived and 4 labelled synthetic cases in the mix`".
`EvalMeasuresTable.tsx`: `EvalMeasuresTable({ rows, heldOut, dev, devLabel, showTarget })`:
- `<table>`; `<caption>` (visible `text-small`): `` `Measures: ${[heldOut && `held-out run ${heldOut.run_id}`, dev && `dev run ${dev.run_id}`].filter(Boolean).join("; ")}` ``.
- `th scope="col"` headers: "Measure", then "Held-out" (only when `heldOut`), then "Dev" with a second line `<span className="block text-small text-text-muted">{devLabel}</span>` (only when `dev`), then "Target" (only when `showTarget`).
- `th scope="row"` = label. Cell for a split: measure present → `nOfN(numerator, denominator, "cases")` hmm with split noun: held-out `held-out cases`, dev `dev cases`; second line `formatShare(value)` and `formatRange` when present; absent → `<span className="text-text-muted">Not in this run</span>`. Target cell: `row.target ?? "—"`.
- Wrap in `div.overflow-x-auto`.
`Scr11.tsx`: `AppFrame variant="page"` → `DemoPageHeader title="Evaluation" subtitle="Latest run"` → `Main` → `ScreenTitle id="SCR-11"` "Evaluation report" → `Report`. `Report` steps:
1. `const res = useOp("getLatestEval", {})` (no poll: the spec has none).
2. Error/loading: `didntLoad="The evaluation report didn't load. Try again."`; loading → `Skeleton height={96}` + `Skeleton height={32} rows={6}`.
3. `d = res.data`; `ho = d.splits.held_out`, `dv = d.splits.dev`. Both null → `EmptyState title="No evaluation run yet." body="When one runs, its results appear here with their test set. No number is shown before then."` and stop.
4. Stale: `runForVersion = ho ?? dv`; `runForVersion.agent_version !== d.current_agent_version` → `StaleLine`: `` `This run used an earlier version of the agent (${runForVersion.agent_version}); the deployed version is ${d.current_agent_version}.` ``.
5. R1 headline `Card` (`CardHeader as="h2" title="Headline"`): `d.headline && ho` → `<p className="t-time-hero">{formatShare(d.headline.value)}</p>`, `<p className="text-ui">{nOfN(d.headline.numerator, d.headline.denominator, "held-out cases")}</p>` (a `Correct resolution`-style label: render `d.headline.label` above), range line when present, `Held-out split: scored only, never tuned against.`, and `<p><span className="t-ref">{ho.run_id}</span> · <Time iso={dateOnlyToIso(ho.date)} format="day" /></p>`. Otherwise (`ho === null`) `<p className="t-lead">No held-out run yet.</p>` and nothing else in the card but the dev note `Dev numbers are below, labelled: {d.dev_label}`.
6. R2 run identity `Card` "Run identity": one `CardRow` per present run: label `Held-out run` / `Dev run`, value `` `${run.run_id} · ${run.date formatted} · ${run.size} cases` `` and `hint = mixSummary(run)`.
7. R3 `Card` "Measures" → `EvalMeasuresTable`.
8. R4 `Card` "Test-set mix": for the held-out run if present, else the dev run (a second table for the dev run when both exist): columns Category, Cases, Origin (`Transcript` / `Synthetic`), What it tests (`tests ?? "—"`); `th scope`.
9. R5 `Card` "Dev failures (dev split only, redacted)": from `dv.dev_failures` only (never from held-out): `<ul>` of `case_id` (`t-ref`) + `redacted_summary`; empty → `None.`; hidden when `dv === null`.
10. Never print `target` anywhere except the Target column; never print a number without its `n of N`.
Tests (`Scr11.test.tsx`, `specExample("getLatestEval", …)`): "headline" (`65%`, `26 of 40 held-out cases`, `Held-out split: scored only, never tuned against.`, `run-2026-10-20-h`, `Range over repeats: 60% – 68%`); "run identity" (both runs, `120 cases`, `40 cases`, mix summary); "caption names the run" (`Measures: held-out run run-2026-10-20-h; dev run run-2026-10-19-d`); "measures table has col and row headers and n of N" (`22 of 25 cases`? use the actual noun strings: `22 of 25 held-out cases`, dev `96 of 120 dev cases`); "dev column carries the dev label" (`Dev (we read and fixed these, so it overstates)`); "no Target column when no measure has a target"; "a target renders only in a column headed Target" (spread BOTH_SPLITS with `measures[0].target = "Target text"` → the text is inside the Target column only); "empty (NO_RUN) shows the sentence and no number" (`not.toMatch(/\d+%/)`); "partial (DEV_ONLY) says no held-out run yet and labels dev" (`No held-out run yet.`, dev label present, no `Held-out split: scored only` line); "stale run version" (`STALE_RUN`: `This run used an earlier version of the agent (agent-0.4.0+kb-2026-10-10); the deployed version is agent-0.4.2+kb-2026-10-14.`); "dev failures come from the dev split only"; "error shows the sentence" and "resetting shows the reset sentence"; "no 24-hour times".
**Check:** `npx vitest run src/screens/scr11 src/screens/reads` green; typecheck; lint.

### Step 15 · Dev layer: transforms, scenarios, reactions
All paths in `src/dev/`. These files are dev-only (loaded only in `--mode mock`). Types come from `src/dev/scenarios/types.ts` (§4.1). Every transform must keep the body valid for its type (it is called with the Prism example body).
**`scenarios/g5-transforms.ts`** exports (pure functions; each takes and returns a body; none mutates its input; typed with `components["schemas"][…]`):
```ts
export function withLiveQueue(n: number): (b: OversightResponse) => OversightResponse;           // live_queue_length = n
export function withoutRow(reference: string): (b: OversightResponse) => OversightResponse;        // remove the row from every lane that holds it and decrement that lane's count; alerts untouched
export function withNullPromises(b: OwnerMetricsResponse): OwnerMetricsResponse;                  // promises_kept_on_time = { ...m, numerator: 0, denominator: 0, value: null, null_reason: "No promises are due yet.", case_refs: [] }; missed_promises = []
export function withExtraFlag(b: FlagsResponse): FlagsResponse;                                    // append { ...b.flags[0], flag_id: "flg-4", message_id: null, reason: null, note: null, flagged_by: "Demo supervisor", at: "2026-10-16T14:55:00-05:00", status: "new", reviewed_by: null, reviewed_note: null }; no-op when flags is empty
export function withReviewed(flagId: string, reviewed: { by: string | null; note: string | null }): (b: FlagsResponse) => FlagsResponse; // that flag: status "reviewed", reviewed_by, reviewed_note
export function rebaseMonitoring(ageMs: number): (b: MonitoringResponse) => MonitoringResponse;    // as_of = new Date(Date.now() - ageMs).toISOString(); all else unchanged
```
`g5-transforms.test.ts` ("withoutRow removes MHC-C-0007 from Unowned and decrements the count", "withExtraFlag adds exactly one new flag with a new id", "withReviewed marks only the named flag", "rebaseMonitoring(0) puts as_of within a second of now; rebaseMonitoring(300000) is five minutes old", "withNullPromises keeps the other measures", "inputs are not mutated" via `structuredClone` comparison), using `specExample` for the inputs.

**`scenarios/scr07.ts`** (`export const screenScenarios: ScreenScenarios = { complete: true, scenarios: [...] }`; every scenario: `screen: "SCR-7"`, `route: "/staff/oversight"`, `role: "supervisor"`; `state` per the table; `getOversight` forced explicitly in every scenario so a left-over force never leaks):

| id | state | label | `ops` (+ `staffing`) | notes |
|---|---|---|---|---|
| `scr07.default` | default | Seeded lanes and the P0 alert | `getOversight: { example: "SEEDED" }` | FLOW-8/10 seeds, "Demo seed" tags |
| `scr07.empty` | empty | Nothing urgent | `getOversight: { example: "NOTHING_URGENT" }` | |
| `scr07.loading` | loading | Lane skeletons | `getOversight: { hang: true }` | |
| `scr07.error` | error | Oversight did not load | `getOversight: { fail: "network" }` | |
| `scr07.error-advance` | error | The clock did not move | `getOversight: SEEDED`, `advanceDemoClock: { fail: "network" }` | click any advance button |
| `scr07.error-reason` | error | Server says a reason is missing | `getOversight: SEEDED`, `applyCaseAction: { example: "REASON_REQUIRED", status: 422 }` | Assign → type a reason → Assign |
| `scr07.error-version-conflict` | error | Case changed under the supervisor | `getOversight: SEEDED`, `applyCaseAction: { example: "VERSION_CONFLICT", status: 409 }` | |
| `scr07.stale-lanes-updated` | stale | A later read changes the lanes | `getOversight: { example: "SEEDED" }` | reaction (below) swaps the force to `AFTER_ADVANCE` about 11 s after the first read; the 10 s poll then shows "Lanes updated." |
| `scr07.success-advanced` | success | Advance to Monday morning | `getOversight: SEEDED`, `getDemoClock: { example: "START" }`, `advanceDemoClock: { example: "NEXT_MORNING" }` | reaction swaps `getOversight` → `AFTER_ADVANCE` and `getDemoClock` → `ADVANCED` |
| `scr07.success-shift-ended` | success | End the shift with a customer waiting | `staffing: "simulated_on_shift"`, `getOversight: { example: "SEEDED", transform: withLiveQueue(1) }`, `setStaffing: { example: "TURNED_OFF_WITH_WAITING" }` | turn the switch off; reaction swaps `getOversight` → `SHIFT_ENDED_WITH_WAITING` |
| `scr07.success-assigned` | success | Assign a case | `getOversight: SEEDED`, `applyCaseAction: { example: "ASSIGNED" }` | Assign → reason → Assign; reaction removes the case from Unowned |
| `scr07.success-priority-changed` | success | Change a case's priority | `getOversight: SEEDED`, `applyCaseAction: { example: "PRIORITY_CHANGED" }` | |
| `scr07.disabled-saving` | disabled | Controls disabled while saving | `getOversight: SEEDED`, `advanceDemoClock: { example: "NEXT_MORNING", delayMs: 4000 }`, `setStaffing: { example: "TURNED_ON", delayMs: 4000 }` | click an advance button and look |
| `scr07.disabled-no-back` | disabled | Demo time is Monday; no back button | `getOversight: { example: "AFTER_ADVANCE" }`, `getDemoClock: { example: "ADVANCED" }` | the hint line "To go back to Fri Oct 16, reset the demo." |
| `scr07.staffed-live-queue` | default | Staffed, two customers waiting | `staffing: "simulated_on_shift"`, `getOversight: { example: "SEEDED", transform: withLiveQueue(2) }` | R5 line |

**`reactions/scr07.ts`** (`export const reactions: Reaction[] = [...]`):
1. `{ when: { op: "getOversight", status: 200 }, then(ctx) { if (!ctx.world.forces.applyCaseAction) ctx.setForce("applyCaseAction", { example: "ASSIGNED" }); } }` — default so Assign shows a sensible mock response when no scenario forced one. (Lines in the UI come from the request, so this only keeps the mock honest.)
2. `{ when: { op: "advanceDemoClock", example: "NEXT_MORNING" }, then(ctx) { ctx.setForce("getDemoClock", { example: "ADVANCED" }); ctx.setForce("getOversight", { example: "AFTER_ADVANCE" }); ctx.refetch(); } }`.
3. `{ when: { op: "setStaffing", example: "TURNED_OFF_WITH_WAITING" }, then(ctx) { ctx.setForce("getOversight", { example: "SHIFT_ENDED_WITH_WAITING" }); ctx.refetch(); } }`.
4. `{ when: { op: "applyCaseAction", example: "ASSIGNED" }, then(ctx) { const ref = (ctx.response?.body as { case?: { reference?: string } } | undefined)?.case?.reference; if (ref) ctx.setForce("getOversight", { example: "SEEDED", transform: withoutRow(ref) }); ctx.refetch(); } }` (the Prism `ASSIGNED` body always names MHC-C-0007: mock artefact).
5. The timed swap, module-level `let armed = false;`: `{ when: { op: "getOversight", example: "SEEDED" }, then(ctx) { if (ctx.world.scenarioId !== "scr07.stale-lanes-updated" || armed) return; armed = true; setTimeout(() => { armed = false; ctx.setForce("getOversight", { example: "AFTER_ADVANCE" }); }, 11_000); } }`.
Rule: `ctx.refetch()` after `setForce`; never combine with `sequence`.

**`scenarios/scr08.ts`** (`complete: true`; `screen: "SCR-8"`, `route: "/staff/flags"`):

| id | state | role | `ops` | notes |
|---|---|---|---|---|
| `scr08.default` | default | supervisor | `listFlags: { example: "THREE" }` | |
| `scr08.empty` | empty | supervisor | `listFlags: { example: "EMPTY" }` | FLOW-12 reset |
| `scr08.loading` | loading | supervisor | `listFlags: { hang: true }` | |
| `scr08.error` | error | supervisor | `listFlags: { fail: "network" }` | |
| `scr08.error-review-forbidden` | error | supervisor | `listFlags: THREE`, `reviewFlag: { example: "ROLE_NOT_ALLOWED", status: 403 }` | click Mark reviewed; the sentence "Supervisors mark flags reviewed." |
| `scr08.error-flag-gone` | error | supervisor | `listFlags: THREE`, `reviewFlag: { example: "FLAG_NOT_FOUND", status: 404 }` | |
| `scr08.stale-new-flag` | stale | supervisor | `listFlags: { example: "THREE" }` | reaction swaps to `THREE` + `withExtraFlag` about 3 s after the first read; the 15 s poll shows the line |
| `scr08.success-reviewed` | success | supervisor | `listFlags: THREE`, `reviewFlag: { example: "REVIEWED" }` | reaction keeps the row reviewed on the next read |
| `scr08.disabled-rep` | disabled | representative | `listFlags: THREE` | |

`reactions/scr08.ts`: (1) `{ when: { op: "reviewFlag", example: "REVIEWED" }, then(ctx) { const b = ctx.response?.body as { flag_id: string; reviewed_by: string | null; reviewed_note: string | null } | undefined; if (b) ctx.setForce("listFlags", { example: "THREE", transform: withReviewed(b.flag_id, { by: b.reviewed_by, note: b.reviewed_note }) }); } }`; (2) the timed swap with its own `armed` flag for `scenarioId === "scr08.stale-new-flag"`: after 3 000 ms `ctx.setForce("listFlags", { example: "THREE", transform: withExtraFlag })`.

**`scenarios/scr09.ts`** (`complete: true`; `screen: "SCR-9"`, `route: "/staff/owner"`, `role: "owner"`):

| id | state | `ops` | notes |
|---|---|---|---|
| `scr09.default` | default | `getOwnerMetrics: SEEDED`, `getDemoClock: START` | |
| `scr09.empty` | empty | `getOwnerMetrics: EMPTY` | FLOW-12 reset |
| `scr09.loading` | loading | `getOwnerMetrics: { hang: true }` | |
| `scr09.partial` | partial | `getOwnerMetrics: { example: "SEEDED", transform: withNullPromises }` | promises tile shows "—" and its reason |
| `scr09.error` | error | `getOwnerMetrics: { fail: "network" }` | |
| `scr09.stale-clock-moved` | stale | `getOwnerMetrics: SEEDED`, `getDemoClock: { example: "ADVANCED" }` | demo clock is Monday 7:00 am, numbers are as of Friday 2:20 pm (the page also needs the 10 s demo-status poll or a focus to pick up the clock; the scenario's `refetchAll()` does it at apply time) |
| `scr09.disabled-zero-denominator` | disabled | `getOwnerMetrics: { example: "SEEDED", transform: withNullPromises }` | the promises number is not a link: "No cases to open." (also the estimate tile) |

`reactions/scr09.ts`: `export const reactions: Reaction[] = [];`.

**`scenarios/scr10.ts`** (`complete: true`; `screen: "SCR-10"`, `route: "/monitoring"`, `role: "customer"` — any role may read it). A local helper `const live = (example: string, ageMs = 0): OpForce => ({ example, transform: rebaseMonitoring(ageMs) });` — **every** scenario here uses it for `getMonitoring` (except hang/fail), because the examples' constant `as_of` of Oct 16 would otherwise read as days old:

| id | state | `ops` |
|---|---|---|
| `scr10.default` | default | `getMonitoring: live("DEFAULT")` |
| `scr10.alerts-cap-and-latency` | default | `live("FIRING")` |
| `scr10.alert-zero-traffic` | default | `live("ZERO_TRAFFIC_FIRING")` |
| `scr10.alert-failure-and-trace` | default | `live("FAILURE_AND_TRACE_FIRING")` |
| `scr10.empty` | empty | `live("EMPTY")` |
| `scr10.loading` | loading | `{ hang: true }` |
| `scr10.partial-too-few-turns` | partial | `live("TOO_FEW_TURNS")` |
| `scr10.error` | error | `{ fail: "network" }` |
| `scr10.error-resetting` | error | `{ example: "RESET_IN_PROGRESS", status: 503 }` |
| `scr10.stale-data-age` | stale | `live("DEFAULT", 5 * 60_000)` |

`reactions/scr10.ts`: `[{ when: { op: "getSession" }, then(ctx) { if (!ctx.world.forces.getMonitoring) ctx.setForce("getMonitoring", { example: "DEFAULT", transform: rebaseMonitoring(0) }); } }]` — so opening `/monitoring` without a scenario (the panel's screen jumper) is fresh too. (Document in the group file: `?ex=getMonitoring:DEFAULT` bypasses this and will read as days old.)

**`scenarios/scr11.ts`** (`complete: true`; `screen: "SCR-11"`, `route: "/eval"`, `role: "customer"`):

| id | state | `ops` |
|---|---|---|
| `scr11.default` | default | `getLatestEval: { example: "BOTH_SPLITS" }` |
| `scr11.empty` | empty | `NO_RUN` |
| `scr11.loading` | loading | `{ hang: true }` |
| `scr11.partial-dev-only` | partial | `DEV_ONLY` |
| `scr11.error` | error | `{ fail: "network" }` |
| `scr11.error-resetting` | error | `{ example: "RESET_IN_PROGRESS", status: 503 }` |
| `scr11.stale-run-version` | stale | `STALE_RUN` |

`reactions/scr11.ts`: `export const reactions: Reaction[] = [];`.

Coverage (so `src/dev/scenarios.coverage.test.ts` passes once `complete: true`): SCR-7 real states default/empty/loading/error/stale/success/disabled; SCR-8 the same seven; SCR-9 default/empty/loading/partial/error/stale/disabled; SCR-10 and SCR-11 default/empty/loading/partial/error/stale. `src/dev/scenarios.integrity.test.ts` also needs: id unique and starting with the file's slug (`scr07.` …), `route` a valid screen path, every `ops` key an `OperationId`, every `example` listed under that operation in `contract.gen.json` (with the `status` where I wrote it), `role` allowed by the screen (SCR-8 allows representative/supervisor/owner; SCR-9 owner/supervisor), no scenario on an n/a cell (none are: SCR-7 has no `partial`, SCR-9 no `success`, SCR-10/11 no `success`/`disabled`).
**Check:** `npx vitest run src/dev` green (the foundation integrity and coverage tests plus `g5-transforms.test.ts`); `npm run typecheck`; `npm run lint` (the dev files may use `any` only where the foundation `OpForce.transform` signature already does).

### Step 16 · Browser verification (Chrome DevTools MCP; no screenshots committed)
Start Prism and Vite, remember the PIDs, stop only those at the end: `(npm run mock > /tmp/g5-prism.log 2>&1 &)`, `(npm run dev:mock > /tmp/g5-vite.log 2>&1 &)`; wait until `curl -s -o /dev/null -w '%{http_code}' -H 'Cookie: mhc_session=x' http://127.0.0.1:4019/api/session` prints 200. Open `http://127.0.0.1:5184/staff/oversight?signedin=1&role=supervisor`. For each scenario id in Step 15 open `…?signedin=1&scenario=<id>` (the installer applies the role and route), at 1280 and 390 wide:
- light and dark (`?theme=dark`): no red/orange/amber, tags filled, no horizontal page scroll (tables scroll inside their own container), focus ring visible on Assign, switch, advance buttons, "Mark reviewed", tile buttons;
- targets ≥ 44 px at 390 (`Assign`, advance buttons, role switch);
- times 12-hour; no `[contract drift]` line in the console; the call log (panel Calls tab) shows only the operations in §3;
- SCR-7: advance to Monday (lanes re-read, "Demo time is now Mon Oct 19 · 7:00 am. 1 case became overdue."), Assign → reason → Assign (row leaves Unowned), shift off with a waiting customer, "Lanes updated." appears ~10-20 s after `scr07.stale-lanes-updated`; SCR-8 mark reviewed, "1 new flag since you opened this page. Show it." in ~15 s; SCR-9 open the cases; SCR-10 "This data is 5 minutes old."; SCR-11 stale line.
Record each result in the group file (Step 17). Fix defects in owned files only.
**Check:** list of scenario ids checked, widths and themes, in the report.

### Step 17 · Group file `docs/ux/04-prototype/groups/g5-oversight-reads.md`
Sections, in order: **Status** (built, date) · **What is clickable** (table: SCR → route → the interactions) · **State → how it is reached** (a table with one row per real state of each of the five screens — 7 + 7 + 7 + 6 + 6 = 33 rows — giving the scenario id, or the real interaction for success states) · **Transforms used** (each `g5-transforms.ts` export, which scenario uses it, why the nearest named example could not show the state, and that the body still type-checks) · **Mock artefacts** (§8.1 items 1, 2, 5, 7) · **Copy this plan added** (the strings not quoted in the specs: "None", "No reason given.", "No customers waiting in chat.", "No case became overdue.", "Review list · no new flags", "Loading the case…", the Assign dialog texts, "Not in this run", the SCR-8 result texts, "Open case") · **Requests** (R-1…R-4 of §8.2) · **Contract notes** (§8.1 items 3-4, 8) · **Checks run** (the table from §7 with results).
**Check:** the file exists with those sections.

### Step 18 · Final gates
Run §7's gate list once, in order, and paste the results into the report.

## 6. Data and fixtures

Synthetic only. Screens use no literal data. Tests read **the OpenAPI named examples at test time** through `src/screens/reads/test/specExample.ts` (so a spec change surfaces in tests), and modify them only with spreads shown in §5 (partial owner measure, extra alert, one target, extra flag). The only inline bodies are the three error bodies in `AssignDialog.test.tsx` and `jsonResponse(…, { error: { code } })` for generic failures; each quotes the OpenAPI `ApiError` shape. People and ids in examples: Omar Patel (MHC-C-0007), Dana Whitaker (MHC-C-0005), Marcus Hill (MHC-C-0006), "No name given" (MHC-C-0008), Riley (demo), Demo supervisor, flag `flg-3`, runs `run-2026-10-19-d` / `run-2026-10-20-h`, agent `agent-0.4.2+kb-2026-10-14`. Demo clock `2026-10-16T14:20:00-05:00`.

## 7. Checks

Package commands run from `/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/`. No git commands.

**While iterating** (the folder you are on):
`npx vitest run src/screens/reads` · `npx vitest run src/screens/scr07` · `…/scr08` · `…/scr09` · `…/scr10` · `…/scr11` · `npx vitest run src/dev/scenarios`.

**Tests the implementer writes with the code (all must exist and pass):**
`src/screens/reads/format.test.ts`, `reads/MetricTile.test.tsx`, `reads/MeasuresTable.test.tsx`; `scr07/signature.test.ts`, `scr07/Scr07.test.tsx`, `scr07/AssignDialog.test.tsx`; `scr08/useShownFlags.test.ts`, `scr08/Scr08.test.tsx`; `scr09/basis.test.ts`, `scr09/Scr09.test.tsx`; `scr10/dataAge.test.ts`, `scr10/SpendBar.test.tsx`, `scr10/Scr10.test.tsx`; `scr11/evalRows.test.ts`, `scr11/Scr11.test.tsx`; `src/dev/scenarios/g5-transforms.test.ts`. Titles are listed in §5; every screen test ends with a "no 24-hour times" check using `expectNo24HourTimes`.

**Existing tests that must stay green:** `src/routes.test.ts`, `src/screens/stubs.test.tsx` (renders all twelve routes; the single `h1` must still contain `SCR-7` … `SCR-11`, which `ScreenTitle` guarantees; for staff routes opened as customer the F-12 sentence must appear and no staff op may be called), `src/dev/scenarios.integrity.test.ts`, `src/dev/scenarios.coverage.test.ts`, `src/styles/guard.test.ts` (no hex, no red/amber/orange, no `Prefer`/`mhc_session=` outside dev), `src/components/**` tests, `src/dev/{resolve,calllog,stream}.test.ts`.

**Once before reporting, in this order, stopping at the first red** (rule `build-loop-test-scope`: lint → types → affected tests; no formatter gate exists; no full suite, because no shared file, fixture, dependency or setting changed):

| # | Command | Passing looks like |
|---|---|---|
| 1 | `npm run lint` | 0 errors, no new warnings (`exhaustive-deps` fixed, not silenced) |
| 2 | `npm run typecheck` | exits 0 |
| 3 | `npx vitest run src/screens/reads src/screens/scr07 src/screens/scr08 src/screens/scr09 src/screens/scr10 src/screens/scr11 src/dev src/styles src/routes.test.ts src/screens/stubs.test.tsx` | all green |
| 4 | Step 16 (browser) | recorded in the group file |

Optional if Prism is already up and the time cap allows: `perl -e 'alarm 300; exec @ARGV' npx playwright test --project chrome-desktop` (foundation smoke over all twelve routes; confirms `h1` prefix, role switch and zero `[contract drift]` lines for SCR-7…11). Report it as run or not run.

## 8. Risks and requests

### 8.1 Findings, mock artefacts and spec conflicts (all handled in this plan; recorded in the group file)

1. **Prism answers the first 2xx example whatever the request says.** `advanceDemoClock` (all steps → `NEXT_MORNING`), `setStaffing` (off → `TURNED_ON`), `applyCaseAction` (→ `CLAIMED`). The screens build their result lines from the request and the response fields they need (`now`, `became_overdue`, `converted_cases`), not from `label`/`result_line`/`mode`. "+1 hour" shows the Monday time in the mock unless the scenario forces `PLUS_1H`.
2. **Polling that changes between calls** (SCR-7 lanes, SCR-8 new flag): done with a timed `setForce` swap in a reaction guarded by `ctx.world.scenarioId` (no `sequence`, because `setWorld({forces})` resets sequence cursors and React StrictMode double-fires mount effects). If the swap does not show, the panel's per-operation select reaches the same state by hand.
3. **SCR-10 "Updated" label conflict.** SCREEN_SPECS R1 and IA say "Updated 2:20 pm (demo time)"; `UI_CONTRACTS.md` CON-19 and "Settled at §6" (2026-10-21, later) say `as_of` is **wall-clock** and only `demo_now` is demo time. This plan follows the later, closed decision: no "(demo time)" suffix. It is a copy question for the next spec pass, not a build blocker.
4. **Measure ids in the OpenAPI examples do not match `docs/design/key-metrics-registry.md`** (the contract has M-5 = handoffs, M-9 = promises kept, M-26 = latency p95; the registry has M-5 = containment, M-13 = promises kept, M-26 = spend; `M-15` repeats across handoff reasons). Behaviour never keys on ids; rows are keyed by position. Report to the contract owners.
5. **The `h1` carries a screen-reader-only `SCR-n · ` prefix** because the foundation's `stubs.test.tsx` and e2e smoke assert it. Cost: slightly odd accessible name. One component (`ScreenTitle`) removes it later (R-3).
6. **SCR-8 polls every 15 s** (spec says "refresh on focus" only). Added so the "1 new flag" line can appear in the demo without a focus event; harmless on the real backend.
7. **Monitoring `as_of` in the examples is a fixed Oct 16 timestamp.** Against a wall-clock rule it would read days old. The dev layer rebases it (`rebaseMonitoring`); the screen logic stays faithful to CON-19. `?ex=getMonitoring:DEFAULT` bypasses the rebase.
8. **Not in the contract, so not built:** (a) the flagged message's text inline on SCR-8 (IA "On demand", CON-16 data class mentions it, but `Flag` has no field): the row shows the staff reason and note, and "Open the message" goes to SCR-6; (b) per-measure definitions that "expand" on SCR-11 (`EvalMeasure` has no definition field): not built, nothing invented; SCR-10's static definitions are written from the metrics registry as the spec allows ("R5 none: static"). Requests R-5, R-6 below.
9. **The 24-hour strings in `alert_config.quiet_hours` (`22:00`/`06:00`) are never displayed** (they would fail `expectNo24HourTimes`); if a later change shows them, convert to 12-hour.
10. **SCR-9 "Open the cases" generalisation:** the spec disables the link for a zero denominator; this plan also disables it when the measure's `case_refs` is empty (SEEDED's estimate tile has a denominator of 12 but no refs), with the same words "No cases to open." Decision made here; the alternative would open an empty list.

### 8.2 Requests to the integrator / other groups (never edited in place)

| # | To | Request |
|---|---|---|
| R-1 | G4 (SCR-6 owner) via the orchestrator | SCR-8's "Open the message" links to `/staff/cases/:reference?tab=conversation&message=<message_id>`. G4 should open the Conversation tab and scroll to that message when those params exist. Without it the link lands on the case view (graceful). SCR-5/SCR-7/SCR-9 link to plain `/staff/cases/:reference` |
| R-2 | Integrator | Nothing needs adding to `src/components/**`. If another group also needs a switch primitive, promote `scr07/DemoControls.tsx`'s shift switch; otherwise it stays local |
| R-3 | Integrator | When SCR-7…11 are real, relax `stubs.test.tsx` and `tests/e2e/smoke.spec.ts` to "exactly one `h1`" and delete the `sr-only` prefix in `src/screens/reads/ScreenTitle.tsx` |
| R-4 | Contract owners (OpenAPI) | Add `version` to `QueueRow` (so SCR-7's Assign needs no extra `getCase` read), or accept the extra read as final |
| R-5 | Contract owners | `Flag.message_text` (redacted) if the inline expand on SCR-8 is wanted |
| R-6 | Contract owners | `EvalMeasure.definition` (string) if SCR-11 measures should expand to definitions |
| R-7 | Contract owners | Add a named `getMonitoring` example whose `as_of` is relative, or document that `as_of` is wall-clock (done in CON-19) and leave the dev rebase in place |

### 8.3 Collisions to watch

- **G4** owns SCR-6 and the `QueueRow` consumer pattern; this slice passes `onSelect` (not `href`) so rows navigate inside the SPA. G4 must not rename `caseHref`. No file overlap.
- **Foundation edits in flight:** if `src/components/shared/QueueRow.tsx`, `states.tsx` or `Dialog.tsx` change signature before this slice is built, Step 0 will not notice; the typecheck will. Re-read the file, adapt the call site, and note it in the report.
- **Dev layer indexes** (`scenarios/index.ts`, `reactions/index.ts`) import the five files by name; keep the exports `screenScenarios` and `reactions` unchanged.
- **Disk is tight** (foundation §8.1 item 9): do not install anything.

## 9. Readiness

**READY.** No `NEEDS-DECISION` for Innocent: every ambiguity (SCR-10 label, data-age rule, Assign version read, zero-denominator link rule, missing message text and definitions) is decided in §5/§8.1 with its basis. No `BLOCKED-ON`, provided Step 0's foundation files exist (they did when this plan was written; `src/state/*`, `src/test/render.tsx`, the shared components and the dev stubs were all present). Report back with: the §7 gate outputs, the Step 16 notes (scenario ids checked, widths, themes), any place you deviated from this plan and why, and the requests R-1…R-7 as they stand.

## Deviations

Recorded by the G5 implementer, 2026-10-21.

1. **`specExample.ts` reads the OpenAPI file with `node:fs`, not `?raw`.** Vite refuses `?raw` for a path outside the project root ("Denied ID"), and `import.meta.url` is not a file URL under jsdom. It resolves `process.cwd()/../../docs/ux/03-structure/ui-contracts.openapi.yaml` (vitest runs from `apps/web`).
2. **Extra test helper `src/screens/reads/test/opsTransport.ts`** (inside the owned `reads/` folder): wraps `shellTransport` with per-operation handlers (including pending promises) and records calls. `shellTransport`'s sync `extra` callback could not express the "pending save" test.
3. **`AssignDialog` mounts its form only while a row is set** (inner `AssignForm`, keyed by reference), instead of resetting state in an effect on `row?.reference`. Same behaviour, simpler.
4. **SCR-10 announces newly firing alerts as one joined sentence** (all new decision lines) because `announce()` replaces the previous message.
5. **Cards on SCR-10 and SCR-11 carry `aria-label`** (Health, Correctness, Headline, ...) so tests and screen readers can find the sections.
6. **Plan Step 16 (browser verification) not done**: this implementer has no browser tool. Recorded in the group file.
7. `npm run typecheck` was run as `npx tsc -b --noEmit` to skip the `pretypecheck` regeneration of shared generated files while other slices were editing.
