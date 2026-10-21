# UX-4 group G5: oversight and read screens (SCR-7 to SCR-11)

## Status

Built 2026-10-21 from `docs/plans/fanout/2026-10-21-ux4/g5-oversight-reads.md`. Code in `apps/web/src/screens/{reads,scr07..scr11}/`, dev layer in `apps/web/src/dev/{scenarios,reactions}/scr07..scr11.ts` and `scenarios/g5-transforms.ts`. Unit and screen tests pass (see Checks run). **Browser verification (plan Step 16) was not done**: the implementer had no browser tool. Screens have not been looked at in light/dark or at 390 px; do that before sign-off.

## What is clickable

| Screen | Route | Interactions |
|---|---|---|
| SCR-7 Supervisor oversight | `/staff/oversight` | Shift switch; +1 hour, +4 hours, Next business morning; five lanes with rows (open the case) and Assign (assign to Riley or the supervisor, or change priority, reason required); alert "Open case"; Review list link |
| SCR-8 Review list of flags | `/staff/flags` | Case link, Open the message link, Mark reviewed with optional note (supervisor only), Show it for new flags |
| SCR-9 Business-owner outcomes | `/staff/owner` | Open the cases on tiles and table rows (expands in place), links to Evaluation, Monitoring, cases, Refresh |
| SCR-10 Monitoring | `/monitoring` | Read only; "What each measure counts" disclosure; refreshes every 30 s |
| SCR-11 Evaluation report | `/eval` | Read only |

## State to how it is reached

Open `?signedin=1&scenario=<id>` in mock mode. "Interaction" means the state needs a click after the scenario is applied.

| Screen | State | Scenario id / interaction |
|---|---|---|
| SCR-7 | default | `scr07.default`, `scr07.staffed-live-queue` |
| SCR-7 | empty | `scr07.empty` |
| SCR-7 | loading | `scr07.loading` |
| SCR-7 | error | `scr07.error`; `scr07.error-advance` (click an advance button); `scr07.error-reason` and `scr07.error-version-conflict` (Assign, reason, Assign) |
| SCR-7 | stale | `scr07.stale-lanes-updated` (wait 10 to 20 s) |
| SCR-7 | success | `scr07.success-advanced`, `scr07.success-shift-ended`, `scr07.success-assigned`, `scr07.success-priority-changed` (each by the interaction in the scenario note) |
| SCR-7 | disabled | `scr07.disabled-saving` (click an advance button), `scr07.disabled-no-back` |
| SCR-8 | default | `scr08.default` |
| SCR-8 | empty | `scr08.empty` |
| SCR-8 | loading | `scr08.loading` |
| SCR-8 | error | `scr08.error`; `scr08.error-review-forbidden`, `scr08.error-flag-gone` (Mark reviewed, confirm) |
| SCR-8 | stale | `scr08.stale-new-flag` (wait up to 15 s) |
| SCR-8 | success | `scr08.success-reviewed` (Mark reviewed, confirm) |
| SCR-8 | disabled | `scr08.disabled-rep` |
| SCR-9 | default | `scr09.default` |
| SCR-9 | empty | `scr09.empty` |
| SCR-9 | loading | `scr09.loading` |
| SCR-9 | partial | `scr09.partial` |
| SCR-9 | error | `scr09.error` |
| SCR-9 | stale | `scr09.stale-clock-moved` |
| SCR-9 | disabled | `scr09.disabled-zero-denominator` |
| SCR-10 | default | `scr10.default`, `scr10.alerts-cap-and-latency`, `scr10.alert-zero-traffic`, `scr10.alert-failure-and-trace` |
| SCR-10 | empty | `scr10.empty` |
| SCR-10 | loading | `scr10.loading` |
| SCR-10 | partial | `scr10.partial-too-few-turns` |
| SCR-10 | error | `scr10.error`, `scr10.error-resetting` |
| SCR-10 | stale | `scr10.stale-data-age` (line appears at the next 15 s tick) |
| SCR-11 | default | `scr11.default` |
| SCR-11 | empty | `scr11.empty` |
| SCR-11 | loading | `scr11.loading` |
| SCR-11 | partial | `scr11.partial-dev-only` |
| SCR-11 | error | `scr11.error`, `scr11.error-resetting` |
| SCR-11 | stale | `scr11.stale-run-version` |

## Transforms used

All in `apps/web/src/dev/scenarios/g5-transforms.ts`, pure, typed with the generated schemas, input never mutated (tested).

| Export | Used by | Why a named example was not enough |
|---|---|---|
| `withLiveQueue(n)` | `scr07.staffed-live-queue`, `scr07.success-shift-ended` | No oversight example carries a live queue length of 1 or 2 |
| `withoutRow(ref)` | reaction on `applyCaseAction` ASSIGNED | Moves the assigned case out of Unowned; no example shows that |
| `withNullPromises` | `scr09.partial`, `scr09.disabled-zero-denominator` | No owner example has a measure without a denominator |
| `withExtraFlag` | reaction in `scr08.stale-new-flag` | A second flag arriving later |
| `withReviewed(id, ...)` | reaction on `reviewFlag` | The next list read shows the flag as reviewed |
| `rebaseMonitoring(ageMs)` | every `scr10.*` read, reaction on `getSession` | Example `as_of` is a fixed Oct 16 timestamp, which would read as days old against the wall-clock rule |

## Mock artefacts

1. Prism answers the first 2xx example whatever the request says (`advanceDemoClock` gives NEXT_MORNING for every step, `setStaffing` gives TURNED_ON, `applyCaseAction` gives CLAIMED). The screens build result lines from the request and typed fields (`now`, `became_overdue`, `converted_cases`), never from `label` or `result_line`. "+1 hour" therefore shows the Monday time unless a scenario forces PLUS_1H.
2. Polling that changes between calls (SCR-7 lanes, SCR-8 new flag) uses a timed `setForce` swap in a reaction guarded by `ctx.world.scenarioId`. No `sequence` is used. If it does not show, pick the example by hand in the panel.
3. Forces with a `transform` are not persisted across a page reload; re-apply with `?scenario=<id>`.
4. `?ex=getMonitoring:DEFAULT` bypasses the rebase and reads as days old.
5. The `applyCaseAction` ASSIGNED body always names MHC-C-0007.

## Copy this plan added

Not quoted in the specs: "None" (empty lane), "No reason given.", "No customers waiting in chat.", "No case became overdue.", "Review list · no new flags", "Loading the case…", "Couldn't load this case. Try again.", the Assign dialog texts ("What do you want to do?", "Assign to a person", "Change priority", "Owner", "Priority", "Reason", "Required.", "Reload", the VERSION_CONFLICT, role, not-found and generic save sentences, the assign and priority result lines), "Not in this run", the SCR-8 result texts ("Marked reviewed.", "That flag is gone. It may have been cleared by a demo reset.", "Couldn't mark it reviewed. Try again."), "Open case", "Staffing didn't change. Try again.", "No restart recorded.", "No escalations since the last reset.", "None yet.", "None." (missed promises, dev failures), "Try again in a moment." (429), and the static measure definitions on SCR-10.

## Requests

- R-1 (G4 / SCR-6): SCR-8 "Open the message" links to `/staff/cases/:reference?tab=conversation&message=<message_id>`; SCR-6 should open the Conversation tab and scroll to that message. Without it the link lands on the case view.
- R-2: nothing needed in `src/components/**`. If another group wants a switch, promote the one in `scr07/DemoControls.tsx`.
- R-3 (integrator): once SCR-7 to 11 are real, relax `stubs.test.tsx` and `tests/e2e/smoke.spec.ts` to "exactly one h1" and remove the sr-only `SCR-n · ` prefix in `src/screens/reads/ScreenTitle.tsx`.
- R-4 (contract owners): add `version` to `QueueRow`, so SCR-7 Assign needs no extra `getCase` read.
- R-5: `Flag.message_text` (redacted) if the inline message expand on SCR-8 is wanted. R-6: `EvalMeasure.definition`. R-7: a relative-`as_of` monitoring example, or keep the dev rebase.

## Contract notes

- SCR-10 "Updated" line follows CON-19 and "Settled at §6" (wall-clock `as_of`, no "(demo time)" suffix), not SCREEN_SPECS R1 and IA, which say "(demo time)". A copy question for the next spec pass.
- Measure ids in the OpenAPI examples do not match `docs/design/key-metrics-registry.md` (and `M-15` repeats across handoff reasons). No behaviour keys on an id; rows are keyed by position. The one use of ids is `buildEvalRows`, which aligns the same measure across the held-out and dev runs.
- SCR-9 "Open the cases" is also disabled when `case_refs` is empty (the SEEDED estimate tile has a denominator but no refs), with the same words "No cases to open."
- `alert_config.quiet_hours` (`22:00`/`06:00`) is never displayed.
- When several alerts start firing in one SCR-10 refresh, one polite announcement joins their decision lines.

## Checks run

| Check | Result |
|---|---|
| `npm run lint` | Clean for this slice. One error in another slice's file: `src/screens/scr01/core/visit.test.ts` 25:32 irregular whitespace |
| `npx tsc -b --noEmit` | Exit 0 |
| `npx vitest run src/screens/reads scr07 scr08 scr09 scr10 scr11 src/dev src/styles src/routes.test.ts src/screens/stubs.test.tsx` | 29 files, 500 passed, 1 skipped |
| Browser verification (plan Step 16) | Not run |
