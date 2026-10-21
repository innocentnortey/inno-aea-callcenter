# G4 group record: staff queue (SCR-5) and case view (SCR-6)

## Built
- `apps/web/src/screens/scr05/`: Scr05, useQueueFeed, queueDiff, useRowKeys, LiveRow, QueueSections, fixtures, tests.
- `apps/web/src/screens/scr06/`: Scr06 plus header, split button, lifecycle line, promise card, brief, evidence column, live box, action area and forms, activity log, rail, reducer and hooks, tests.
- Dev layer: `dev/scenarios/{scr05,scr06,case-transforms}.ts`, `dev/reactions/scr06.ts`, `dev/stream/case-scripts.ts`, `dev/directors/{case-actions,case-store}.ts`, tests. FR-1 hook was present (integrator).

## States and how they are reached
Scenario ids `scr05.*` and `scr06.*` (each has a `notes` line). SCR-6 reads `?tab=conversation&message=<id>` (G5 link): opens the Conversation tab and highlights that message.

## Mock artefacts
1. Case pages for 0005, 0006, 0012 have empty briefs, no sources, no conversation.
2. Release/start/close-unresolved result lines, owner/supervisor allowed_actions and stream events beyond FRAMES are dev fixtures.
3. Activity log shows contacts only.
4. Queue poll repeats one example unless a scenario uses a sequence. A forced op bypasses the case director.
5. Version conflicts only when forced. 6. resolve kept/missed uses the fixed demo start time.

## Requests to the integrator
FR-1 present and used. FR-2 not needed to build (`scr06.no-case` not added). FR-3: stubs.test / e2e h1-prefix checks (not edited). FR-4: this file name. FR-5: contract wishes (OWNER_READ_ONLY, SUPERVISOR_VIEW, LIVE_QUEUED examples, `snapshot_at`, fee-bearing date Fri vs Sat).

## Deviations
- Added `scr06/useCaseActions.ts` to keep Scr06.tsx wiring-only.
- `case.fixtures.ts` uses createElement (no JSX in .ts).
- `scr05.success-resolved-return` has screen "*" (its route is a SCR-6 path).
- Visual check used Playwright screenshots, not DevTools MCP.

## Proposed strings (review fix M2, 2026-10-21)
Claim succeeded but the join failed (no wording existed in SCREEN_SPECS SCR-5/SCR-6); needs sign-off:
- SCR-6: "You claimed this case, but joining the chat didn't go through. Try Join chat."
- SCR-5: "You claimed the case, but joining the chat didn't go through. Open it and try Join chat."
Both live in `apps/web/src/screens/scr06/errorCopy.ts` (`CLAIMED_NOT_JOINED_CASE`, `CLAIMED_NOT_JOINED_QUEUE`).

## Checks
scr05, scr06, dev, styles, components tests green (550 passed); lint and typecheck clean for G4 files.
