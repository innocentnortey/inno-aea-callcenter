# UX-4 prototype · slice G4 (staff queue SCR-5 and case view SCR-6)

> **Planner:** `fanout-planner` · **Date:** 2026-10-21 · **Project:** `/home/linuxuser/workspaces/inno-aea-callcenter` · **Direction:** A5 Service desk, light first · **Implementer:** `fanout-implementer` (Sonnet) · **Builds on:** `docs/plans/fanout/2026-10-21-ux4/foundation.md` (cited below as **F§n**) · **Readiness:** READY once the foundation slice has finished, plus the integrator requests in §8 (FR-1 is needed for Steps 13–16 only; Steps 1–12 do not depend on it).
> **Lane / loop:** `lane::build-loop`, not `risk::security` (prototype on a mock). Loop: plan, implement code and its tests together, affected tests, code review. No test-writer, no frozen tests, no security agent. **No WP-N worked pair:** this slice changes no model behaviour.
> **No git here:** the folder is not a git repository. Do not run `git init`, commit or push.

## 1. Goal and sources

**Deliver, in `apps/web/src/screens/scr05/` and `scr06/`, plus G4's dev-layer files:**

1. **SCR-5 Representative queue** at `/staff/queue`: console header, "Waiting in chat" live rows (only while simulated staff are on shift), "Needs my action" rows, keyboard hint, every state of the SCREEN_SPECS SCR-5 table (default, empty, loading, partial, error, stale "N cases changed. Show them.", success, disabled) and its flow states.
2. **SCR-6 Case view** at `/staff/cases/:reference`: three-column layout (queue rail, brief, evidence), case header with the split button, lifecycle line, promise card, eight-heading brief with source chips and the "Customer says · not checked" claims card, evidence column with Sources and Conversation tabs, the live box, action area (call/email log, flag, release, wait, resolve, close, supervisor assign / priority), activity log, version conflicts, the CON-21 case stream, and every state and flow state of the SCR-6 card.
3. **Dev layer for G4** so each state can be forced from the state switcher and the write-then-read flows (claim, wait, resolve, release, join, send) behave consistently: scenarios, reactions, scripted case streams, and a request-aware "case director" with a small in-memory case store.
4. `docs/ux/04-prototype/groups/g4-staff-queue-case.md` (the group's record).

**Sources (read in full by the planner; cite when in doubt):**

| Source | Sections used |
|---|---|
| `docs/ux/03-structure/SCREEN_SPECS.md` | SCR-5 (lines 271–302), SCR-6 (304–373), "Copy rules that apply on every screen" (19–31), state matrix (602–621), N-3, N-16 … N-20, N-22 |
| `docs/ux/03-structure/IA.md` | SCR-5 (127), SCR-6 (139–160), layout breakpoints, cross-screen links |
| `docs/ux/03-structure/UI_CONTRACTS.md` | CON-11 (304), CON-12 (319), CON-13 (334), CON-14 (349), CON-15 (364), CON-16 (379), CON-21 (461), error table (≈100–110), state coverage (504–505) |
| `docs/ux/03-structure/ui-contracts.openapi.yaml` | `getQueue` (l. 3292), `getCase` (3546), `applyCaseAction` (5473), `liveChatAction` (5763), `streamCaseEvents` (5925), `recordContactActivity` (5993), `createFlag` (6155); `components.responses.CaseNotFound` |
| `docs/design/design.md` | §8.8 console/queue/priority tags, §8.9 case header/state line/promise/eight headings, §8.10 sources, §8.11 action area and live box, §9.2 console responsive, §10 copy tone, §4.5 colour rules |
| `docs/artifacts/2026-10-21-direction-A5-service-desk.html` | reference look only (`.qrow`, `.split`, `.srcchip`, `.acard`); `design.md` wins on any difference |
| Foundation plan F§2.4, F§4.4–4.9, F§5 Steps 6–10, F§8.2–8.3 | frozen interfaces, group split, dev layer, change-request procedure |

## 2. Boundary

All paths relative to `/home/linuxuser/workspaces/inno-aea-callcenter/`.

### 2.1 Owned files (the implementer may create or edit only these)

```
apps/web/src/screens/scr05/
  index.ts                     (foundation stub, keep: export { default } from "./Scr05";)
  Scr05.tsx                    (replace the stub)
  useQueueFeed.ts  queueDiff.ts  useRowKeys.ts  LiveRow.tsx  QueueSections.tsx
  queue.fixtures.ts            (test-only helper, not a *.test file)
  queueDiff.test.ts  useRowKeys.test.tsx  LiveRow.test.tsx  Scr05.test.tsx
apps/web/src/screens/scr06/
  index.ts                     (foundation stub, keep)
  Scr06.tsx                    (replace the stub; layout + wiring only)
  specExample.ts               (test-only: reads a named example out of the OpenAPI file)
  case.fixtures.ts             (test-only)
  caseReducer.ts  useCase.ts  useCaseStream.ts  useMediaQuery.ts
  caseText.ts  errorCopy.ts  actionPlan.ts  claimAndJoin.ts  wakeUp.ts
  CaseHeader.tsx  LifecycleLine.tsx  PromiseCard.tsx  SplitButton.tsx
  BriefView.tsx  BriefSection.tsx  SourceChip.tsx
  EvidenceColumn.tsx  SourceCard.tsx  SnapshotTable.tsx  ConversationTab.tsx  LiveBox.tsx
  ActionArea.tsx  ActionForms.tsx  ActivityLog.tsx  ActionResult.tsx  RailColumn.tsx
  *.test.ts / *.test.tsx       (one per module named in §5, see §7)
apps/web/src/dev/scenarios/scr05.ts           (replace the foundation stub)
apps/web/src/dev/scenarios/scr06.ts           (replace the foundation stub)
apps/web/src/dev/scenarios/case-transforms.ts (NEW: pure transform helpers used by both scenario files)
apps/web/src/dev/reactions/scr05.ts           (foundation stub: leave unchanged, G4 has no reaction that belongs here)
apps/web/src/dev/reactions/scr06.ts           (replace the stub)
apps/web/src/dev/stream/case-scripts.ts       (replace the stub)
apps/web/src/dev/directors/case-actions.ts    (NEW: the case director, §5 Step 14; needs FR-1)
apps/web/src/dev/directors/case-store.ts      (NEW: in-memory case store + server-rule replica)
apps/web/src/dev/directors/case-store.test.ts  case-actions.test.ts   (NEW)
docs/ux/04-prototype/groups/g4-staff-queue-case.md   (NEW; the caller's name. F§2.4 says g4-staff-case.md: use the caller's name and tell the integrator)
```

### 2.2 Read-only shared surfaces (never edit; request changes per F§8.3)

`src/components/ui/**`, `src/components/shared/**`, `src/components/shell/**`, `src/api/**`, `src/state/**`, `src/styles/**`, `src/lib/**`, `src/routes.ts`, `src/router.tsx`, `src/test/**`, `src/dev/{install.ts,Panel.tsx,Kit.tsx,resolve.ts,transport.ts,world.ts,defaults.ts,calllog.ts,session-fake.ts}`, `src/dev/scenarios/{index.ts,types.ts,matrix.ts,shared.ts}`, `src/dev/reactions/{index.ts,shared.ts}`, `src/dev/directors/index.ts`, `src/dev/stream/{types.ts,dev-stream.ts,events.ts}`, `package.json`, `docs/ux/03-structure/*` (incl. the OpenAPI file), `docs/design/design.md`, `docs/artifacts/**`, `.claude/**`, `CLAUDE.md`, `PROJECT-CHECKLIST.md`.

### 2.3 Collisions to avoid

- **G5** owns `src/screens/scr07..scr11/**` and `src/screens/reads/**`; they use the shared `QueueRow` and `PriorityTag` only. G4 never imports from `src/screens/reads/**` and G5 never imports from G4. G4's own `LiveRow` stays in `scr05/`; `scr06/RailColumn.tsx` imports it from `../scr05/LiveRow`.
- **G1/G2/G3** own `scr01..scr04`, `scr12`. G4 touches none.
- `src/dev/scenarios/scr0{5,6}.ts` and `src/dev/reactions/scr06.ts`, `src/dev/stream/case-scripts.ts` are G4's; the foundation registers them (F§Step 7 items 3–5). Do not edit the index files.

### 2.4 Do not (in addition to F§2.3, which applies in full)

- Do not call `fetch`; do not read or write `document.cookie`; do not import anything under `src/dev/**` from `src/screens/**` (ESLint bans it). Screens never mention `Prefer`, example names, scenario ids or `import.meta.env.MODE`.
- No red, orange, amber, hex literal, `--color-safety` or `--safety-*` anywhere in G4 files (guard test F§Step 3 item 9). P0 rows and Overdue are ink weight, words and icons only.
- No 24-hour times, no `text-transform: uppercase` on any time or date, no countdowns, no wait estimates, no "charged", "overcharged", "done" or "booked". Do not invent data a contract does not carry: names, counts and times come from responses. Where a string must be composed, §5 gives the exact composition.
- Do not pre-validate required fields on the client (reason, wake-up, outcome): the server decides and the screen shows its error (SCREEN_SPECS SCR-6 error state; UI_CONTRACTS "the screen needs no client-side rules"). Do not add client-side rules that disable buttons: use `allowed_actions` only.
- Do not use `useEffect` to fetch; use `useOp` / `useAction` / `callOp`. Do not poll SCR-6 (the stream and the Reload button cover it).
- Do not edit `stubs.test.tsx`, `routes.test.ts` or the e2e smoke when they complain about the h1 (see §8, FR-3); report instead.
- Do not exceed 300 lines in a component file or test file (rule `code-structure`); split along the module list in §2.1.

## 3. Requirements table

`V` column commands run from `apps/web/` (§7). "Unit" = a vitest file named in §7.

### 3.1 SCR-5

| # | Requirement (source) | How implemented | Verified by |
|---|---|---|---|
| Q-01 | Route `/staff/queue`, behind login and a staff role; as the customer: the SCR-4 stale panel and **no staff data** (SCR-5 route line; F-12) | `Scr05` renders `AppFrame variant="console"` → `ConsoleHeader` → `RoleGate allow={["representative","supervisor"]}` → inner `QueueBody`; data hooks live only in `QueueBody`, so nothing is called under the gate | Unit `Scr05.test.tsx` "customer role renders the gate sentence and never calls getQueue" |
| Q-02 | R1 console header (F§4.8 `ConsoleHeader`) | shared component, no G4 code | Step 17 DevTools |
| Q-03 | R2 Live queue: only while `staffing.mode === "simulated_on_shift"`: "Waiting in chat" with count, oldest first, P0/P1 on top (the server orders), priority tag, reference, reason, customer, "Waiting since 2:14 pm" (a time, never an estimate), "Claim and join" | `LiveQueueSection` in `QueueSections.tsx` renders `LiveRow` per `data.live` row; "Waiting since" = `formatTimePoint(row.queued_at)` (fallback `row.age_label`) | Unit `LiveRow.test.tsx`; `Scr05.test.tsx` "staffed queue shows waiting rows" |
| Q-04 | R3 Needs my action: heading with count; hint "Safety and danger first, then by due time."; rows via shared `QueueRow` | `NeedsActionSection` → `<ul>` of `QueueRow` (`onSelect={open}`, `selected={ref === cursor}`, `showStaffTags`) | Unit `Scr05.test.tsx` "default lists the four seeded rows in server order" |
| Q-05 | Row accessible name "P0 safety, MHC-C-0008, gas smell reported in chat, unowned, no due time: safety" (SCR-5 a11y) | produced by `QueueRow` (F§4.8); G4 asserts it | `Scr05.test.tsx` `getByRole("button", {name: "P0 safety, MHC-C-0008, gas smell reported in chat, unowned, no due time: safety"})` |
| Q-06 | R4 "J / K to move, Enter to open" laptops only | `useRowKeys` + hint line with `Kbd`, class `hidden min-[1100px]:block` | Unit `useRowKeys.test.tsx` |
| Q-07 | State default: seeded rows MHC-C-0008, 0005, 0006, 0007 | scenario `scr05.default` (forced `getQueue: SEEDED`) | Unit; Step 17 |
| Q-08 | State empty: "You're all caught up. No case needs your action. New handoffs from the chat appear here." | `EmptyState` when `needs_my_action.length === 0` and `live.length === 0` | Unit `Scr05.test.tsx`; scenario `scr05.empty` |
| Q-09 | State loading: header renders; five row-shaped skeletons | `Skeleton height={44} rows={5}` while `status === "loading"` and no data | Unit |
| Q-10 | State partial: `brief_status === "being_written"` shows "Brief being written" in place of the follow-up line | provided by `QueueRow` (F§4.8, tag "Brief being written") | Unit asserts text for `BRIEF_BEING_WRITTEN` fixture |
| Q-11 | State error: "The queue didn't load. Try again." with retry; header stays | `ErrorLine message="The queue didn't load. Try again." onRetry={refetch}` | Unit: retry issues a second `getQueue` call |
| Q-12 | State stale: list refreshes every 10 s and on focus; "2 cases changed. Show them." applies the update **without moving the selected row**; clock move recomputes Overdue on refresh | `useQueueFeed`: `useOp("getQueue", {}, {pollMs: 10000, refetchOnFocus: true})`; keeps `shown` separate from `fresh`; `StaleLine` with `countChangedRows`; cursor tracked by **reference**, not index | Unit `queueDiff.test.ts`, `Scr05.test.tsx` with fake timers |
| Q-13 | State success: returning from a resolved case: row gone and "MHC-C-0007 resolved." for 4 s; a claimed row shows its owner | `Scr05` reads `useLocation().state?.resultLine`, shows it in `ActionResult` for 4000 ms, then clears router state with `navigate(".", {replace:true, state:null})`. The row disappears because the next `getQueue` no longer has it (dev: case director) | Unit "result line from router state clears after 4 s" |
| Q-14 | State disabled: nobody online: "Nobody is on shift, so there is no live queue. Turn on the simulation in the demo guide to try it." | R2 region renders that sentence (plain text, not a button) when `staffing.mode === "nobody_online"` | Unit; scenario `scr05.disabled` |
| Q-15 | Flow: new handoff (FLOW-7) → stale then default | scenario `scr05.new-handoff` (sequence) | Step 17 |
| Q-16 | Flow: live-queued customer (FLOW-8) → R2 row | scenario `scr05.live-queued` (STAFFED_WITH_WAITING, staffing on) | Unit + Step 17 |
| Q-17 | Flow: shift ended before claim → row moves R2 → R3 with its original creation time | scenario `scr05.shift-ended` (sequence + transform) | Step 17 |
| Q-18 | Flow: overdue after clock advance (FLOW-10) | scenario `scr05.overdue-after-advance` | Step 17 |
| Q-19 | Flow: seeded cases show "Demo seed"; reset restores seeds (FLOW-12) | `QueueRow` shows the tag; dev reaction `resetDemo` → `resetCaseStore()` | `case-store.test.ts` "reset clears overrides" |
| Q-20 | Interaction: click or Enter opens SCR-6; "Claim and join" = CON-13 claim **then** CON-14 join, then SCR-6 | `claimAndJoin(reference)` in `scr06/claimAndJoin.ts`, then `navigate(caseHref(reference))` | Unit `claimAndJoin.test.ts` (call order and `expected_version`) |
| Q-21 | Copy: due times 12-hour; "Overdue" word with icon, never red; no estimates; priority word beside the code | shared components; G4 adds `expectNo24HourTimes` to every screen test | Unit |
| Q-22 | A11y: list is `ul` of buttons, `aria-current` on selected, polite stale line, rows ≥ 44 px | shared `QueueRow`; stale line via `StaleLine` | Unit; Step 17 |

### 3.2 SCR-6

| # | Requirement (source) | How implemented | Verified by |
|---|---|---|---|
| C-01 | Route `/staff/cases/:reference`; roles representative, supervisor, owner; customer → gate panel (F§4.9 `SCREENS`) | `Scr06` as `Scr05`; inner `CaseBody` gets `reference` from `useParams()` | Unit |
| C-02 | Landmarks: `nav` (queue), `main` (brief, one `h1` = case title), `aside` (evidence); skip link "Go to queue"; brief sections an ordered list with `h3` | `CaseLayout` in `Scr06.tsx`; the `h1` is the reason pill ("Billing dispute · P3 Standard"); while loading / not found the single `h1` is "Case {reference}" (visually hidden) / "Case not found" | Unit `Scr06.test.tsx` counts `h1` in every state |
| C-03 | R2 queue column ≥ 1100 px; drawer 700–1099 ("Queue · 4 cases"); one column < 700 with Brief · Evidence tabs (IA, design §9.2) | `RailColumn` (hidden for owner: `getQueue` is not allowed for owner); `Disclosure` drawer; `useMediaQuery` | Step 17 resize 390 / 800 / 1280 |
| C-04 | R3 case header: "Billing dispute · P3 Standard"; `MHC-C-0007`; split button; due headline ("Due Mon Oct 19 · 7:00 pm", "No due time: safety"); "Overdue" tag with clock icon; "Created Fri Oct 16, 2:14 pm"; owner or "Unassigned, nobody owns it yet"; "Demo seed" | `CaseHeader` with `caseText.ts` helpers (§4.4) | Unit `caseText.test.ts`, `Scr06.test.tsx` |
| C-05 | R4 lifecycle line, current state a strong tag, "Live-queued" first on the staffed path | `LifecycleLine` (algorithm §5 Step 7) | Unit |
| C-06 | R5 promise card: exact promise text; cells Follow up by · Destination (on record / not on record) · Best time; status Open / Kept / Missed / Changed + reason | `PromiseCard` (§5 Step 8) | Unit |
| C-07 | R6 brief: eight numbered sections, fixed headings, source chip per fact; section 4 "Customer says · not checked" claims card (dashed edge, grey well, no chips); trimmed section line "Something here didn't match the record and was removed."; empty section "Nothing recorded."; brief index chips 1–8 | `BriefView` + `BriefSection` + `SourceChip` (§5 Step 9) | Unit `BriefView.test.tsx` |
| C-08 | R8 evidence column "Evidence" / "What the AI saw, next to what is true now"; tabs **Sources (n)** and **Conversation** (ARIA tab pattern) | `EvidenceColumn` on `@radix-ui/react-tabs` | Unit (arrow keys switch tabs) |
| C-09 | R8a source cards: title, file/record, version label; snapshot-vs-now table or the quoted passage; status "No change since the snapshot" / "Changed since the AI saw it: was $144.00, now $149.00"; unreadable → "This record can't be read right now; the snapshot is shown alone."; `staff_only` marked | `SourceCard` + `SnapshotTable` (§5 Step 10) | Unit `SnapshotTable.test.tsx` |
| C-10 | R8b conversation with speaker labels and times; live box once joined: "You are replying as Riley (demo representative). The assistant is paused." + field + Send + "Hand back to the assistant" + "Close the chat"; disabled after hand-back/close | `ConversationTab`, `LiveBox` | Unit `LiveBox.test.tsx` |
| C-11 | R9 "Other cases for this customer" by reference, status in words | list in the evidence column foot (links to `caseHref`) | Unit |
| C-12 | R7 action bar by state; one emerald split button: Claim / Claim and join → Resolve; menu Release, Set waiting, Close unresolved; bar Log a call, Log an email, Flag, (supervisor) Assign, Change priority; **no emerald primary while a chat is live**; disabled items carry the reason | `actionPlan.ts` (pure) + `SplitButton` + `ActionArea` (§5 Step 6, 11) | Unit `actionPlan.test.ts` (lifecycle × role matrix) |
| C-13 | Inline forms: release (reason), wait (wake-up), resolve (outcome), close unresolved (reason), call/email (outcome, note), flag (what is wrong, note), assign (assignee, reason), priority (priority, reason) | `ActionForms.tsx` (§5 Step 11) | Unit `ActionForms.test.tsx` |
| C-14 | Activity log: 12-hour time column, "Demo: recorded, not sent" on every contact; "Called ···02 · Reached the customer · Demo: recorded, not sent" | `ActivityLog` (§5 Step 12). The `···02` mask comes from the promise `destination_label` only if present in the activity note; **do not compose it**: show `activity.kind` word, outcome sentence and `activity.label` | Unit |
| C-15 | Success lines: Claim "Claimed · Riley (demo)" (`result_line`), contact logged, resolved → redirect to queue with the line, flag "Added to the review list." | `ActionResult` shows the server `result_line`; flag line is the fixed string | Unit `Scr06.test.tsx` |
| C-16 | Errors under the action bar: "Waiting needs a wake-up time." / "Add a reason to release this case." / "Resolving needs an outcome." / "Claim the case first." | `errorCopy.ts` (§4.5) | Unit `errorCopy.test.ts` |
| C-17 | Case not found: "No case MHC-C-0099. It may have been cleared by a demo reset." + "Back to the queue" | `CaseBody` error branch | Unit |
| C-18 | Owner: case opens **read-only**, no buttons, quiet line "Read-only for the business owner role" (CON-12 settled 2026-10-21) | `actionPlan.readOnly`; owner scenario derives it from the role | Unit + scenario `scr06.error-owner-readonly` |
| C-19 | Stale: "Changed since the AI saw it" with both values and a "changed" mark on the brief fact's chip; version conflict "This case changed since you opened it (… at …). Reload to see it." + Reload | `SnapshotTable`, `SourceChip`, `ActionResult` + `ReloadLine` in `Scr06` | Unit |
| C-20 | Partial: brief being written: "The brief is being written. The conversation is complete."; source unavailable; trimmed | `BriefView` / `SourceCard` | Unit |
| C-21 | Empty: "Pick a case from the queue." (no reference) and "Nothing recorded." | `CaseBody` branch when `reference` is undefined; empty headings | Unit (direct render with no param); scenario for the first only if FR-2 is accepted |
| C-22 | Loading: header and eight section skeletons in the final layout; evidence skeleton; buttons disabled | `Skeleton` blocks sized to the real heights | Unit asserts 8 skeleton groups; Step 17 |
| C-23 | Disabled: Join chat disabled with "Join chat works only while the customer is waiting in a live chat."; log/wait/resolve/close "Claim the case first."; assign/priority hidden for the representative; live box disabled after hand-back/close | `actionPlan.ts` | Unit |
| C-24 | CON-21 stream: customer replies arrive in the conversation (announced politely), controller changes, chat closed, demo reset "This chat ended because the demo was reset.", case changed elsewhere prompts a reload | `useCaseStream` → `caseReducer` (§5 Steps 3–4) | Unit `caseReducer.test.ts`, `Scr06.test.tsx` with a fake `openStream` |
| C-25 | Flow states: live-queued; joined AI paused; handed back; chat closed; customer chat ended by reset; shift ended before claim; waiting; stuck waiting; overdue; released; changed since; fee-bearing; safety; seeded; assign/reprioritise | table in §6.2: each has a scenario id and the exact reach | `scenarios.integrity.test.ts` (foundation) + Step 17 |
| C-26 | Focus moves to the result line after an action; incoming messages announced politely; "assistant paused" is text | `ActionResult` (focus wrapper), `useAnnounce` | Unit |
| C-27 | Targets ≥ 32 px (laptop console density), ≥ 44 px at phone width | `Button density="console"`, `min-[700px]` density swap via class | Step 17 |
| C-28 | Back to queue: previous else SCR-5 (IA cross-screen row) | `BackLink`: `navigate(-1)` when `location.key !== "default"`, else `navigate(HOME)` where HOME is `/staff/queue` for rep/supervisor and `HOME_BY_ROLE.owner` for owner; label "Back to queue" (owner: "Back") | Unit |

## 4. Shared code to use

### 4.1 Imports (exact; confirm each file exists after the foundation finished, per F§4 and F§5)

```ts
import { callOp, type OkBody, type ReqBody } from "@/api/client";            // F§4.4
import { useOp, useAction } from "@/api/useOp";                               // F§4.6
import { useEventStream } from "@/api/useEventStream";                        // F§4.6
import { ApiError } from "@/api/errors";                                      // F§4.5
import type { components } from "@/api/types.gen";
import { useSession } from "@/state/session";                                 // F§4.9
import { useDemoStatus } from "@/state/demoStatus";                           // F§4.9: clock?.now is the demo "now"
import { useAnnounce } from "@/components/ui";                                // F§4.7 LiveRegion / AnnounceProvider
import { Button, Card, CardHeader, CardBody, CardRow, Tag, Skeleton, Disclosure, Field, TextInput, TextArea, VisuallyHidden, Kbd,
         IconBack, IconClock, IconCheck, IconWarning, IconDoc, IconChevron, IconInfo, IconQuestion, IconQuote, IconUser } from "@/components/ui";
import { Time, TimeWindow, RefChip, PersonDisc, MessageRow, EventLine, QueueRow, PriorityTag, ErrorLine, EmptyState,
         StaleLine, ResultLine, RoleGate, ConsoleHeader, AppFrame, Main } from "@/components/shared"; // shell ones from "@/components/shell" if the barrel splits; check the index files
import { caseHref, SCREENS } from "@/routes";
import { HOME_BY_ROLE, ROLE_LABEL, type Role } from "@/lib/roles";
import { formatTimePoint, formatDateTimeShort, formatStaffTime, formatDayShort, formatSentence, formatClockLabel } from "@/lib/time";
import { cn } from "@/lib/cx";
```
`Time` props (F§4.8): `iso: string|null; format: "point"|"short"|"staff"|"day"|"sentence"|"clock"; variant?: "hero"|"due"|"row"|"meta"; fallback?: string`. Format mapping to `lib/time.ts`: point = `formatTimePoint` ("7:00 pm"), short = `formatDateTimeShort` ("Mon Oct 19 · 7:00 pm"), staff = `formatStaffTime` ("Mon 7:00 pm"), day = `formatDayShort` ("Wed Oct 21"), sentence = `formatSentence`, clock = `formatClockLabel`. Use `<Time>` where JSX is allowed; use the lib function when a sentence is composed as a string.

**First action of Step 0:** open `src/screens/ScreenStub.tsx` and copy its frame wiring exactly (`AppFrame variant="console"`, `ConsoleHeader`, `RoleGate`, `document.title = "{id} · {title} · Meridian"` from the `SCREENS` entry). Read `src/styles/theme.css` for the Tailwind colour utility names (`bg-surface`, `bg-surface-well`, `text-text-muted`, `border-border-hair`, `text-accent` …); read `src/components/shared/QueueRow.tsx` to see whether it renders its own `<li>`; read `ResultLine.tsx` and `StaleLine.tsx` for their exact props.

### 4.2 Generated types used (names are in `src/api/types.gen.ts`)

```ts
type S = components["schemas"];
S["QueueResponse"]   // { as_of; staffing: Staffing; live: QueueRow[]; needs_my_action: QueueRow[] }
S["QueueRow"]        // { reference; priority:{level,word}; reason; customer_display_name; owner|null; created_at; due_at|null; due_label|null;
                     //   due_state:"on_time"|"due_soon"|"overdue"|"no_due_time"; wake_up_at|null;
                     //   lifecycle:"live_queued"|"unassigned"|"claimed"|"in_progress"|"waiting"|"resolved"|"closed_unresolved";
                     //   follow_up_short|null; seed; brief_status:"ready"|"being_written"|"failed"; queued_at|null; age_label|null }
S["Staffing"]        // { mode:"nobody_online"|"simulated_on_shift"; label; banner|null }
S["CaseDetail"]      // { case: CaseSummary; promise: PromiseRecord; brief: Brief; identity:{status,line,demo_note}; sources: CaseSource[];
                     //   conversation: ChatLine[]; activities: Activity[]; live: LiveState; other_cases:{reference,status}[]; agent_version; as_of }
S["CaseSummary"]     // { reference; reason; priority; lifecycle; owner|null; created_at; due_at|null; due_label|null; due_state; wake_up_at|null;
                     //   promise_status:"open"|"kept"|"missed"|"changed"; seed; version:number;
                     //   allowed_actions:("claim"|"claim_and_join"|"release"|"start"|"wait"|"resolve"|"close_unresolved"|"assign"|"change_priority"|"join_chat"|"send_live_message"|"hand_back"|"close_chat"|"log_call"|"log_email"|"flag")[] }
S["Brief"]           // { status:"ready"|"being_written"|"failed"; headings: BriefHeading[] }   // always 8
S["BriefHeading"]    // { number; key:"why"|"needs"|"know"|"says"|"ai_did"|"told"|"decide"|"who"; title; checked:boolean; items: BriefItem[]; trimmed; trim_note|null; not_generated }
S["BriefItem"]       // { text; kind:"fact"|"claim"|"ai_action"|"told_customer"|"decision"|"contact"; source_ids:string[]; changed:boolean }
S["CaseSource"]      // { source_id; lookup_log_id; audience:"customer"|"staff_only"; title; ref; version_date|null; snapshot:Record<string,unknown>; current|null;
                     //   changed_since; changed_note|null; current_unavailable; version_label }   // snapshot/current are typed Record<string,never>: cast to Record<string, unknown>
S["ChatLine"]        // { message_id; speaker: Speaker; at; text }       S["Speaker"] = { kind:"assistant"|"customer"|"representative"|"event"; display_name|null }
S["Activity"]        // { activity_id; kind:"call"|"email"; outcome:"reached"|"no_answer"|"left_message"; note|null; at; by; label:"Demo: recorded, not sent" }
S["PromiseRecord"]   // { text; due_at|null; due_label|null; policy_row; status; follow_up:{channel:"email"|"phone"; destination_label; on_record; window|null}|null; history:{at;text;reason}[] }
S["LiveState"]       // { state:"not_live"|"queued"|"joined"|"handed_back"|"closed"; since|null; controller:"ai"|"human" }
S["CaseActionRequest"]  // { action:"claim"|"release"|"start"|"wait"|"resolve"|"close_unresolved"|"assign"|"change_priority"; expected_version; reason?; wake_up_at?; outcome?; assignee?:"riley"|"supervisor"|null; priority?:"P0".."P4"|null }
S["CaseActionResponse"] // { case: CaseSummary; result_line: string }
S["LiveActionRequest"]  // { action:"join"|"send"|"hand_back"|"close"; text?|null }
S["LiveActionResponse"] // { controller:{kind:"ai"|"human"; display_name|null}; live: LiveState; message: ChatLine|null }
S["ActivityRequest"]    // { kind:"call"|"email"; outcome:"reached"|"no_answer"|"left_message"; note?; expected_version }
S["ActivityResponse"]   // { activity: Activity; case: CaseSummary }
S["FlagRequest"]        // { case_ref; target:"answer"|"brief"|"escalation"; message_id?; note?; reason? }
S["CaseEvent"] = CeCustomerMessage | CeControllerChanged | CeChatClosed | CeDemoReset | CeCaseChanged
  // CeCustomerMessage { event_id; type:"customer_message"; at; message: ChatLine }
  // CeControllerChanged { event_id; type:"controller_changed"; at; controller:{kind:"ai"|"human"; display_name|null}; line:string }
  // CeChatClosed { event_id; type:"chat_closed"; at; reason:"closed_by_staff"|"shift_ended" }
  // CeDemoReset { event_id; type:"demo_reset"; at; line:string }
  // CeCaseChanged { event_id; type:"case_changed"; at; version:number; lifecycle }
```

### 4.3 Contract operations used (roles from `contract.gen.json`)

| operationId | Call | Roles | Named examples (statuses) |
|---|---|---|---|
| `getQueue` | `useOp("getQueue", {}, {pollMs:10000, refetchOnFocus:true})` | representative, supervisor | 200: SEEDED, STAFFED_WITH_WAITING, ALL_CAUGHT_UP, BRIEF_BEING_WRITTEN; 401; 403 |
| `getCase` | `useOp("getCase", {path:{reference}})` | rep, supervisor, owner | 200: DEFAULT, BRIEF_BEING_WRITTEN, TRIMMED_STOP, SAFETY_CASE (0008), LIVE_JOINED, WAITING, FEE_BEARING_CHANGE (0009); 404 CASE_NOT_FOUND |
| `applyCaseAction` | `callOp("applyCaseAction", {path:{reference}, body})` | rep, supervisor | 200: CLAIMED, WAITING, RESOLVED, ASSIGNED, PRIORITY_CHANGED; 409: VERSION_CONFLICT, CASE_ALREADY_CLAIMED, NOT_ALLOWED_IN_STATE; 422: REASON_REQUIRED, WAKE_UP_REQUIRED, OUTCOME_REQUIRED; 400 VALIDATION_ERROR; 404 |
| `liveChatAction` | `callOp("liveChatAction", {path:{reference}, body})` | **representative only** | 200: JOINED, SENT, HANDED_BACK, CLOSED; 403 NOT_CLAIMED_BY_YOU; 409: NOT_LIVE, CASE_ALREADY_CLAIMED |
| `recordContactActivity` | `callOp("recordContactActivity", {path, body})` | representative | 201: CALL_REACHED, EMAIL_LEFT_MESSAGE; 409: NOT_ALLOWED_IN_STATE, VERSION_CONFLICT |
| `createFlag` | `callOp("createFlag", {body})` | representative, supervisor | 201: ANSWER |
| `streamCaseEvents` | `useEventStream({op:"streamCaseEvents", path:{reference}}, onEvent)` | rep, supervisor, owner | FRAMES (customer_message id 5, chat_closed id 6) |

Request bodies copied from the OpenAPI examples: `{"action":"claim","expected_version":3}`; `{"action":"wait","expected_version":5,"wake_up_at":"2026-10-19T09:00:00-05:00","reason":"Customer asked for Monday morning"}`; `{"action":"resolve","expected_version":8,"outcome":"Credit decision recorded; customer told by phone (demo)"}`; `{"action":"release","expected_version":4,"reason":"Not my area"}`; `{"action":"assign","expected_version":3,"assignee":"riley","reason":"Billing dispute, Riley has the context"}`; `{"action":"change_priority","expected_version":3,"priority":"P2","reason":"Customer reports a second invoice"}`; live: `{"action":"join"}`, `{"action":"send","text":"Hi Omar, I can look at the after-hours charge with you."}`, `{"action":"hand_back"}`, `{"action":"close"}`; activity: `{"kind":"call","outcome":"reached","note":"Explained the credit review","expected_version":4}`; flag: `{"case_ref":"MHC-C-0007","target":"answer","message_id":"m-2","note":"Quoted $144 as the fee","reason":"Quoted $144 as the after-hours fee"}`.

Error bodies (class `ApiError`, fields `status, code, details, field`): VERSION_CONFLICT `details {changed_by:"Demo supervisor", changed_at:"2026-10-16T14:31:00-05:00", current_version:4}`; CASE_ALREADY_CLAIMED `details {claimed_by, claimed_at?}`; NOT_ALLOWED_IN_STATE `details {state:"unassigned", needs:"claimed"}`; NOT_LIVE `details {reason:"demo_reset"}`; NOT_CLAIMED_BY_YOU `details {owner}`; CASE_NOT_FOUND `details {reference:"MHC-C-0099"}`. Composed errors are not thrown (F§4.5) but none of G4's operations has HTTP-200 error blocks.

### 4.4 Pure text helpers (`scr06/caseText.ts`, exact behaviour; unit-tested)

```ts
type CaseSummary = components["schemas"]["CaseSummary"];  type CaseDetail = components["schemas"]["CaseDetail"];
export function dueHeadline(c: CaseSummary): string;
//  1. c.due_state === "no_due_time" → "No due time: safety"
//  2. c.due_at → "Due " + formatDateTimeShort(c.due_at) + suffix, where suffix = the match of /,\s*the window start$/ in c.due_label (else "")   // FEE_BEARING_CHANGE label "Sat Oct 17 · 12:00 pm, the window start"
//  3. else c.due_label ?? "No due time"
export function createdLine(c: CaseSummary): string;     // `Created ${formatDayShort(c.created_at)}, ${formatTimePoint(c.created_at)}` → "Created Fri Oct 16, 2:14 pm"
export function ownerLine(c: CaseSummary): string;       // owner ? `Owned by ${owner}` : "Unassigned, nobody owns it yet"
export function headerStatusLine(d: CaseDetail, nowIso: string): string | null;
//  1. d.live.state === "joined" → "Live · you are replying · assistant paused"
//  2. d.case.lifecycle === "live_queued" && d.live.since → `The customer is waiting in the chat since ${formatTimePoint(d.live.since)}.`
//  3. d.case.lifecycle === "waiting" && d.case.wake_up_at:
//       Date.parse(nowIso) >= Date.parse(wake) → `Wake-up time passed (${formatStaffTime(wake)}). Pick it back up.`
//       else `Wakes ${formatDateTimeShort(wake)}`
//  4. null
export const LIFECYCLE_LABEL: Record<CaseSummary["lifecycle"], string> = {
  live_queued: "Live-queued", unassigned: "Unassigned", claimed: "Claimed", in_progress: "In progress",
  waiting: "Waiting", resolved: "Resolved", closed_unresolved: "Closed unresolved" };
export const PROMISE_STATUS_LABEL = { open: "Open", kept: "Kept", missed: "Missed", changed: "Changed" } as const;
export function bestTimeLabel(window: string | null): string;   // "morning"→"Mornings", "afternoon"→"Afternoons", "any"→"Any time", null→"No preference", other→as given
export function channelLabel(ch: "email" | "phone"): string;     // "Email" | "Phone"
export function humanizeKey(key: string): string;                 // "after_hours_dispatch" → "After hours dispatch"
export function caseTitle(c: CaseSummary): string;                // `${c.reason} · ${c.priority.level} ${c.priority.word}` → "Billing dispute · P3 Standard"
```
`nowIso` = `useDemoStatus().clock?.now ?? detail.as_of`.

### 4.5 Error copy (`scr06/errorCopy.ts`, exact strings)

```ts
export type ActionKey = components["schemas"]["CaseActionRequest"]["action"] | "log_call" | "log_email" | "flag" | "join" | "send" | "hand_back" | "close";
export interface ShownError { text: string; offerReload: boolean }
export function errorText(err: ApiError, action: ActionKey, role: Role): ShownError;
```
| `err.code` | text | offerReload |
|---|---|---|
| `REASON_REQUIRED` | by action: release "Add a reason to release this case."; assign "Add a reason to assign this case."; change_priority "Add a reason to change the priority."; close_unresolved "Add a reason to close this case."; other "Add a reason." | false |
| `WAKE_UP_REQUIRED` | "Waiting needs a wake-up time." | false |
| `OUTCOME_REQUIRED` | "Resolving needs an outcome." | false |
| `NOT_ALLOWED_IN_STATE` | `details.needs === "claimed"` → "Claim the case first."; else "That isn't possible in the case's current state." | true unless needs==="claimed" |
| `NOT_CLAIMED_BY_YOU` | "Claim the case first." | false |
| `VERSION_CONFLICT` | `This case changed since you opened it (${changed_by} at ${formatTimePoint(changed_at)}). Reload to see it.` (fallbacks when details are missing: omit the parenthesis) | true |
| `CASE_ALREADY_CLAIMED` | `Already claimed by ${claimed_by}${claimed_at ? " at " + formatTimePoint(claimed_at) : ""}. Reload.` | true |
| `NOT_LIVE` | `details.reason === "demo_reset"` → "This chat ended because the demo was reset."; else "This chat has ended." | false |
| `ROLE_NOT_ALLOWED` | `You can't do that as ${ROLE_LABEL[role].full}.` | false |
| `CASE_NOT_FOUND` | `No case ${details.reference}. It may have been cleared by a demo reset.` | false |
| `NETWORK`, anything else | "That didn't go through. Try again." | false |

(SCREEN_SPECS words the conflict as "(claimed by the demo supervisor at 2:31 pm)"; the contract carries only `changed_by` and `changed_at`, so the screen uses UI_CONTRACTS' "[who] at [time]". Record this in the group file.)

### 4.6 Action plan (`scr06/actionPlan.ts`, exact shape)

```ts
type Allowed = CaseSummary["allowed_actions"][number];
export type BarKey = "log_call" | "log_email" | "join_chat" | "flag" | "assign" | "change_priority";
export type MenuKey = "release" | "wait" | "close_unresolved" | "resolve" | "start";
export interface PlanItem<K extends string> { key: K; label: string; enabled: boolean; reason?: string }
export interface ActionPlan {
  readOnly: boolean;                                   // role === "owner"
  primary: { kind: "claim_and_join" | "claim" | "resolve" | "start"; label: string } | null;
  menu: PlanItem<MenuKey>[];                           // inside the split button's menu (or a "More actions" menu when primary is null)
  bar: PlanItem<BarKey>[];                             // secondary buttons under the brief
  liveBox: "hidden" | "active" | "disabled";
}
export function planActions(detail: CaseDetail, role: Role): ActionPlan;
export function disabledReason(lifecycle: CaseSummary["lifecycle"], key: string): string;
```
`planActions` rules, numbered (invariant: every enabled flag is `allowed_actions.includes(key)`; no other rule enables anything):
1. `role === "owner"` → `{readOnly: true, primary: null, menu: [], bar: [], liveBox: "hidden"}` (the page still shows the live conversation read-only; the live box is never offered to the owner).
2. `joined = detail.live.state === "joined"`. `liveBox`: joined → `"active"`; `handed_back` or `closed` → `"disabled"`; else `"hidden"`.
3. Primary: not joined and `claim_and_join` allowed → `{kind:"claim_and_join", label:"Claim and join"}`; else `claim` allowed → "Claim"; else `resolve` allowed → "Resolve"; else `start` allowed → "Pick it back up"; else null. **When joined, primary is null** (design §8.9: no emerald primary while a chat is live).
4. Menu (order): Release (`release`), Set waiting (`wait`), Close unresolved (`close_unresolved`); plus Resolve (`resolve`) when the primary is not Resolve; plus `start` ("Pick it back up") when primary is not Start and `start` is allowed. Each item `enabled = allowed.includes(key)`; when not enabled `reason = disabledReason(lifecycle, key)`.
5. Bar (order): Log a call (`log_call`), Log an email (`log_email`), Join chat (`join_chat`), Flag (`flag`); for `role === "supervisor"` also Assign (`assign`, label "Reassign" when `case.owner !== null`) and Change priority (`change_priority`). The representative never gets assign / change_priority items (hidden, not disabled). Join chat is shown only for the representative role.
6. `disabledReason`: `join_chat` → "Join chat works only while the customer is waiting in a live chat."; lifecycle `unassigned` or `live_queued` → "Claim the case first."; `waiting` → "Pick the case back up first."; `resolved` or `closed_unresolved` → "This case is closed."; otherwise "Not available right now."

## 5. Steps (build order; each step ends with a check)

Work in `apps/web/`. Preflight: `ls src/screens/scr05/Scr05.tsx src/screens/scr06/Scr06.tsx src/components/shared/QueueRow.tsx src/dev/scenarios/types.ts src/dev/directors/index.ts` must all exist (the foundation finished). If not, stop and report BLOCKED. Run `npm run typecheck` once to make sure the baseline is green before editing.

### Step 0 · Read and note
Do the reads listed under §4.1 (first action). Note in the group file (`docs/ux/04-prototype/groups/g4-staff-queue-case.md`, create now with headings *Built*, *States and how they are reached*, *Mock artefacts*, *Requests to the integrator*, *Deviations*, *Checks*) any prop that differs from F§4.8. Where it differs, adapt the call sites, never the shared component.

### Step 1 · SCR-5 data layer (`useQueueFeed.ts`, `queueDiff.ts`)
```ts
// queueDiff.ts
export function rowSignature(r: QueueRow): string;   // JSON of [reference, priority.level, owner, lifecycle, due_at, due_state, wake_up_at, brief_status, follow_up_short, queued_at]
export function countChangedRows(shown: QueueResponse, fresh: QueueResponse): number;
//  1. index rows of shown.live ∪ shown.needs_my_action by reference → signature; same for fresh.
//  2. count references present in only one side, plus references present in both whose signature differs. (as_of and age_label are ignored: they change on every read.)
// useQueueFeed.ts
export function useQueueFeed(): {
  shown: QueueResponse | undefined; status: OpStatus; error: ApiError | undefined; isRefetching: boolean;
  changedCount: number; showChanged(): void; retry(): void;
};
```
Algorithm (invariant: the list never moves under the user's eye unless they ask, except when the staffing mode flips):
1. `const q = useOp("getQueue", {}, {pollMs: 10_000, refetchOnFocus: true})`.
2. `shown` state, set from the first `q.data`.
3. On each new `q.data`: if `shown` is undefined → set it. Else if `q.data.staffing.mode !== shown.staffing.mode` → set it (the world changed; no stale line). Else `n = countChangedRows(shown, q.data)`; if `n === 0` → set `shown = q.data` silently (same content); else keep `shown` and expose `changedCount = n`.
4. `showChanged()` sets `shown = q.data`. `retry()` calls `q.refetch()`.
5. On `q.error` with a `shown` already present keep showing `shown` (no error screen on a failed poll); show the error only when there is no `shown`.
**Check:** `npx vitest run src/screens/scr05/queueDiff.test.ts`.

### Step 2 · SCR-5 components
- `useRowKeys.ts`: `useRowKeys(refs: string[], opts: {onOpen(ref: string): void; enabled: boolean}): { cursor: string | null; setCursor(ref: string | null): void }`. One `document` `keydown` listener (added/removed in an effect). Ignore when `e.defaultPrevented`, `e.metaKey/ctrlKey/altKey`, or the target is `input`, `textarea`, `select`, `[contenteditable]`, or inside a `dialog`. `j` → next ref (clamped), `k` → previous (clamped), first press with null cursor selects the first row. `Enter` opens the cursor row **only when `document.activeElement` is `document.body`** (a focused row button handles its own Enter). After a cursor move call `scrollIntoView({block:"nearest"})` on `document.querySelector('[aria-current="true"]')` when the function exists (guard for jsdom). The cursor is a **reference**, so `showChanged()` never moves it; if the reference vanishes clamp to the nearest remaining ref.
- `LiveRow.tsx`: `LiveRow({row, onOpen, onClaimAndJoin?, pending?, compact?, selected?})`. A `<li>` with a main `<button>` (opens the case) and, unless `compact`, a second `Button variant="secondary" density="console"` "Claim and join" (`aria-label` `Claim and join {reference}`, `loading={pending}`). Button content: line 1 reason (600) + `<PriorityTag priority={row.priority}/>`; line 2 `{customer_display_name} · <RefChip reference/> · Waiting since <Time iso={row.queued_at} format="point" variant="meta" fallback={row.age_label ?? ""}/>`. Main button accessible name: `{level} {word lowercased}, {reference}, {reason lowercased}, {owner ?? "unowned"}, waiting since {formatTimePoint(queued_at)}` (e.g. `P3 standard, MHC-C-0012, asked for a person, unowned, waiting since 2:14 pm`). Never any duration or estimate text. `aria-current="true"` when selected. This is G4's own component because the shared `QueueRow` would print "No due time: safety" for a live row (`due_state` is `no_due_time` on live rows).
- `QueueSections.tsx`: `LiveQueueSection({staffing, rows, cursor, onOpen, onClaimAndJoin, pendingRef})` renders: heading "Waiting in chat" (`.t-section`) with a count `Tag`; when `staffing.mode === "nobody_online"` the paragraph "Nobody is on shift, so there is no live queue. Turn on the simulation in the demo guide to try it."; when staffed and `rows.length === 0` the paragraph "Nobody is waiting in chat right now."; else the `LiveRow`s. `NeedsActionSection({rows, cursor, onOpen})`: heading "Needs my action" with count, hint "Safety and danger first, then by due time.", `<ul>` of `<QueueRow row selected={row.reference===cursor} showStaffTags onSelect={onOpen}/>`.
- `Scr05.tsx` (≤ 160 lines): frame as in §4.1; `QueueBody`: `useQueueFeed`, `useRowKeys([...live refs, ...needs refs], {onOpen: open, enabled: true})`, `open = (ref) => navigate(caseHref(ref))`, `onClaimAndJoin = async (ref) => { setPending(ref); try { await claimAndJoin(ref); navigate(caseHref(ref)); } catch (e) { setActionError(errorText(toApiError(e), "claim", role)); } finally { setPending(null) } }`. `h1` "Representative queue". Render order: `h1`, `ActionResult` (router-state result line, see below; or the claim error as a polite line), `StaleLine` ("1 case changed. Show them." / "N cases changed. Show them.", action "Show them" → `showChanged`), `LiveQueueSection`, `NeedsActionSection` or `EmptyState`, the R4 hint (`hidden min-[1100px]:block`, text `J / K to move, Enter to open` using `<Kbd>`). Loading: five `Skeleton height={44}` rows. Error without `shown`: `ErrorLine`. Result line: `useLocation().state as {resultLine?: string} | null`; show for 4000 ms (`setTimeout` in an effect, cleared on unmount) then `navigate(".", {replace:true, state:null})`.
**Check:** `npx vitest run src/screens/scr05` (tests from §7 written alongside).

### Step 3 · SCR-6 state: `caseReducer.ts`, `useCase.ts`
```ts
export interface LocalEvent { id: string; at: string; text: string }
export interface CaseState {
  detail: CaseDetail | null;
  messages: ChatLine[];            // detail.conversation + streamed + sent, de-duplicated by message_id
  events: LocalEvent[];            // event lines (handed back, chat closed, reset, controller changes)
  changedElsewhere: boolean;       // a case_changed event with a newer version, or a shift_ended close
  endedByReset: boolean;
}
export type CaseAction =
  | { type: "loaded"; detail: CaseDetail }                                         // resets everything (also used by Reload)
  | { type: "summary"; summary: CaseSummary }                                      // merge an action response
  | { type: "activity"; activity: Activity; summary: CaseSummary }
  | { type: "live"; live: LiveState; message: ChatLine | null; eventText?: string; eventAt?: string }
  | { type: "stream"; event: CaseEvent };
export const initialCaseState: CaseState;
export function caseReducer(s: CaseState, a: CaseAction): CaseState;
```
Rules (each is a unit test):
1. `loaded`: `{detail, messages: detail.conversation, events: [], changedElsewhere: false, endedByReset: false}`.
2. `summary`: `detail.case = summary` (version, lifecycle, owner, allowed_actions, promise_status, wake_up_at, due_*, priority). Nothing else changes.
3. `activity`: prepend the activity to `detail.activities` and merge `summary`.
4. `live` (a `liveChatAction` response): `detail.live = live`; append `message` if non-null; if `eventText` add a `LocalEvent`. The caller builds `eventText` for hand-back: `Handed back to the assistant at ${formatTimePoint(live.since)}`; for close: `Chat closed at ${formatTimePoint(live.since)}` (SCREEN_SPECS flow states).
5. `stream`: by `event.type`:
   - `customer_message`: append `event.message` unless its `message_id` is already present.
   - `controller_changed`: `detail.live.controller = event.controller.kind`; add `LocalEvent{text: event.line}`.
   - `chat_closed`: `detail.live = {state:"closed", since: event.at, controller:"ai"}`; add `LocalEvent{text:"Chat closed at " + formatTimePoint(event.at)}`; if `event.reason === "shift_ended"` also set `changedElsewhere = true`.
   - `demo_reset`: `detail.live = {state:"closed", since: event.at, controller:"ai"}`; `endedByReset = true`; add `LocalEvent{text: event.line}`.
   - `case_changed`: if `event.version > detail.case.version` set `changedElsewhere = true`.
6. Any action with `detail === null` returns the state unchanged.
```ts
// useCase.ts
export function useCase(reference: string | undefined): {
  state: CaseState; status: OpStatus; error: ApiError | undefined;
  dispatch(a: CaseAction): void; reload(): Promise<void>;
}
```
`useCase`: `useOp("getCase", reference ? {path:{reference}} : null)`; `useReducer(caseReducer, initialCaseState)`; effect on `op.data` identity → `dispatch({type:"loaded", detail: op.data})`; `reload = op.refetch` (the effect then resets the state). **Check:** `npx vitest run src/screens/scr06/caseReducer.test.ts`.

### Step 4 · Stream hook (`useCaseStream.ts`)
`useCaseStream(reference: string | undefined, enabled: boolean, dispatch): { status: StreamStatus }`: `useEventStream(enabled && reference ? {op:"streamCaseEvents", path:{reference}} : null, (data) => { const ev = data as CaseEvent; dispatch({type:"stream", event: ev}); if (ev.type === "customer_message") announce("Customer: " + ev.message.text) })`. `enabled` = detail loaded and no error. Unknown event types are ignored (switch with no default action). **Check:** covered by `Scr06.test.tsx` (fake `openStream`).

### Step 5 · Pure helpers
Write `caseText.ts` (§4.4), `errorCopy.ts` (§4.5), `actionPlan.ts` (§4.6), `wakeUp.ts`, `claimAndJoin.ts`, `useMediaQuery.ts`.
- `wakeUp.ts`: `export function toDemoIso(date: string, time: string): string | undefined` — `date` is `YYYY-MM-DD`, `time` is `HH:mm`; returns undefined if either is empty. Algorithm: (1) wall = `${date}T${time}:00`; (2) `guess = Date.parse(wall + "Z")`; (3) `offsetAt(ms)` = the offset in minutes of America/Chicago at that instant from `Intl.DateTimeFormat("en-US",{timeZone:"America/Chicago",timeZoneName:"longOffset"}).formatToParts(ms)` part `timeZoneName` (`"GMT-05:00"`); (4) `iso = wall + offsetString(offsetAt(guess - offsetAt(guess)*60000))` (recompute at the candidate instant so the DST change day is right); returns e.g. `"2026-10-19T09:00:00-05:00"`. Also `export const TIME_OPTIONS: { value: string; label: string }[]` — every 30 minutes 6:00 am–8:00 pm, `value` `"06:00"`, `label` `"6:00 am"` (12-hour, lowercase; built from `h % 12 || 12` + `am/pm`, not from `Intl`). Tests: `toDemoIso("2026-10-19","09:00") === "2026-10-19T09:00:00-05:00"`; `toDemoIso("2026-11-02","08:00") === "2026-11-02T08:00:00-06:00"`; empty → undefined; `TIME_OPTIONS` has 29 entries, first label "6:00 am", none match `/ |[AP]M/`.
- `claimAndJoin.ts`: `export async function claimAndJoin(reference: string, knownVersion?: number): Promise<{ claim: CaseActionResponse; join: LiveActionResponse }>`: (1) `version = knownVersion ?? (await callOp("getCase",{path:{reference}})).case.version`; (2) `claim = await callOp("applyCaseAction",{path:{reference}, body:{action:"claim", expected_version: version}})`; (3) `join = await callOp("liveChatAction",{path:{reference}, body:{action:"join"}})` **only after step 2 resolved** (CON-13 then CON-14, in that order); a failure in either step throws that `ApiError` unchanged and never retries. Test asserts the call order and the `expected_version`.
- `useMediaQuery.ts`: `useMediaQuery(query: string, fallback = false): boolean` with `window.matchMedia` guarded by `typeof window.matchMedia === "function"` (jsdom has none): returns `fallback` then. `Scr06` uses `useMediaQuery("(max-width: 699px)", false)` for the phone layout and `useMediaQuery("(prefers-reduced-motion: reduce)", false)` for the highlight.

### Step 6 · Split button and header
- `SplitButton.tsx`: `SplitButton({primary, menu, onPrimary, onMenu, busy, moreLabel}: {primary: ActionPlan["primary"]; menu: PlanItem<MenuKey>[]; onPrimary(): void; onMenu(key: MenuKey): void; busy: boolean; moreLabel?: string})`. Built on `@radix-ui/react-dropdown-menu` (installed). Main segment = `Button variant="primary" density="console"` with the primary label (`loading={busy}`); chevron segment = icon `Button` `aria-label="More actions"` opening the menu; the pair shares one 8 px-radius frame with `--btn-primary-split-rule` between them (component tokens in F§Step 3, `tokens.css`). Menu items render `label`; disabled items are `aria-disabled` and show `reason` as a second muted line (Radix `DropdownMenu.Item disabled` plus the description text). When `primary === null` and `menu` has at least one enabled item, render a `Button variant="secondary"` "More actions" trigger instead of the split. When `menu` is empty and `primary` is null render nothing.
- `CaseHeader.tsx`: `CaseHeader({detail, nowIso, plan, onPrimary, onMenu, busy})`. Row 1: `<h1>` pill with `caseTitle(c)` (class `bg-surface-well rounded-tag`, weight 500), `<RefChip reference copyable/>`, the `SplitButton` at the right. Row 2: `dueHeadline(c)` in the `t-time-due` class; a strong `Tag` "Overdue" with `IconClock` when `c.due_state === "overdue"`; "Demo seed" `Tag` when `c.seed`. Row 3 (`text-small`, muted): `createdLine(c)` · `ownerLine(c)`. Row 4: `headerStatusLine(detail, nowIso)` when non-null (`aria-live="polite"`).
- `LifecycleLine.tsx`: `LifecycleLine({lifecycle, staffedPath})`. Steps: `["live_queued"?, "unassigned","claimed","in_progress","waiting","resolved|closed_unresolved"]`. `staffedPath = lifecycle === "live_queued" || detail.live.state !== "not_live"` adds the "Live-queued" first step. If the case is terminal show the single final step (`Resolved` or `Closed unresolved`); otherwise show the combined last step "Resolved / Closed unresolved". Done steps (index < current): `IconCheck` + muted text; current: strong `Tag` with `aria-current="step"`; upcoming muted; chevrons between (`IconChevron`, decorative). `<ol aria-label="Case state">`.
**Check:** `npx vitest run src/screens/scr06/actionPlan.test.ts src/screens/scr06/caseText.test.ts src/screens/scr06/SplitButton.test.tsx`.

### Step 7 · Promise card (`PromiseCard.tsx`)
`PromiseCard({promise})`: `Card` with `CardHeader` (`AssistantMark`-free: use `IconQuote`, title "Promise shown to the customer", `as="h2"`). Body: the exact `promise.text` in `t-lead` (never altered, never mint). Rows (`CardRow`): "Follow up by" → `channelLabel(follow_up.channel)` (or "Not chosen yet" when `follow_up === null`); "Destination" → `${destination_label}` plus a plain `Tag` "On record" / "Not on record"; "Best time" → `bestTimeLabel(window)`. A status `Tag` with `PROMISE_STATUS_LABEL[promise.status]`; when `status === "changed"` a line `Changed: {history.at(-1).reason}` (e.g. "Shift ended before a claim"); a `Disclosure` "History (n)" listing each `history` entry as `<Time format="short" iso={at}/> · {text} ({reason})` when `history.length > 0`. Due time inside the card: `<Time iso={promise.due_at} format="short" fallback={promise.due_label ?? ""}/>` as the row "Due".

### Step 8 · Brief (`BriefView.tsx`, `BriefSection.tsx`, `SourceChip.tsx`)
- `BriefView({brief, sources, onJump})`:
  1. Header line `Brief written by the assistant` (`text-small` muted, with `IconDoc`) — when `brief.status === "ready"`.
  2. `brief.status === "being_written"` → the single sentence **"The brief is being written. The conversation is complete."** instead of the sections (the eight headings are still rendered as skeletons? **No:** sentence only, no section cards), and the index chips are hidden.
  3. `brief.status === "failed"` → `ErrorLine message="The brief couldn't be written. The conversation is complete."` (proposal; no onRetry).
  4. Brief index: a sticky row `nav aria-label="Brief sections"` of eight 32 px chips "1"…"8", each a `<button>` with accessible name = the heading title; click scrolls to and focuses `#brief-{number}`. (`html { scroll-padding-top: var(--sticky-offset) }` is set by the foundation; set `--sticky-offset` to the chip row height via a style on the row's wrapper.)
  5. `<ol>` of eight `BriefSection`s in the order given (the contract always sends eight).
- `BriefSection({heading, sources, onJump})`: a `Card` (`<li id="brief-{n}">`) with header row: numeral `Tag` (`{number}`), `<h3>` title (`heading.title` exactly as sent), and for `checked === false` the strong `Tag` "Customer says · not checked" with `IconQuestion`. Body:
  - `not_generated` or `items.length === 0` → "Nothing recorded." (plain text).
  - Else a list of items; each item text, then (only when `kind` is not `claim`) one `SourceChip` per `source_ids` entry.
  - Visual kind by `heading.key`: `says` → **claims card**: dashed 1 px border (`border-dashed border-border-control`), `bg-surface-well`, no chips (even if `source_ids` were present, render none); `needs` and `told` → items in quotation marks (`“…”`), weight 600, `IconQuote`; `decide` → each item led by `IconQuestion`; `why` and `know` → fact list with chips; `ai_did` and `who` → plain list. Item text is rendered as sent (React text node, never `dangerouslySetInnerHTML`).
  - `heading.trimmed` → under the header a line with `IconInfo` and `heading.trim_note ?? "Something here didn't match the record and was removed."`.
- `SourceChip({source, changed, onJump})`: 28 px `Button`-like `<button>` with `IconDoc` and `source.title`; `changed || source.changed_since` appends a ` · changed` word inside a `Tag` (text, not colour). `onClick` → `onJump(source.source_id)`. A `source_id` with no matching source renders nothing (never an empty chip).
**Check:** `npx vitest run src/screens/scr06/BriefView.test.tsx`.

### Step 9 · Evidence column (`EvidenceColumn.tsx`, `SourceCard.tsx`, `SnapshotTable.tsx`, `ConversationTab.tsx`, `LiveBox.tsx`)
- `EvidenceColumn(props)`: `<aside aria-label="Evidence">`; head `Evidence` (`.t-section`) + the line "What the AI saw, next to what is true now"; `@radix-ui/react-tabs` with triggers `Sources ({sources.length})` and `Conversation`; controlled `value` from props (`tab`, `onTab`) so `Scr06` can switch to Sources on a chip click and to Conversation on join. Below the tabs: "Other cases for this customer" (`other_cases` as links `<a href={caseHref(ref)}>{reference}</a> {status}`; hidden when empty).
- `SourceCard({source, asOf, highlighted})`: `Card` with `id={"src-" + source.source_id}` `tabIndex={-1}`; header: `IconDoc` + title; meta line (mono 12 px) `{source.ref} · {source.version_label}`; `staff_only` → `Tag` "Staff only". Body: `current_unavailable` → "This record can't be read right now; the snapshot is shown alone." followed by the snapshot rendered alone. Tail under a dashed rule: `changed_since` → `IconInfo` + `changed_note` at weight 600; else `IconCheck` + (`changed_note ?? "No change since the snapshot"`), with the sentence ending as given (no added full stop); nothing when `current_unavailable`. `highlighted` adds the landed wash class (`bg-surface-selected` for 1.2 s via a timeout in `Scr06`; no animation).
- `SnapshotTable({snapshot, current, asOf, unavailable})`:
  1. If `snapshot` has exactly one key `passage` (a KB source): `<blockquote>` of the snapshot passage on `bg-surface-well`; when `current` exists and differs, a second labelled blockquote "Now".
  2. Else a `<table>` with a visually hidden `<caption>` "What the AI saw and what is true now", `th scope="col"` headers: *(field)* · "What the AI saw" · `Now · {formatTimePoint(asOf)}` (omit the Now column when `unavailable`). Rows = union of keys in snapshot order; field label `humanizeKey(key)` in `th scope="row"`; values `String(v)`, right-aligned tabular. A row is *changed* when `String(snapshot[k]) !== String(current[k])`: its Now cell is weight 600 followed by a strong `Tag` "Changed since" with `IconInfo`; the "What the AI saw" cell keeps normal weight and is **not struck through**. Wrap the table in `overflow-x-auto`.
  (The contract carries no snapshot time; the column header omits one. Record as a contract request in §8.)
- `ConversationTab({messages, events, live, endedByReset})`: merge `messages` and `events` sorted by `at` (stable). Each message → `<MessageRow speaker={m.speaker} at={m.at} layout="flat">{m.text}</MessageRow>`; each local event → `<EventLine at={e.at}>{e.text}</EventLine>`. `aria-live="polite"` on the list. Below: `LiveBox` when `live` mode is not `hidden`.
- `LiveBox({mode, ownerName, onSend, onHandBack, onClose, error, endedByReset, busy})`: `Card`. Head row: when `endedByReset` → "This chat ended because the demo was reset." (no field); when `mode === "active"` → `You are replying as ${ownerName} (demo representative). The assistant is paused.` (`ownerName` = `detail.case.owner`; if null omit the name: "You are replying as the demo representative. The assistant is paused."); when `mode === "disabled"` → "This chat is no longer live." Body: `TextArea` (label "Reply", visible `<label>`), `Button variant="send" density="console"` "Send", `Button variant="secondary"` "Hand back to the assistant", `Button variant="secondary"` "Close the chat"; all disabled unless `mode === "active"` and not `busy`. Send posts `{action:"send", text}` and on success clears the field and focuses it. `error` shows `errorText(...)` under the box (polite).
**Check:** `npx vitest run src/screens/scr06/SnapshotTable.test.tsx src/screens/scr06/LiveBox.test.tsx`.

### Step 10 · Action area, forms, activity log
- `ActionResult.tsx`: `ActionResult({id, children})` — `<div ref tabIndex={-1} id={id}><ResultLine>{children}</ResultLine></div>`; exports `focusResult(id)` which focuses that wrapper (called after every successful action).
- `ActionArea.tsx`: `ActionArea({detail, plan, role, onOpenForm, openForm, onSubmit, error, resultLine, busy})`. Renders: `plan.readOnly` → the quiet line "Read-only for the business owner role" and nothing else; else the bar buttons as `Button variant="secondary" density="console"`, a disabled one is `aria-disabled` + `title`-free visible hint (`<p class="text-small muted">` under the button row listing each disabled button's `reason`, deduplicated). The open form (one at a time) renders below the buttons in a `bg-surface-well` block. Then `error` (polite line, with a "Reload" `Button variant="text"` when `offerReload`), then `ActionResult`, then `ActivityLog`.
- `ActionForms.tsx` (≤ 300 lines): one small component per form, all with the same props `{onSubmit(values), onCancel(), busy, error?: string}`; each has a first field that receives focus on mount, Escape cancels, `Button variant="primary"` submit (only one primary in the block) and "Cancel" text button:
  - `ReleaseForm` (label "Reason", `TextArea`, submit "Release"): body `{action:"release", expected_version, reason}`.
  - `WaitForm` (fields "Wake-up date" `<input type="date">` with `min` = date part of `nowIso` converted to Chicago, "Wake-up time" `<select>` of `TIME_OPTIONS` with a blank first option "Choose a time", "Reason" optional `TextInput`; submit "Set waiting"): body `{action:"wait", expected_version, wake_up_at: toDemoIso(date,time), reason?}`; `wake_up_at` is omitted when either field is empty (the server answers `WAKE_UP_REQUIRED`).
  - `ResolveForm` (label "Outcome", `TextArea`, submit "Resolve"): `{action:"resolve", expected_version, outcome}`.
  - `CloseForm` (label "Reason", submit "Close unresolved"): `{action:"close_unresolved", expected_version, reason}`.
  - `ContactForm({kind})` (title "Log a call" / "Log an email"; outcome radios "Reached the customer" (`reached`), "No answer" (`no_answer`), "Left a message" (`left_message`) — native radios in a `fieldset` with `legend` "Outcome"; "Note" `TextArea` optional; hint "Demo: recorded, not sent. No call is placed." for call and "Demo: recorded, not sent." for email; submit "Record"): `callOp("recordContactActivity", {path, body:{kind, outcome, note?, expected_version}})`. Outcome radio default: none selected (a missing outcome is a `VALIDATION_ERROR` shown as "That didn't go through. Try again." — acceptable; the radio group is `required`).
  - `FlagForm` (legend "What is wrong": radios "An answer was wrong" (`answer`), "The brief left something out" (`brief`), "The escalation was not needed" (`escalation`); "Note" optional `TextArea`; submit "Add to review list"): `callOp("createFlag", {body:{case_ref, target, reason?: note, message_id?}})`; `message_id` = the `message_id` of the last assistant line in `messages` when `target === "answer"`, else omitted. Success text is the fixed string **"Added to the review list."**
  - `AssignForm` (supervisor; select "Assign to" with options `riley` → "Riley (demo representative)" and `supervisor` → "Demo supervisor"; "Reason" `TextArea`; submit "Assign"): `{action:"assign", expected_version, assignee, reason}`.
  - `PriorityForm` (supervisor; select "Priority" P0–P4 shown as "P0 · Safety", "P1 · Danger", "P2 · Time-sensitive", "P3 · Standard", "P4 · Routine"; "Reason" `TextArea`; submit "Change priority"): `{action:"change_priority", expected_version, priority, reason}`.
  `expected_version` always comes from `state.detail.case.version` at submit time.
- `ActivityLog.tsx`: `ActivityLog({activities})` — heading "Activity" (`h2`), `<ul>` newest first (sort by `at` descending); each item: a 56 px time column `<Time iso={at} format="point" variant="row"/>`, then `${kindWord} · ${outcomeWord}` where kindWord = "Called" / "Emailed" and outcomeWord = "Reached the customer" / "No answer" / "Left a message", then the note when present, then the fixed `activity.label` ("Demo: recorded, not sent") on every entry. Empty list → "No activity yet." Claims and releases are not in `activities` (the contract carries contacts only), so the log shows contacts only; say so in the group file.
**Check:** `npx vitest run src/screens/scr06/ActionForms.test.tsx`.

### Step 11 · Page assembly (`Scr06.tsx`, `RailColumn.tsx`)
`Scr06.tsx` (≤ 250 lines; wiring only). `CaseBody`:
1. `reference = useParams().reference`; `role = useSession().role`; `nowIso = useDemoStatus().clock?.now`.
2. `const c = useCase(reference)`; `useCaseStream(reference, !!c.state.detail, c.dispatch)`.
3. `plan = c.state.detail ? planActions(c.state.detail, role) : null`.
4. `useAction`-less writes through a local `run(actionKey, fn)` helper: sets `busy`, clears `error`/`resultLine`, awaits `fn()`, then dispatches the right reducer action, sets `resultLine`, calls `announce(resultLine)` and `focusResult("case-result")`; on `ApiError` sets `error = errorText(e, actionKey, role)`.
   - Primary / menu `claim`: `applyCaseAction` claim → `dispatch({type:"summary", summary: res.case})`, `resultLine = res.result_line`.
   - `claim_and_join`: `claimAndJoin(reference, detail.case.version)` → `dispatch(summary: claim.case)`, then `dispatch({type:"live", live: join.live, message: join.message})`, then **`await c.reload()`** (the post-join `getCase` supplies the joined `allowed_actions`; the joined state is the server's), then switch the evidence tab to Conversation.
   - `resolve` and `close_unresolved` success → `navigate("/staff/queue", {state:{resultLine: res.result_line}})` (SCREEN_SPECS: redirect to the queue with the success line). Owner cannot reach this.
   - `wait`, `release`, `start`, `assign`, `change_priority` success → `summary` + result line.
   - `recordContactActivity` → `dispatch({type:"activity", activity, summary})`, `resultLine = `${kindWord} · ${outcomeWord} · ${activity.label}``.
   - `createFlag` → `resultLine = "Added to the review list."`.
   - `liveChatAction` `send` → `live` dispatch with `message`; `hand_back` → `live` with `eventText`; `close` → `live` with `eventText`; `join` (only via the "Join chat" bar button for a claimed live-queued case) → then `reload()` as above.
5. Branches (one `h1` each): `reference` undefined → `EmptyState title="Pick a case from the queue."` (rail still rendered); `c.status === "loading"` with no detail → layout skeleton (header block, eight section skeletons `Skeleton height={96}`, evidence skeleton `height={240}`), buttons absent; `c.error?.code === "CASE_NOT_FOUND"` → `EmptyState title={"No case " + reference + "."} body="It may have been cleared by a demo reset."` combined so the page reads `No case MHC-C-0099. It may have been cleared by a demo reset.` (a single sentence node; test with `getByText`), plus `Button` link "Back to the queue"; other `c.error` → `ErrorLine message="The case didn't load. Try again." onRetry={c.reload}`.
6. Layout (`min-[1100px]:grid-cols-[var(--col-queue)_minmax(0,1fr)_var(--col-evidence)]`): rail (`<nav aria-label="Queue" id="queue-rail">`, via `RailColumn`, only when role is representative or supervisor) | `<Main>` (back link, `CaseHeader`, `LifecycleLine`, `StaleLine` when `changedElsewhere` ("This case changed. Show the latest." with action "Reload" → `c.reload`), reload line after VERSION_CONFLICT, `PromiseCard`, `BriefView`, `ActionArea`) | `EvidenceColumn`. Below 700 px (`useMediaQuery`) render a top-level two-tab control "Brief" / "Evidence" (Radix Tabs) and show only the active column; chip click sets it to Evidence. A skip link "Go to queue" (`href="#queue-rail"`, visible on focus) is the first element inside `<Main>`.
7. Source-chip jump: `onJump(id)`: set tab to Sources (and the phone tab to Evidence), then after the next paint `document.getElementById("src-" + id)?.scrollIntoView({block:"nearest", behavior: reduced ? "auto" : "smooth"})`, `.focus()`, set `highlight = id` and clear it after 1200 ms (no highlight timer animation under reduced motion: still set the class, no transition).
8. Live auto-switch: an effect on `detail.live.state` transition to `"joined"` sets the tab to Conversation once.
9. Announce `Now viewing case {reference}` is not needed; `document.title` set as in the stub.
- `RailColumn.tsx`: `RailColumn({currentRef})`: `useOp("getQueue", {}, {pollMs:10000})`; renders the compact list: `LiveRow compact` for `live` rows and `QueueRow` for `needs_my_action`, `selected={ref === currentRef}`, `onSelect → navigate(caseHref(ref))`; on narrow widths wraps in `Disclosure` with summary `Queue · {n} cases` (`n = live.length + needs.length`). Error → `ErrorLine message="The queue didn't load. Try again."`. Not rendered for the owner.
**Check:** `npx vitest run src/screens/scr06` then `npm run typecheck`.

### Step 12 · Group file and mid-point gates
Fill the group file sections that are known. Run `npm run lint && npm run typecheck && npx vitest run src/screens/scr05 src/screens/scr06 src/styles`. Fix everything; `react-hooks/exhaustive-deps` warnings are errors in review.

### Step 13 · Dev layer: stream scripts (`src/dev/stream/case-scripts.ts`)
`export const caseScripts: Record<string, StreamScript>` (type from `src/dev/stream/types.ts`: `{thread?, steps: {afterMs, event: unknown}[], dropAfterMs?}`). Each script has `thread` = the case reference it targets and `event_id`s starting at 31 (the OpenAPI's `Last-Event-ID` example is 30). Events are typed `CaseEvent` (`satisfies components["schemas"]["CaseEvent"]`), so a schema change breaks the build.
| Script key | Steps | Source of the values |
|---|---|---|
| `customerReply` | +4000 ms `customer_message` {message_id "m-90", speaker {kind "customer", display_name "You"}, at "2026-10-16T14:23:10-05:00", text "Thanks, that helps."} | OpenAPI `streamCaseEvents` `FRAMES`, first frame (copy the values; ids differ) |
| `replyThenClosed` | `customerReply` + 3000 ms `chat_closed` {reason "closed_by_staff", at "2026-10-16T14:24:00-05:00"} | `FRAMES` second frame |
| `handedBack` | +3000 ms `controller_changed` {controller {kind "ai", display_name null}, line "Handed back to the assistant at 2:22 pm", at "2026-10-16T14:22:00-05:00"} | `// dev fixture: no named example` (the `HANDED_BACK` live response carries `since` 14:22) |
| `resetEnded` | +3000 ms `demo_reset` {line "This chat ended because the demo was reset.", at "2026-10-16T14:25:00-05:00"} | `// dev fixture` (SCREEN_SPECS flow state wording) |
| `caseChangedElsewhere` | +3000 ms `case_changed` {version 4, lifecycle "claimed", at "2026-10-16T14:31:00-05:00"} | `// dev fixture`; version 4 and 14:31 mirror the VERSION_CONFLICT example's `current_version` / `changed_at` |
| `shiftEnded` | +3000 ms `chat_closed` {reason "shift_ended", at "2026-10-16T14:26:00-05:00"}, +500 ms `case_changed` {version 4, lifecycle "unassigned"} | `// dev fixture` |
Every fixture event carries a comment naming either the OpenAPI example it copies or `// dev fixture: no named example in the OpenAPI (foundation plan §8.2)`.

### Step 14 · Dev layer: case store and director (`directors/case-store.ts`, `directors/case-actions.ts`) — **needs FR-1**
Confirm FR-1 is in the foundation (`grep -n "pickCaseCall" src/dev/directors/index.ts src/dev/resolve.ts`). If not present, **stop here, skip Steps 14 and 15**, build Step 16 with forced-example scenarios only (single-example forces, sequences for continuity), write the gap into the group file and the report, and mark the report `PARTIAL`.

**FR-1 contract (what the foundation provides):** in `src/dev/directors/index.ts`
```ts
export interface CaseCall { op: OperationId; reference: string | null; body: unknown; world: World }
export interface CasePick { example: string; status?: number; transform?: (body: any) => any }   // status only to disambiguate; transform is applied to whatever JSON body returns for that pick, errors included
export type CasePicker = (call: CaseCall) => CasePick | undefined;
export function pickCaseCall(call: CaseCall): CasePick | undefined;   // returns the first defined result of `casePicker` from ./case-actions
```
and `resolve.ts` step 6b (between today's steps 6 and 7): for `op ∈ {getQueue, getCase, applyCaseAction, liveChatAction, recordContactActivity}` with no explicit force, call `pickCaseCall({op, reference: <the "reference" path param parsed from ctx.path, else null>, body: ctx.body, world})`; a defined pick resolves to Prism with `Prefer: code=<status>, example=<example>` and its `transform`. **G4 exports** `export const casePicker: CasePicker` from `case-actions.ts`.

`case-store.ts` (pure data + the replica of server rules; every function unit-tested):
```ts
export interface CaseOverride {
  lifecycle?: CaseSummary["lifecycle"]; owner?: string | null; version?: number; wake_up_at?: string | null;
  promise_status?: CaseSummary["promise_status"]; priority?: CaseSummary["priority"];
  live?: LiveState; activities: Activity[]; messages: ChatLine[]; resolvedSummary?: string;
}
export function getOverride(ref: string): CaseOverride | undefined;
export function patchOverride(ref: string, patch: Partial<CaseOverride>): CaseOverride;   // creates on first write; activities/messages append
export function resetCaseStore(): void;
export interface CatalogRow { reference: string; reason: string; priority: Priority; customer: string; created_at: string; due_at: string|null; due_label: string|null; due_state: QueueRow["due_state"]; follow_up_short: string|null; lifecycle: QueueRow["lifecycle"]; queued_at: string|null }
export const CATALOG: Record<string, CatalogRow>;     // MHC-C-0005, 0006, 0007, 0008, 0012: values copied from the OpenAPI getQueue SEEDED and STAFFED_WITH_WAITING examples (cite them in a comment). MHC-C-0009: copied from the getCase FEE_BEARING_CHANGE example (reason "Fee-bearing change request", P2 Time-sensitive, due_at "2026-10-17T12:00:00-05:00", due_label "Sat Oct 17 · 12:00 pm, the window start", created_at "2026-10-16T14:14:00-05:00").
export function allowedFor(lifecycle: CaseSummary["lifecycle"], role: Role, liveState: LiveState["state"]): CaseSummary["allowed_actions"];
```
`allowedFor` replicates the examples (comment `// dev replica of the server rules, derived from the CLAIMED / LIVE_JOINED / WAITING / ASSIGNED / DEFAULT examples`):
- `unassigned`: rep `["claim","flag"]`; supervisor `["claim","assign","change_priority","flag"]`.
- `live_queued`: rep `["claim_and_join","claim","flag"]`; supervisor as unassigned.
- `claimed` or `in_progress` and `liveState === "joined"`: `["send_live_message","hand_back","close_chat","log_call","log_email","wait","resolve","close_unresolved","release","flag"]`.
- `claimed` or `in_progress` otherwise: `["start","log_call","log_email","wait","resolve","close_unresolved","release","flag"]` (drop `start` for `in_progress`); a claimed case with `liveState === "queued"` also inserts `"join_chat"` after `"log_email"`.
- `waiting`: `["start","release","flag"]`. `resolved` / `closed_unresolved`: `["flag"]`.
- Supervisor in claimed/in_progress/waiting additionally gets `"assign","change_priority"` before `"flag"`. `owner` → `[]` for every state.

`case-actions.ts` — `casePicker(call)` by `call.op` (numbered; the first matching rule wins; **picks are pure; every store write happens inside a `transform`, which runs only if the response is actually delivered**):
1. **`getQueue`**: example `world.staffing === "simulated_on_shift" ? "STAFFED_WITH_WAITING" : "SEEDED"`. Transform: for each row in `live` and `needs_my_action` apply `getOverride(row.reference)` (lifecycle, owner, wake_up_at, priority); drop rows whose lifecycle is `resolved` or `closed_unresolved`; move a `live` row whose lifecycle is no longer `live_queued` into `needs_my_action` (append, keep `created_at`, set `queued_at: null`).
2. **`getCase`**: `ref = call.reference`.
   1. `ref === "MHC-C-0007"` → `DEFAULT`; `"MHC-C-0008"` → `SAFETY_CASE`; `"MHC-C-0009"` → `FEE_BEARING_CHANGE`.
   2. `ref` in `CATALOG` otherwise (0005, 0006, 0012) → `DEFAULT` with the *reskin* transform (below).
   3. Anything else (including `MHC-C-0099`) → `{example:"CASE_NOT_FOUND", status:404, transform: (b) => ({...b, error:{...b.error, details:{reference: ref}}})}`.
   Then every successful pick's transform runs `applyOverride(ref, role)`: set `case` fields from `getOverride(ref)` (lifecycle, owner, version, wake_up_at, promise_status, priority); `live` from the override; append override `activities` (dedupe by `activity_id`) and `messages`; **then recompute `case.allowed_actions = allowedFor(case.lifecycle, world.role, live.state)`** (so the supervisor and owner views are derived, and the owner gets `[]`). *Reskin* (for refs without a named example): `case` ← `CATALOG[ref]` fields (reference, reason, priority, created_at, due_*, owner null, lifecycle from the catalog, seed `ref !== "MHC-C-0012"`); `brief.headings[*].items = []` (titles unchanged: every section reads "Nothing recorded."); `sources = []`; `conversation = []`; `promise.text = promise.text.replace("MHC-C-0007", ref)`, `promise.due_at/due_label` from the catalog; for `MHC-C-0012` also `live = {state:"queued", since: CATALOG.queued_at, controller:"ai"}`.
3. **`applyCaseAction`** (`body` is `CaseActionRequest`): validate in this order, each returning an error pick (no transform unless stated): (a) `release`, `assign`, `change_priority`, `close_unresolved` with an empty `reason` → `REASON_REQUIRED` (422); (b) `wait` without `wake_up_at` → `WAKE_UP_REQUIRED` (422); (c) `resolve` with an empty `outcome` → `OUTCOME_REQUIRED` (422); (d) when the store has an override and `action` is not covered by `allowedFor(...)` (map `claim`→"claim", `release`→"release", `start`→"start", `wait`→"wait", `resolve`→"resolve", `close_unresolved`→"close_unresolved", `assign`→"assign", `change_priority`→"change_priority"): `claim` on a case that is not unassigned/live_queued → `CASE_ALREADY_CLAIMED` (409), anything else → `NOT_ALLOWED_IN_STATE` (409). With no override the request is accepted (permissive: a forced snapshot is not in the store). Success picks: `claim`→`CLAIMED`, `wait`→`WAITING`, `resolve`→`RESOLVED`, `assign`→`ASSIGNED`, `change_priority`→`PRIORITY_CHANGED`, and for `release`, `start`, `close_unresolved` (no named example) → `CLAIMED` with a reshaping transform. The success transform: `next = nextState(ref, body, world)` (below) → `patchOverride(ref, next)`; set `body.case = {...catalogBase(ref), ...next, allowed_actions: allowedFor(next.lifecycle, world.role, next.live.state)}` and `body.result_line` per the table; `catalogBase(ref)` = the case summary skeleton from `CATALOG[ref]` (reference, reason, priority, created_at, due_*, due_state, seed, promise_status default `open`).
   | action | next lifecycle / owner / other | `result_line` |
   |---|---|---|
   | claim | `claimed`; owner = `world.role === "supervisor" ? "Demo supervisor" : "Riley"`; version+1 | rep: the example's "Claimed · Riley (demo)"; supervisor: `Claimed · Demo supervisor` |
   | start | `in_progress`; `wake_up_at: null` | `Picked back up.` `// dev fixture: no named example` |
   | wait | `waiting`; `wake_up_at = body.wake_up_at` | `Waiting until ${formatDateTimeShort(body.wake_up_at)}` (matches the WAITING example "Waiting until Mon Oct 19 · 9:00 am") |
   | resolve | `resolved`; `promise_status = Date.parse(demoNow) > Date.parse(due_at) ? "missed" : "kept"` | the example's "MHC-C-0007 resolved." with the reference replaced: `${ref} resolved.` |
   | close_unresolved | `closed_unresolved` | `Closed unresolved.` `// dev fixture` |
   | release | `unassigned`; owner null | `Released.` `// dev fixture` |
   | assign | `claimed` if it was `unassigned`; owner `body.assignee === "riley" ? "Riley" : "Demo supervisor"` | `Assigned to ${owner} (demo).` for riley (example: "Assigned to Riley (demo).") |
   | change_priority | priority = `{level: body.priority, word: WORD[level]}` with `WORD = {P0:"Safety",P1:"Danger",P2:"Time-sensitive",P3:"Standard",P4:"Routine"}` | `Priority is now ${level} · ${word}.` (matches the PRIORITY_CHANGED example) |
   `demoNow` for the resolve rule: the `CASE` skeleton has no clock; use the constant `DEMO_NOW = "2026-10-16T14:20:00-05:00"` (the demo clock's start; comment it).
4. **`liveChatAction`** (`body` is `LiveActionRequest`): `join` → if the override exists and is `unassigned`/`live_queued` → `NOT_CLAIMED_BY_YOU` (403); else `JOINED`, transform `patchOverride(ref, {lifecycle:"in_progress", live:{state:"joined", since, controller:"human"}})`. `send` with an empty `text` → `VALIDATION_ERROR` (400); if the override says `live.state` is `handed_back` or `closed` → `NOT_LIVE` (409) with transform setting `details.reason` to `"closed"`; else `SENT` with transform `message.text = body.text`, `patchOverride(ref,{messages:[message]})`. `hand_back` → `HANDED_BACK` (when not live per override → `NOT_LIVE`), transform `patchOverride(ref,{live: response.live})`. `close` → `CLOSED`, same. No override entry means permissive success.
5. **`recordContactActivity`** (`body` is `ActivityRequest`): if an override exists and the case is not `claimed`/`in_progress` → `NOT_ALLOWED_IN_STATE` (409). Else `body.kind === "email" ? "EMAIL_LEFT_MESSAGE" : "CALL_REACHED"`, transform: `activity.kind/outcome/note` from the request, `activity.activity_id = "act-" + (n + 17)` where `n` = the override's activity count (so ids stay unique), `case` rebuilt as in rule 3 with the same lifecycle, `patchOverride(ref, {activities:[activity]})`. `activity.at`, `by`, `label` stay as in the example.
6. Everything else → `undefined` (falls through to the foundation defaults).
`reactions/scr06.ts`: `export const reactions: Reaction[] = [{ when: {op: "resetDemo", status: 200}, then: () => resetCaseStore() }]` (reset restores the seeds, FLOW-12; the foundation's shared reaction already resets the world, role and refetch).
**Check:** `npx vitest run src/dev/directors` (tests in §7 and a smoke through `resolveCall` once FR-1 landed: `resolve.test.ts` is the foundation's; write a G4 test that calls `casePicker` directly, not `resolveCall`).

### Step 15 · Dev layer: scenarios (`scenarios/case-transforms.ts`, `scr05.ts`, `scr06.ts`)
`case-transforms.ts` exports pure helpers (each unit-tested in `case-actions.test.ts`): `claimedByMe(body)` (lifecycle "claimed", owner "Riley", version 4, `allowed_actions` = the CLAIMED example's list), `emptyHeadings(numbers: number[])`, `queueChange(refs: Record<string, Partial<QueueRow>>)` (returns a transform over a `QueueResponse`), `moveLiveToNeeds()` (sets `live: []`, appends each live row to `needs_my_action` with `lifecycle:"unassigned"`, `queued_at:null`, `age_label:null`, and `staffing` → `{mode:"nobody_online", label:"Nobody online", banner:null}`), `addNeedsRow(row)`, `stuckWaiting(isoWake)`, `shiftEndedPromise()`.
`scr05.ts` and `scr06.ts` export `screenScenarios: ScreenScenarios` with `complete: true` **only after** the scenario list in §6 is fully written and `scenarios.integrity.test.ts` plus `scenarios.coverage.test.ts` pass (the coverage test fails if any real standard state of SCR-5 / SCR-6 has no scenario). Every scenario: `id` = `scr05.<kebab>` / `scr06.<kebab>`, `screen`, `state`, `flowState` (exact first-column text from the SCREEN_SPECS flow table when it is a flow state), `label`, `route` (concrete), `role`, `staffing`, `ops` (via `OpForce`), `stream` (from `caseScripts`), `notes` (how to reach what a pure force cannot). Use only example names that exist in `OPS[op].responses` (the integrity test checks).
**Check:** `npx vitest run src/dev/scenarios.integrity.test.ts src/dev/scenarios.coverage.test.ts src/dev/directors`.

### Step 16 · Interactive verification (Chrome DevTools MCP; no screenshots committed)
Start `npm run mock` and `npm run dev:mock` in the background (remember the PIDs; stop only those). Open `http://127.0.0.1:5184/login?...` is not needed: use `?signedin=1&role=representative`. For each scenario in §6 open `/staff/queue?signedin=1&role=representative&scenario=<id>` (the id's route is applied by the switcher) and check it by eye against the table's "Expect". Resize to 1280, 800 and 390 for SCR-5 default and SCR-6 default: three columns at 1280; drawer at 800; tabs "Brief · Evidence" and 44 px buttons at 390; no horizontal page scroll (only the snapshot table scrolls inside itself); focus rings visible when tabbing through the split button, forms and tabs; no red; all times 12-hour. Walk the live flow: staffing on, queue, "Claim and join", reply arrives (stream), Send, Hand back, Close, Resolve → queue shows "MHC-C-0007 resolved." for ~4 s and the row is gone. Fix defects in owned files. Stop both servers.

### Step 17 · Group file and final gates
Complete `docs/ux/04-prototype/groups/g4-staff-queue-case.md`: *Built* (files), *States and how they are reached* (copy §6 with the final scenario ids), *Mock artefacts* (§8.2 list below), *Requests to the integrator* (FR-1…FR-5 with their status), *Deviations*, *Checks* (the §7 output). Then run the §7 final gate list once.

## 6. Data and fixtures

Synthetic only. **Every value comes from the OpenAPI named examples** (Omar Patel, Dana Whitaker, Marcus Hill, MHC-C-0005…0009, 0012, INV-204411, Riley, Demo supervisor, the demo clock `2026-10-16T14:20:00-05:00`). The only values the dev layer adds are marked `// dev fixture` (§5 Steps 13–15) and listed under *Mock artefacts*.

**Test fixtures:** `scr06/specExample.ts` exports `specExample<T>(path: string, method: "get"|"post", status: string, name: string): T` — reads the OpenAPI file once with the `yaml` package (v2; ISO timestamps stay strings) using `readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../../../docs/ux/03-structure/ui-contracts.openapi.yaml"), "utf8")` (5 `..` from `apps/web/src/screens/scr06/` reach the repo root; use string paths, never a `URL` object, because jsdom replaces `URL`), and returns `paths[path][method].responses[status].content["application/json"].examples[name].value`. `queue.fixtures.ts` and `case.fixtures.ts` wrap it: `seededQueue()`, `staffedQueue()`, `caughtUpQueue()`, `pendingBriefQueue()`, `defaultCase()`, `liveJoinedCase()`, `waitingCase()`, `safetyCase()`, `briefPendingCase()`, `trimmedCase()`, plus `claimedResponse()`, `waitingResponse()`, `resolvedResponse()`, `joinedResponse()`, `sentResponse()`, `callReachedResponse()` and `apiErrorBody(name)` for the 4xx examples. Tests then use `makeFakeTransport` / `jsonResponse` from `src/test/fakeTransport.ts` (F§Step 5) and `renderWithProviders` from `src/test/render.tsx` (F§Step 6; its `role` option picks the session).

### 6.1 SCR-5 states and how each is reached (matrix cells: all 8 real)

| Scenario id | Cell / flow state | Role · staffing | `ops` force | How reached / Expect |
|---|---|---|---|---|
| `scr05.default` | default | rep · off | `getQueue: {example:"SEEDED"}` | four rows in server order (0008 P0 first); R2 shows the nobody-online sentence; Overdue tag on 0005 |
| `scr05.empty` | empty | rep · off | `getQueue: {example:"ALL_CAUGHT_UP"}` | "You're all caught up…" text |
| `scr05.loading` | loading | rep | `getQueue: {hang:true}` | header + five skeleton rows |
| `scr05.partial-brief-pending` | partial | rep | `getQueue: {example:"BRIEF_BEING_WRITTEN"}` | row shows "Brief being written" |
| `scr05.error` | error | rep | `getQueue: {sequence:[{fail:"network"},{example:"SEEDED"}]}` | "The queue didn't load. Try again."; Try again succeeds |
| `scr05.stale-cases-changed` | stale | rep | `getQueue: {sequence:[{example:"SEEDED"},{example:"SEEDED", transform: queueChange({"MHC-C-0006":{owner:"Demo supervisor", lifecycle:"claimed"}, "MHC-C-0005":{owner:"Demo supervisor", lifecycle:"claimed"}})}]}` | wait 10 s or refocus the tab: "2 cases changed. Show them."; the cursor row does not move |
| `scr05.success-resolved-return` | success | rep | `getCase: {example:"DEFAULT", transform: claimedByMe}` , route `/staff/cases/MHC-C-0007` | notes: "Resolve with any outcome (e.g. type one word) to land on `/staff/queue` with the 4 s line `MHC-C-0007 resolved.`; with the case director active the row is also gone" (the director hook, FR-1, removes it; without FR-1 the row stays: say so in the report) |
| `scr05.success-claimed-row` | success | rep | `getQueue: {example:"SEEDED", transform: queueChange({"MHC-C-0007":{owner:"Riley", lifecycle:"claimed"}})}` | the row's owner reads "Riley" |
| `scr05.disabled-no-live-queue` | disabled | rep · off | `getQueue: {example:"SEEDED"}` | R2 sentence "Nobody is on shift, so there is no live queue…" |
| `scr05.live-queued` | default (flow "live-queued customer (FLOW-8)") | rep · on | `getQueue: {example:"STAFFED_WITH_WAITING"}` | R2 row MHC-C-0012 "Waiting since 2:14 pm" with "Claim and join" |
| `scr05.new-handoff` | stale (flow "new handoff from the chat (FLOW-7)") | rep · off | `getQueue: {sequence:[{example:"SEEDED"},{example:"SEEDED", transform: addNeedsRow(<the MHC-C-0012 row copied from STAFFED_WITH_WAITING with lifecycle "unassigned">)}]}` | after 10 s: "1 case changed. Show them." |
| `scr05.shift-ended` | stale (flow "shift ended before claim (FLOW-8)") | rep · on | `getQueue: {sequence:[{example:"STAFFED_WITH_WAITING"},{example:"STAFFED_WITH_WAITING", transform: moveLiveToNeeds()}]}` | after 10 s the staffing flips to nobody online and the row moves to Needs my action with its original `created_at` (the mode flip applies without a stale line, Step 1 rule 3) |
| `scr05.overdue-after-advance` | stale (flow "overdue after the clock advances (FLOW-10)") | rep | `getQueue: {sequence:[{example:"SEEDED"},{example:"SEEDED", transform: queueChange({"MHC-C-0006":{due_state:"overdue"}})}]}` | after 10 s: "1 case changed. Show them." then the Overdue tag on 0006 |
| (customer role) | — | customer | none | the F-12 sentence from `RoleGate`, no `getQueue` call (shared `shared.*` scenarios and the role select reach it) |
| (reset, FLOW-12) | — | any | none | `resetDemo` reaction; reach via SCR-3's reset; seeds return |

All SCR-5 routes are `/staff/queue`.

### 6.2 SCR-6 states and how each is reached (matrix cells: all 8 real). Default role rep; route `/staff/cases/MHC-C-0007` unless stated.

| Scenario id | Cell / flow state | Role · staffing | Forces / derivation | Expect |
|---|---|---|---|---|
| `scr06.default` | default | rep | none (director: `DEFAULT`) | Claim split button; Sources tab; Demo seed; Join chat disabled with its reason |
| `scr06.empty-nothing-recorded` | empty | rep | `getCase: {example:"DEFAULT", transform: emptyHeadings([5,7])}` | sections 5 and 7 read "Nothing recorded." |
| `scr06.no-case` *(only if FR-2 is accepted)* | empty | rep | route `/staff/cases`; none | "Pick a case from the queue." with the rail |
| `scr06.loading` | loading | rep | `getCase: {hang:true}` | header + eight section skeletons + evidence skeleton |
| `scr06.partial-brief-pending` | partial | rep | `getCase: {example:"BRIEF_BEING_WRITTEN"}`, `getQueue: {example:"BRIEF_BEING_WRITTEN"}` | "The brief is being written. The conversation is complete."; Conversation tab full |
| `scr06.partial-source-unavailable` | partial | rep | none (`DEFAULT` already has `src-faq` unreadable) | the FAQ card reads "This record can't be read right now; the snapshot is shown alone." |
| `scr06.partial-trimmed` | partial | rep | `getCase: {example:"TRIMMED_STOP"}` | section 3 shows "Something here didn't match the record and was removed." |
| `scr06.error-not-found` | error | rep | route `/staff/cases/MHC-C-0099`; none (director → `CASE_NOT_FOUND`); with FR-1 absent: `getCase: {example:"CASE_NOT_FOUND"}` | "No case MHC-C-0099. It may have been cleared by a demo reset." + Back to the queue |
| `scr06.error-owner-readonly` | error | **owner** | none: the director recomputes `allowed_actions = []` for the owner role. With FR-1 absent: `getCase: {example:"DEFAULT", transform: (b) => ({...b, case:{...b.case, allowed_actions: []}})}` | no buttons; line "Read-only for the business owner role"; no queue rail; **no named OpenAPI example exists for the owner view** |
| `scr06.error-reason-missing` | error | rep | `getCase: {example:"DEFAULT", transform: claimedByMe}` | open Release, submit empty: "Add a reason to release this case." (also Wait: "Waiting needs a wake-up time."; Resolve: "Resolving needs an outcome.") |
| `scr06.stale-changed-since` | stale | rep | none (`DEFAULT` has `src-membership` changed) | membership card shows "Changed since the AI saw it: was Basic, now Comfort Plus"; chips carry "changed" where `BriefItem.changed` or the source changed |
| `scr06.stale-version-conflict` | stale | rep | `applyCaseAction: {example:"VERSION_CONFLICT", status:409}`, `getCase: {sequence:[{example:"DEFAULT"},{example:"DEFAULT", transform: claimedByDemoSupervisor}]}` | click Claim: "This case changed since you opened it (Demo supervisor at 2:31 pm). Reload to see it." + Reload; Reload shows it claimed by the demo supervisor |
| `scr06.stale-case-changed-elsewhere` | stale | rep | `stream: caseScripts.caseChangedElsewhere` | after 3 s the "This case changed. Show the latest." line with Reload |
| `scr06.stale-stuck-waiting` | stale (flow "Stuck waiting (FLOW-10)") | rep | `getCase: {example:"WAITING", transform: stuckWaiting("2026-10-16T14:00:00-05:00")}` | header "Wake-up time passed (Fri 2:00 pm). Pick it back up." and the primary "Pick it back up" |
| `scr06.stale-overdue` | stale (flow "Overdue (FLOW-9, FLOW-10)") | rep | route `/staff/cases/MHC-C-0005` (director reskin: `due_state: overdue`) | due headline followed by the Overdue tag with a clock; promise status stays "Open" |
| `scr06.stale-shift-ended` | stale (flow "Shift ended before claim (FLOW-8)") | rep | `getCase: {example:"DEFAULT", transform: shiftEndedPromise()}` | promise card status "Changed" with "Changed: Shift ended before a claim" and a History entry |
| `scr06.success-claimed` | success | rep | none | click Claim: result line "Claimed · Riley (demo)", lifecycle line moves to Claimed, "Log a call" enabled |
| `scr06.success-contact-logged` | success | rep | `getCase: {example:"DEFAULT", transform: claimedByMe}` | Log a call → Reached → Record: activity "Called · Reached the customer … Demo: recorded, not sent" |
| `scr06.success-resolved` | success | rep | `getCase: {example:"DEFAULT", transform: claimedByMe}` | Resolve + outcome → navigates to `/staff/queue` with "MHC-C-0007 resolved." |
| `scr06.success-flagged` | success | rep | none | Flag → Add to review list: "Added to the review list." |
| `scr06.success-waiting` | success (flow "Waiting (FLOW-9)") | rep | `getCase: {example:"DEFAULT", transform: claimedByMe}` | Set waiting with a date and time: header "Wakes Mon Oct 19 · 9:00 am" (the WAITING response's `wake_up_at` is replaced by the request's when the director is active) |
| `scr06.success-released` | success (flow "Released (FLOW-9)") | rep | `getCase: {example:"DEFAULT", transform: claimedByMe}` | Release + reason: back to Unassigned, result line `Released.` |
| `scr06.success-assigned` | success (flow "Assign or reprioritise (supervisor) (FLOW-10)") | **supervisor** | none (the director derives the supervisor's `allowed_actions`: Assign and Change priority appear) | Assign → Riley + reason: "Assigned to Riley (demo)."; Change priority → P2: "Priority is now P2 · Time-sensitive." |
| `scr06.disabled-before-claim` | disabled | rep | none | Resolve / Set waiting / Close unresolved show "Claim the case first."; Join chat explains itself; assign / priority absent for the rep |
| `scr06.disabled-live-box` | disabled (flow "Handed back" state success) | rep | `getCase: {example:"LIVE_JOINED"}`, `liveChatAction: {example:"HANDED_BACK"}` | click Hand back: event line "Handed back to the assistant at 2:22 pm", live box disabled |
| `scr06.flow-live-queued` | default (flow "Live-queued case (FLOW-8)") | rep · on | route `/staff/cases/MHC-C-0012` (director reskin: queued) | lifecycle starts at Live-queued; primary "Claim and join"; header "The customer is waiting in the chat since 2:14 pm." |
| `scr06.flow-live-joined` | success (flow "Joined, AI paused (FLOW-8)") | rep · on | `getCase: {example:"LIVE_JOINED"}`, `stream: caseScripts.customerReply` | live box: "You are replying as Riley (demo representative). The assistant is paused."; header "Live · you are replying · assistant paused"; after 4 s "Thanks, that helps." arrives and is announced |
| `scr06.flow-chat-closed` | success (flow "Chat closed (FLOW-8)") | rep | `getCase: {example:"LIVE_JOINED"}`, `stream: caseScripts.replyThenClosed` | after 7 s the event line "Chat closed at 2:24 pm"; live box disabled; Resolve / Close unresolved available |
| `scr06.flow-reset-ended` | error (flow "Customer chat ended by reset (FLOW-12)") | rep | `getCase: {example:"LIVE_JOINED"}`, `stream: caseScripts.resetEnded`, `liveChatAction: {example:"NOT_LIVE", status:409}` | live box "This chat ended because the demo was reset."; Send also answers with the same sentence |
| `scr06.flow-safety` | default (flow "Safety case (FLOW-2)") | rep | route `/staff/cases/MHC-C-0008`; none (director → `SAFETY_CASE`) | "P0 · Safety" in the title, "No due time: safety" |
| `scr06.flow-fee-bearing` | default (flow "Fee-bearing change request (FLOW-6)") | rep | route `/staff/cases/MHC-C-0009`; none (director → `FEE_BEARING_CHANGE`) | due headline "Due Sat Oct 17 · 12:00 pm, the window start" (the example's label is Sat; SCREEN_SPECS prints Fri: a contract data difference, record it) |

*Seeded demo case (FLOW-10)* is `scr06.default` (the "Demo seed" tag). The flow-state names in the `flowState` field must equal the SCREEN_SPECS first-column text exactly (copy them from lines 342–356 of `SCREEN_SPECS.md`).

### 6.3 States with no named OpenAPI example and how the dev layer derives them

| State | Derivation | Request to the contract owners |
|---|---|---|
| Owner read-only case | role `owner` + `allowed_actions: []` recomputed by the director (or the `scr06.error-owner-readonly` transform when FR-1 is absent) | `getCase` OWNER_READ_ONLY |
| Supervisor view (Assign / Change priority) | director recomputes `allowed_actions` by role from the `ASSIGNED` example's list | `getCase` SUPERVISOR_VIEW |
| Live-queued case (0012) with "Claim and join" | `DEFAULT` re-skinned from the `STAFFED_WITH_WAITING` live row, `live.state: "queued"`, `allowed_actions: ["claim_and_join","claim","flag"]` | `getCase` LIVE_QUEUED |
| MHC-C-0005 / 0006 case pages | `DEFAULT` with header fields from the queue rows, brief items empty, no sources or conversation | `getCase` examples per seeded reference |
| Release / start / close-unresolved results | `CLAIMED` reshaped; result lines are dev fixtures | `applyCaseAction` RELEASED, STARTED, CLOSED_UNRESOLVED |
| Stuck waiting, shift-ended promise | transforms on `WAITING` / `DEFAULT` | `getCase` STUCK_WAITING, SHIFT_ENDED |
| Stream events beyond `FRAMES` | `caseScripts` fixtures typed against `CaseEvent` | more `streamCaseEvents` frames |
| Snapshot time ("What the AI saw · 2:10 pm") | not shown (the contract has no snapshot time); the Now column header uses `as_of` | `snapshot_at` on `CaseSource` |

## 7. Checks

From `apps/web/`. Prism is not needed for unit tests. Fast order while iterating: lint, then typecheck, then tests.

**Tests the implementer writes with the code (each ≤ 300 lines; names are the `it(...)` titles):**

| File | Must cover |
|---|---|
| `scr05/queueDiff.test.ts` | "counts an added row once"; "counts a removed row once"; "counts a changed owner once"; "ignores as_of and age_label"; "returns 0 for identical payloads" |
| `scr05/useRowKeys.test.tsx` | "j and k move the cursor and clamp"; "ignores keys typed in an input"; "Enter opens the cursor row when nothing is focused"; "Enter does not open when a row button is focused"; "cursor stays on its reference when rows reorder" |
| `scr05/LiveRow.test.tsx` | "accessible name ends with waiting since 2:14 pm"; "shows no duration or estimate text"; "Claim and join calls the handler and shows loading"; "compact omits the button" |
| `scr05/Scr05.test.tsx` | "customer role renders the gate sentence and never calls getQueue"; "default lists the four seeded rows in server order"; "row accessible name for MHC-C-0008"; "empty state copy"; "loading shows five skeleton rows"; "partial shows Brief being written"; "error shows retry and retry refetches"; "staffed queue shows the waiting row and Claim and join runs getCase, claim, join in order then navigates"; "nobody online shows the disabled sentence"; "poll finds 2 changed rows: stale line, Show them applies without moving the cursor" (fake timers, 10 s); "staffing flip applies without a stale line"; "result line from router state clears after 4 s"; "no 24-hour times" (`expectNo24HourTimes`) |
| `scr06/caseReducer.test.ts` | one test per rule in Step 3 (1–6) |
| `scr06/caseText.test.ts` | "dueHeadline for safety, normal, window-start and label-only cases"; "createdLine"; "ownerLine"; "headerStatusLine for joined, live-queued, waiting, stuck waiting"; "bestTimeLabel"; "humanizeKey" |
| `scr06/errorCopy.test.ts` | every row of the §4.5 table, including the fallback without details |
| `scr06/actionPlan.test.ts` | lifecycle × role matrix: unassigned/rep, live_queued/rep, claimed/rep, joined/rep (no primary, More actions menu), waiting/rep, resolved/rep, unassigned/supervisor (Assign visible, label Reassign when owned), any/owner (readOnly); and the invariant "an item is enabled only if its key is in allowed_actions" over all combinations |
| `scr06/wakeUp.test.ts` | the four cases in Step 5 |
| `scr06/claimAndJoin.test.ts` | "claims with the case version then joins"; "does not join when the claim fails"; "uses the known version without calling getCase" |
| `scr06/SplitButton.test.tsx` | "main segment calls onPrimary"; "menu lists items and disabled items show their reason"; "no primary renders More actions"; "keyboard opens the menu" |
| `scr06/BriefView.test.tsx` | "renders eight headings in order with exact titles"; "claims card has the Customer says tag and no chips"; "facts show one chip per source id and changed adds the word"; "trimmed section shows the note"; "being written shows only the sentence"; "empty items read Nothing recorded."; "index chip focuses its section" |
| `scr06/SnapshotTable.test.tsx` | "table with th scope and a changed row"; "KB passage renders as a blockquote"; "unavailable shows the sentence and the snapshot alone" |
| `scr06/LiveBox.test.tsx` | "active shows the reply label with the owner name"; "send posts text and clears the field"; "disabled after hand back"; "reset message replaces the field" |
| `scr06/ActionForms.test.tsx` | one test per form: the exact request body (e.g. Release posts `{action:"release", expected_version:3, reason}`); "Escape cancels"; "first field is focused"; "wait omits wake_up_at when the time is empty" |
| `scr06/Scr06.test.tsx` | "customer role: gate sentence, no getCase"; "owner role: read-only line, no getQueue call, no buttons"; "default renders header, promise, eight sections, Sources (5)"; "one h1 in loading, error and loaded states"; "Claim posts {action:'claim', expected_version:3} then shows the result line and focuses it"; "VERSION_CONFLICT shows the sentence and Reload refetches"; "REASON_REQUIRED shows the release sentence"; "case not found panel"; "a streamed customer message appears and is announced"; "a streamed demo_reset shows the reset sentence"; "source chip switches to Sources and highlights the card"; "claim and join runs claim, join, then getCase"; "resolve navigates to the queue with the result line in router state"; "no 24-hour times" |
| `dev/directors/case-store.test.ts` | "allowedFor rep/supervisor/owner per lifecycle"; "patchOverride appends activities and messages"; "resetCaseStore clears overrides" |
| `dev/directors/case-actions.test.ts` | each picker rule in Step 14 (e.g. "release without reason picks REASON_REQUIRED 422", "claim twice picks CASE_ALREADY_CLAIMED", "unknown reference picks CASE_NOT_FOUND", "getCase for the owner recomputes allowed_actions to []", "claim by a supervisor sets owner Demo supervisor", "wait result line uses the request time", "transform writes the store only when called"), plus the pure helpers in `case-transforms.ts` |

**While iterating:** `npx vitest run src/screens/scr05` · `npx vitest run src/screens/scr06` · `npx vitest run src/dev/directors`.

**Once before reporting (cheapest first, stop at the first red):**

| # | Command | Passing looks like |
|---|---|---|
| 1 | `npm run lint` | 0 errors, no new warnings (fix every `react-hooks/exhaustive-deps`) |
| 2 | `npm run typecheck` | exits 0 |
| 3 | `npx vitest run src/screens/scr05 src/screens/scr06 src/dev src/styles src/components src/routes.test.ts` | all green. `src/dev` runs the foundation's `scenarios.integrity.test.ts` and `scenarios.coverage.test.ts` against G4's scenario files (set `complete: true` first); `src/styles` runs `guard.test.ts` which scans every file under `src/` (no hex, no safety tokens, no `Prefer` outside `src/dev`) |
| 4 | `npm run build && npm run check:dist` | build exits 0; no dev-layer strings in `dist/` |
| 5 | Step 16 (DevTools) | list what was checked in the report |
| 6 | Only if Prism and Chrome are available: `(npm run mock &); sleep 6; perl -e 'alarm 300; exec @ARGV' npx playwright test tests/e2e/smoke.spec.ts` | SCR-5 and SCR-6 rows green except the h1-prefix assertion discussed in FR-3; report, do not edit |

**Full suite:** not needed. This slice adds files inside its own screen folders and G4's dev files; it changes no shared fixture, configuration, dependency, lockfile or cross-codebase module. (Rule `build-loop-test-scope`: affected tests only.) The Python suite is untouched and not run.
**Existing tests that must stay green:** all foundation tests (`src/lib`, `src/api`, `src/state`, `src/components`, `src/routes.test.ts`, `src/styles`, `src/dev/{resolve,calllog,stream}.test.ts`, `src/dev/scenarios.*.test.ts`), except as noted in FR-3.

## 8. Risks and requests

### 8.1 Requests to the integrator (shared surfaces G4 must not edit; F§8.3 procedure)

| ID | Request | Needed by | If refused |
|---|---|---|---|
| **FR-1** | Add the case-aware director hook (§5 Step 14: `CaseCall`, `CasePick`, `CasePicker`, `pickCaseCall` in `src/dev/directors/index.ts`; resolve.ts step 6b; transforms apply to error bodies as well; `reference` parsed from the request path). Reason: Prism answers `getCase` with MHC-C-0007's body for **any** reference, and `applyCaseAction` / `liveChatAction` with the first 2xx example whatever the request body says (a Resolve click would return "Claimed · Riley (demo)"). `OpForce` is keyed by operation only and `Reaction.then` receives no request, so neither can map action → example. | Steps 14–15 | G4 ships forced-example scenarios only, no case store, and reports `PARTIAL`: Resolve / Wait / Release show the wrong result line in the dev layer (screens and unit tests are unaffected) |
| **FR-2** | Register `/staff/cases` (no param) as an alias path for SCR-6 in `src/router.tsx` so the "no case picked" empty state can be reached. | optional | The component branch is unit-tested directly; `scr06.no-case` is not added |
| **FR-3** | The foundation's `stubs.test.tsx` and `tests/e2e/smoke.spec.ts` require every screen's `h1` to start with `SCR-<n>`. Real screens must not (SCR-6's single `h1` is the case title). Change them to "exactly one non-empty h1" for screens whose group has flipped `complete`, or drop the prefix check. Applies to all five groups. | before G4's final gates | The implementer reports the failure and does not edit those files |
| **FR-4** | The group file for G4 is `docs/ux/04-prototype/groups/g4-staff-queue-case.md` (caller's name); F§2.4 and the PROTOTYPE_PLAN link say `g4-staff-case.md`. | docs | none |
| **FR-5** | Contract/OpenAPI additions that would remove dev fixtures (owner of the contract decides): the names in §6.3's right column; `snapshot_at` on `CaseSource`; and the SCREEN_SPECS vs OpenAPI date mismatch for the fee-bearing case (spec prints "Due Fri Oct 16 · 12:00 pm", example `due_label` says "Sat Oct 17 · 12:00 pm"). | UX-5 | none |

### 8.2 Mock artefacts to list in the group file (visible differences from a real backend)

1. Case pages for MHC-C-0005, 0006 and 0012 have empty briefs, no sources and no conversation (no example exists).
2. Result lines for release, start and close-unresolved, the owner/supervisor `allowed_actions`, and every stream event except the two in `FRAMES` are dev fixtures.
3. Only contacts appear in the activity log; the contract has no claim/release history list.
4. The 10 s queue poll returns the same example each time unless a scenario uses a `sequence`; the "N cases changed" state is reached only through the `stale-*`, `new-handoff`, `shift-ended` and `overdue-after-advance` scenarios.
5. Version conflicts occur only when a scenario forces them (the director does not compare versions).
6. `resolve` decides `kept` vs `missed` against the constant demo start time, not the live demo clock.

### 8.3 Spec gaps found while planning (decisions made here; no product decision needed)

1. **Claim and join needs a version the queue row lacks.** `CaseActionRequest.expected_version` is required and `QueueRow` has no `version`; SCR-5's "Claim and join" therefore reads `getCase` first (one extra call), then claims, then joins (Step 5 `claimAndJoin`).
2. **Shared `QueueRow` cannot render live rows** (it prints "No due time: safety" for `due_state: no_due_time`, which live rows carry). G4 builds `LiveRow` in its own folder instead of asking to change the frozen component.
3. **`getQueue` is refused to the owner**, so the SCR-6 rail is hidden for the owner (the owner opens cases from metrics).
4. **Version-conflict wording:** SCREEN_SPECS says "(claimed by the demo supervisor at 2:31 pm)"; the contract carries only `changed_by` and `changed_at`, so the screen says "(Demo supervisor at 2:31 pm)" (UI_CONTRACTS wording).
5. **"Claimed · Riley (demo)" on SCR-5:** shown as the row's owner ("Riley") and as the result line on SCR-6; SCR-5 shows a result line only when it arrives through router state (resolve). Recorded as an interpretation.
6. **SCR-6 Join chat for a claimed live-queued case** appears in the action bar and is enabled only if the server lists `join_chat`; the primary "Claim and join" does both in one go. No example lists `join_chat`; the director derives it.
7. **Wake-up input** is a date field plus a 12-hour time select (not `datetime-local`, whose display follows the browser locale and can show 24-hour times).
8. **"Created …" line** is composed as `formatDayShort + ", " + formatTimePoint` because `lib/time.ts` has no comma format.
9. **`h1` content:** SCR-5 "Representative queue"; SCR-6 the case title pill, "Case {reference}" (visually hidden) while loading, "Case not found" for CASE_NOT_FOUND.

## 9. Readiness

**READY.** No `NEEDS-DECISION`: the open points are copy or constants this plan fixes (§8.3) and contract wishes (FR-5) that need no answer to build. **Prerequisite:** the foundation slice has finished (Step 0 checks that the files exist; if not the implementer reports `BLOCKED`). **Partial-build risk:** FR-1 is the only request that changes how much of the dev layer works; Steps 1–13 and 16 (screens, tests, streams, forced scenarios) do not depend on it.

Report back with: the §7 gate outputs, which scenarios were checked in DevTools (and which routes and widths), whether FR-1/2/3 were present, the list of `// dev fixture` values added, and every place the plan was deviated from with the reason.
