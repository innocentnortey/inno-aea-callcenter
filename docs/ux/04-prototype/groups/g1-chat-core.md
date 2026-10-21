# G1 · chat core (SCR-1 shell and chat plumbing)

Built 2026-10-21 by the G1 implementer from `docs/plans/fanout/2026-10-21-ux4/g1-chat-core.md` (its `## Deviations` section lists every departure).

## What G1 built

- `apps/web/src/screens/scr01/Scr01.tsx`: the customer chat at `/` (`AppFrame variant="chat"`, `data-screen="SCR-1"`).
- `apps/web/src/screens/scr01/core/`: `model` `reducer` `replyGroups` `settledSummary` `visit` `pending` `errors` `storage` `rowText` (pure); `gateway` (the one seam over `callOp`); `useChat` `usePendingPhase` `useMediaQuery` (hooks); `chat.css`; `components/` `TopBar ChatHeader SettledAside SettledPanel PinnedSafety Thread CustomerRow AssistantGroup MessageEntry EventEntry PendingLine FailedLine Composer StartingGreeting`; `testFixtures.ts` (test-only, reads the OpenAPI named examples).
- Dev layer: `src/dev/scenarios/scr01-core.ts` (41 scenarios, `complete: true`), `src/dev/stream/chat-scripts.ts` (9 scripts), `src/dev/reactions/scr01-core.ts` (2), `src/dev/directors/chat-core.ts` (the `test:` phrases).

## State coverage (SCR-1, all eight standard states)

Result column: what was observed. "browser" = Chrome via Playwright against Prism and the dev layer, screenshots in `/tmp/g1-evidence` (not committed); "jsdom" = a passing test.

| Scenario id | State | Result |
|---|---|---|
| `scr01-core.default`, `empty` | default, empty | browser (phone, desktop, dark): greeting, strip "Nothing yet", panel empty copy |
| `scr01-core.default-resumed`, `disabled-ended-on-resume` | default, disabled | jsdom (resume path, 410 -> ended chat) |
| `scr01-core.loading-starting`, `loading-replying`, `loading-timeout`, `loading-busy` | loading | jsdom (300 ms / 10 s phases with fake timers; skeleton then "Starting the chat…"); timeout and busy cards are G2's |
| `scr01-core.partial-part-answered`, `partial-handoff-unsaved`, `flow-no-info` | partial | scenario wiring checked by `scr01-core.test.ts`; cards are G2's |
| `scr01-core.error-send-failed` | error | browser: "That didn't send. Your message is still here." + Try again |
| `scr01-core.error-giveup-fast` | error | jsdom (65 s give-up via fake timers); shortened-limits transform tested |
| `scr01-core.error-session-gone`, `error-start-reset`, `error-start-offline` | error | browser (start-reset: 503 shows the reset sentence); jsdom (start failure + retry) |
| `scr01-core.flow-limit-rate`, `flow-limit-booking`, `flow-spend-cap` | error | browser (rate: field disabled with the sentence, key enabled); jsdom (lock, release after `RATE_HOLD_MS`, booking cap no lock, spend lock) |
| `scr01-core.flow-session-ended` | error | wiring only: the 401 goes through the shared session handling (FND) |
| `scr01-core.stale-reconnecting`, `stale-staffing-on`, `stale-staffing-off`, `stale-clock-moves` | stale | jsdom (reconnecting line; staffing event shows banner and line; clock event); scripts tested |
| `scr01-core.success-booked`, `success-verified`, `success-change-request` | success | browser (booked: panel visit block, strip line, phone strip opens at 390 px) |
| `scr01-core.success-handoff`, `success-person-again`, `success-live-queued`, `success-followup-saved` | success | jsdom (case created adds row and card; already_open adds nothing and sets the scroll target; follow-up replaces settled); browser (handoff) |
| `scr01-core.success-rep-joined`, `success-handed-back`, `success-shift-ended` | success | browser (rep joined: top bar, placeholder "Message Riley", panel Replying block, event lines, Riley message); reducer tests for hand-back and shift end |
| `scr01-core.flow-safety-takeover`, `flow-safety-midbooking`, `flow-conditional-safety` | success | browser (phone and desktop: card pinned, strip "DANGER · Leave the home immediately"); jsdom (same DOM node after two more turns, one `role="alert"`) |
| `scr01-core.disabled-empty-field`, `disabled-pending` | disabled | jsdom (Send disabled when empty or pending; field editable; person key enabled) |
| `scr01-core.disabled-chat-closed`, `flow-reset-live-chat` | disabled | browser (closed: "Start a new chat" primary, "This chat has ended."); reducer tests (reset) |

Not walked in a browser: loading-starting (4 s start), loading-replying (12 s), giveup-fast, session-ended (401 redirect), conditional safety. The Step 11 tab-order and focus-ring pass was not done by hand; tab order is a jsdom test.

## Contract use

- CON-1 `startChatSession` / `getChatThread`: thread id and limits in `sessionStorage["mhc.chat.thread"]`; a 404 starts a new chat, a 410 shows an ended chat. The thread carries no greeting and no limits, so resume shows history only and takes limits from storage.
- CON-2 `submitTurn`: `turn_id` minted by the browser and reused by Try again; 409 `TURN_IN_PROGRESS` retried after `retry_after_ms` with the same id; give-up at `limits.browser_give_up_after_ms`.
- CON-3 `streamChatEvents`: nine event types become rows and state; event keys are de-duplicated.
- CON-4 `requestPerson`, CON-5 `saveFollowUp`: `settled` replaced from the response.
- What each `settled` field drives: `visit` -> Your visit block and strip date and window; `request` -> Your request block, strip reference and due time, top bar reference chip; `identity` -> Identity block; `replying` / controller -> top bar, Replying block, composer placeholder; `actions` -> the earlier-visits list under Your visit.

## Fakes and transforms (dev layer only)

- Reactions: a demo reset forces `getChatThread` to `SESSION_ENDED` 410; a new chat clears that force.
- Director: `test: rate limit`, `test: booking cap`, `test: spend cap`, `test: timeout`, `test: busy`, `test: paused` in free text give the matching server condition. Gas words are G2's.
- `scr01-core.error-giveup-fast` shortens the limits to 5 s and 2 s (note says so).
- `RATE_HOLD_MS = 60_000` is a proposal `[A]` in `core/pending.ts`; no source gives the hold.

## Proposal strings `[P]`

"The chat didn't start. Try again." · "We couldn't reach a person just now. Tap Talk to a person to try again." · "Your choice didn't save. Try again." · "Choice sent" (customer row for a card answer whose label is unknown, and for history turns with no text). All in `core/errors.ts` and `core/rowText.ts`.

## Decisions made by this plan

D1 only `safety` is pinned (conditional safety stays inline) · D2 no back button; second top-bar line is "Meridian assistant · automated" · D3 the role row is always its own 44 px row · D4 an ended chat replaces "Talk to a person" with "Start a new chat" · D5 rate hold 60 s, spend cap for the chat, booking cap never locks · D6 code and form rows use fixed words · D7 thread id and limits in sessionStorage.

## Requests to the integrator and contract owners

1. The dev panel's bottom-right "Prototype only" button covers the Send button's label at 390 px (Send is still reachable from its left edge). Move the launcher away from the composer on phones, or raise it above it.
2. Contract: add `starts_at` / `ends_at` ISO fields to `SettledVisit` (so the visit window can be a `<time datetime>`); include the greeting turn and `limits` in `ChatThread`.
3. Contract: add `retry_turn_id` to `NoticeBlock` (G2's C-2); until then `retry` with an empty id means the latest customer turn.
4. `getChatThread` examples always show `nobody_online` staffing, so after a resume G1 calls `getStaffing` through `demoStatus.refresh()`.

## Deviations

See the plan's `## Deviations` section (13 items). The main ones: ids `scr01-core.*`; no gas rule in the director; visit and request landings and announcements are G2's; history cards get no-op `landed` and `announce`; layout from `blockLayout`; `RESUME_GONE`; the phone role row is tightened; `PinnedSafety` is a plain `div`.

## Checks

Run from `apps/web` on 2026-10-21:

- `npx eslint .` : 0 problems.
- `npx tsc -b --noEmit` : exit 0.
- `npx vitest run src/screens/scr01 src/dev src/styles src/routes.test.ts src/screens/stubs.test.tsx` : 58 files, 632 passed, 1 skipped.
- `npx vite build` then `node scripts/check-dist.mjs` : "dist is clean: no dev-layer markers".
