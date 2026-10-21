# UX-4 · slice G1 chat-core (SCR-1 shell and chat plumbing)

> **Planner:** `fanout-planner` · **Date:** 2026-10-21 · **Project:** `/home/linuxuser/workspaces/inno-aea-callcenter` · **Implementer:** `fanout-implementer` (Sonnet) · **Readiness:** READY (section 9)
> **Lane / loop:** `lane::build-loop`, not `risk::security` (prototype on a mock; no secrets; the one-time code is typed by the customer and passed straight to the API, never stored or echoed). Loop: plan -> implement (code **and** its tests) -> affected tests -> code review. No test-writer, no frozen tests, no security agent. **WP-N worked pair: none** (this slice changes no model behaviour).
> **Runs after** the foundation slice (`docs/plans/fanout/2026-10-21-ux4/foundation.md`, called "FND" below) has finished. **Runs in parallel with** G2 (chat-cards, owns `scr01/cards/**`). No git here: do not `git init`, commit or push.
> **Before you write any code:** read `apps/web/src/screens/scr01/contract.ts`, `blocks.ts`, `apps/web/src/components/shared/*` (props), `apps/web/src/components/ui/index.ts`, `apps/web/src/dev/scenarios/{types.ts,index.ts}` and `apps/web/src/dev/scenarios.integrity.test.ts` **as built**. This plan quotes FND's frozen interfaces; if a built file differs from FND in a way that breaks a step, stop and report it (do not edit the file; section 8.3 of FND is the request route).

## 1. Goal and sources

**Deliver SCR-1 (route `/`, role gate `ALL`) as the real customer chat shell:** top bar (R1), demo bar (R2), role-switch row (R2b), staffing banner (R3), "What's settled" strip (phone) and panel (>= 900 px) (R4), pinned safety region (R5), thread (R6) with message rows, event lines, pending lines and failure lines, composer (R7), the CON-1/2/3/4/5 plumbing (start, resume, turn, stream, person, follow-up), the 300 ms / 10 s / 65 s timers, ended-chat handling, and safety **pinning**. G2 fills every reply-block renderer; G1 never renders a block body itself, it calls `renderBlock()`.

| Source | Sections used |
|---|---|
| `docs/ux/03-structure/SCREEN_SPECS.md` | SCR-1 (lines 35-168): regions R1-R7, Components, States table, Flow-states table, Interactions, Copy notes, Accessibility notes; "Copy rules that apply on every screen"; State matrix row SCR-1; N-1...N-9, N-26, N-27, N-31 |
| `docs/ux/03-structure/IA.md` | "Rules that apply to every screen", "Layout breakpoints", SCR-1 priority table (phone height budget) |
| `docs/ux/03-structure/UI_CONTRACTS.md` | conventions; "Named errors"; CON-1, CON-2, CON-3, CON-4, CON-5 cards |
| `docs/ux/03-structure/ui-contracts.openapi.yaml` | schemas `Settled`, `SettledVisit`, `SettledRequest`, `Write`, `Speaker`, `Option`, `ReplyBlock` (24 block types), `TurnRequest`, `TurnResponse`, `Notice`, `StartSessionResponse`, `Limits`, `ChatThread`, `HandoffRequest/Response`, `FollowUpRequest/Response`, `ChatEvent` (9 events), `Staffing`, `DemoClock`; operations `startChatSession getChatThread submitTurn streamChatEvents requestPerson saveFollowUp`; example `FRAMES` (line 2501) |
| `docs/design/design.md` | 8.1 top bar, 8.2 buttons/fields, 8.3 message rows and pending lines, 8.5 panel blocks, 8.6 safety (pinning only; the card itself is G2), 8.7 demo bar/banner/composer/strip, 9.1 responsive, 6 motion (landed wash), 10 copy tone, 11 do/don't |
| `docs/artifacts/2026-10-21-direction-A5-service-desk.html` | look reference only (`.topbar`, `.demo`, `.dock`, `.strip`, `.ai/.me/.cap`); `design.md` wins on any difference |
| FND sections | 2.4 (group split, seams), 4.4-4.9 (client, errors, hooks, UI/shared components, frozen interfaces), 5 Step 9 (scripted streams), 6.3 (matrix), 8.2 (what Prism cannot show), 8.3 (change requests) |

## 2. Boundary

### 2.1 Owned files (create / modify; relative to `/home/linuxuser/workspaces/inno-aea-callcenter/`)

```
apps/web/src/screens/scr01/index.ts                      (stub from FND; keep exactly: export { default } from "./Scr01";)
apps/web/src/screens/scr01/Scr01.tsx                     (replace the stub)
apps/web/src/screens/scr01/core/**                       (everything below)
  chat.css  model.ts  reducer.ts  storage.ts  pending.ts  visit.ts  settledSummary.ts  replyGroups.ts
  errors.ts  gateway.ts  useChat.ts  usePendingPhase.ts  useMediaQuery.ts
  components/{ChatHeader,TopBar,SettledAside,SettledStrip,SettledPanel,PinnedSafety,Thread,CustomerRow,AssistantGroup,MessageEntry,EventEntry,PendingLine,FailedLine,Composer,StartingGreeting}.tsx
  **/*.test.ts  **/*.test.tsx
apps/web/src/dev/scenarios/scr01-core.ts                 (replace FND's stub)
apps/web/src/dev/reactions/scr01-core.ts                 (replace FND's stub)
apps/web/src/dev/directors/chat-core.ts                  (replace FND's stub)
apps/web/src/dev/stream/chat-scripts.ts                  (replace FND's stub)
apps/web/src/dev/scenarios/scr01-core.test.ts            (new)
apps/web/src/dev/directors/chat-core.test.ts             (new)
apps/web/src/dev/stream/chat-scripts.test.ts             (new)
docs/ux/04-prototype/groups/g1-chat-core.md              (new; template in Step 12)
```

### 2.2 Read-only shared surfaces (import, never edit)

`apps/web/src/screens/scr01/{contract.ts,blocks.ts}` (frozen, FND), `src/components/ui/**`, `src/components/shared/**`, `src/components/shell/**`, `src/api/**`, `src/state/**`, `src/lib/**`, `src/routes.ts`, `src/styles/**`, `src/test/**`, `src/dev/**` except the four files above, `src/dev/scenarios/{types.ts,matrix.ts,index.ts,shared.ts}`, `src/dev/stream/{types.ts,events.ts,dev-stream.ts}`, `docs/ux/03-structure/**`, `docs/design/design.md`, `docs/artifacts/**`, `.claude/**`, `package.json`, `vite.config.ts`, `eslint.config.js`.

### 2.3 Owned by others; do not touch

- G2: `src/screens/scr01/cards/**` (all renderers incl. the safety card, notices, error blocks, session-ended block, handoff/follow-up chooser UI), `src/dev/{scenarios/scr01-cards.ts,reactions/scr01-cards.ts,directors/chat-cards.ts}`.
- FND: every other file (shared components, API client, dev layer core, styles, routes, `package.json`, the existing foundation tests).
- G3-G5 screens and their dev files.

### 2.4 Do not

- Do not render block bodies (text, cards, safety, notices, errors) in G1. Call `renderBlock` only. Do not import from `../cards` anywhere except what `../blocks` does already (you never import `cards`).
- Do not call `fetch`, read/write `document.cookie`, or use `Prefer`/example names/scenario names outside `src/dev/**`. Do not import `@/dev/**` from `src/screens/**` or `src/components/**` (ESLint bans it). Dev files may import `core/storage.ts` for the storage key.
- Do not use red/orange/amber, hex literals, `--color-safety*`, `--safety-*` (guard test). The red safety card is G2's; G1 only places it.
- Do not show 24-hour times, countdowns, queue positions, wait estimates, "shortly", "an agent will be with you", the word "charged", the word "sent" for a follow-up, or any completion word ("booked", "cancelled", "moved") that is not in `writes[]`/`settled.actions` (that wording comes from the server; G1 invents none).
- Do not add a typing indicator, animated dots, a spinner for the reply, or a shimmer.
- Do not echo the one-time code or PII values into the thread (customer rows for `code` and `form` use fixed words, Step 6).
- Do not add dependencies. Do not edit `src/screens/stubs.test.tsx` or `tests/e2e/smoke.spec.ts` (section 8.2).
- Do not leave Vite/Prism running at the end; stop only PIDs you started.

## 3. Requirements table

IDs `C1-nn` are this plan's. "Run" = `cd apps/web && npx vitest run <path>`.

| ID | Requirement (source) | How implemented | How verified |
|---|---|---|---|
| C1-01 | Route `/`, behind login, customer is default; phone first (SCR-1 Route) | `Scr01.tsx` renders `AppFrame variant="chat"`; no own auth code (FND `RequireSession`) | `Scr01.test.tsx` renders under `renderWithProviders` |
| C1-02 | R1 top bar: brand "Meridian Home Comfort" (the page `h1`), who is replying: "Meridian assistant · automated" or "Riley (demo representative). Assistant paused."; reference after a case exists; "Demo guide" link -> SCR-3 (SCR-1 R1; design 8.1) | `TopBar.tsx` reads `replying` + `settled.request.reference` | `TopBar.test.tsx` (3 variants + link `href="/demo"`) |
| C1-03 | R2 demo bar "Fri Oct 16, 2026 (demo date) · Nobody online" / "Simulated staff on shift (demo)" from the contract, not the browser clock (CON-1 Guarantees) | Shared `DemoBar`; G1 feeds `useDemoStatus().setFromChat` from CON-1/CON-3 and `setSource("chat")` | `Scr01.test.tsx`: clock_changed event changes date text |
| C1-04 | R2b role switch in its own 44 px row with Sign out beside it, available in every state incl. ended and error (SCR-1 R2b, Interactions) | `RoleSwitch variant="row"` + `SignOutButton` in `ChatHeader.tsx`, always rendered | `Scr01.test.tsx`: radiogroup "Acting as" present while starting, ended, failed |
| C1-05 | R3 banner "Simulated staffing (demo). No Meridian employee is online." only while the simulation is on | Shared `StaffingBanner` (reads `useDemoStatus`) | `Scr01.test.tsx` (staffing_changed ON then OFF) |
| C1-06 | R4: phone strip under the top bar, collapsed by default, one-line summary, expands on tap; >= 900 px panel always open beside the thread (SCR-1 R4, design 8.5/8.7/9.1) | `SettledAside.tsx` picks strip (`Disclosure`) vs panel by `useMediaQuery("(min-width: 900px)")`; one `<aside aria-label="What's settled">` | `SettledAside.test.tsx` (both widths via mocked `matchMedia`) |
| C1-07 | Strip line facts: "Wed Oct 21 · 8:00 am – 12:00 pm · MHC-C-0007 · due Mon 7:00 pm", "Nothing yet", danger line "DANGER · Leave the home immediately" (IA SCR-1 table; design 8.7; SCR-1 flow "Safety takeover") | `settledSummary.stripLine()` pure | `settledSummary.test.ts` |
| C1-08 | Panel blocks: Replying (only while simulation on), Your visit, Your request, Identity; empty copy "Nothing booked yet." / "No request open." / "Not checked. Only needed for private details."; "Original stays until a representative confirms." beside an open change request; hints (SCR-1 copy notes) | `SettledPanel.tsx` using `Card/CardHeader/CardRow` | `SettledAside.test.tsx` |
| C1-09 | Panel renders from `settled` only (N-4, N-27); never from the last turn's facts | `settled` replaced wholesale from every `TurnResponse`, `StartSessionResponse`, `ChatThread`, `HandoffResponse`, `FollowUpResponse`, `shift_ended` event | `reducer.test.ts` ("settled replaced, not merged") |
| C1-10 | Safety takeover: safety card pinned above the thread, outside the log, not dismissible, mounted once (announced once), strip switches to the danger line, panel shows nothing else, composer enabled but focus does not move, an open slot/code card stays in the thread below (SCR-1 R5, flow "Safety takeover"; design 8.6) | `replyGroups.findPinnedSafety()`; `PinnedSafety.tsx` keyed by `block_id`; safety block removed from log groups | `replyGroups.test.ts`, `Thread.test.tsx` (same DOM node after 2 more turns), `SettledAside.test.tsx` (danger) |
| C1-11 | Thread is `role="log"` `aria-live="polite"` `aria-relevant="additions"`; speaker name line on every message; time 12-hour (SCR-1 a11y; copy rules) | `Thread.tsx`; `MessageRow`/`SpeakerLine`/`EventLine` shared components | `Thread.test.tsx` + `expectNo24HourTimes` |
| C1-12 | Customer's own message appears immediately; after 300 ms "Meridian assistant is replying…" (static, no dots); about 10 s "Still working on this…" (same row, polite `role="status"`, announced once); 60 s deadline -> server `TURN_TIMEOUT` notice (G2 renders); browser gives up at 65 s with "That didn't send. Your message is still here." + Try again (SCR-1 loading/error; CON-2 Guarantees; design 8.3) | `pending.ts` + `usePendingPhase.ts` use `limits` from `StartSessionResponse`; `PendingLine.tsx`; `FailedLine.tsx` | `pending.test.ts`, `usePendingPhase.test.tsx` (fake timers: 299 ms none, 300 ms replying, 10 000 still, 65 000 gave-up), `Thread.test.tsx` |
| C1-13 | Send disabled while the field is empty or a reply is pending; field stays editable; **"Talk to a person" never disabled** while the chat is open (SCR-1 disabled state; IA rule) | `Composer.tsx` | `Composer.test.tsx` |
| C1-14 | "Talk to a person" before the message field in focus order; same place always (WCAG 3.2.6) | DOM order in `Composer.tsx` | `Composer.test.tsx` (tab order) |
| C1-15 | CON-1 start/resume: greeting turn; skeleton <= 1 s then "Starting the chat…"; resume after reload/role switch with the stored thread id (N-31) | `useChat` bootstrap + `storage.ts` | `useChat.test.tsx` (start; resume; 404 -> start new; 410 -> ended) |
| C1-16 | CON-2 turn: `turn_id` minted by the browser, reused unchanged by Try again; payload kinds text/choice/code/form (CON-2 Writes) | `useChat.dispatch` + `gateway.submit` | `useChat.test.tsx` (retry reuses id) |
| C1-17 | CON-2 TURN_IN_PROGRESS (409) keeps "replying…" and retries after `retry_after_ms` with the same `turn_id` (Named errors) | loop in `useChat.runTurn` | `useChat.test.tsx` |
| C1-18 | CON-3 stream open on every chat; events become rows/state; ids replayed in order; dedupe by event id; "Reconnecting… Staffing and messages may be out of date." while `reconnecting`, clears after replay (SCR-1 stale; N-1, N-2) | `useEventStream` in `useChat`; reducer `EVENT`; `StaleLine` | `reducer.test.ts`, `Scr01.test.tsx` (mock `useEventStream`) |
| C1-19 | Event lines (exact copy from the event's `line`): joined, paused, handed back, closed, shift ended, demo reset, staffing changed; top bar and composer placeholder follow the controller ("Message Riley") (SCR-1 flow states) | `EventEntry.tsx`, reducer | `reducer.test.ts`, `Thread.test.tsx` |
| C1-20 | CON-4 person: first tap creates the case (customer row "Talk to a person" + the returned block via `renderBlock`); `already_open` creates no second row, scrolls to the existing handoff/live-queued card and highlights *Your request*; HANDOFF_FAILED shows an error line, key stays (CON-4; SCR-1 Interactions) | `useChat.dispatch({kind:"person"})` | `useChat.test.tsx` |
| C1-21 | CON-5 follow-up: `dispatch({kind:"followUp"})` -> `saveFollowUp`; `settled` replaced (so `settled.request.followup` is set); *Your request* lands; announce `followup.saved_line`; NOT_ALLOWED_IN_STATE -> quiet line "There's no open request to attach this to." (CON-5) | `useChat` | `useChat.test.tsx` |
| C1-22 | Landed wash on the matching panel block header for 1.2 s, none under reduced motion; separate polite region announces the landing ("Your visit: Wednesday, October 21, 8:00 am to 12:00 pm") (design 6; SCR-1 Interactions, a11y) | `landing` state + `chat.css` + local `<LiveRegion>`; automatic from `writes[]`; also `BlockProps.landed` | `SettledAside.test.tsx` (class present then removed with fake timers), `useChat.test.tsx` (writes -> landings) |
| C1-23 | Limit handling: RATE_LIMITED -> field disabled with the limit sentence (hint line), person key stays; SPEND_CAP_REACHED -> field disabled (handoff-only); BOOKING_CAP -> field stays enabled (SCR-1 disabled state; CON-2 Named errors) | `useChat` derives `composerLock` from the last `notice` block code | `Composer.test.tsx`, `useChat.test.tsx` |
| C1-24 | Ended chat (reset, closed by Riley, 410, 404, `session_ended` block): composer disabled, "This chat has ended.", primary "Start a new chat" in the tile's place; role switch still works (SCR-1 disabled state; flow states) | `EndedReason` in state; `Composer.tsx` | `Composer.test.tsx`, `useChat.test.tsx` |
| C1-25 | Send failed (network/5xx): under the customer's message "That didn't send. Your message is still here." + Try again, text kept (SCR-1 error) | `errors.describe()`; `FailedLine.tsx` | `errors.test.ts`, `Thread.test.tsx` |
| C1-26 | Card-button actions post through the same operation; every action lands in the thread as a "You" row (SCR-1 Interactions; design 8.3) | `dispatch` maps `ChatAction` -> `TurnPayload`; customer row text rules (Step 6) | `useChat.test.tsx` |
| C1-27 | `BlockProps` supplied to `renderBlock` exactly as in the frozen `contract.ts`: `block, settled, answered, disabled, dispatch, announce, landed` | `AssistantGroup.tsx` | `Thread.test.tsx` (mock `../../blocks`) asserts props |
| C1-28 | Landmarks: `header` (R1-R3), `aside` "What's settled", `main` (thread + composer `form`), skip link first (FND `AppFrame`), one `h1` (a11y notes) | `Scr01.tsx` layout | `Scr01.test.tsx` (roles) + e2e axe (FND, section 8.2) |
| C1-29 | Focus: new cards do not steal focus; composer autofocus only at >= 900 px with a fine pointer; Enter sends only in that same case | `Composer.tsx` | `Composer.test.tsx` |
| C1-30 | Every spec'd state of SCR-1 reachable via the state switcher (section 6 matrix) | `dev/scenarios/scr01-core.ts` + `stream/chat-scripts.ts` + `reactions` + `directors` | `scr01-core.test.ts`, FND `scenarios.integrity.test.ts`, `scenarios.coverage.test.ts` with `complete = true` |
| C1-31 | No invented data in screens: all strings come from the contract or the SCREEN_SPECS copy notes; the few proposal strings are marked `[P]` in section 4.6 and listed in `groups/g1-chat-core.md` | review | Step 12 doc + code review |

## 4. Shared code to use (copied; do not paraphrase)

### 4.1 Imports

```ts
import { callOp, OPS, type OperationId, type Role } from "@/api/client";          // FND 4.4
import { ApiError } from "@/api/errors";                                          // FND 4.5
import { useEventStream } from "@/api/useEventStream";                            // FND 4.6
import { onRefetchAll } from "@/api/refetch";                                     // FND 4.5
import type { components } from "@/api/types.gen";
import { useDemoStatus } from "@/state/demoStatus";                               // FND 4.9
import { useSession } from "@/state/session";
import { newTurnId } from "@/lib/ids";                                            // newTurnId(): string
import { cn } from "@/lib/cx";
import { formatTimePoint, formatDateTimeShort, formatStaffTime } from "@/lib/time";   // ISO in, Chicago 12-hour out
import { AppFrame, Main, ... } from "@/components/shell/...";                     // read the built barrel: names per FND 4.8
import { Button, Card, CardHeader, CardBody, CardRow, Disclosure, Skeleton, TextArea, Tag, LiveRegion, VisuallyHidden, useAnnounce } from "@/components/ui";
import { IconHeadset, IconInfo, IconUser, IconCheck, IconClock, IconWarning, IconChevron, IconTicket, IconCalendar, IconQuestion } from "@/components/ui/icons";
import { AssistantMark, MessageRow, SpeakerLine, EventLine, RefChip, Time, RoleSwitch, SignOutButton, DemoBar, StaffingBanner, ErrorLine, StaleLine } from "@/components/shared/...";
import type { ChatAction, BlockProps, BlockType, ReplyBlock, Settled } from "../contract";   // relative from core/: "../contract"
import { renderBlock } from "../blocks";                                                      // relative from core/: "../blocks"
```
Find the exact export paths/barrels by reading the built `src/components/*/index.ts`; the names are FND 4.7/4.8's. If a component named here is missing or its props differ, build a local fallback inside `core/components/` only for presentation and list it under *Requests* in `groups/g1-chat-core.md`; never edit the shared one.

### 4.2 Schema types (alias once in `core/model.ts`)

```ts
type S = components["schemas"];
export type StartSessionResponse = S["StartSessionResponse"];   // {thread_id, greeting: TextBlock, demo_clock, staffing, controller, settled, events:{url,last_event_id}, limits}
export type ChatThread = S["ChatThread"];                       // {thread_id, state:"open"|"closed"|"ended_by_reset", turns[{turn_id,speaker,at,text|null,blocks[]}], settled, demo_clock, staffing, last_event_id}
export type TurnRequest = S["TurnRequest"]; export type TurnPayload = S["TurnPayload"];
export type TurnResponse = S["TurnResponse"];                   // {thread_id,turn_id,sequence,blocks,settled,writes,controller,notice|null,last_event_id}
export type HandoffResponse = S["HandoffResponse"];             // {result:"case_created"|"live_queued"|"already_open", block: HandoffBlock|LiveQueuedBlock, settled}
export type FollowUpRequest = S["FollowUpRequest"]; export type FollowUpResponse = S["FollowUpResponse"];  // {followup: FollowUpView, settled}
export type ChatEvent = S["ChatEvent"];                         // 9 events, discriminant `type`
export type Speaker = S["Speaker"]; export type Limits = S["Limits"]; export type Staffing = S["Staffing"]; export type DemoClock = S["DemoClock"];
export type Write = S["Write"];
```

### 4.3 Operation calls (exact)

```ts
callOp("startChatSession")                                                        // 201 StartSessionResponse (no body, no path)
callOp("getChatThread",  { path: { thread_id } })                                 // 200 ChatThread; 404 SESSION_NOT_FOUND; 410 SESSION_ENDED
callOp("submitTurn",     { path: { thread_id }, body: { turn_id, payload }, signal })   // 200 TurnResponse (composed failures are 200 blocks)
callOp("requestPerson",  { path: { thread_id }, body: { turn_id } })              // 200 HandoffResponse; 503 HANDOFF_FAILED
callOp("saveFollowUp",   { path: { thread_id }, body: { channel, destination, window } })   // 200 FollowUpResponse; 409 NOT_ALLOWED_IN_STATE
// stream (CON-3):
useEventStream({ op: "streamChatEvents", path: { thread_id }, lastEventId }, (data, id, type) => { ... })   // returns {status: "connecting"|"open"|"reconnecting"|"closed", lastEventId}
```
Example names (for scenarios; verified in `contract.gen.json`): `startChatSession` 201 `STARTED SIMULATION_ON`, 503 `RESET_IN_PROGRESS`, 429 `REQUEST_RATE_LIMITED`; `getChatThread` 200 `OPEN ENDED_BLOCK`, 404 `SESSION_NOT_FOUND`, 410 `SESSION_ENDED`; `submitTurn` 200 `ANSWER_WITH_SOURCE SAFETY CONDITIONAL_SAFETY BURNING_CHECK EMERGENCY_LINE NO_INFO QUICK_CHECKS URGENCY_QUESTIONS WHERE_PROMPT SLOT_CARD SLOT_CARD_MEMBER LOCATE_PROMPT CODE_SENT VERIFIED_ACCOUNT_INVOICE ACCOUNT_MEMBERSHIP ACCOUNT_WARRANTY BOOKED APPOINTMENT CANCELLED CHANGE_REQUEST HANDOFF LIVE_QUEUED FAILURE_OFFER SLOT_TAKEN OUT_OF_AREA CODE_WRONG CODE_EXPIRED CODE_LOCKED CODE_CAP_REACHED NOT_VERIFIED RATE_LIMITED BOOKING_CAP SPEND_CAP_REACHED TURN_TIMEOUT BUSY AI_PAUSED HANDOFF_STAFFED`, 400 `VALIDATION_ERROR`, 404 `SESSION_NOT_FOUND`, 409 `TURN_IN_PROGRESS`, 410 `SESSION_ENDED`, 503 `RESET_IN_PROGRESS`; `requestPerson` 200 `CASE_CREATED LIVE_QUEUED ALREADY_OPEN`, 503 `HANDOFF_FAILED`; `saveFollowUp` 200 `PHONE_MORNINGS`, 409 `NOT_ALLOWED_IN_STATE`; `streamChatEvents` 200 `FRAMES`. Any 401 example: `UNAUTHENTICATED`, `UNAUTHENTICATED_EXPIRED`.

### 4.4 Frozen chat contract (FND 4.9; import, never edit)

```ts
export type ChatAction =
  | { kind: "text"; text: string }
  | { kind: "choice"; cardId: string; option: string }
  | { kind: "code"; cardId: string; code: string }
  | { kind: "form"; cardId: string; values: Record<string, string> }
  | { kind: "person" }
  | { kind: "followUp"; channel: "email"|"phone"; destination: "on_record"|"general"; window: "morning"|"afternoon"|"any" }
  | { kind: "retry"; turnId: string }
  | { kind: "newChat" };
export interface BlockProps<T extends BlockType> {
  block: BlockOf<T>; settled: Settled | null;
  answered: boolean; disabled: boolean;
  dispatch(action: ChatAction): Promise<void>;
  announce(message: string): void;
  landed(target: "visit" | "request" | "identity"): void;
}
// blocks.ts: export function renderBlock(props: BlockProps<BlockType>): ReactNode   // "Unsupported block: {type}" when G2 has no renderer
```
**Decision (fills a gap the frozen type leaves): `dispatch` NEVER rejects.** Every failure is shown by G1 (failure line under the customer row, or a quiet system line) and the promise resolves. G2 must not rely on a rejection (section 8.1 item 2).

### 4.5 Dev-layer interfaces (FND 4.9, quoted)

```ts
export interface Scenario { id: string; screen: ScreenId | "*"; state: StandardState; flowState?: string; label: string; route: string; role?: Role; staffing?: "nobody_online"|"simulated_on_shift"; ops?: Partial<Record<OperationId, OpForce>>; stream?: StreamScript; notes?: string }
export interface ScreenScenarios { complete?: boolean; scenarios: Scenario[] }       // file exports: export const screenScenarios: ScreenScenarios
export type OpForce = { example: string; status?: number; delayMs?: number; transform?: (body: any) => any } | { fail: "network"; delayMs?: number } | { hang: true } | { sequence: OpForce[] };
export interface Reaction { when: { op: OperationId; status?: number; example?: string }; then(ctx: DevCtx): void }   // file exports: export const reactions: Reaction[]
// DevCtx: world (read-only), setForce(op, force|null), setRole, setStaffing, emit(thread, event), refetch()
export interface DirectorRule { (req: components["schemas"]["TurnRequest"], ctx: ChatDirectorCtx): string | undefined }   // file exports: export const rules: DirectorRule[]
export interface StreamStep { afterMs: number; event: unknown }
export interface StreamScript { thread?: string; steps: StreamStep[]; dropAfterMs?: number }   // chat-scripts.ts exports: export const chatScripts: Record<string, StreamScript>
```
`StandardState = "default"|"empty"|"loading"|"partial"|"error"|"stale"|"success"|"disabled"`. SCR-1 has all eight as real cells (`MATRIX["SCR-1"]`). Resolve precedence (FND Step 8): signed-out > explicit force > role emulation > defaults; delays: force `delayMs` else world delay.

### 4.6 Copy used by G1 (exact; `[P]` = proposal by this plan, no source gives words; record each in `groups/g1-chat-core.md`)

| Where | Text | Source |
|---|---|---|
| Top bar brand / second line | `Meridian Home Comfort` / `Meridian assistant · automated` | SCREEN_SPECS R1 + flow "Handed back" |
| Top bar with a case | second line + ` · ` + `<RefChip reference>` | design 8.1 |
| Top bar with Riley | `{display_name} (demo representative). Assistant paused.` (display_name "Riley") | SCREEN_SPECS R1 |
| Link | `Demo guide` -> `/demo` | SCREEN_SPECS R1 |
| Panel header | `What's settled`, hint `What's been confirmed so far` | design 8.5 |
| Strip, nothing | `Nothing yet` | SCREEN_SPECS default |
| Strip, danger | `DANGER · Leave the home immediately` (warning icon + words, ink, not red) | design 8.6 Strip |
| Replying | title `Replying`, hint `Who is answering you now`; `The automated assistant` / `{name} (demo representative). Assistant paused.` | design 8.5 |
| Your visit | title `Your visit`, hint `Your booking`; empty `Nothing booked yet.`; change pending `Original stays until a representative confirms.` | design 8.5 |
| Your request | title `Your request`; empty `No request open.`; live joined `A representative has joined this chat.`; follow-up empty `Not chosen yet`; labels `Reference` (hint `Your reference number`), `Due` (hint `The latest we've promised to get back to you`), `Follow-up` | design 8.5, SCREEN_SPECS hints |
| Identity | title `Identity`, hint `Whether you've confirmed it's you`; `Not checked. Only needed for private details.` / `Code sent to the phone ending in 02` (use `settled.identity.hint`; never invent digits: `Code sent to {hint}` where hint is e.g. "the phone ending in 02") / `Verified for this chat · {hint}` / not_verified and locked: `I can't confirm your account here. A representative will help.` | SCREEN_SPECS flow rows |
| Pending | `Meridian assistant is replying…` then `Still working on this…` (the `…` is U+2026) | SCREEN_SPECS loading |
| Send failed | `That didn't send. Your message is still here.` + button `Try again` | SCREEN_SPECS error |
| Reconnecting | `Reconnecting… Staffing and messages may be out of date.` | SCREEN_SPECS stale |
| Starting | skeleton (1 line, 24 px) for <= 1 s, then `Starting the chat…` | SCREEN_SPECS loading |
| Composer | tile `Talk to a person`; field placeholder `Type a message` (visually hidden label `Message`); with Riley placeholder `Message Riley` and label `Message to Riley`; send `aria-label="Send"` | SCREEN_SPECS R7, copy |
| Ended | `This chat has ended.` + primary `Start a new chat` | SCREEN_SPECS disabled |
| Reset (event line, from `line`) | `The demo was reset, so this chat has ended. Nothing from it was kept.` | CON-3 |
| Start failed [P] | `The chat didn't start. Try again.` + `Try again` | no source |
| Reset in progress (503/409) | `The demo is resetting. Try again in a few seconds.` | UI_CONTRACTS named errors |
| Read rate limit (429) | `Try again in a moment.` | UI_CONTRACTS named errors |
| Person failed (HANDOFF_FAILED) [P] | `We couldn't reach a person just now. Tap Talk to a person to try again.` | UI_CONTRACTS says "error line with the person key still shown; tap again", no words |
| Follow-up not allowed | `There's no open request to attach this to.` | CON-5 |
| Follow-up other failure [P] | `Your choice didn't save. Try again.` | no source |
| Customer rows for non-text actions | `Talk to a person` (person); option label found by `card_id` (Step 6) else `Choice sent`; `Code entered` (code, never digits); `Details sent` (form) | design 8.3 "A reply sent from a card's button also says You" + data class rules |

## 5. Steps (build order; each step ends with its check)

Work in `/home/linuxuser/workspaces/inno-aea-callcenter/apps/web`. Commands: `npx vitest run <paths>`, `npm run typecheck`, `npm run lint`. Dependency direction: `components/*` (presentational, props only) <- `Scr01.tsx` <- `useChat` <- `gateway` (I/O adapter over `callOp`) and pure modules (`reducer`, `replyGroups`, `settledSummary`, `visit`, `pending`, `errors`). `useChat` takes a `ChatGateway` (default `apiGateway`) so tests inject a fake; this is the one seam, justified because `callOp` is the external system. No other abstractions.

### Step 0 · Preflight
1. `ls src/screens/scr01` shows `contract.ts blocks.ts index.ts Scr01.tsx cards/` and `ls src/dev/scenarios` shows `scr01-core.ts`. If not, FND has not finished: stop (BLOCKED-ON FND).
2. Read the files listed at the top of this plan. Note: (a) the exact export names of shared components; (b) whether `integrity.test.ts` requires scenario ids to start with the *file* slug; (c) the `ChatDirectorCtx` type; (d) what `SpeakerLine`/`MessageRow` print for `kind: "assistant"` (expected "Meridian assistant · automated").
**Check:** `npm run typecheck` is green before you start.

### Step 1 · Pure modules (no React)

**`core/model.ts`** (types + initial state; write exactly):
```ts
export type EndedReason = "closed" | "reset" | "gone";            // gone = 404/410/session_ended block
export type EventIcon = "joined" | "paused" | "resumed" | "closed" | "shift" | "reset" | "staffing";
export type CustomerPayload = TurnPayload | { kind: "person" };
export type Entry =
  | { kind: "customer"; id: string; turnId: string; at: string | null; text: string; payload: CustomerPayload;
      delivery: "pending" | "sent" | "failed"; failure: string | null; retryable: boolean }
  | { kind: "reply"; id: string; blocks: ReplyBlock[] }                       // id = `${turnId}:reply`, "greeting", or `person:${turnId}`
  | { kind: "message"; id: string; speaker: Speaker; at: string; text: string } // staff_message, history text-only turns
  | { kind: "event"; id: string; at: string | null; line: string; icon: EventIcon }
  | { kind: "line"; id: string; text: string };                               // quiet system line (follow-up failure, person failure)
export interface ChatState {
  phase: "starting" | "ready" | "start-failed";
  startFailure: string | null;
  threadId: string | null;
  limits: Limits | null;
  entries: Entry[];
  settled: Settled | null;
  replying: { kind: "ai" | "human"; display_name: string | null };
  pending: { turnId: string; startedAtMs: number } | null;
  ended: EndedReason | null;
  lastNotice: { code: "RATE_LIMITED"|"BOOKING_CAP"|"SPEND_CAP_REACHED"|"TURN_TIMEOUT"|"BUSY"|"AI_PAUSED"; text: string } | null;
  rateHeld: boolean;                       // RATE_LIMITED hold active
  answered: Record<string, string>;        // card_id -> option chosen locally
  seenEvents: string[];                    // event keys already applied (dedupe)
}
export const initialState: ChatState;      // phase "starting", replying {kind:"ai", display_name:null}, everything else empty/null
```
**`core/reducer.ts`** `export function chatReducer(state: ChatState, action: Action): ChatState` (pure, no Date/random). `Action` union (exact):
```ts
export type Action =
  | { type: "START_BEGIN" }
  | { type: "START_OK"; res: StartSessionResponse }
  | { type: "START_FAIL"; message: string }
  | { type: "RESUME_OK"; thread: ChatThread; limits: Limits }
  | { type: "RESYNC_OK"; thread: ChatThread }                       // refetchAll: replace server-owned entries, keep local pending/failed customer entries
  | { type: "ENDED"; reason: EndedReason }
  | { type: "SEND_BEGIN"; entry: Extract<Entry, { kind: "customer" }>; startedAtMs: number }
  | { type: "RETRY_BEGIN"; turnId: string; startedAtMs: number }
  | { type: "TURN_OK"; turnId: string; res: TurnResponse }
  | { type: "TURN_FAIL"; turnId: string; message: string; retryable: boolean }
  | { type: "PERSON_OK"; turnId: string; res: HandoffResponse; entry: Extract<Entry, { kind: "customer" }> | null }
  | { type: "LINE"; id: string; text: string }
  | { type: "FOLLOWUP_OK"; res: FollowUpResponse }
  | { type: "ANSWERED"; cardId: string; option: string }
  | { type: "EVENT"; key: string; event: ChatEvent }
  | { type: "RATE_HOLD_END" };
```
Reducer rules (each protects an invariant):
1. `START_OK`: `threadId`, `limits`, `settled`, `replying = res.controller`, `entries = [{kind:"reply", id:"greeting", blocks:[res.greeting]}]`, `phase "ready"`, `ended null`, clear `answered`, `seenEvents`, `lastNotice`. (Greeting is the empty state; N-4.)
2. `RESUME_OK`/`RESYNC_OK` map `thread.turns` with `turnsToEntries()` (Step 1, `replyGroups.ts`): speaker `customer` -> `customer` entry (`delivery "sent"`, `text` or "", payload `{kind:"text",text}`), `blocks.length > 0` -> `reply`, text-only non-customer -> `message`, speaker `event` with text -> `event` (icon `"paused"`... use `"staffing"` as the neutral icon). `thread.state`: `closed` -> `ended:"closed"`, `ended_by_reset` -> `ended:"reset"`. A `session_ended` block anywhere -> `ended:"gone"`. `RESYNC_OK` keeps customer entries with `delivery !== "sent"` appended at the end and keeps `pending`. Invariant: the server list is the truth (N-27), local unsent text is never lost.
3. `SEND_BEGIN`: append entry; `pending = {turnId, startedAtMs}`. `RETRY_BEGIN`: find the entry by `turnId`, set `delivery "pending"`, `failure null`; `pending = {...}`. Invariant: Try again reuses the entry and `turnId`.
4. `TURN_OK` (ignore if `state.pending?.turnId !== turnId` **and** the entry is not `pending`; this drops late results after the 65 s give-up marked it failed? NO: a late success for a failed entry is accepted, it is the real answer: set `delivery "sent"`, `failure null`): set the customer entry `delivery "sent"`, `at = res.blocks[0]?.at ?? null`; append `{kind:"reply", id:`${turnId}:reply`, blocks: res.blocks}` if `blocks.length` (idempotent: skip if an entry with that id exists); `settled = res.settled`; `replying = res.controller`; `pending = null` if it matches; `lastNotice` from `res.notice` (find the `notice` block in `res.blocks` for its `text`; if none, `null`); `rateHeld = res.notice?.code === "RATE_LIMITED"`; if any block `type === "session_ended"` -> `ended "gone"`.
5. `TURN_FAIL`: the entry gets `delivery "failed"`, `failure message`, `retryable`; `pending = null` if it matches.
6. `PERSON_OK`: if `res.result === "already_open"` -> only `settled = res.settled`. Else append `entry` (the "Talk to a person" customer row, `delivery "sent"`), append `{kind:"reply", id:`person:${turnId}`, blocks:[res.block]}`, `settled`. Both paths: `replying` unchanged.
7. `FOLLOWUP_OK`: `settled = res.settled`. `LINE`: append a `line` entry if the id is new.
8. `ANSWERED`: `answered[cardId] = option` (only the first answer is kept).
9. `EVENT` (skip when `key` is in `seenEvents`; push the key): by `event.type`
   - `representative_joined`: append `event` (line, icon `joined`, at); `replying = {kind:"human", display_name: event.display_name}`.
   - `ai_paused`: append `event` (icon `paused`); `replying` unchanged.
   - `staff_message`: append `message` (`id "msg:"+event.message_id`, speaker `event.speaker`, at, text).
   - `ai_resumed`: append `event` (icon `resumed`); `replying = {kind:"ai", display_name:null}`.
   - `chat_closed`: append `event` (icon `closed`); `ended "closed"` when `event.composer_disabled` (always true in the schema; keep the check).
   - `staffing_changed`: append `event` (icon `staffing`). (The hook, not the reducer, calls `setFromChat`.)
   - `shift_ended`: append `event` (icon `shift`) then `{kind:"reply", id:`shift:${key}`, blocks:[event.handoff]}`; `settled = event.settled`.
   - `clock_changed`: no entry (the hook calls `setFromChat`).
   - `demo_reset`: append `event` (icon `reset`); `ended "reset"`.
10. `RATE_HOLD_END`: `rateHeld = false`.

**`core/replyGroups.ts`** (pure):
```ts
export interface ReplyGroup { key: string; speaker: Speaker; at: string; blocks: ReplyBlock[] }   // consecutive blocks with the same speaker.kind + display_name
export function groupBlocks(entryId: string, blocks: ReplyBlock[]): ReplyGroup[];
export function findPinnedSafety(entries: Entry[]): Extract<ReplyBlock, { type: "safety" }> | null;   // FIRST block with type "safety" in entry order; only `safety` is pinned (decision D1)
export function withoutPinned(blocks: ReplyBlock[]): ReplyBlock[];                                      // drops `safety` blocks
export function cardIdOf(block: ReplyBlock): string | null;                                             // "card_id" in block ? block.card_id : null
export function isAnswered(block: ReplyBlock, answered: Record<string,string>): boolean;                // (block.answered != null) || (cardId in answered)
export function optionLabel(entries: Entry[], cardId: string, option: string): string | null;           // search reply blocks having card_id === cardId and options[].option === option -> .label
export function turnsToEntries(turns: ChatThread["turns"]): Entry[];
export function lastNoticeOf(blocks: ReplyBlock[]): { code: ...; text: string } | null;                  // from the last `notice` block
```
`groupBlocks` is called on `withoutPinned(blocks)`; an empty result renders nothing.

**`core/pending.ts`**:
```ts
export const SHOW_AFTER_MS = 300;                                   // design --delay-pending
export type PendingPhase = "hidden" | "replying" | "still" | "gave-up";
export function pendingPhase(elapsedMs: number, limits: Pick<Limits, "still_working_after_ms" | "browser_give_up_after_ms">): PendingPhase;
// elapsed < 300 -> hidden; < still_working_after_ms -> replying; < browser_give_up_after_ms -> still; else gave-up
export const DEFAULT_LIMITS: Limits = { turn_deadline_ms: 60000, still_working_after_ms: 10000, browser_give_up_after_ms: 65000, max_message_chars: 2000 };   // = CON-1 values, only a fallback for a malformed stored value
```

**`core/visit.ts`** (no timezone maths; `Settled.visit` has `date` "YYYY-MM-DD" and `window` "HH:MM-HH:MM", no ISO; **never** `new Date("2026-10-21")` formatted in Chicago, it shows Oct 20):
```ts
export function hhmmTo12h(hhmm: string): string;                     // "08:00" -> "8:00 am", "12:00" -> "12:00 pm", "00:00" -> "12:00 am", "16:00" -> "4:00 pm"
export function formatWindow(window: string, fallbackLabel: string): string;        // "08:00-12:00" -> "8:00 am – 12:00 pm" (en dash U+2013 with spaces); fallbackLabel when it does not parse
export function formatDateOnlyShort(date: string): string;          // "2026-10-21" -> "Wed Oct 21"   (Intl with timeZone "UTC" on Date.UTC parts)
export function formatDateOnlyLong(date: string): string;           // "Wednesday, October 21"
export function visitSentence(date: string, window: string, fallbackLabel: string): string;   // "Wednesday, October 21, 8:00 am to 12:00 pm"  (for the polite landing region)
```
Assemble from `formatToParts` or fixed arrays; no U+202F; output lowercase `am`/`pm`.

**`core/settledSummary.ts`**:
```ts
export function stripLine(s: Settled | null, danger: boolean): string;
// danger -> "DANGER · Leave the home immediately"; nothing -> "Nothing yet";
// else join with " · ": visit ? `${formatDateOnlyShort(date)} · ${formatWindow(...)}` : null, request ? reference : null, request?.due_at ? `due ${formatStaffTime(due_at)}` : null
export function promiseSentence(r: NonNullable<Settled["request"]>): string;
// `${promise_text}` + (due_label non-empty ? `, ${due_label}` : "") + "."   // due_label may be "" or null (examples use ""): treat both as absent. Do not append extra_lines (they repeat the reference).
export function followUpLabel(f: NonNullable<NonNullable<Settled["request"]>["followup"]>): string;   // phone+morning -> "Phone · mornings"; phone+afternoon "Phone · afternoons"; phone+any "Phone · any time"; email -> "Email"
export function identityLine(i: Settled["identity"]): string;       // table in 4.6
export function landingText(target: "visit"|"request"|"identity", s: Settled): string;   // visit: `Your visit: ${visitSentence}`; request: `Your request: ${promiseSentence}`; identity: `Identity: ${identityLine}`
export function landingsFromWrites(writes: Write[]): Array<"visit"|"request"|"identity">;
// booked|moved|cancelled -> visit; change_request_sent -> visit AND request; case_opened|followup_saved -> request; verified -> identity; unique, order of first appearance
```
`stripLine` example: visit 2026-10-21 "08:00-12:00" + request MHC-C-0007 due `2026-10-19T19:00:00-05:00` -> `"Wed Oct 21 · 8:00 am – 12:00 pm · MHC-C-0007 · due Mon 7:00 pm"`.

**`core/errors.ts`**:
```ts
export type Ctx = "start" | "turn" | "person" | "followup";
export interface Described { message: string; retryable: boolean; ended: EndedReason | null }
export function describe(err: unknown, ctx: Ctx): Described;
```
Table (first match wins; `err` is an `ApiError` or anything; non-ApiError -> treated as `status 0`):
| ctx | condition | message | retryable | ended |
|---|---|---|---|---|
| any | `status 404 && code "SESSION_NOT_FOUND"` or `status 410` | `This chat has ended.` | false | `"gone"` |
| start | `status 503 && code "RESET_IN_PROGRESS"` | reset sentence | true | null |
| start | `status 429` | `Try again in a moment.` | true | null |
| start | other | `The chat didn't start. Try again.` [P] | true | null |
| turn | `503 RESET_IN_PROGRESS` | reset sentence | true | null |
| turn | `429` | `Try again in a moment.` | true | null |
| turn | other (incl. status 0, 5xx, 400, 401, CONTRACT_DRIFT) | `That didn't send. Your message is still here.` | true | null |
| person | `503 HANDOFF_FAILED` or other | person-failed sentence [P] | true | null |
| followup | `409 NOT_ALLOWED_IN_STATE` | `There's no open request to attach this to.` | false | null |
| followup | other | follow-up failure [P] | true | null |

**`core/storage.ts`**:
```ts
export const THREAD_KEY = "mhc.chat.thread";            // sessionStorage; value JSON {threadId: string, limits: Limits}
export function loadThread(): { threadId: string; limits: Limits } | null;   // try/catch; null on any parse problem; fill missing limits fields from DEFAULT_LIMITS
export function saveThread(v: { threadId: string; limits: Limits }): void;
export function clearThread(): void;
```
**Check:** write `reducer.test.ts`, `replyGroups.test.ts`, `pending.test.ts`, `visit.test.ts`, `settledSummary.test.ts`, `errors.test.ts` (cases in section 7) and run `npx vitest run src/screens/scr01/core` -> green. Build the test fixtures from OpenAPI example values (Omar Patel, MHC-C-0007, thread `thr_9d41`, `2026-10-16T14:20:00-05:00`) in `core/testFixtures.ts` (name the OpenAPI example in a comment).

### Step 2 · Gateway
`core/gateway.ts`:
```ts
export interface ChatGateway {
  start(): Promise<StartSessionResponse>;
  resume(threadId: string): Promise<ChatThread>;
  submit(threadId: string, body: TurnRequest, signal?: AbortSignal): Promise<TurnResponse>;
  requestPerson(threadId: string, turnId: string): Promise<HandoffResponse>;
  saveFollowUp(threadId: string, body: FollowUpRequest): Promise<FollowUpResponse>;
}
export const apiGateway: ChatGateway;   // each method is one callOp from section 4.3
```
**Check:** `npm run typecheck`.

### Step 3 · Hooks
**`core/useMediaQuery.ts`**: `useMediaQuery(query: string): boolean` using `window.matchMedia` + `change` listener; returns `false` when `matchMedia` is undefined (jsdom). Constants exported: `WIDE = "(min-width: 900px)"`, `LAPTOP = "(min-width: 900px) and (pointer: fine)"`.

**`core/usePendingPhase.ts`**: `usePendingPhase(pending: ChatState["pending"], limits: Limits | null): PendingPhase`. Uses `setTimeout` for the three boundaries relative to `pending.startedAtMs` (`Date.now()`), clears on change/unmount; returns `"hidden"` when `pending` is null. Never `setInterval`.

**`core/useChat.ts`** `export function useChat(gateway: ChatGateway = apiGateway)` returns:
```ts
{ state: ChatState; phase: PendingPhase; streamStatus: StreamStatus; composerLock: null | { reason: "rate" | "spend" | "ended" | "starting"; hint: string };
  landing: { target: "visit"|"request"|"identity"; nonce: number } | null; landingText: string;     // landingText feeds the local polite LiveRegion
  dispatch(a: ChatAction): Promise<void>; land(t: "visit"|"request"|"identity"): void; retryStart(): void;
  announce(msg: string): void;                                    // = useAnnounce()
  scrollTarget: { id: string; nonce: number } | null }           // thread scroll request (Thread reads it)
```
Behaviour, in order (each numbered item is a code block with a test):
1. **Bootstrap** (effect, guarded by a `startedRef` so React StrictMode runs it once): `setSource("chat")` on mount, `setSource("poll")` on unmount. `loadThread()`: if present -> `gateway.resume(id)`; success -> `RESUME_OK` (limits from storage), `setFromChat({clock: thread.demo_clock})`, then `demoStatus.refresh()` once (staffing is authoritative from `getStaffing`; see 8.1 item 6), stream start id = `thread.last_event_id`. On `describe(...,"start").ended === "gone"` (404/410) -> `clearThread()` and fall through to start. Otherwise (no stored thread, or gone) -> `gateway.start()`; success -> `saveThread`, `START_OK`, `setFromChat({clock: res.demo_clock, staffing: res.staffing})`, stream start id = `res.events.last_event_id`; failure -> `START_FAIL(describe(e,"start").message)`. A module-level in-flight promise `startInFlight` is shared so "Talk to a person" before the thread exists awaits it (step 8).
2. **Stream:** `useEventStream(spec, onEvent)` where `spec = useMemo(() => threadId && !ended ? {op:"streamChatEvents", path:{thread_id: threadId}, lastEventId: startEventId} : null, [threadId, ended, startEventId])`. `startEventId` is set once per thread and never changes with later events (a changing spec would reconnect). `onEvent(data, id, type)`: `key = String(id ?? (data as ChatEvent).event_id)`; ignore if no `type`; dispatch `EVENT`; then side effects: `staffing_changed` -> `setFromChat({staffing: event.staffing})`; `clock_changed` -> `setFromChat({clock: event.demo_clock})`; `shift_ended` -> `demoStatus.refresh()`; announce `event.line` for joined/paused/resumed/closed/shift_ended/staffing_changed/demo_reset (polite, `useAnnounce`); for `staff_message` announce `${speaker.display_name}: ${text}`.
3. **sendTurn(payload, display text)** (internal, used by text/choice/code/form):
   1. return if `state.ended`, `state.pending`, `composerLock?.reason` is `"rate"|"spend"` for `text` kind (card choices still allowed while rate-held? NO: choices post to the same op, so block them too), or no `threadId`.
   2. `turnId = newTurnId()`; build the customer `Entry` (Step 6 row text); `dispatch SEND_BEGIN` with `startedAtMs = Date.now()`.
   3. `ac = new AbortController()`; `result = await raceGiveUp(runTurn(...), limits.browser_give_up_after_ms)`.
   4. `runTurn`: loop `gateway.submit(threadId, {turn_id, payload}, ac.signal)`; on `ApiError` with `status 409 && code "TURN_IN_PROGRESS"` wait `details.retry_after_ms` (number, default 1000) and call again **with the same turn_id**; other errors rethrow. (The 65 s race bounds the loop.)
   5. If the race times out: `ac.abort()`, `TURN_FAIL` with `That didn't send. Your message is still here.` retryable true. A response that arrives after this is still applied by `TURN_OK` (reducer rule 4) if the promise resolves; with `abort()` it will not, which is fine.
   6. Success: `TURN_OK`; then `setFromChat` nothing; run **landings** from `landingsFromWrites(res.writes)` (call `land` for each, in order, 1.3 s apart is NOT needed: set the first, queue the rest by replacing `landing` each `1200 ms`; simplest correct: set `landing` to the first target and, if there are more, schedule the next with `setTimeout(1200)`; unit-tested with fake timers); announce each via `landingText`; if `res.notice?.code === "RATE_LIMITED"` start a `setTimeout(RATE_HOLD_MS = 60_000)` -> `RATE_HOLD_END` (`[A]`: no source gives the hold; constant named and listed in the group doc).
   7. Failure: `d = describe(e,"turn")`; if `d.ended` -> `ENDED` and `TURN_FAIL(message=d.message, retryable=false)`; else `TURN_FAIL(d.message, d.retryable)`.
   8. If the response blocks include a `choice`-answerable card, `ANSWERED` was dispatched at step 2 for choice/code/form (`cardId`, option or `"code"` / `"form"`); on `TURN_FAIL` do **not** un-answer (the failed row offers Try again; the card stays marked; documented in the group doc).
4. **dispatch(action)** switch:
   - `text`: trim; ignore empty; `sendTurn({kind:"text", text}, text)`.
   - `choice`: `ANSWERED`; `sendTurn({kind:"choice", card_id, option}, ...)`.
   - `code`: `sendTurn({kind:"code", card_id, code}, "Code entered")`; `ANSWERED(cardId,"code")`.
   - `form`: `sendTurn({kind:"form", card_id, values}, "Details sent")`; `ANSWERED(cardId,"form")`.
   - `retry`: find the failed customer entry by `turnId`; if `payload.kind === "person"` re-run person; else `RETRY_BEGIN` and re-run the loop in 3.4 with that entry's stored `payload` and the same `turn_id`.
   - `person`: see item 5.
   - `followUp`: item 6.
   - `newChat`: `clearThread()`, reset state (`START_BEGIN`), run bootstrap start path again (not resume). Stream closes because `threadId` changes.
5. **Person:** await `startInFlight` if `phase === "starting"`; ignore if a person request is already in flight (`personBusy` ref); `turnId = newTurnId()`; `res = await gateway.requestPerson(threadId, turnId)`. `case_created`/`live_queued`: `PERSON_OK` with the customer entry (`text "Talk to a person"`, `payload {kind:"person"}`) then landing `request`; `already_open`: `PERSON_OK(entry null)`; set `scrollTarget` to the id of the latest `reply` entry that holds a `handoff` or `live_queued` block (search `state.entries` from the end), and `land("request")`. Failure: `describe(e,"person")` -> if `ended` `ENDED`; else `LINE` with id `person-fail:${turnId}` and the [P] sentence. Never disable the key.
6. **Follow-up:** `gateway.saveFollowUp(threadId, {channel,destination,window})` -> `FOLLOWUP_OK`, `land("request")`, `announce(res.followup.saved_line)`. Failure -> `LINE` id `followup-fail:${Date.now()}` with `describe(e,"followup").message`. Never rejects.
7. **Resync:** `onRefetchAll(() => {...})` subscription: if `threadId` and no `pending`, `gateway.resume(threadId)` -> `RESYNC_OK` (+ `setFromChat({clock})`, `refresh()`); 404/410 -> `ENDED("gone")`. Unsubscribe on unmount. (Also how the mock reaches resume-class states, section 6.)
8. `composerLock`: `ended` -> `{reason:"ended", hint:"This chat has ended."}`; `phase "starting"` -> `{reason:"starting", hint:""}`; `lastNotice?.code === "RATE_LIMITED" && rateHeld` -> `{reason:"rate", hint: lastNotice.text}`; `lastNotice?.code === "SPEND_CAP_REACHED"` -> `{reason:"spend", hint: lastNotice.text}`; else null. Notice text comes from the `notice` block (`lastNoticeOf`).
9. `land(target)`: `setLanding({target, nonce: ++n})`, clear after 1200 ms; also sets `landingText` from `landingText(target, state.settled)` once `settled` is available (use a ref to the latest settled). Idempotent within 1.2 s for the same target.

**Check:** `useChat.test.tsx` (section 7) with a fake gateway and `vi.mock("@/api/useEventStream")`, fake timers -> green; `npm run typecheck`.

### Step 4 · Presentational components (`core/components/`, all props-only, no hooks that fetch)
Each forwards `className`; Tailwind utilities reading tokens (arbitrary values `[var(--token)]` are fine; **no hex**). Read `src/styles/theme.css` for which utility names exist; where unsure use `bg-[var(--strip-bg)]`-style arbitrary values.

1. **`TopBar.tsx`** `{ replying: ChatState["replying"]; reference: string | null }`: `<div class="flex items-center gap-3 px-3.5 py-3">` `AssistantMark size={30}`, then a block: `<h1>` "Meridian Home Comfort" (`text-name` class `t-name`), second line `text-small` muted: `Meridian assistant · automated` (+ ` · ` `<RefChip reference />`), or, for human, `{display_name} (demo representative). Assistant paused.`; right-aligned `Link` (react-router) text button "Demo guide" `to="/demo"` (use `SCREENS.find(s => s.id==="SCR-3")!.path`), min 44 px target. (The design's back button is omitted: SCR-1 is the home screen and has nowhere to go back to. Deviation recorded.)
2. **`ChatHeader.tsx`** composes R1-R3: `<header>`: `TopBar`, `DemoBar`, the role row (`<div class="min-h-[44px] flex items-center justify-between gap-2 px-3.5">` `RoleSwitch variant="row"` + `SignOutButton`), `StaffingBanner`, then `{streamStatus === "reconnecting" && <StaleLine>Reconnecting… Staffing and messages may be out of date.</StaleLine>}`.
3. **`SettledAside.tsx`** `{ settled; danger: boolean; replying; staffingOn: boolean; landing; landingText }`: `<aside aria-label="What's settled">`. `useMediaQuery(WIDE)`: wide -> `<section>` panel (`w-[var(--panel-width)]`, rail background, left hairline `--line-hair`), narrow -> `<Disclosure>` strip: summary `min-h-[44px]`, background `--strip-bg`, bottom rule `--strip-rule`, text "What's settled" 13 px 600 then `stripLine(...)` 13 px tabular, chevron; body `max-h-[52vh] overflow-y-auto`. Collapsed by default (uncontrolled). Both render `SettledPanel`.
4. **`SettledPanel.tsx`** `{ settled; danger; replying; staffingOn; landing }`: header `h2` "What's settled" + hint. If `danger` render the header only. Else blocks in this order, each a `Card` + `CardHeader` (title, hint, `as="h3"`): *Replying* (only when `staffingOn`), *Your visit*, *Your request*, *Identity*. Dashed empty card for visit/request empty (`border-dashed`, `--line-dash`). Visit body: window text in the hero style (class `t-time-hero`, plain `<span>`, no `<time>` because no ISO exists, see 8.1 item 4), date line `formatDateOnlyShort`, rows `Technician`, `Fee` (`visit.fee_line`); if `visit.status === "original_stays"` or `visit.change_request`: the line `Original stays until a representative confirms.` and, when `change_request`, rows `Requested` (`wanted_text`) and `Fee` (`change_request.fee_line`); below, if `settled.actions` has more than one entry of kind booked/moved/cancelled, a muted list of the **earlier** ones' `summary` strings (the latest is the visit shown). Request body: `Reference` row (`RefChip copyable`, hint), the promise sentence (`promiseSentence`, class `t-lead`), a `Due` row only when `due_at` is not null (`formatDateTimeShort(due_at)` -> "Mon Oct 19 · 7:00 pm", in `<Time format="short" variant="due">`), `Follow-up` row (`followUpLabel` or `Not chosen yet`); when `live_queued`: promise_text only, and if `replying.kind === "human"` the line `A representative has joined this chat.` instead. Identity body: `identityLine`. **Landing:** the block whose key equals `landing?.target` (`visit`/`request`/`identity`) gets class `landed` on its header row wrapper.
5. **`PinnedSafety.tsx`** `{ block; props: Omit<BlockProps<"safety">, "block"> }`: renders `<section aria-label="Danger: safety instruction">` containing `renderBlock({block, ...props})`. No close control. The parent passes `key={block.block_id}`; the component is not memoised away and never re-keys. It sits in `<Main>` above the log, `flex-none`.
6. **`Thread.tsx`** `{ entries; answered; settled; disabled; dispatch; announce; landed; phase; pending; scrollTarget; retry }`: wrapper `div` with `role="log" aria-live="polite" aria-relevant="additions"`, `overflow-y-auto`, `flex-1 min-h-0`, `px-3.5`. Maps entries: `customer` -> `CustomerRow`; `reply` -> `AssistantGroup`; `message` -> `MessageEntry`; `event` -> `EventEntry`; `line` -> `<p class="text-small text-muted">`. The `PendingLine` is rendered **after the entry whose `turnId === pending.turnId`**, outside the `role="log"` subtree (so "replying…" is not announced as an addition; its own `role="status"` announces only the 10 s change). Scrolls: effect on `entries.length`: newest `reply` group -> `scrollIntoView({block:"start"})`, otherwise `{block:"end"}`, instant if `matchMedia("(prefers-reduced-motion: reduce)").matches`; both guarded `el.scrollIntoView?.`. `scrollTarget` effect scrolls that entry and adds a 1.2 s highlight class `landed`.
7. **`CustomerRow.tsx`** `{ entry }`: `MessageRow speaker={{kind:"customer", display_name:"You"}} at={entry.at ?? undefined} layout="bubble"` with the text (`white-space: pre-wrap`, `overflow-wrap: anywhere`). When `delivery === "failed"`: `FailedLine`.
8. **`AssistantGroup.tsx`** `{ entryId; blocks; ...BlockProps stuff }`: for each `ReplyGroup` from `groupBlocks(entryId, withoutPinned(blocks))`: speaker kind `event` -> `EventLine at` wrapping the rendered blocks; otherwise `MessageRow speaker at layout="bubble"` containing, per block: `renderBlock({ block, settled, answered: isAnswered(block, answered), disabled, dispatch, announce, landed })`. `disabled = ended || pending !== null`.
9. **`MessageEntry.tsx`** (`kind:"message"`): `MessageRow` with the speaker (representative: white bubble, indigo disc handled by the shared row), text pre-wrap. **`EventEntry.tsx`** (`kind:"event"`): `EventLine icon at` + line text; icon map: joined `IconUser`, paused `IconInfo`, resumed `IconCheck`, closed `IconInfo`, shift `IconClock`, reset `IconInfo`, staffing `IconInfo`. New lines fade in via `chat.css` (`opacity` only, `--dur-fade`, reduced-motion safe).
10. **`PendingLine.tsx`** `{ phase }`: renders nothing for `"hidden"`/`"gave-up"`; else `<div role="status" class="min-h-[24px] flex items-center gap-2 text-small muted">` `AssistantMark size={18}` + text per phase. Same node for `replying` and `still` (text swaps in place).
11. **`FailedLine.tsx`** `{ message; retryable; onRetry }`: polite line (`<p>` not `role="alert"`) with the message and, if retryable, a secondary `Button density="chat"` "Try again".
12. **`Composer.tsx`** `{ lock: ReturnType<typeof useChat>["composerLock"]; pending: boolean; replying; limits; dispatch; assistantLabel }`: `<form aria-label="Message">` docked (`flex-none`, white, top hairline). Order in DOM: (a) `Button variant="secondary" icon={<IconHeadset/>}` "Talk to a person" (full width on phones, `onClick={() => dispatch({kind:"person"})}`; **never `disabled`** while not ended; when `lock.reason === "ended"` this slot instead holds `Button variant="primary"` "Start a new chat" `onClick={() => dispatch({kind:"newChat"})}`), (b) a visually hidden `<label htmlFor>` + `TextArea` (`min-h-[var(--composer-min-h)]`, `maxLength={limits?.max_message_chars ?? 2000}`, disabled when `lock` is `rate|spend|ended|starting`; keeps its text while disabled), (c) `Button variant="send" aria-label="Send" type="submit"` disabled when the trimmed text is empty or `pending` or locked, (d) hint line `text-small muted` (`lock.hint`). Submit: `dispatch({kind:"text", text})` then clear the field. Enter sends (Shift+Enter = newline) only when `useMediaQuery(LAPTOP)`; on phones Enter inserts a newline. `autoFocus` only when LAPTOP and `lock === null` after first ready; never refocus after a safety card. Rate-limited: field disabled with the sentence in the hint, key enabled.
13. **`StartingGreeting.tsx`** `{ phase: "starting" | "start-failed"; message; onRetry }`: starting -> `Skeleton height={24}` for the first 1 000 ms (timer inside the component), then `<p>Starting the chat…</p>`; start-failed -> `ErrorLine message onRetry`.

**`chat.css`** (imported by `Scr01.tsx`): `@media (prefers-reduced-motion: no-preference)` keyframes: `.landed { position: relative }`, `.landed::after { content:""; position:absolute; inset:0; background: var(--landed-wash); border-bottom: 1px solid var(--landed-edge); pointer-events:none; opacity:0; animation: chat-landed calc(var(--dur-landed-in) + var(--dur-landed-hold) + var(--dur-landed-out)) var(--ease-enter) 1 }` with `@keyframes chat-landed { 0% {opacity:0} 13.3% {opacity:1} 66.7% {opacity:1} 100% {opacity:0} }` (160/1200, 800/1200); and `.chat-fade-in { animation: chat-fade var(--dur-fade) var(--ease-enter) 1 } @keyframes chat-fade { from {opacity:0} to {opacity:1} }`. Outside that media query no animation rules exist. Animate `opacity` only. No hex.

**Check:** component tests (section 7) green; `npm run lint` clean for these files.

### Step 5 · `Scr01.tsx` and layout
```tsx
// default export
export default function Scr01() {
  const chat = useChat();                       // apiGateway
  document.title via useEffect: "SCR-1 · Customer chat · Meridian"
  const { staffing } = useDemoStatus();
  const danger = findPinnedSafety(chat.state.entries) !== null;
  return (
    <AppFrame variant="chat">
      <div data-screen="SCR-1" className="flex flex-col ... h-[100dvh] min-[700px]:h-[calc(100dvh-48px)] max-h-[900px] bg-[var(--app-bg)]">   // verify the 24 px frame in DevTools (Step 11); adjust the calc only
        <ChatHeader .../>                                  // header: R1-R3 + reconnecting line
        <div className="flex flex-1 min-h-0 flex-col min-[900px]:flex-row">
          <SettledAside .../>                              // DOM order: strip before main (focus order: top bar -> demo bar -> strip -> safety -> thread -> composer); on >= 900 px it sits to the right via `min-[900px]:order-2`
          <Main className="flex flex-1 min-h-0 flex-col min-[900px]:order-1">
            {pinned && <PinnedSafety key={pinned.block_id} .../>}
            {phase starting/failed ? <StartingGreeting/> : <Thread/>}
            <Composer/>
          </Main>
        </div>
        <LiveRegion politeness="polite">{chat.landingText}</LiveRegion>     // separate region for panel landings
      </div>
    </AppFrame>
  );
}
```
`Main` must accept `className` (FND: `Main({children, id?})`; if it does not, wrap its children in your own `div` with the classes and put `Main` outside). `index.ts` stays `export { default } from "./Scr01";`. Import `./core/chat.css`.
**Check:** `npx vitest run src/screens/scr01` green; `npm run typecheck`.

### Step 6 · Customer row text and card answered rules (inside `useChat`, pure helper `core/rowText.ts`)
`customerRowText(action, entries): string`: `text` -> the trimmed text; `choice` -> `optionLabel(entries, cardId, option) ?? "Choice sent"`; `code` -> `"Code entered"`; `form` -> `"Details sent"`; `person` -> `"Talk to a person"`. Add `rowText.test.ts`.

### Step 7 · Dev layer: stream scripts (`src/dev/stream/chat-scripts.ts`)
Export `chatScripts: Record<string, StreamScript>` with these keys. Each event is typed `ChatEvent` (`satisfies`) and the file starts with a comment block naming the OpenAPI source of each literal. `event_id` values 40+ ascending per script; `at` values near `2026-10-16T14:22:00-05:00`. Values:
- `rep-joins`: `representative_joined` (copy FRAMES line: `speaker {kind:"representative", display_name:"Riley"}`, `display_name "Riley"`, `line "Riley (demo representative) has joined."`) at 1500 ms; `ai_paused` (`speaker {kind:"event", display_name:null}`, `line "The assistant is paused while Riley is here."`) at 1600 ms; `staff_message` (`message_id "m-88"`, `text "Hi Omar, I can look at the after-hours charge with you."`) at 4000 ms. (All three copied from `FRAMES`, line 2501.)
- `rep-hands-back`: `rep-joins` steps then `ai_resumed` at 8000 ms (`line "Riley handed the chat back to the automated assistant."`, from SCREEN_SPECS copy notes; `// dev fixture: no named example`).
- `rep-closes`: `rep-joins` steps then `chat_closed` at 8000 ms (`line "Riley closed this chat."`, `composer_disabled: true`; dev fixture).
- `shift-ends`: one `shift_ended` at 4000 ms: `line "The simulated shift ended before a representative joined."`, `handoff` = the `handoff` block copied from the `submitTurn` example `HANDOFF` (nobody online; same reference MHC-C-0007), `settled` = the `settled` object of that same example. Comment: copied from `submitTurn` example `HANDOFF`.
- `staffing-on`: `staffing_changed` at 2000 ms: `staffing` = the `getStaffing` example `ON` value (`mode simulated_on_shift`, its `label`, its `banner`), `line "Staffing changed: simulated staff on shift (demo)."` (SCREEN_SPECS flow row).
- `staffing-off`: `staffing_changed` at 2000 ms: `getStaffing` example `OFF` value, `line "Staffing changed: nobody online."` (dev fixture: the spec gives only the "on" wording).
- `clock-moves`: `clock_changed` at 2000 ms with `demo_clock` = the `getDemoClock` example `ADVANCED` value.
- `demo-reset`: `demo_reset` at 2500 ms, `line "The demo was reset, so this chat has ended. Nothing from it was kept."`.
- `drop-and-late`: `{ dropAfterMs: 1500, steps: [ { afterMs: 6000, event: staff_message ("m-89", "Are you still there?" dev fixture) } ] }` (connection drops, message buffered; Stream tab "Reconnect" replays it).
Test `chat-scripts.test.ts`: every script has steps sorted by `afterMs`; every `event.type` is one of the nine; every event has `event_id`, `at`, `speaker`; `shift-ends` handoff block has `type "handoff"` and `reference "MHC-C-0007"`.

### Step 8 · Dev layer: reactions and directors
**`reactions/scr01-core.ts`** `export const reactions: Reaction[]`:
1. `{ when:{op:"resetDemo", status:200}, then(ctx){ ctx.setForce("getChatThread", {example:"SESSION_ENDED", status:410}); } }` (after a reset the stored thread reads as ended, as the real backend does).
2. `{ when:{op:"startChatSession", status:201}, then(ctx){ ctx.setForce("getChatThread", null); } }` (a new chat clears that force).
**`directors/chat-core.ts`** `export const rules: DirectorRule[]` (order matters, first non-undefined wins; only a `text` payload is examined; read `req.payload.kind`):
1. `/\b(gas|carbon monoxide|co alarm|smell(s)? gas)\b/i` -> `"SAFETY"`.
2. `/^\s*test:\s*rate limit/i` -> `"RATE_LIMITED"`; `/^\s*test:\s*booking cap/i` -> `"BOOKING_CAP"`; `/^\s*test:\s*spend cap/i` -> `"SPEND_CAP_REACHED"`; `/^\s*test:\s*timeout/i` -> `"TURN_TIMEOUT"`; `/^\s*test:\s*busy/i` -> `"BUSY"`; `/^\s*test:\s*paused/i` -> `"AI_PAUSED"`. (Documented in the group doc as the reviewer's way to trigger server-side conditions in free play; dev layer only.)
Everything else returns `undefined` (FND defaults to `ANSWER_WITH_SOURCE`). Test `chat-core.test.ts`: each pattern -> example; a plain "hello" -> `undefined`; a `choice` payload -> `undefined`; every returned name exists in `OPS.submitTurn.responses` examples.

### Step 9 · Dev layer: scenarios (`scenarios/scr01-core.ts`)
`export const screenScenarios: ScreenScenarios = { complete: true, scenarios: [...] }`. **Set `complete: true` only in the last commit of this step, after `scr01-core.test.ts` and FND's `scenarios.coverage.test.ts` pass.** Scenario list = section 6.2 (copy the table into code field by field). Every scenario: `screen: "SCR-1"`, `route: "/"`, `role: "customer"` (omit; it is the default), `ops` keys are `OperationId`s, `example` names exist in `OPS`. ID rule: `scr01.<kebab>` exactly as listed (if `scenarios.integrity.test.ts` requires the file slug `scr01-core` as prefix, use `scr01-core.<kebab>` for all and say so in the group doc). `scr01-core.test.ts`: (a) ids unique and exactly the section 6.2 list; (b) every one of the eight `StandardState`s appears at least once; (c) every `flowState` string equals a first-column text from the SCREEN_SPECS SCR-1 flow-state table (copy the allowed list into the test); (d) every `stream` is one of `Object.values(chatScripts)`.

### Step 10 · Integration test and e2e-style check
`Scr01.test.tsx` (RTL, `renderWithProviders({route:"/"})` with a fake `ChatGateway` injected through a test-only prop? **No:** `Scr01` takes no props. Use `vi.mock("./core/gateway", ...)` to replace `apiGateway` with the fake, and `vi.mock("@/api/useEventStream")` to drive events from the test). Cases in section 7.

### Step 11 · Visual and responsive check (Chrome DevTools MCP; no screenshots committed)
Start Prism (`npm run mock`) and `npm run dev:mock` in the background; remember PIDs. Open `http://127.0.0.1:5184/?signedin=1&role=customer`. At 390 x 844 and 1280 x 800, light and dark: header stack (top bar, demo bar, role row 44 px, strip 44 px collapsed), strip opens (max 52 vh), panel at >= 900 px, composer docked with the "Talk to a person" tile above the field, no horizontal scroll, focus ring visible on every control, tab order = skip link, role switch, Demo guide, strip, thread, "Talk to a person", field, Send. Walk the scenarios in section 6.2 with the panel (States tab) and record in the group doc which you saw (one line each). Fix the root height calc here. Stop both servers.

### Step 12 · Group doc `docs/ux/04-prototype/groups/g1-chat-core.md`
Sections in order: **What G1 built** (files) · **State coverage** (section 6.1 table with the result you observed) · **Contract use** (ops, what each `settled` field drives) · **Fakes and transforms** (reactions, directors, `test:` phrases, shortened-limits scenarios, `RATE_HOLD_MS`) · **Proposal strings `[P]`** (section 4.6) · **Decisions made by this plan** (D1-D7 in 8.4) · **Requests to the integrator / contract owners** (8.1-8.3 items G1 still needs) · **Deviations** (no back button; visually hidden composer label; no `<time>` for visit window) · **Checks** (commands and results from section 7).

## 6. Data, fixtures and the state switcher

Synthetic only: every value comes from OpenAPI named examples (Omar Patel, MHC-C-0007/0009, thread `thr_9d41`, demo clock `2026-10-16T14:20:00-05:00`, technician Jun Park, Riley). Test fixtures are built from them in `core/testFixtures.ts`, each with a comment naming the example. No invented names, counts or times.

### 6.1 Every spec'd SCR-1 state and how it is reached

"A" = apply the scenario in the panel (States tab). "S" = then send any message (type text, Send). "R" = resume-class: open the chat once first (so the tab has a stored thread), apply the scenario (the panel calls `refetchAll`, which resyncs the thread through `getChatThread`) or reload; the forced `getChatThread` result then shows. Standard states first.

| State / flow state (SCREEN_SPECS) | Scenario id | How it is reached |
|---|---|---|
| default | `scr01.default` | A; page loads: greeting "Meridian assistant · automated", demo bar "Fri Oct 16, 2026 (demo date) · Nobody online", strip "What's settled · Nothing yet" |
| default (resumed thread) | `scr01.default-resumed` | R with `getChatThread: OPEN` |
| empty | `scr01.empty` | A: greeting is the empty state; panel blocks read "Nothing booked yet." / "No request open." / "Not checked. Only needed for private details." |
| loading: session start | `scr01.loading-starting` | A then reload (stored thread cleared by the scenario note: use the panel "Restart"): `startChatSession` `STARTED` with `delayMs: 4000` shows skeleton <= 1 s then "Starting the chat…" |
| loading: turn pending (300 ms, 10 s) | `scr01.loading-replying` | A, S: `submitTurn` `ANSWER_WITH_SOURCE` with `delayMs: 12000` |
| loading: 60 s timeout card | `scr01.loading-timeout` | A, S: `submitTurn` `TURN_TIMEOUT` (G2 renders the notice; G1 shows Try again via the card's `retry`) |
| loading: busy | `scr01.loading-busy` | A, S: `submitTurn` `BUSY` |
| partial: part answered | `scr01.partial-part-answered` | A, S twice: sequence `ANSWER_WITH_SOURCE` then `NO_INFO` |
| partial: handoff, follow-up unsaved | `scr01.partial-handoff-unsaved` | A, S: `submitTurn` `HANDOFF`; chooser open (G2); `saveFollowUp` `PHONE_MORNINGS` |
| No current source | `scr01.flow-no-info` | A, S: `NO_INFO` |
| error: send failed | `scr01.error-send-failed` | A, S: sequence `{fail:"network"}` then `ANSWER_WITH_SOURCE`; Try again succeeds with the same `turn_id` |
| error: browser gives up (65 s) | `scr01.error-giveup-fast` | A, S: `submitTurn` `{hang:true}` and `startChatSession` `STARTED` with a `transform` that sets `limits.browser_give_up_after_ms` to 5000 and `still_working_after_ms` to 2000 (note: "demo: shortened from 65 s / 10 s so the state is reachable") then reload/Restart |
| error: session gone | `scr01.error-session-gone` | A, S: `submitTurn` `SESSION_NOT_FOUND` status 404 |
| error: start failed (demo resetting) | `scr01.error-start-reset` | A then Restart: `startChatSession` `RESET_IN_PROGRESS` status 503 |
| error: start failed (offline) | `scr01.error-start-offline` | A then Restart: `startChatSession` `{fail:"network"}` |
| Limit reached (rate) | `scr01.flow-limit-rate` | A, S: `RATE_LIMITED`; field disabled with the sentence, person key enabled |
| Limit reached (booking cap) | `scr01.flow-limit-booking` | A, S: `BOOKING_CAP`; field stays enabled |
| Spend cap reached | `scr01.flow-spend-cap` | A, S: `SPEND_CAP_REACHED`; field disabled |
| Session ended while the chat is open | `scr01.flow-session-ended` | A, S: `submitTurn` `UNAUTHENTICATED_EXPIRED` status 401 -> SCR-12 (FND), back to `/` resumes the stored thread |
| stale: live updates lost | `scr01.stale-reconnecting` | A: stream `drop-and-late`; line "Reconnecting…"; Stream tab "Reconnect" replays and clears it |
| Simulation switched on while open | `scr01.stale-staffing-on` | A: stream `staffing-on`; demo bar, banner and event line update without reload |
| Simulation switched off while open | `scr01.stale-staffing-off` | A with `staffing: "simulated_on_shift"`: stream `staffing-off` |
| Demo date moves | `scr01.stale-clock-moves` | A: stream `clock-moves` |
| success: booked | `scr01.success-booked` | A, S: `BOOKED`; *Your visit* lands |
| success: handoff, nobody online | `scr01.success-handoff` | A, tap "Talk to a person": `requestPerson` `CASE_CREATED`; *Your request* lands |
| second tap while a case is open | `scr01.success-person-again` | A, tap twice: `requestPerson` sequence `CASE_CREATED`, `ALREADY_OPEN`; no second row, scroll + highlight |
| success: follow-up saved | `scr01.success-followup-saved` | A, S (`HANDOFF`), choose + save in the chooser: `saveFollowUp` `PHONE_MORNINGS`; announcement "Follow-up saved: phone call, the number ending in 02, mornings." |
| Verified | `scr01.success-verified` | A, S: `VERIFIED_ACCOUNT_INVOICE`; Identity block shows the status the example's `settled.identity` carries |
| Fee-bearing change request | `scr01.success-change-request` | A, S: `CHANGE_REQUEST`; *Your visit* keeps the original with "Original stays until a representative confirms." |
| Live-queued | `scr01.success-live-queued` | A (`staffing: simulated_on_shift`), tap "Talk to a person": `requestPerson` `LIVE_QUEUED`; banner visible |
| Representative joined, AI paused | `scr01.success-rep-joined` | A (`staffing: simulated_on_shift`): stream `rep-joins`; top bar "Riley (demo representative). Assistant paused.", placeholder "Message Riley" |
| Handed back | `scr01.success-handed-back` | A (`staffing: simulated_on_shift`): stream `rep-hands-back` |
| Shift ended before a claim | `scr01.success-shift-ended` | A (`staffing: simulated_on_shift`), tap "Talk to a person" (`LIVE_QUEUED`), stream `shift-ends` |
| Safety takeover | `scr01.flow-safety-takeover` | A, S: `SAFETY`; card pinned, strip "DANGER · Leave the home immediately", panel header only |
| Safety mid-booking | `scr01.flow-safety-midbooking` | A, S twice: sequence `SLOT_CARD` then `SAFETY`; the slot card stays in the thread below |
| Burning smell, risk unclear (conditional card stays inline, not pinned) | `scr01.flow-conditional-safety` | A, S: `CONDITIONAL_SAFETY` |
| disabled: send empty | `scr01.disabled-empty-field` | A: Send disabled until text is typed |
| disabled: reply pending | `scr01.disabled-pending` | A, S: `submitTurn` `ANSWER_WITH_SOURCE` `delayMs: 12000`; Send disabled, field editable, person key enabled |
| disabled: chat closed by Riley | `scr01.disabled-chat-closed` | A (`staffing: simulated_on_shift`): stream `rep-closes`; "This chat has ended." + "Start a new chat" |
| Reset during a live chat | `scr01.flow-reset-live-chat` | A: stream `demo-reset` |
| disabled/ended: thread ended on resume | `scr01.disabled-ended-on-resume` | R with `getChatThread` `SESSION_ENDED` status 410 |

**Owned by G2 (listed so the integrator sees full SCR-1 coverage; not in this file):** burning-smell question, emergency-line, quick checks, urgency questions, where card, slot card (incl. day tabs, members), locate card, code sent/wrong/expired/locked/cap, NOT_VERIFIED, account answers, dispute/unsupported, slot taken, out of area, no window fits, confirm existing visit, fee-free move/cancel, fee-bearing cancel, refund handoff, failure signal, limit/notice *rendering*. G1's limit scenarios above exist because composer locking is G1's. G2 must not reuse G1's ids (the table above is the reserved set).

### 6.2 `scr01-core.ts` scenario spec (state | flowState | forces)

State and flowState values to put in code (flowState only where the SCREEN_SPECS flow-table first-column text exists; copy it exactly):
`scr01.default` default | `scr01.default-resumed` default | `scr01.empty` empty | `scr01.loading-starting` loading | `scr01.loading-replying` loading | `scr01.loading-timeout` loading | `scr01.loading-busy` loading | `scr01.partial-part-answered` partial | `scr01.partial-handoff-unsaved` partial | `scr01.flow-no-info` partial, flowState `No current source` | `scr01.error-send-failed` error | `scr01.error-giveup-fast` error | `scr01.error-session-gone` error | `scr01.error-start-reset` error | `scr01.error-start-offline` error | `scr01.flow-limit-rate` error, flowState `Limit reached (rate, booking cap)` | `scr01.flow-limit-booking` error, same flowState | `scr01.flow-spend-cap` error, flowState `Spend cap reached` | `scr01.flow-session-ended` error, flowState `Session ended while the chat is open` | `scr01.stale-reconnecting` stale | `scr01.stale-staffing-on` stale, flowState `Simulation switched on or off while open` | `scr01.stale-staffing-off` stale, same flowState | `scr01.stale-clock-moves` stale | `scr01.success-booked` success, flowState `Booked` | `scr01.success-handoff` success, flowState `Handoff, nobody online` | `scr01.success-person-again` success | `scr01.success-followup-saved` success | `scr01.success-verified` success, flowState `Verified` | `scr01.success-change-request` success, flowState `Fee-bearing change request` | `scr01.success-live-queued` success, flowState `Live-queued (simulated staff on shift)` | `scr01.success-rep-joined` success, flowState `Representative joined, AI paused` | `scr01.success-handed-back` success, flowState `Handed back` | `scr01.success-shift-ended` success, flowState `Shift ended before a claim` | `scr01.flow-safety-takeover` success, flowState `Safety takeover` | `scr01.flow-safety-midbooking` success, flowState `Safety takeover` | `scr01.flow-conditional-safety` success, flowState `Burning smell, risk unclear` | `scr01.disabled-empty-field` disabled | `scr01.disabled-pending` disabled | `scr01.disabled-chat-closed` disabled, flowState `Chat closed by Riley` | `scr01.flow-reset-live-chat` disabled, flowState `Reset during a live chat` | `scr01.disabled-ended-on-resume` disabled.
`staffing: "simulated_on_shift"` on: `stale-staffing-off`, `success-live-queued`, `success-rep-joined`, `success-handed-back`, `success-shift-ended`, `disabled-chat-closed`.
Streams: `stale-reconnecting` -> `chatScripts["drop-and-late"]`; `stale-staffing-on` -> `staffing-on`; `stale-staffing-off` -> `staffing-off`; `stale-clock-moves` -> `clock-moves`; `success-rep-joined` -> `rep-joins`; `success-handed-back` -> `rep-hands-back`; `success-shift-ended` -> `shift-ends`; `disabled-chat-closed` -> `rep-closes`; `flow-reset-live-chat` -> `demo-reset`.
`notes` text on every scenario states the A / S / R recipe from 6.1 in one sentence.

## 7. Checks

All from `/home/linuxuser/workspaces/inno-aea-callcenter/apps/web`. Affected tests only (rule `build-loop-test-scope`); this slice adds files and a stylesheet but changes no shared module, config, lockfile or fixture, so **no full-suite run**.

### 7.1 Tests the implementer writes with the code (file -> cases that must exist)

- `core/reducer.test.ts`: START_OK greeting entry + settled; SEND_BEGIN/TURN_OK marks sent and appends reply once (idempotent id); TURN_FAIL then RETRY_BEGIN reuses `turnId`; late TURN_OK after failure still applies; settled replaced not merged (visit disappears if server sends null); PERSON_OK `already_open` adds no entries; every EVENT type (joined sets human, resumed sets ai, closed ends, demo_reset ends, shift_ended appends handoff + settled, staff_message adds message, clock/staffing add no/one entry as specified); duplicate event key ignored; RESYNC keeps failed/pending customer entries; `session_ended` block ends the chat.
- `core/replyGroups.test.ts`: `groupBlocks` by speaker; `findPinnedSafety` first safety only and `conditional_safety` not pinned; `withoutPinned`; `isAnswered`; `optionLabel` found / not found; `turnsToEntries` for the `OPEN` thread (customer turn + assistant locate_prompt turn).
- `core/pending.test.ts`: 0 / 299 -> hidden, 300 -> replying, 9 999 -> replying, 10 000 -> still, 64 999 -> still, 65 000 -> gave-up.
- `core/usePendingPhase.test.tsx`: fake timers drive the phases; null pending -> hidden; unmount clears timers.
- `core/visit.test.ts`: `hhmmTo12h` ("00:00", "08:00", "12:00", "12:30", "16:00"); `formatWindow("08:00-12:00","x") === "8:00 am – 12:00 pm"`; `formatDateOnlyShort("2026-10-21") === "Wed Oct 21"` (guards the UTC-shift bug); `visitSentence("2026-10-21","08:00-12:00","") === "Wednesday, October 21, 8:00 am to 12:00 pm"`; no output matches `/ |[AP]M/`.
- `core/settledSummary.test.ts`: strip examples (nothing, visit only, request only with and without `due_at`, both, danger); `promiseSentence` with `due_label` "by Monday, October 19, 7:00 pm", with `""` and `null`; `followUpLabel` phone/morning, email; `identityLine` all five statuses; `landingsFromWrites` (booked -> visit; change_request_sent -> visit + request; verified -> identity; duplicates collapse).
- `core/errors.test.ts`: every row of the table in Step 1.
- `core/rowText.test.ts`: the five rules.
- `core/useChat.test.tsx` (fake gateway, mocked `useEventStream`, fake timers): start path stores the thread and sets greeting; resume path calls `resume` not `start`; 404 on resume clears storage then starts; 410 -> ended; send text -> SEND_BEGIN immediately then reply; Try again re-sends the **same** `turn_id`; 409 TURN_IN_PROGRESS retries after `retry_after_ms` with the same id; give-up at `browser_give_up_after_ms` marks failed; RATE_LIMITED notice locks the field then releases after `RATE_HOLD_MS`; SPEND_CAP locks; BOOKING_CAP does not; `dispatch` never rejects (gateway throws -> resolves); person `case_created` adds 2 entries; second `already_open` adds none and sets `scrollTarget`; follow-up success replaces settled and announces `saved_line`; follow-up 409 adds the quiet line; writes -> landings in order; `newChat` clears storage and starts; refetchAll resyncs; stream events: staffing_changed calls `setFromChat`.
- `core/components/*.test.tsx`: `TopBar.test.tsx` (3 variants, link), `SettledAside.test.tsx` (strip vs panel by mocked `matchMedia`; all panel blocks empty and filled; danger shows header only and the danger line; Replying only with staffing on; "Original stays…" line; `landed` class applied then removed after 1200 ms), `Composer.test.tsx` (Send disabled when empty/pending; Talk to a person enabled in every non-ended state incl. rate/spend lock and pending; ended swaps in "Start a new chat"; Enter behaviour by mocked `LAPTOP`; maxLength from limits; tab order), `Thread.test.tsx` (mock `../../blocks` `renderBlock`: props passed are exactly `block, settled, answered, disabled, dispatch, announce, landed`; safety is **not** in the log and the pinned node is the same DOM node after two more turns; pending line sits after the pending customer row and not inside `role="log"`; failed line shows text + Try again; event line has hidden "System event" prefix via `EventLine`; `expectNo24HourTimes`), `PendingLine.test.tsx`, `FailedLine.test.tsx`, `StartingGreeting.test.tsx` (skeleton then text at 1 000 ms).
- `Scr01.test.tsx`: renders header landmarks (`banner`, `complementary` named "What's settled", `main`, a `form`), exactly one `h1` "Meridian Home Comfort", radiogroup "Acting as" present while starting / ended / start-failed; `data-screen="SCR-1"`; reconnecting line appears when the mocked stream status is `reconnecting`; staffing_changed event shows the banner; unsafe-copy sweep: rendered text never contains `charged`, `shortly`, `queue position`.
- `dev/scenarios/scr01-core.test.ts`, `dev/directors/chat-core.test.ts`, `dev/stream/chat-scripts.test.ts` as in Steps 7-9.

### 7.2 Commands

While iterating (one file at a time):
```
npx vitest run src/screens/scr01/core
npx vitest run src/dev/scenarios/scr01-core.test.ts src/dev/directors/chat-core.test.ts src/dev/stream/chat-scripts.test.ts
```
Once before reporting, in this order, stopping at the first red:
1. `npm run lint`: 0 errors, no new warnings.
2. `npm run typecheck`: exit 0.
3. Affected tests: `npx vitest run src/screens/scr01 src/dev src/styles src/routes.test.ts`. `src/dev` includes FND's `scenarios.integrity.test.ts` and `scenarios.coverage.test.ts` (must pass with `complete: true`); `src/styles` includes `guard.test.ts` (must pass with the new files: no hex, no safety tokens, no `Prefer`/`mhc_session=`/`document.cookie` outside `src/dev`).
4. `npx vitest run src/screens/stubs.test.tsx`: **expected to fail only for the SCR-1 case** (the stub's `h1` "SCR-1 …" is gone, section 8.2). Do not edit that file. Report the failure text. All other cases must pass.
5. `npm run build && npm run check:dist`: the dev scenario/stream/reaction files must not leak into `dist` (`check:dist` passes).
6. Step 11 browser check (not a command): list scenarios walked.
Existing tests that must stay green: everything in `apps/web` except the one `stubs.test.tsx` SCR-1 case above; the Python suite is untouched and not run. No formatter gate exists.

## 8. Risks and requests

### 8.1 Collisions and cross-group assumptions (orchestrator: check against G2's plan)

1. **G1/G2 seam is `contract.ts` + `blocks.ts` only.** G1 passes `BlockProps`; G2 renders. Assumptions G1 makes about G2: (a) the `safety` renderer includes the block's `contact_line` quiet line under the card and uses `role="alert"` on first render; G1 mounts it once, keyed by `block_id`, in the pinned region; (b) `conditional_safety` renders inline in the thread (not pinned): decision D1; (c) the `notice`, `error`, `session_ended` renderers call `dispatch({kind:"retry", turnId})`, `dispatch({kind:"person"})` and `dispatch({kind:"newChat"})` as needed; `retry` for a `TURN_TIMEOUT` notice uses `block`/`notice.retry_turn_id`; **G1 only retries turn ids it created (the failed customer row).** For a server `TURN_TIMEOUT`, G1 treats `retry_turn_id` the same: `retry` finds the customer entry with that `turnId` (the timed-out turn's own entry, which is `sent` not `failed`): so in `dispatch({kind:"retry"})` G1 accepts any customer entry by `turnId` regardless of `delivery`. (d) `dispatch` never rejects (4.4). **If G2's plan assumes a rejection or a different retry contract, resolve before implementing.**
2. **Scenario ids / coverage.** Both G1 (`scr01-core.ts`) and G2 (`scr01-cards.ts`) target SCR-1 and each will set `complete: true`. G1's file alone covers all eight standard states (6.2), so the per-file coverage rule holds; G2 only needs unique ids (G1's set in 6.1 is reserved). Integrator: confirm the integrity test's prefix rule (Step 0 item b).
3. **Directors:** FND's `pickTurnExample` returns "the first rule's answer" across `chat-core` then `chat-cards`. G1's rules are narrow (gas words, `test:` phrases). G2 should avoid `test:` and gas words.
4. **`Settled.visit` has no ISO timestamps** (only `date` and `"HH:MM-HH:MM"`). G1 formats those strings directly (`visit.ts`) and cannot render a `<time datetime>` for the visit window (design 11 asks for one). **Request to contract owners:** add `starts_at` / `ends_at` ISO fields to `SettledVisit`.
5. **`ChatThread` carries no greeting and no `limits`.** On resume the greeting is missing from `turns` (the `OPEN` example starts with the customer's turn) and G1 takes limits from storage. **Request:** include the greeting turn in `turns` or return it; and `limits` in `ChatThread`.
6. **Dev-mock inconsistency (handled):** `getChatThread` examples always show `nobody_online`; G1 therefore calls `refresh()` (reads `getStaffing`) after a resume instead of trusting the thread's staffing.
7. **`due_label` and `extra_lines`** appear as `""` / `[]` in the staffed examples (not `null`): G1 treats empty string like null (`promiseSentence`).

### 8.2 Existing foundation tests that conflict with a real SCR-1

`src/screens/stubs.test.tsx` asserts every route renders one `h1` containing its id (`SCR-1`), and `tests/e2e/smoke.spec.ts` expects an `h1` starting `SCR-1`. G1's `h1` is "Meridian Home Comfort" (the brand is the correct accessible page heading). **Request to the integrator (foundation owner):** change those two checks for replaced screens to assert `document.title` (G1 sets `SCR-1 · Customer chat · Meridian`) or `[data-screen="SCR-1"]` (G1 sets it on its root). G1 does not edit either file.

### 8.3 Shared-primitive requests (to the integrator, never added by G1)

- A `Main` that accepts `className` (if the built one does not) and an `AppFrame variant="chat"` content area with `min-height: 0` flex behaviour so the thread can scroll internally. Fallback in the plan: wrap in own `div`.
- `useScrollToLatest` is NOT requested; the scroll effect lives in `Thread.tsx` (FND 8.3 allows G1 to ask; one use only, so no abstraction yet).
- A `Scenario.storage` seed (sessionStorage key/values applied before navigation) would remove the "R" recipe for resume-class scenarios; not required.

### 8.4 Decisions made by this plan (no product input needed; record in the group doc)

- **D1** Only `safety` (DANGER) is pinned; `conditional_safety` stays inline (the `pinned` field exists only on `safety`; SCREEN_SPECS R5 says "safety card").
- **D2** The back button of design 8.1 is omitted (nothing to go back to); the second top-bar line is "Meridian assistant · automated" (SCREEN_SPECS R1 wins over design 8.1's "Automated assistant").
- **D3** Role row is always its own 44 px row under the demo bar, at every width.
- **D4** On an ended chat the "Talk to a person" slot is replaced by the primary "Start a new chat" (a person cannot be requested on a closed thread; 410).
- **D5** `RATE_LIMITED` locks the field for `RATE_HOLD_MS = 60_000` `[A]` then releases; `SPEND_CAP_REACHED` locks for the rest of the chat; `BOOKING_CAP` never locks.
- **D6** Customer rows for `code`/`form` use fixed words, never the values (data classes D2/D3).
- **D7** Thread id and limits persist in `sessionStorage["mhc.chat.thread"]` (per tab, N-31); a role switch away and back resumes the same chat.

### 8.5 Spec gaps (recorded; none blocks)

`ChatThread` event lines are not stored (history shows no joined/closed lines on resume); the customer row shows no time until the reply arrives (the browser has no demo clock tick); the stripped `Settled.actions` summaries are server text and shown as given.

## 9. Readiness

**READY**, once the foundation slice has finished (BLOCKED-ON FND only if Step 0 item 1 fails). No `NEEDS-DECISION`: every choice that the specs leave open is decided in 8.4 and is a copy/behaviour constant, changeable in one place. Report back with: the section 7.2 outputs, the Step 11 scenario walk-through, the list of `[P]` strings, and any place you deviated from this plan and why.

## Deviations

Recorded by the G1 implementer, 2026-10-21.

1. **Scenario ids are `scr01-core.<kebab>`**, not `scr01.<kebab>`: `scenarios.integrity.test.ts` requires the file slug as prefix.
2. **Director rules: no gas rule.** G2's keyword rule 9 already maps gas / carbon monoxide to `SAFETY` (G1-e), so `chat-core.ts` keeps only the `test:` phrases.
3. **Landings and announcements for visit and request are G2's** (G1-b): `useChat` lands and announces only the `verified` write (Identity) and the `already_open` person tap, which renders no block. `landingsFromWrites` stays in `settledSummary.ts` (tested) but `useChat` filters it to `identity`. The staggered multi-landing queue (1.2 s apart) is therefore not built; there is at most one G1 landing at a time. Follow-up saved: G1 only replaces `settled` (G2 announces).
4. **History is quiet** (G1-b): reply entries carry `live: false` when rebuilt from `getChatThread` or the greeting, and `AssistantGroup` hands their cards no-op `announce` and `landed`.
5. **Layout by `blockLayout`** (G1-c), imported directly from `../cards`: bubble blocks share the grey turn, card blocks render bare under one speaker line, event blocks sit in an `EventLine`. `MessageRow` is not used for assistant replies (it always wraps its children in a bubble).
6. **`retry` with `turnId: ""`** (G1-a) resolves to the latest customer turn that is not a person request. `retry` accepts any customer entry by id, sent or failed. Each retry bumps `attempt` on the entry, so every attempt's reply gets its own entry id (`<turn>:reply:<n>`); the reducer is otherwise idempotent per id.
7. **`RESUME_GONE` action added** to the reducer: a 410 on resume shows an ended chat (composer disabled, "Start a new chat"); only a 404 clears storage and starts a new chat (the plan text for Step 3.1 and its test list disagreed).
8. **`PinnedSafety` is a plain `div`**, not a named `section`: G2's safety card already renders `<section aria-label="Danger: safety instruction" role="alert">`, and a second landmark of the same name would be a duplicate. Marker: `data-pinned-safety`.
9. **Form `aria-label`** is "Send a message" (not "Message", which is the field's own label).
10. **Role row on phones**: at 390 px the four roles plus Sign out did not fit one 44 px row, so `ChatHeader` tightens the (read-only) shared `RoleSwitch` radios below 700 px with arbitrary child selectors on its wrapper (`px-1`, 13 px text, `gap-1`). Verified at 390 px: all four roles and Sign out visible.
11. **Pending line** sits directly under the log, not after the pending customer entry (it is outside `role="log"` either way). It is the last thing in the thread except when a timed-out turn older than the last one is retried.
12. **Tests**: `PendingLine`, `FailedLine`, `StartingGreeting` and `EventEntry` share `core/components/small.test.tsx`; `usePendingPhase.test.tsx` is its own file; an extra `dev/reactions/scr01-core.test.ts` covers the two reactions.
13. **`customer` rows rebuilt from history** whose turn has no text show "Choice sent".
