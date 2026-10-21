# UX-4 · slice G2 chat-cards (every SCR-1 reply-block renderer)

> **Planner:** `fanout-planner` · **Date:** 2026-10-21 · **Project:** `/home/linuxuser/workspaces/inno-aea-callcenter` · **Implementer:** `fanout-implementer` (Sonnet) · **Readiness:** READY (see §9; items in §8 are decided in this plan, with requests to owners)
> **Lane / loop:** `lane::build-loop`, **not** `risk::security` (prototype on a mock; the code field handles a fake one-time code only). Loop: plan → implement (code **and** its tests) → affected tests → code review. No test-writer, no frozen tests, no security agent (rule `build-loop-test-scope`). Worked pairs used as tests: **WP-5** (safety card) and **WP-4** (fee-bearing change request); **WP-1** (partial answer) as a supporting test.
> **No git here:** the folder is not a git repository. Do not run `git`.
> **Plans against:** `docs/plans/fanout/2026-10-21-ux4/foundation.md` (call it **FND**). At planning time the foundation was still being built: `src/components/{ui,shared,shell}`, `src/lib`, `src/api`, `src/test/{no24h,fakeTransport,fixtures,setup}.ts` and `src/styles` existed; `src/screens/**`, `src/dev/**` content, `src/test/render.tsx` did not yet. Step 0 checks what exists before any code.

## 1. Goal and sources

**Deliver** the renderer for every SCR-1 reply block, in `apps/web/src/screens/scr01/cards/**`, registered in `cardRenderers` (FND §4.9 `RendererMap`), so G1's thread calls `renderBlock()` and gets the right card for all 24 `ReplyBlock` types and every composed error (`SLOT_TAKEN`, `CODE_*`, `NOT_VERIFIED`, `OUT_OF_AREA`, notices). Plus the G2 dev-layer pieces (scenarios, one-shot forces, chat director, fixtures) so the state switcher can show every card state, and `docs/ux/04-prototype/groups/g2-chat-cards.md`.

| Source | Sections used |
|---|---|
| `docs/ux/03-structure/SCREEN_SPECS.md` | "Copy rules that apply on every screen"; **SCR-1**: Components bullets, States table (8 states), Flow states table (44 rows), Interactions, **Copy notes (exact wording)**, Accessibility notes; **N-6, N-7, N-8, N-26, N-27** |
| `docs/ux/03-structure/UI_CONTRACTS.md` | "Named errors, and what each screen does" (composed table); **CON-2** (block list, `settled`, `writes[]`, promise join rule UXR-19), **CON-4**, **CON-5**; CON-6 (inbox link) |
| `docs/ux/03-structure/ui-contracts.openapi.yaml` | `components.schemas` `*Block`, `ReplyBlock`, `Settled`, `TurnRequest`, `FollowUpOptions`; the 37 `submitTurn` 200 examples, `requestPerson` (`CASE_CREATED`, `LIVE_QUEUED`, `ALREADY_OPEN`), `saveFollowUp` `PHONE_MORNINGS`, `getChatThread` `ENDED_BLOCK` |
| `docs/design/design.md` | §3.2–3.5 type, time, hints; §4.5–4.6 colour rules (red = safety card only; mint = customer's own choices); §5.3–5.5 radii/lines; §6 motion; **§8.2** primitives, **§8.4** cards in the thread, **§8.6** safety card; §9.1 container queries; §10 copy tone; §11 do/don't |
| `docs/ux/03-structure/IA.md` | rules that apply to every screen (talk-to-a-person always present; red only safety); cross-screen link "SCR-1 code card → SCR-2 (new tab)" |
| `docs/artifacts/2026-10-21-direction-A5-service-desk.html` | look reference only (`.daytab`, `.win`, `.safety`, card anatomy); `design.md` wins |
| `docs/data/worked-pairs.md` | WP-1, WP-4, WP-5 (what the cards must and must not say) |
| FND | §2.4 (group split, seams), §4.7–4.9 (components, frozen `contract.ts`/`blocks.ts`, dev-layer interfaces), §5 Step 3 (guard test), Step 7–8 (scenarios, resolve precedence), §8.2 (what Prism cannot show), §8.3 (change-request procedure) |

## 2. Boundary

### 2.1 Owned files (create / modify; paths relative to `/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/`)

```
src/screens/scr01/cards/index.ts                     (modify: replaces the FND stub; re-exports only)
src/screens/scr01/cards/registry.tsx                 (new: cardRenderers map)
src/screens/scr01/cards/layout.ts                    (new: blockLayout)
src/screens/scr01/cards/TextCard.tsx  SourceChipView.tsx  sourceDedupe.ts
src/screens/scr01/cards/SafetyCard.tsx               (file name MUST contain "Safety": the guard test allowlist, FND Step 3)
src/screens/scr01/cards/EmergencyLineCard.tsx
src/screens/scr01/cards/ChoiceCards.tsx              (burning_check, quick_checks, urgency_questions)
src/screens/scr01/cards/WherePromptCard.tsx  LocatePromptCard.tsx  CodePromptCard.tsx
src/screens/scr01/cards/SlotCard.tsx
src/screens/scr01/cards/AccountCard.tsx
src/screens/scr01/cards/VisitCards.tsx               (confirmation, appointment, cancelled)
src/screens/scr01/cards/ChangeRequestCard.tsx
src/screens/scr01/cards/HandoffCard.tsx  FollowUpChooser.tsx  LiveQueuedCard.tsx
src/screens/scr01/cards/NoticeCards.tsx              (notice, failure_offer, no_info)
src/screens/scr01/cards/ErrorCard.tsx  SessionEndedCard.tsx
src/screens/scr01/cards/parts/{dates.ts,promise.ts,useCardAction.ts,landed.ts,OptionTile.tsx,CardParts.tsx}
src/screens/scr01/cards/testing/{examples.ts,props.tsx,stateMap.ts}      (test helpers; imported only by *.test.* files)
src/screens/scr01/cards/**/*.test.ts(x)              (one per module, §7)
src/dev/scenarios/scr01-cards.ts                     (replace the FND stub)
src/dev/scenarios/scr01-cards.fixtures.ts            (new: typed fixtures/transforms)
src/dev/scenarios/scr01-cards.test.ts                (new)
src/dev/reactions/scr01-cards.ts                     (replace the FND stub)
src/dev/reactions/scr01-cards.test.ts                (new)
src/dev/directors/chat-cards.ts                      (replace the FND stub)
src/dev/directors/chat-cards.test.ts                 (new)
docs/ux/04-prototype/groups/g2-chat-cards.md         (new)
```
**No `src/dev/stream/*` file.** The caller listed `stream`, but FND §2.4 gives G2 `scenarios/reactions/directors` only (`stream/chat-scripts.ts` is G1's). No card needs a stream; one scenario (`shift-ended-handoff`) is out of scope for G2 (G1 owns event-driven states, the card it contains is covered by the `HANDOFF` scenarios).

### 2.2 Read-only shared surfaces (never edit)
`src/screens/scr01/{contract.ts,blocks.ts}` (frozen), `src/screens/scr01/{index.ts,Scr01.tsx,core/**}` (G1), `src/components/**`, `src/api/**`, `src/state/**`, `src/styles/**`, `src/lib/**`, `src/test/**`, `src/routes.ts`, `src/dev/{install,Panel,Kit,resolve,transport,defaults,world,calllog,session-fake}.*`, `src/dev/scenarios/{types,matrix,index,shared}.ts`, `src/dev/reactions/{index,shared}.ts`, `src/dev/directors/{index,chat-core}.ts`, `src/dev/stream/**`, `package.json`, `docs/ux/03-structure/**` (incl. the OpenAPI file: a gap is a *request*, §8), `docs/design/**`, `.claude/**`, `CLAUDE.md`.

### 2.3 Do not
- Do not edit a foundation or G1 file. If a primitive is missing, write the request in `groups/g2-chat-cards.md` (FND §8.3) and build a local equivalent inside `cards/` (default for `OptionTile`, day tabs).
- Do not import anything from `src/dev/**` in `cards/**` non-test code (ESLint `no-restricted-imports`). Do not call `fetch`; cards only call `props.dispatch`.
- Do not use red, orange, amber, hex values, or the safety tokens outside `SafetyCard.tsx`. Do not use a pill-shaped or outlined tag. Do not use mint for anything but the customer's chosen tile.
- Do not add any wording the contract or SCREEN_SPECS copy notes do not give, **except** the short client-side validation lines listed in §5 Step 5 (each marked "client copy" in the g2 doc).
- Do not write "charged" in any form; do not write "sent" for a follow-up; no completion word ("booked", "cancelled", "moved", "verified") unless the guard in Step 8 passes (`writes`/`settled.actions` carry that kind).
- Do not render a time from a string split. 12-hour output comes from `Time`/`TimeWindow`/`lib/time` fed an ISO, or from a contract `*_label` that is already 12-hour text (§4.3).
- Do not put a card's buttons behind `props.disabled` for "Talk to a person" or the session-ended "Start a new chat": those are never disabled.
- Do not render hooks in `registry.tsx` entries: each entry is a plain arrow that returns an element (`(p) => <TextCard {...p} />`) because `renderBlock` may call the renderer as a function (G1 would then run our hooks conditionally).
- Do not log, store or echo the one-time code or the phone value (clear the code input after submit; no `console.*` in cards).
- Do not leave servers running; do not install packages.

## 3. Requirements table

`W:` = SCREEN_SPECS SCR-1 Flow-states row; `C:` = SCR-1 Components bullet; `S:` = State row; `Cp:` = Copy notes; `A:` = Accessibility notes; `D:` = design.md; `U:` = UI_CONTRACTS.

| # | Requirement (source) | How implemented | Verified by |
|---|---|---|---|
| G2-01 | Every `ReplyBlock["type"]` (24) has a renderer (U: CON-2 block table; N-6) | `registry.tsx` `cardRenderers` has all 24 keys | `cards.coverage.test.tsx` "every block type has a renderer" (reads the type list from the OpenAPI schema) |
| G2-02 | Every block type and state maps to a named OpenAPI example or a typed dev fixture (caller) | `testing/stateMap.ts` (§6) + `scr01-cards.fixtures.ts` | `cards.coverage.test.tsx` "state map"; `src/dev/scenarios/scr01-cards.test.ts` |
| G2-03 | Safety card: DANGER band + warning icon, two numbered instructions verbatim, "Call 911 (from outside)" `tel:911`, closed by 4 px rule, quiet contact line below, **no follow-up time anywhere**, no field, not dismissible, no motion (C: Safety card; Cp: Safety card; W: Safety takeover; D §8.6) | `SafetyCard.tsx` `SafetyCard` | `SafetyCard.test.tsx` **WP-5** |
| G2-04 | Safety card announced once with `role="alert"`, then static; `<section aria-label="Danger: safety instruction">` (A: live regions; D §8.6) | module `alerted` Set keyed by `block_id`; first render gets `role="alert"` | `SafetyCard.test.tsx` "announces once even when rendered twice" |
| G2-05 | Conditional safety: WARNING, conditional text, emergency-number line (C; Cp: Conditional card; W: Burning smell, risk unclear) | `ConditionalSafetyCard` in `SafetyCard.tsx` | `SafetyCard.test.tsx` |
| G2-06 | Burning-smell question: question + "Yes" "No" "Not sure" (W: Burning smell, unknown) | `ChoiceCards.tsx` `BurningCheckCard` | `ChoiceCards.test.tsx` |
| G2-07 | Emergency-line card: 2 px ink edge (not red), phone icon, number as 44 px `tel:` target, 1-business-day line under a divider **only** when `separate_line` is non-null (C; Cp: R-8; W: Someone in danger) | `EmergencyLineCard.tsx` | `EmergencyLineCard.test.tsx` |
| G2-08 | Quick checks: one line, "Skip and book" primary, "Show the checks" secondary, list opens inline (C) | `QuickChecksCard` | `ChoiceCards.test.tsx` |
| G2-09 | Urgency questions: three questions, answer buttons, "Skip" (C; Cp: Urgency questions) | `UrgencyQuestionsCard`; one `choice` per card (§5 Step 5 encoding) | `ChoiceCards.test.tsx` |
| G2-10 | Where card: one field "ZIP code or city", "Show windows" (C) | `WherePromptCard.tsx`; `form` payload `{zip_or_city}` | `WherePromptCard.test.tsx` |
| G2-11 | Locate card: "Name on the account" + "Phone", or "Customer ID", or "Invoice number"; "Send the code"; demo hint (C; D §8.4) | `LocatePromptCard.tsx`; alternatives from `field_sets` | `LocatePromptCard.test.tsx` |
| G2-12 | Code card: masked hint, 6-digit field `inputmode="numeric"` `autocomplete="one-time-code"`, "Verify", "Open the demo inbox" link (new tab), hint "Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries." (C; Cp: Code prompt; A: labels) | `CodePromptCard.tsx` | `CodePromptCard.test.tsx` |
| G2-13 | Code states: wrong (invalid field), expired ("Send a new code" only while `resend_offered`), locked (field disabled) (W: Code wrong / expired / locked) | `CodePromptCard` by `block.state`; the sentence comes from the paired `error` block (§5 Step 9) | `CodePromptCard.test.tsx`, `ErrorCard.test.tsx` |
| G2-14 | `NOT_VERIFIED`, `CODE_LOCKED`, `CODE_CAP_REACHED` render the **identical** sentence and structure (no account-existence leak) (U: NOT_VERIFIED; W: No match) | one code path in `ErrorCard.tsx` for the three codes | `ErrorCard.test.tsx` "three codes render identical markup apart from nothing" |
| G2-15 | Slot card: header "Choose a window"; day tabs ("Wed 21 · 2 open" / "Mon 19 · Full"); window tiles (accessible name adds "open"); taken tiles struck through with "Taken", disabled; "Members" tag on member-only; standard fee row; "Windows are shown, not held."; "Continue with this window" (C; D §8.4; S: disabled) | `SlotCard.tsx` (Radix Tabs + `OptionTile`) | `SlotCard.test.tsx` |
| G2-16 | Slot choice posts a `choice` with `option = slot_id`; the chosen tile is mint + 2 px emerald edge + check; once answered the card keeps the choice and the button is disabled (S: disabled; D §8.4) | `SlotCard` local `picked` + `block.answered` | `SlotCard.test.tsx` |
| G2-17 | `SLOT_TAKEN`: "Sorry, that window just went. Here are the next open ones." + a fresh slot card from `fresh_windows`; nothing booked (W: Slot taken at write) | `ErrorCard.tsx` renders text then `SlotCard` with `fresh_windows` | `ErrorCard.test.tsx` |
| G2-18 | `OUT_OF_AREA`: sentence + "Talk to a person" (W: Out of area) | `ErrorCard` + `PersonKey` | `ErrorCard.test.tsx` |
| G2-19 | Account card: invoice (hero balance, "Balance · unpaid · due Nov 1, 2026", lines table as billed, total with 1 px ink rule, **no verdict**), membership (tier, renewal date), warranty (install date, sentence) (C; W: Account answer; R-17) | `AccountCard.tsx` | `AccountCard.test.tsx` |
| G2-20 | Confirmation: header "Your visit" + "Booked" tag; hero window `8:00 am → 12:00 pm`; sentence with long date; rows Date/Technician/Fee that applies; checked "What happens next" list; free-change note; "Keep this" foot with day and window (C; D §8.4; W: Booked) | `VisitCards.tsx` `ConfirmationCard` | `VisitCards.test.tsx` |
| G2-21 | Appointment card = same anatomy labelled `block.label` ("Your booked visit"), no timeline (C; W: Confirm existing visit) | `AppointmentCard` | `VisitCards.test.tsx` |
| G2-22 | Cancelled: "Your visit on Wed Oct 21 is cancelled." + `fee_line` ("There's no fee.") only after a `cancelled` write (W: Fee-free move / cancel; Copy rules: Completion) | `CancelledCard` + guard | `VisitCards.test.tsx` |
| G2-23 | Completion wording only when `writes`/`settled.actions` carry the kind (Copy rules "Completion"; U: CON-2 `writes[]`; N-8) | `hasWrite(settled, kind)` in `parts/CardParts.tsx`; used by confirmation ("Booked" tag), cancelled | `VisitCards.test.tsx` "no Booked word without a booked write" |
| G2-24 | Change-request card: header "Change request", reference; "Your visit stays" original window; "Requested"; fee line; original-stays line; windows shown (not held); promise line + Due row; can't-guarantee line when present; phone line only when present; **no primary button**; never "charged"/"sent" (C; W: Fee-bearing change/cancel; D §8.4; WP-4) | `ChangeRequestCard.tsx` | `ChangeRequestCard.test.tsx` **WP-4** |
| G2-25 | Handoff card: "Your request", reference (mono, copy), promise as one `t-lead` sentence joined per UXR-19, Due row only when `due_at` non-null, Status tag "Waiting for a representative", **no countdown, no queue position** (C; Cp: Promise texts; U: CON-2; W: Handoff) | `HandoffCard.tsx`, `parts/promise.ts` | `HandoffCard.test.tsx`, `promise.test.ts` |
| G2-26 | Promise text joined exactly: `"{promise_text}, {due_label}. {extra_lines…}"`; staffed variant has no time (U: UXR-19, R-26) | `joinPromise` | `promise.test.ts` (3 examples, expected sentences in §5 Step 1) |
| G2-27 | Follow-up chooser: legend; Email / Phone call radios; "Best time to call" Mornings/Afternoons/Any time when phone; "Save my choice"; saved line "Follow-up saved: phone call, the number ending in 02, mornings." from the contract, nothing says a message was sent (C; Cp: Follow-up; U: CON-5) | `FollowUpChooser.tsx`; dispatches `{kind:"followUp",…}` | `HandoffCard.test.tsx` |
| G2-28 | Unverified customer: `general_only` → destination `"general"` always (U: CON-5 guarantees; N-10) | `FollowUpChooser` | `HandoffCard.test.tsx` "general_only sends destination general" |
| G2-29 | Live-queued card: promise text + checked list You asked → A representative joins → Back to the assistant, or the chat closes; step state follows `settled.replying` (C; D §8.4) | `LiveQueuedCard.tsx` | `LiveQueuedCard.test.tsx` |
| G2-30 | Limit notices (`RATE_LIMITED`, `BOOKING_CAP`, `SPEND_CAP_REACHED`): neutral card, one sentence, "Talk to a person", no emerald primary, no triangle (C; D §8.4; W: Limit reached, Spend cap) | `NoticeCards.tsx` | `NoticeCards.test.tsx` |
| G2-31 | `TURN_TIMEOUT`: header "This is taking longer than it should."; **Try again** (primary) + **Talk to a person** (secondary); Try again disables while re-sending (C; S: loading) | `NoticeCards.tsx`; `dispatch({kind:"retry", turnId: ""})` (§8 C-2) | `NoticeCards.test.tsx` |
| G2-32 | `BUSY`: one plain line + secondary "Talk to a person", no header; `AI_PAUSED`: one plain line, no failure styling (C; U) | `NoticeCards.tsx` | `NoticeCards.test.tsx` |
| G2-33 | `failure_offer` and `no_info`: one line + "Talk to a person" when `person_key` (C; W: Failure signal, No current source) | `NoticeCards.tsx` | `NoticeCards.test.tsx` |
| G2-34 | "Talk to a person" is never disabled, in any card, in any state (S: disabled; IA rule) | `PersonKey` ignores `disabled`/`answered`; only re-tap guard | `NoticeCards.test.tsx` "Talk to a person stays enabled when props.disabled" |
| G2-35 | `session_ended`: sentence + "Start a new chat" (`newChat`), not disabled (S: disabled; U: SESSION_ENDED) | `SessionEndedCard.tsx` | `SessionEndedCard.test.tsx` |
| G2-36 | Text answer with source chip(s): "Source" chip = file (mono 12) + section + `version_label` (never an invented date); opens the quoted passage; hint "Where this comes from"; 44 px hit area (C: Source chip; D §8.3) | `TextCard.tsx`, `SourceChipView.tsx` | `TextCard.test.tsx` |
| G2-37 | `text.sources[]` and a following `source_chip` block with the same passage render **one** chip (contract repeats it in `ANSWER_WITH_SOURCE`) | `sourceDedupe.ts` | `TextCard.test.tsx` "one chip for ANSWER_WITH_SOURCE" |
| G2-38 | Partial reply: answered text with source + `no_info` ("I don't have that information." + person key) (S: partial; WP-1) | fixture `partial-reply` | `TextCard.test.tsx` WP-1 line; scenario |
| G2-39 | Times 12-hour, lowercase, en dash with spaces / arrow for hero; `<time datetime>`; never 24-hour (Copy rules: Times; F-14) | `Time`/`TimeWindow` fed ISO from `parts/dates.ts` | `expectNo24HourTimes` in every card test; `dates.test.ts` |
| G2-40 | Targets ≥ 44 px (tiles, day tabs, chips, buttons) (A: Targets) | `min-h-[var(--target-min)]` on every interactive part | `OptionTile`/`SlotCard` tests assert the class; DevTools check (Step 12) |
| G2-41 | Cards never steal focus, except an error on a field the customer just submitted: the invalid code field takes focus once (A: Focus order) | `CodePromptCard` focus effect guarded by a module `focused` Set | `CodePromptCard.test.tsx` |
| G2-42 | Panel landings go to the polite region (A: Live regions); mint wash is G1's panel concern | `parts/landed.ts` calls `props.landed(...)` + `props.announce(...)` once per `block_id` | per-card tests assert calls; `landed.test.ts` |
| G2-43 | Colour: red only on the safety card; errors/limits/overdue use words + icon + ink weight (Copy rules: Colour; D §4.5) | tokens only; `src/styles/guard.test.ts` | `npx vitest run src/styles` |
| G2-44 | Every scenario in the state switcher forces a real card state; ids valid; routes valid (FND F-26) | `src/dev/scenarios/scr01-cards.ts` | `src/dev/scenarios.integrity.test.ts` (FND) + `scr01-cards.test.ts` |
| G2-45 | The chat director picks the reply example from what the customer types or taps (FND §8.2 "typed words are never echoed") | `src/dev/directors/chat-cards.ts` | `chat-cards.test.ts` |
| G2-46 | A second "Talk to a person" tap returns `ALREADY_OPEN` (U: CON-4 idempotent) | reaction on `requestPerson` | `reactions/scr01-cards.test.ts` |
| G2-47 | Handoff card for `shift_ended`, `demo_reset` etc. are G1's events; the cards they contain render through the same renderers | none (renderers are pure of source) | covered by G2-25 tests |

## 4. Shared code to use (copied from the code as of planning; confirm in Step 0)

### 4.1 Frozen chat contract (FND §4.9; file `src/screens/scr01/contract.ts`, written by the foundation)
```ts
import type { ReactNode } from "react";
import type { components } from "@/api/types.gen";
export type ReplyBlock = components["schemas"]["ReplyBlock"];
export type Settled = components["schemas"]["Settled"];
export type BlockType = ReplyBlock["type"];
export type BlockOf<T extends BlockType> = Extract<ReplyBlock, { type: T }>;
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
export type BlockRenderer<T extends BlockType> = (props: BlockProps<T>) => ReactNode;
export type RendererMap = { [T in BlockType]?: BlockRenderer<T> };
```
`blocks.ts` imports `cardRenderers` from `./cards`. **Import contract types with a relative path from `cards/`:** `import type { BlockProps, ChatAction, BlockType } from "../contract";`.

### 4.2 Foundation components that exist at planning time (verified by reading the files)
```ts
// "@/components/ui" (index.ts re-exports Button, Tag, Field, Card, Skeleton, Disclosure, Dialog, LiveRegion, misc, icons)
Button({ variant?: "primary"|"secondary"|"send"|"text", density?: "chat"|"console", loading?: boolean, icon?: ReactNode, ...button props })   // loading => disabled + aria-busy
Tag({ tone?: "plain"|"strong", icon?: ReactNode, ...span props })
Field({ label: string, hint?: string, error?: string, className?, children: (ids: { id: string; describedBy: string|undefined; invalid: boolean }) => ReactNode })
TextInput({ invalid?: boolean, density?, ...input props })            // forwardRef; aria-invalid from `invalid`
Card (a <section>), CardHeader({ icon?, title: ReactNode, hint?: ReactNode, meta?: ReactNode, as?: "h2"|"h3"|"h4" }), CardBody, CardRow({ label, hint?, mono?, children })
Disclosure({ summary: ReactNode, children, open?, onOpenChange?, className? })   // native <details>
useAnnounce(): (msg: string) => void     // from LiveRegion.tsx (AnnounceProvider supplies it)
// icons ("@/components/ui" or "@/components/ui/icons"), each takes lucide props, use ICON_PROPS-like size 14-18, strokeWidth 1.8, aria-hidden:
IconHeadset IconCalendar IconClock IconTicket IconCopy IconCheck IconWarning IconDoc IconChevron IconInfo IconPhone IconQuestion IconQuote
// shared
import { Time, TimeWindow } from "@/components/shared/Time";   // Time({ iso, format: "point"|"short"|"staff"|"day"|"sentence"|"clock", variant?: "hero"|"due"|"row"|"meta", fallback? }); TimeWindow({ startIso, endIso, arrow?, variant? })
import { RefChip } from "@/components/shared/RefChip";        // RefChip({ reference, copyable? })
import { AssistantMark } from "@/components/shared/marks";
import { cn } from "@/lib/cx";
// lib/time.ts (all take an ISO string with offset)
formatTimePoint formatTimeRange formatTimeRangeArrow formatDateTimeShort formatStaffTime formatDayShort formatDayLong formatSentence formatClockLabel formatDemoDate;  DEMO_TZ = "America/Chicago"
// test helpers that exist: "@/test/no24h" expectNo24HourTimes(container: HTMLElement); "@/test/setup" (jsdom shims)
```
If a name differs when you get there (the foundation is still being finished), adjust the import **only**, never the foundation file, and note it in the g2 doc.
CSS utility classes that exist (`src/styles/base.css`, `theme.css`): `t-lead t-title t-card-title t-ref t-code t-signal t-time-hero t-time-due t-time-row t-time-meta`, `motion-control`, `motion-fade`, `sr-only`; Tailwind tokens from `@theme`: `text-small text-ui text-body text-caption`, `bg-surface bg-surface-well bg-surface-rail text-text text-text-muted border-border-hair border-border-control text-accent rounded-card rounded-control rounded-tag`. Component tokens via arbitrary values, e.g. `bg-[var(--tile-selected-bg)] border-[var(--tile-selected-edge)] min-h-[var(--target-min)]`.

### 4.3 Block shapes (copied from `src/api/types.gen.ts`; the generated file wins if it differs)
- `BlockBase`: `{ block_id: string; type: string; speaker: Speaker; at: string }`.
- `Option`: `{ option: string; label: string; disabled: boolean; reason: string | null }`. Card blocks with `card_id: string; options: Option[]; answered: string | null`: `burning_check` (+`question`), `quick_checks` (+`offer_text`, `checks: {text; source: SourceChip}[] | null`), `urgency_questions` (+`questions: {question_id; text; answers: Option[]}[]`, `skippable: true`), `where_prompt` (+`label`, `submit_label`), `locate_prompt` (+`reason_text`, `field_sets: ("name"|"phone"|"customer_id"|"invoice_number")[][]`), `code_prompt` (+`state: "sent"|"wrong"|"expired"|"locked"`, `hint`, `tries_left: number|null`, `expires_at: string|null`, `resend_offered: boolean`, `resends_left: number|null`, `inbox_link: string`, `code_in_response: "never"`), `slot_card` (+`urgent: boolean`, `days: {date; label; open_count; windows: {slot_id; date; window; window_label; technician; member_only; taken}[]}[]`, `standard_fee: {amount_cents; display}`, `hint`, `members_note: string|null`), `handoff` (+`reference`, `variant: "nobody_online"|"refund"|"staffed"`, `promise_text`, `due_at: string|null`, `due_label: string|null`, `extra_lines: string[]`, `produced_by_code: true`, `followup_chooser: FollowUpOptions`).
- `FollowUpOptions`: `{ legend: string; channels: {channel: "email"|"phone"; label: string; on_record: boolean}[]; windows: {window: "morning"|"afternoon"|"any"; label: string}[]; general_only: boolean }`.
- `text`: `{ text; sources: SourceChip[] }`; `source_chip`: `{ source }`; `SourceChip`: `{ passage_id; file; section; version_date: string|null; excerpt; audience: "customer"; version_label }`.
- `safety`: `{ level: "DANGER"; signal_word; steps: string[]; call_key: {label; number}; contact_line; case_priority: "P0"; case_reference: string|null; fixed_text: true; pinned: true }`. `conditional_safety`: `{ level: "WARNING"; text; emergency_line; case_priority: "P1"; case_reference; fixed_text: true }`. `emergency_line`: `{ lead_text; number; number_note; separate_line: string|null; case_priority: "P1"; case_reference: string }`.
- `confirmation`: `{ appointment_id; date; window_label; technician; fee_line; timeline: string[]; free_change_note }`. `appointment`: `{ appointment_id; date; window_label; technician; fee_line; label: "Your booked visit" }`. `cancelled`: `{ appointment_id; date; fee_line }`. `account_card`: `{ kind: "invoice"|"membership"|"warranty"; invoice: {invoice_id; lines: {description; amount: Money; source: SourceChip|null}[]; total: Money; balance: Money; due_on; paid} | null; membership: {tier; renewal_date} | null; warranty: {install_date; sentence} | null }`; `Money`: `{amount_cents; display}`.
- `change_request`: `{ change: "move"|"cancel"; fee_line; original_stays_line; wanted_text; windows_shown: {slot_id; window_label; date}[]; reference; promise_text; due_at: string|null; due_label: string|null; extra_lines: string[]; cant_guarantee_line: string|null; phone_support_line: string|null; produced_by_code: true }`.
- `live_queued`: `{ reference; promise_text; produced_by_code: true }`. `failure_offer` / `no_info`: `{ text; person_key: boolean }`. `notice`: `{ code: "RATE_LIMITED"|"BOOKING_CAP"|"SPEND_CAP_REACHED"|"TURN_TIMEOUT"|"BUSY"|"AI_PAUSED"; text; person_key }`. `error`: `{ code: "SLOT_TAKEN"|"OUT_OF_AREA"|"CODE_WRONG"|"CODE_EXPIRED"|"CODE_LOCKED"|"CODE_CAP_REACHED"|"NOT_VERIFIED"; text; tries_left: number|null; fresh_windows: SlotCardBlock | null; person_key }`. `session_ended`: `{ text; new_chat_action: string }`.
- `Settled`: `{ built_from; visit: SettledVisit|null; request: SettledRequest|null; identity: {status: "not_checked"|"code_sent"|"verified"|"not_verified"|"locked"; hint}; replying: {kind: "ai"|"human"; display_name}; actions: Write[] }`; `Write.kind` ∈ `"booked"|"moved"|"cancelled"|"change_request_sent"|"case_opened"|"followup_saved"|"verified"`; `SettledVisit`: `{appointment_id; date; window: "HH:MM-HH:MM"; window_label; technician; service_type; fee_line; status: "booked"|"moved"|"original_stays"; change_request}`; `SettledRequest`: `{reference; promise_text; due_at; due_label; extra_lines; live_queued; followup: FollowUpView|null}`; `FollowUpView`: `{channel; destination_label; on_record; window; saved_line}`.

### 4.4 Data facts the code depends on (verified against the OpenAPI examples)
- Dates such as `date: "2026-10-21"` are **date-only** (no offset). Passing them straight to `formatDayShort` would parse as UTC midnight and land on the previous day in Chicago. Use `parts/dates.ts` (Step 1).
- `window` is `"08:00-12:00"` (24-hour, machine); `window_label` is `"8:00 am – 12:00 pm"` (12-hour, en dash). Display `window_label`; use `window` only to build ISO for `<time datetime>`.
- `SLOT_CARD.options[]` lists open windows only; `option` equals the window's `slot_id`. Taken windows exist only in `days[].windows[]` with `taken: true`.
- `ANSWER_WITH_SOURCE` returns a `text` block whose `sources[0]` is **identical** to the following `source_chip` block (blk-201 / blk-202).
- `CHANGE_REQUEST.extra_lines[1]` **equals** `cant_guarantee_line`.
- `CODE_WRONG` / `CODE_EXPIRED` examples return **two** blocks: an `error` block (carries the sentence) then a `code_prompt` (`state: "wrong"` / `"expired"`).
- `CODE_LOCKED`, `CODE_CAP_REACHED`, `NOT_VERIFIED` return an `error` block (same sentence, `person_key: true`) then a `handoff` block.
- `TURN_TIMEOUT` block has no turn id; the id is only in the top-level `notice.retry_turn_id`, which `BlockProps` does not carry (§8 C-2).
- `BOOKED.settled.actions` kinds: `["verified","booked"]`; `CANCELLED.settled.actions`: `["verified","booked"]` (**no** `cancelled` entry although `CANCELLED.writes` has one) — so the cancelled guard must read **`writes` or `actions`**, and `BlockProps` has only `settled`. See Step 8: the guard for `cancelled` accepts either `settled.actions` `cancelled` **or** `settled.visit === null` after a booking; implement `hasWrite(settled,"cancelled")` as `actions.some(kind==="cancelled")` and make the **test fixture** for `CANCELLED` add the missing action (documented fixture, §6). In the live mock the cancelled card will therefore render without its completion sentence; record it in the g2 doc as contract request C-9.

## 5. Steps (build order; each step ends with a check)

Work in `/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/`. Node v24. Disk: `df -h /home` ≥ 3 GB free.

### Step 0 · Preflight (no code)
1. `ls src/screens/scr01/contract.ts src/screens/scr01/blocks.ts src/screens/scr01/cards/index.ts src/test/render.tsx src/dev/scenarios/scr01-cards.ts src/dev/reactions/scr01-cards.ts src/dev/directors/chat-cards.ts src/dev/scenarios/types.ts`. **All must exist.** If any is missing the foundation is not finished: stop and report `BLOCKED-ON foundation <names>`; write nothing.
2. Read `src/screens/scr01/contract.ts` and `blocks.ts`; confirm the types in §4.1. Read `src/dev/scenarios/index.ts` and find the `slug` the `scr01-cards` entry uses in `SCENARIO_FILES` (call it `SLUG`; expected `"scr01-cards"`). Read `src/dev/scenarios/types.ts` for `OpForce`, `Scenario`, `Reaction`, `DirectorRule` and `DevCtx` exactly as defined (FND §4.9).
3. Read one existing component test, e.g. `src/components/shared/*.test.tsx`, to copy the house test style (`renderWithProviders` import path, `userEvent.setup()`).
**Check:** you can state the slug and the three dev file shapes.

### Step 1 · Pure parts (dates, promise) and their tests
1. `parts/dates.ts`:
```ts
import { DEMO_TZ } from "@/lib/time";
/** "2026-10-21", "08:00" -> "2026-10-21T08:00:00-05:00" (Chicago offset for that date, via Intl longOffset). */
export function chicagoIso(date: string, hhmm: string): string;
export function windowIsos(date: string, window: string): { startIso: string; endIso: string };   // window "08:00-12:00"
export function dayIso(date: string): string;                 // chicagoIso(date, "12:00"): safe input for formatDayShort/formatDayLong
export function spokenWindow(windowLabel: string): string;    // "8:00 am – 12:00 pm" -> "8:00 am to 12:00 pm"
export function formatMonthDayYear(date: string): string;     // "2026-11-01" -> "Nov 1, 2026"
```
Offset: `new Intl.DateTimeFormat("en-US", { timeZone: DEMO_TZ, timeZoneName: "longOffset" }).formatToParts(new Date(`${date}T${hhmm}:00Z`))` → part `timeZoneName` value `"GMT-05:00"` → `"-05:00"`; `"GMT"` → `"+00:00"`. (Invariant: the ISO fed to the shared formatters always carries the correct Chicago offset, so they print the intended wall-clock time.) `formatMonthDayYear`: `Intl.DateTimeFormat("en-US",{timeZone:DEMO_TZ,month:"short",day:"numeric",year:"numeric"}).format(new Date(dayIso(date)))`.
2. `parts/promise.ts`:
```ts
/** UXR-19: "{promise_text}, {due_label}. {extra_lines…}". `omit` removes lines shown elsewhere (exact string match). */
export function joinPromise(p: { promise_text: string; due_label: string | null; extra_lines: string[] }, omit?: Array<string | null>): string;
```
Steps: (a) `lead = due_label ? `${promise_text}, ${due_label}.` : promise_text`; (b) if `lead` does not end with `.`, `!` or `?`, append `.`; (c) `lines = extra_lines.filter(l => !omit?.includes(l))`; (d) return `[lead, ...lines].join(" ")`.
3. Tests (write now, run them):
   - `parts/dates.test.ts`: `chicagoIso("2026-10-21","08:00") === "2026-10-21T08:00:00-05:00"`; `chicagoIso("2026-11-02","08:00") === "2026-11-02T08:00:00-06:00"`; `windowIsos("2026-10-21","12:00-16:00")` → `{ startIso: "2026-10-21T12:00:00-05:00", endIso: "2026-10-21T16:00:00-05:00" }`; `formatDayShort(dayIso("2026-10-21")) === "Wed Oct 21"`; `formatDayLong(dayIso("2026-10-21")) === "Wednesday, October 21, 2026"`; `spokenWindow("8:00 am – 12:00 pm") === "8:00 am to 12:00 pm"`; `formatMonthDayYear("2026-11-01") === "Nov 1, 2026"`.
   - `parts/promise.test.ts`, expected strings **exactly** (these are SCREEN_SPECS "Promise texts" word for word):
     - `HANDOFF` → `"No representative is online right now. A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm. Your reference is MHC-C-0007."`
     - `HANDOFF_STAFFED` → `"A representative will join this chat when available. You can keep chatting with me while you wait, if you like. Your reference is MHC-C-0007."`
     - `CHANGE_REQUEST` with `omit=[cant_guarantee_line]` → `"No representative is online right now. A representative will get back to you within 1 business day, by Saturday, October 17, 12:00 pm. Your reference is MHC-C-0009."`
     - refund fixture: `promise_text "A representative will get to your refund request within 2 business days."`, `due_label null`, `extra_lines ["I can't promise an outcome.", "Your reference is MHC-C-0007."]` → `"A representative will get to your refund request within 2 business days. I can't promise an outcome. Your reference is MHC-C-0007."`
**Check:** `npx vitest run src/screens/scr01/cards/parts` green.

### Step 2 · Test helpers and shared UI parts
1. `testing/examples.ts` (imported by tests and by `src/dev/**/*.test.ts` only):
```ts
import type { components } from "@/api/types.gen";
export type TurnResponse = components["schemas"]["TurnResponse"];
/** Parses ../../docs/ux/03-structure/ui-contracts.openapi.yaml (path from process.cwd(), which is apps/web under vitest) with the `yaml` package. */
export function turnExample(name: string): TurnResponse;                         // submitTurn 200 example `value`
export function turnExampleNames(): string[];                                    // the 37 names
export function chatThreadExample(name: "OPEN" | "ENDED_BLOCK"): components["schemas"]["ChatThread"];
export function handoffExample(name: "CASE_CREATED" | "LIVE_QUEUED" | "ALREADY_OPEN"): components["schemas"]["HandoffResponse"];
export function schemaBlockTypes(): string[];                                    // the 24 `ReplyBlock` discriminator values
export function blockOf<T extends BlockType>(res: TurnResponse, type: T, index?: number): BlockOf<T>;
```
2. `testing/props.tsx`: `makeProps<T extends BlockType>(block: BlockOf<T>, over?: Partial<BlockProps<T>>): BlockProps<T> & { dispatch: Mock; announce: Mock; landed: Mock }` (use `vi.fn()`; defaults `settled: null, answered: false, disabled: false`, `dispatch: vi.fn().mockResolvedValue(undefined)`); `renderCard(ui: ReactElement)` = `renderWithProviders(ui)` from `@/test/render`.
3. `parts/useCardAction.ts`:
```ts
export function useCardAction(dispatch: (a: ChatAction) => Promise<void>): { pending: boolean; run(a: ChatAction): Promise<boolean> };
```
`run`: if a call is in flight return `false` immediately (double-tap guard); set `pending`; `await dispatch(a)`; return `true`; on rejection return `false` (G1 shows the error line); always clear `pending` if still mounted.
4. `parts/landed.ts`:
```ts
export type LandProps = { landed(t: "visit" | "request" | "identity"): void; announce(m: string): void };
/** On the first mount per block_id: props.landed(target) then props.announce(message). Remounts (StrictMode, history reload) do nothing. */
export function useLandedOnce(blockId: string, target: "visit" | "request" | "identity", message: string, props: LandProps): void;
export function resetLandedForTests(): void;
```
Implementation: module `Set<string>`; `useEffect(() => { if (set.has(blockId)) return; set.add(blockId); props.landed(target); props.announce(message); }, [])`. Test `landed.test.ts`: two renders of the same id → one call each.
5. `parts/OptionTile.tsx`:
```tsx
export interface OptionTileProps { label: ReactNode; accessibleName?: string; selected?: boolean; disabled?: boolean; taken?: boolean; tag?: ReactNode; onClick(): void; className?: string }
```
A `<button type="button" aria-pressed={selected}>`; classes: `min-h-[var(--target-min)] rounded-control border border-[var(--tile-edge)] bg-[var(--tile-bg)] px-3 text-ui motion-control`; selected: `bg-[var(--tile-selected-bg)] border-2 border-[var(--tile-selected-edge)] font-semibold` + `<IconCheck/>`; taken: `bg-[var(--tile-taken-bg)] text-[var(--tile-taken-text)]`, the label `line-through`, the visible word **Taken** (`text-caption font-semibold`), `disabled` + `aria-disabled`. `aria-label={accessibleName}`. The check appears at once (draw animation not built: no keyframes in `base.css`; request R-3).
6. `parts/CardParts.tsx` (small exports, one file under 200 lines):
   - `InlineNotice({ icon?, children, role?: "alert"|"status", id? })`: row with `IconInfo` 14 px and `text-small`; ink only.
   - `DoneLine({ children })`: `IconCheck` + text, `text-ui`.
   - `PersonKey({ dispatch }: { dispatch: BlockProps<BlockType>["dispatch"] })`: secondary `Button` with `IconHeadset`, text **Talk to a person**, `onClick` → `dispatch({ kind: "person" })`; guarded against re-entry with a ref; **never `disabled`**.
   - `StepList({ steps }: { steps: { text: string; state: "done" | "current" | "todo"; at?: string }[] })`: `<ol>`; done = `IconCheck`; current = `aria-current="step"` + weight 600; todo = muted; optional `<Time format="point" variant="meta">` after text.
   - `HintLine({ id?, children })` (`text-small text-text-muted`).
   - `hasWrite(settled: Settled | null, kind: Write["kind"]): boolean` = `Boolean(settled?.actions.some(a => a.kind === kind))`.
   - `choiceKept(block: { answered: string | null }, props: { answered: boolean }): boolean` = `props.answered || block.answered !== null`.
7. Tests: `parts/useCardAction.test.tsx` (second call while pending is ignored; rejection → `false`), `parts/OptionTile.test.tsx` (selected has check + `aria-pressed="true"`; taken is disabled, shows "Taken" and `line-through`; class contains `min-h-[var(--target-min)]`), `parts/CardParts.test.tsx` (`PersonKey` stays enabled and dispatches `{kind:"person"}`; `hasWrite`).
**Check:** `npx vitest run src/screens/scr01/cards/parts` green; `npm run typecheck`.

### Step 3 · Text and source chips
- `sourceDedupe.ts`: `markChipRendered(at: string, passageId: string): void`, `chipAlreadyRendered(at: string, passageId: string): boolean` over a module `Map<string, Set<string>>` keyed by the block's `at`; both idempotent (React StrictMode double render is safe). `resetDedupeForTests()`.
- `SourceChipView.tsx`: `SourceChipView({ source }: { source: SourceChip })` = `Disclosure` whose summary is a chip (`min-h-[var(--target-min)]`, `bg-[var(--chip-bg)] border border-[var(--chip-edge)] rounded-control`): `IconDoc`, the word **Source**, `source.file` in mono 12 px (`t-ref`), `source.section`, `source.version_label` muted. Never `version_date`. Open body: a `text-small text-text-muted` line **Where this comes from**, then the `excerpt` in a `bg-surface-well` block (`text-ui`, `IconQuote` leading). `aria-label` on the summary: `Source: {file}, {section}, {version_label}`.
- `TextCard.tsx`: `TextCard(props: BlockProps<"text">)`: `<p className="text-body whitespace-pre-line">{block.text}</p>` then, for each `sources[i]`, `markChipRendered(block.at, source.passage_id)` and `<SourceChipView/>`. `SourceChipCard(props: BlockProps<"source_chip">)`: returns `null` when `chipAlreadyRendered(block.at, block.source.passage_id)`, else `<SourceChipView/>`.
- Test `TextCard.test.tsx`: renders `ANSWER_WITH_SOURCE` blocks in order inside one container → exactly **one** element with the accessible name `Source: policies/fee_schedule_2026.pdf, After-hours dispatch, Effective Jan 1, 2026`; clicking it shows "After-hours dispatch: $149."; text "Where this comes from" present; no `2026-01-01` string (no invented date). **WP-1 line:** render fixture `partial-reply` (§6): the text with one chip, then "I don't have that information." and an enabled "Talk to a person". `expectNo24HourTimes`.
**Check:** `npx vitest run src/screens/scr01/cards/TextCard.test.tsx`.

### Step 4 · Safety and emergency (the only red)
`SafetyCard.tsx` (the filename must contain `Safety`; the guard test only lets such files read `--safety-*`, `--color-safety`, `--color-on-safety`, `--focus-ring-on-safety`, `radius-sharp`). Exports `SafetyCard(props: BlockProps<"safety">)` and `ConditionalSafetyCard(props: BlockProps<"conditional_safety">)`; one internal `SafetySheet` renders both.
1. Fragment = `<section aria-label=…>` (the sheet) + a quiet `<p className="text-small text-text-muted">` line. Sheet: `rounded-none bg-[var(--safety-bg)]`, `style={{ borderBottom: "var(--line-safety)" }}`.
2. Band: `bg-[var(--safety-band-bg)] text-[var(--safety-band-text)] px-4 py-2.5 flex items-center gap-2`: `<IconWarning size={18}/>` and `<span className="t-signal">{signal}</span>`; `signal = block.signal_word` (safety) or `block.level` (conditional).
3. Safety body: `<ol className="t-title list-decimal pl-9 pr-4 py-3 space-y-1">` with `block.steps` verbatim (the generated copy is Meridian's: "Leave the home immediately and call 911 or your gas utility from outside." / "Don't flip switches, open windows near the furnace, or restart equipment."). Call button: `<a href={`tel:${digits(block.call_key.number)}`}>` styled as the red 48 px square button: `block min-h-12 rounded-none bg-[var(--safety-btn-bg)] text-[var(--safety-btn-text)] focus-visible:outline-[var(--focus-ring-on-safety)] text-center font-semibold`, text `block.call_key.label` ("Call 911 (from outside)"), full content width. `digits(n) = n.replace(/[^\d+]/g, "")`. Under the sheet: `block.contact_line` ("Once you're outside and safe, you can leave a number here if you'd like.").
4. Conditional body: `<p className="t-title …">{block.text}</p>` then `<p className="text-ui …">{block.emergency_line}</p>`. No call button (the block has no `call_key`). The sentence "Meridian's 24/7 emergency number is (512) 555-0199 (demo number)." stays plain text.
5. Announce once: module `const alerted = new Set<string>()`; `const [first] = useState(() => { const f = !alerted.has(block.block_id); alerted.add(block.block_id); return f; })` (initialiser runs once per mount); then `role={first ? "alert" : undefined}`. (G1 may mount the same safety block in the pinned region and the thread: only the first mounted gets the alert.) `aria-label`: safety `"Danger: safety instruction"`, conditional `"Warning: safety instruction"`.
6. No `landed`, no `announce`, no motion class, no `case_reference` shown, no time, no "business day", no "due".
`EmergencyLineCard.tsx`: `EmergencyLineCard(props: BlockProps<"emergency_line">)`: `<Card style={{ border: "var(--line-emergency)" }}>` (heavier 2 px ink edge; not red); body with `IconPhone`, `<p className="text-body">{lead_text}</p>`, then `<a href={`tel:${digits(number)}`} className="t-title inline-flex min-h-[var(--target-min)] items-center">{number} {number_note}</a>`; when `separate_line` is non-null: `<hr className="border-t border-dashed border-border-hair">` then `<p className="text-ui">{separate_line}</p>`. No Due/reference rows.
Tests: `SafetyCard.test.tsx`:
- `it("WP-5: the SAFETY example renders Meridian's two instructions verbatim and no follow-up time")`: the two `li` texts equal the two `steps`; link name "Call 911 (from outside)" has `href="tel:911"`; `contact_line` present; text does not match `/business day|within|due|reference|MHC-C-/i`; `expectNo24HourTimes`; the sheet has `aria-label="Danger: safety instruction"`; no button/input/textarea in the sheet.
- `it("announces once even when rendered twice")`: render the same block twice (two containers) → exactly one `[role=alert]` in total.
- `it("CONDITIONAL_SAFETY shows WARNING and the emergency-number line, no 911 button")`.
`EmergencyLineCard.test.tsx`: `EMERGENCY_LINE` has the number link `href="tel:5125550199"`, the separate line after a divider; fixture `emergency-line-staffed` (§6) has no `hr` and no "1 business day"; no 24-hour times.
**Check:** `npx vitest run src/screens/scr01/cards/SafetyCard.test.tsx src/screens/scr01/cards/EmergencyLineCard.test.tsx src/styles`.

### Step 5 · Choice, where, locate, code cards
All use `useCardAction(props.dispatch)`; `locked = choiceKept(block, props) || props.disabled || pending`; a card never moves focus.
**`ChoiceCards.tsx`:**
- `BurningCheckCard`: `Card` (no header) with `<p className="text-body">{question}</p>` and a row of `OptionTile`s from `options`; click → `run({ kind: "choice", cardId: block.card_id, option: o.option })`; chosen tile = `block.answered === o.option` or the locally picked one; others disabled when locked.
- `QuickChecksCard`: `<p>{offer_text}</p>`; the option whose `option === "skip_and_book"` is a **primary** `Button`; every other option is a secondary `Button` (`show_checks`). Exactly one primary. When `block.checks` is non-null render `<ul>` of `check.text` each followed by `SourceChipView`.
- `UrgencyQuestionsCard`: for each question a `<fieldset><legend className="text-body">{text}</legend>` with answer `OptionTile`s (yes/no/skip). Local `answers: Record<question_id, option>`. **One turn per card (decision C-1):** when every question has an answer, dispatch once `{ kind: "choice", cardId, option: questions.map(q => `${q.question_id}:${answers[q.question_id]}`).join(";") }` (example `"temp:yes;water:no;risk:skip"`). A block-level text button **Skip** (from `block.options`, option `"skip"`) dispatches `{ kind:"choice", cardId, option:"skip" }` and locks the card. Answered/locked: tiles disabled, choices kept.
- Test `ChoiceCards.test.tsx`: BURNING_CHECK buttons "Yes" "No" "Not sure"; click "No" → dispatch `{kind:"choice",cardId:"burn-1",option:"no"}`; with `answered:"no"` all disabled and "No" has `aria-pressed="true"`; QUICK_CHECKS has one primary; fixture `quick-checks-shown` lists two checks each with a Source chip; URGENCY_QUESTIONS: answering the three questions yields one dispatch `"temp:yes;water:no;risk:skip"`; "Skip" yields `"skip"`.

**`WherePromptCard.tsx`:** `Card`; `Field label={block.label}` + `TextInput` (`name="zip_or_city"`, `autoComplete="postal-code"`); primary `Button` `{block.submit_label}`; submit (form `onSubmit`, Enter works) with trimmed non-empty value → `run({ kind: "form", cardId, values: { zip_or_city } })`; empty → `Field error="Enter a ZIP code or city."` (client copy). Locked → input disabled showing the value, button disabled.
**`LocatePromptCard.tsx`:** `CardHeader` with icon `IconUser`, title **Verify**, hint **Prove it's your account**, meta **Before booking**. Body: `<p>{reason_text}</p>`; the active field set = `field_sets[active]` (default 0). Labels: `name` → "Name on the account", `phone` → "Phone" (`type="tel"`, `autoComplete="tel"`), `customer_id` → "Customer ID", `invoice_number` → "Invoice number". When `field_sets.length > 1`, below the fields a row of text `Button`s switching set: "Use my customer ID instead" / "Use my invoice number instead" / "Use my name and phone instead" (generated from the other sets' keys; client copy). Primary **Send the code**; hint line "Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries." All fields of the active set required; missing → `Field error="Fill in every field above."`. Submit → `run({ kind:"form", cardId, values })` with **only** the active set's keys. Never log values.
**`CodePromptCard.tsx`:** `CardHeader icon=<IconUser/>` title **Verify**, hint **Prove it's your account**, meta by state: sent/wrong/expired → "Code sent", locked → "Locked". Body:
- instruction `t-lead`: `I've sent a 6-digit code to {block.hint}. Please type it here.`
- `Field label="6-digit code"` + `TextInput` with `className="t-code"`, `inputMode="numeric"`, `autoComplete="one-time-code"`, `pattern="[0-9]*"`, `maxLength={6}`, `invalid={state==="wrong"||state==="expired"}`; **disabled** when `state==="locked"` or `state==="expired"` or locked.
- Primary **Verify** (shown for `sent`/`wrong`): submit with exactly 6 digits → `run({ kind:"code", cardId, code })`, then `setValue("")`. Not 6 digits → `Field error="Enter the 6-digit code."` (client copy).
- `state==="expired"` and `block.resend_offered`: replace Verify with a primary **`{options.find(o => o.option==="resend").label}`** (example "Send a new code") → `run({ kind:"choice", cardId, option:"resend" })`. `resend_offered === false`: no button.
- `state==="locked"`: no Verify, no resend.
- Text link `<a href={block.inbox_link} target="_blank" rel="noopener noreferrer" className="link-text">Open the demo inbox →</a>` (shown unless locked); hint line "Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries."
- Focus: when `state === "wrong"`, not locked, focus the input once on mount; module `focused: Set<block_id>` (decision: no other card ever focuses).
- The code is never echoed in any announcement and never stored beyond the input state.
- Tests: `WherePromptCard.test.tsx`, `LocatePromptCard.test.tsx` (FORM_LOCATE fields; switching to the customer-ID set posts only `customer_id`), `CodePromptCard.test.tsx` (CODE_SENT: label, attributes `inputmode="numeric"`, `autocomplete="one-time-code"`; typing `482913` + Verify → `dispatch({kind:"code",cardId:"code-1",code:"482913"})` and the input is cleared; 5 digits → inline error and no dispatch; CODE_WRONG's code_prompt → `aria-invalid="true"` and `document.activeElement` is the input; CODE_EXPIRED → "Send a new code" dispatches `option:"resend"`, no Verify, input disabled; CODE_LOCKED handoff path not here; a code_prompt with `resend_offered:false,state:"expired"` has no resend button; inbox link `target="_blank"` and `href="/demo/inbox"`).
**Check:** `npx vitest run src/screens/scr01/cards/ChoiceCards.test.tsx src/screens/scr01/cards/WherePromptCard.test.tsx src/screens/scr01/cards/LocatePromptCard.test.tsx src/screens/scr01/cards/CodePromptCard.test.tsx`.

### Step 6 · Slot card
`SlotCard.tsx`: `SlotCard(props: BlockProps<"slot_card">)`; reused by `ErrorCard` for `fresh_windows` (pass the nested block with the same other props).
1. `CardHeader icon=<IconCalendar/> title="Choose a window" hint="The technician arrives any time in the window you pick" meta="this week"`; when `block.urgent` add `Tag tone="strong"` "Urgent" right of the title (inside `meta`).
2. Day tabs: `@radix-ui/react-tabs` (`Tabs.Root value onValueChange`, `Tabs.List aria-label="Day"`, `Tabs.Trigger`, `Tabs.Content`). Default value = first day with `open_count > 0`, else the first day. Each trigger `min-h-[var(--target-min)]`: line 1 = `label.split(" · ")[0]` (e.g. "Wed 21"), line 2 = the rest ("2 open" / "Full"); no separator → whole label on one line. Active = weight 600 + `border-b-2 border-[var(--tab-underline)]`. The tab list scrolls horizontally inside the card (`overflow-x-auto`), never the page.
3. Window tiles in a two-column grid (`grid grid-cols-2 gap-2`): `OptionTile`; label `window_label` (class `t-time-row`); `taken` → `taken`; `member_only` → `tag=<Tag>Members</Tag>`; `accessibleName`: `` `${window_label}, open` `` (or `, taken` / `, members only`). Selection: local `picked` (slot_id) initialised from `block.answered`; selected tile mint + 2 px emerald.
4. Rows: `CardRow label="Standard fee" hint="What you pay if you're not a member"` value `standard_fee.display`. `HintLine` with `block.hint` ("Windows are shown, not held."); when `members_note` non-null another `HintLine`.
5. Footer primary `Button` **Continue with this window**: disabled until `picked` set, and when `locked`; click → `run({ kind:"choice", cardId: block.card_id, option: picked })`. While nothing is picked show `HintLine` "Choose a window to continue." (client copy).
6. Answered: the picked tile stays selected; Continue disabled; nothing else changes. Taken tiles are never focusable.
Test `SlotCard.test.tsx`: SLOT_CARD: default tab "Wed 21", tiles "8:00 am – 12:00 pm, open" and "12:00 pm – 4:00 pm, open"; switch to the "Mon 19" tab → its tile is disabled, shows "Taken", has `line-through`; Continue disabled → click the first tile → enabled → click → dispatch `{kind:"choice",cardId:"slots-7",option:"56"}`; `answered:true` + `block.answered:"56"` → tile 56 `aria-pressed="true"`, Continue disabled; SLOT_CARD_MEMBER: a "Members" tag on the 4:00 pm tile, no `members_note`; fixture `slot-card-urgent` shows "Urgent"; `expectNo24HourTimes`.
**Check:** `npx vitest run src/screens/scr01/cards/SlotCard.test.tsx`.

### Step 7 · Account, visits, change request
**`AccountCard.tsx`** (`AccountCard(props: BlockProps<"account_card">)`): `CardHeader icon=<IconDoc/>`; title `Invoice {invoice_id}` / `Membership` / `Warranty`. Invoice: `<p className="t-time-hero">{balance.display}</p>` (money in the hero style), caption `` `Balance · ${paid ? "paid" : "unpaid"} · due ${formatMonthDayYear(due_on)}` ``, then `<table>` with `<caption className="sr-only">Invoice lines</caption>`, rows `description` (+ `SourceChipView` when `source`) and amount (right, tabular), a `tfoot` total row with `border-t border-[var(--color-text)]`-equivalent: use `border-t border-text`. **No verdict words** (no "overcharged", "error", "should"). Membership: `CardRow label="Tier"` → `tier`; `CardRow label="Renewal date"` → `formatMonthDayYear(renewal_date)`. Warranty: `CardRow label="Install date"` → `formatMonthDayYear`; `<p>{sentence}</p>`.
**`VisitCards.tsx`:**
- `ConfirmationCard`: `CardHeader icon=<IconCheck/> title="Your visit" hint="Your booking" meta={hasWrite(settled,"booked")||hasWrite(settled,"moved") ? <Tag icon={<IconCheck/>}>Booked</Tag> : null}`. Hero: `<TimeWindow arrow variant="hero" {...windowIsosFromLabel}/>`. **ISO for the window:** the confirmation block has only `date` and `window_label` (no `HH:MM-HH:MM`); take `settled?.visit?.window` when `settled.visit.appointment_id === block.appointment_id`; otherwise parse `window_label` with `/^(\d{1,2}):(\d{2}) (am|pm) – (\d{1,2}):(\d{2}) (am|pm)$/` into 24-hour parts and call `chicagoIso` (`parseWindowLabel(label): {start:string,end:string}|null` in `dates.ts`; if it returns null render `window_label` as plain text). Sentence `text-ui text-text-muted`: `` `${formatDayLong(dayIso(date))} · arrives between ${start12} and ${end12}` `` where `start12/end12` are `formatTimePoint(startIso)`/`formatTimePoint(endIso)`. Rows: `Date` → `<Time iso={dayIso(date)} format="day" variant="row"/>`, `Technician`, `Fee that applies` → `fee_line`. **What happens next:** `StepList` from `timeline` (index 0 `done` with `at={block.at}`, index 1 `current`, rest `todo`), then `free_change_note` in `text-ui`. Foot: `CardRow label="Keep this" hint="Save or screenshot this"` → `` `${formatDayShort(dayIso(date))} · ${window_label}` ``. `useLandedOnce(block.block_id, "visit", `Your visit: ${formatDayLong(dayIso(date))}, ${spokenWindow(window_label)}`, props)`. No button.
- `AppointmentCard`: same header (`title={block.label}`, no Booked tag), hero, rows Date/Technician/Fee that applies; no timeline, no landing.
- `CancelledCard`: only if `hasWrite(settled,"cancelled")` → `DoneLine` `` `Your visit on ${formatDayShort(dayIso(date))} is cancelled.` `` then `<p>{fee_line}</p>`; otherwise only `<p>{fee_line}</p>` with no "cancelled" word. `useLandedOnce(…, "visit", `Visit on ${formatDayShort(...)} cancelled`)` only in the guarded branch.
**`ChangeRequestCard.tsx`:** `CardHeader icon=<IconTicket/> title="Change request" hint="Waiting for a representative to confirm" meta=<RefChip reference copyable/>`. Rows (`CardRow`): **Your visit stays** → if `settled?.visit` (status `original_stays` or any) `<TimeWindow variant="due" …windowIsos(visit.date, visit.window)/>` + `<Time iso={dayIso(visit.date)} format="day" variant="meta"/>`; if no `settled.visit` omit the row and rely on `original_stays_line`. **Requested** → `wanted_text` (normal weight, not struck). **Fee** → `fee_line`. Then `<p className="text-ui">{original_stays_line}</p>`; `HintLine` "Windows are shown, not held." followed by `windows_shown` as a plain list (`window_label` + `<Time iso={dayIso(date)} format="day" variant="meta"/>`); then the promise `<p className="t-lead">{joinPromise(block, [block.cant_guarantee_line, block.phone_support_line])}</p>`; `Due` row (`hint="The latest we've promised to get back to you"`) only if `due_at` non-null (`<Time format="short" variant="row">`); then `cant_guarantee_line` and `phone_support_line` each as their own `<p>` when non-null (**once each**, because `extra_lines` also holds the first). Never a Button. `useLandedOnce(block.block_id, "request", `Your request: ${reference}`, props)`.
Tests: `AccountCard.test.tsx` (VERIFIED_ACCOUNT_INVOICE: the invoice lines, total "$478.00" and balance "$478.00", "Balance · unpaid · due Nov 1, 2026", source chip on the after-hours line; no `/overcharg|wrong|should|error/i`; ACCOUNT_MEMBERSHIP "Comfort Plus", "Mar 14, 2027"; ACCOUNT_WARRANTY sentence). `VisitCards.test.tsx` (BOOKED with its example `settled`: hero text via `time` elements "8:00 am" and "12:00 pm" with the visually hidden "to", sentence "Wednesday, October 21, 2026 · arrives between 8:00 am and 12:00 pm", Booked tag, timeline three steps with the second `aria-current="step"`; same block with `settled:{…actions:[]}` → **no** word "Booked"; `landed` called once with `"visit"`; APPOINTMENT label "Your booked visit"; CANCELLED with the fixture settled (adds a `cancelled` action) → "Your visit on Wed Oct 21 is cancelled." and "There's no fee.", without it only "There's no fee."). `ChangeRequestCard.test.tsx`: `it("WP-4: CHANGE_REQUEST shows fee, original-stays and cannot-guarantee once each, and never says charged or sent")` → each of the three sentences appears exactly once (`getAllByText` length 1); text has no `/\bcharged\b|\bsent\b/i`; no `button` in the card; "Due" row shows "Sat Oct 17 · 12:00 pm"; with fixture `change-request-staffed` (§6) no Due row and the phone line "Phone support is open until 7:00 pm today if you'd like to call." appears once; cancel fixture uses the same markup.
**Check:** `npx vitest run src/screens/scr01/cards/AccountCard.test.tsx src/screens/scr01/cards/VisitCards.test.tsx src/screens/scr01/cards/ChangeRequestCard.test.tsx`.

### Step 8 · Handoff, follow-up chooser, live-queued
**`HandoffCard.tsx`** (`HandoffCard(props: BlockProps<"handoff">)`): `CardHeader icon=<IconTicket/> title="Your request" hint="Your reference number" meta=<RefChip reference={block.reference} copyable/>`. Body: `<p className="t-lead">{joinPromise(block)}</p>`; `CardRow label="Due" hint="The latest we've promised to get back to you"` → `<Time iso={block.due_at} format="short" variant="row"/>` **only if `due_at` non-null**; `CardRow label="Status"` → `<Tag icon={<IconClock/>}>Waiting for a representative</Tag>`. Then `FollowUpChooser`. No countdown, no queue position, no "shortly". `useLandedOnce(block.block_id, "request", `Your request: ${block.reference}`, props)`.
**`FollowUpChooser.tsx`:** props `{ block: BlockOf<"handoff">; settled: Settled | null; dispatch; announce; landed; disabled }`. If `settled?.request?.reference === block.reference && settled.request.followup` → `DoneLine` with `followup.saved_line` and nothing else (saved; no inputs). Else: `<fieldset><legend>{chooser.legend}</legend>` native radios in `OptionTile`-looking labels (`<label>` with a native `<input type="radio" name="channel-{block_id}">`, `min-h-[var(--target-min)]`), one per `chooser.channels` (label text = `channel.label`, e.g. "Email · the address on your account"); default checked = `email` channel if present. When `phone` is selected show a second fieldset `<legend>Best time to call</legend>` with radios from `chooser.windows` (default `any`). Primary **Save my choice** (`loading={pending}`): `destination = chooser.general_only || !channel.on_record ? "general" : "on_record"`; `window = channel==="phone" ? chosenWindow : "any"`; `run({ kind:"followUp", channel, destination, window })`; on `true` → `props.landed("request")` and `props.announce("Follow-up saved")`. Disabled when `props.disabled`. Nothing in the UI says a message was sent.
**`LiveQueuedCard.tsx`:** `CardHeader icon=<IconClock/> title="Your request" meta=<RefChip/>`; `<p>{promise_text}</p>`; `StepList` three steps: "You asked for a person" (`done`), "A representative joins this chat" (`current`, or `done` when `settled?.replying.kind === "human"`), "Back to the assistant, or the chat closes" (`todo`, or `current` when human). `useLandedOnce(..., "request", …)`.
Tests: `HandoffCard.test.tsx`: HANDOFF renders the joined promise sentence (§5 Step 1), "Due" "Mon Oct 19 · 7:00 pm", Status tag, reference chip; `HANDOFF_STAFFED` has no Due row and no time; refund fixture sentence; choose Phone call → "Best time to call" appears → Mornings → Save → `dispatch({kind:"followUp",channel:"phone",destination:"on_record",window:"morning"})`; default Save → `{channel:"email",destination:"on_record",window:"any"}`; fixture `handoff-general-only` → destination `"general"`; with `settled.request.followup` (copied from `saveFollowUp` `PHONE_MORNINGS`) → the card shows exactly "Follow-up saved: phone call, the number ending in 02, mornings." and no radios; `landed` called once with `"request"`; no `/shortly|queue position|charged|\bsent\b/i`. `LiveQueuedCard.test.tsx`: LIVE_QUEUED three steps, second `aria-current`; with `settled.replying = {kind:"human",display_name:"Riley"}` the second is done.

### Step 9 · Notices, offers, errors, session ended
**`NoticeCards.tsx`:**
- `NoticeCard(props: BlockProps<"notice">)` switch on `block.code`:
  - `RATE_LIMITED` / `BOOKING_CAP` / `SPEND_CAP_REACHED`: `Card` neutral: `IconInfo`, `<p className="text-body">{text}</p>`, `PersonKey` if `person_key`. No primary.
  - `TURN_TIMEOUT`: `Card` with `CardHeader icon=<IconClock/> title={block.text}`; buttons: primary **Try again** → `run({ kind:"retry", turnId:"" })` (`loading={pending}`; disabled when `props.answered`), then `PersonKey`.
  - `BUSY`: no card: `<p className="text-body">{text}</p>` + `PersonKey`.
  - `AI_PAUSED`: `InlineNotice` with the text; `PersonKey` only if `person_key`.
- `FailureOfferCard`, `NoInfoCard`: `<p className="text-body">{text}</p>` + `PersonKey` when `person_key`.
**`ErrorCard.tsx`** (`ErrorCard(props: BlockProps<"error">)`):
- `CODE_WRONG`, `CODE_EXPIRED`: `InlineNotice role="alert"` with `block.text` (this is the visible sentence for the code field; the paired `code_prompt` supplies the invalid field styling only). No person key.
- `SLOT_TAKEN`: `InlineNotice role="status"` with `block.text`, then `<SlotCard {...props} block={block.fresh_windows} />` when `fresh_windows` is non-null.
- `OUT_OF_AREA`: `InlineNotice role="status"` + `PersonKey` if `person_key`.
- `CODE_LOCKED`, `CODE_CAP_REACHED`, `NOT_VERIFIED`: **one shared branch**: `InlineNotice role="status"` with `block.text` + `PersonKey` when `person_key`; no code-specific class, id or text.
**`SessionEndedCard.tsx`:** a centred quiet block: `InlineNotice` with `block.text`; primary **`{block.new_chat_action}`** ("Start a new chat") → `dispatch({ kind:"newChat" })`; ignores `disabled`.
Tests: `NoticeCards.test.tsx` (RATE_LIMITED, BOOKING_CAP, SPEND_CAP_REACHED render their exact sentences + Talk to a person, **no** primary; TURN_TIMEOUT: heading text, Try again → `dispatch({kind:"retry",turnId:""})`, second click ignored while pending; BUSY sentence and no heading; AI_PAUSED; FAILURE_OFFER; NO_INFO; **"Talk to a person stays enabled when props.disabled is true"** in every card; no `/\bcharged\b/`), `ErrorCard.test.tsx` (SLOT_TAKEN: sentence + a slot card with one open tile; OUT_OF_AREA: sentence + person key; CODE_WRONG role alert; **`it("NOT_VERIFIED, CODE_LOCKED and CODE_CAP_REACHED render identical markup")`**: render the three, compare `container.innerHTML` after replacing `block_id`-free text; they must be equal), `SessionEndedCard.test.tsx` (ENDED_BLOCK block from `chatThreadExample("ENDED_BLOCK")`: sentence, button click → `{kind:"newChat"}`, still enabled with `disabled:true`).
**Check:** `npx vitest run src/screens/scr01/cards/NoticeCards.test.tsx src/screens/scr01/cards/ErrorCard.test.tsx src/screens/scr01/cards/SessionEndedCard.test.tsx`.

### Step 10 · Registry, layout, coverage
1. `registry.tsx`: `export const cardRenderers: RendererMap = { text: (p) => <TextCard {...p} />, source_chip: …, safety, conditional_safety, burning_check, emergency_line, quick_checks, urgency_questions, where_prompt, locate_prompt, code_prompt, slot_card, confirmation, appointment, cancelled, account_card, change_request, handoff, live_queued, failure_offer, no_info, notice, error, session_ended }` (24 keys; each entry a plain arrow returning an element).
2. `layout.ts`:
```ts
import type { ReplyBlock } from "../contract";
export type BlockLayout = "bubble" | "card" | "pinned" | "event";
/** Proposal to G1: where each block belongs. bubble = text inside the grey assistant turn; card = standalone hairline card under the name line; pinned = the safety card; event = centred quiet line. */
export function blockLayout(block: ReplyBlock): BlockLayout;
```
Rule: `safety` → `"pinned"`; `session_ended` → `"event"`; `text`, `source_chip`, `no_info`, `failure_offer`, and `notice` with `code` `BUSY` or `AI_PAUSED` → `"bubble"`; everything else `"card"` (including `conditional_safety`, `emergency_line`, `error`).
3. `index.ts`: `export { cardRenderers } from "./registry"; export { blockLayout } from "./layout"; export type { BlockLayout } from "./layout";`.
4. `cards.coverage.test.tsx`: (a) `Object.keys(cardRenderers).sort()` equals `schemaBlockTypes().sort()` (24); (b) for **every** `turnExampleNames()` (37) render each of its blocks through `cardRenderers[type]` with `settled` and `makeProps` and assert: no throw, no text "Unsupported block", `expectNo24HourTimes`, no `/\bcharged\b/i`; (c) `stateMap` check: every row in `testing/stateMap.ts` names either an existing example (`turnExampleNames()` / `handoffExample` / `chatThreadExample`) or a fixture id that `scr01-cards.fixtures.ts` exports; (d) `blockLayout` of each example block returns one of the four values and `safety` is `"pinned"`.
**Check:** `npx vitest run src/screens/scr01/cards src/styles` (all green; `guard.test.ts` proves no red/hex/safety-token leaks). If the guard flags a string you wrote (a hex-like `#abc` anchor, the substring `red-` in a class or id such as `answered-…`), rename it.

### Step 11 · Dev layer (scenarios, fixtures, director, reactions)
Scenarios must work against the FND resolver (FND Step 8): precedence is signed-out → **explicit force** → role → … → director. A scenario's `ops` is a force; the scenario `route` is `"/"`, `role` customer, `screen: "SCR-1"`. IDs are `` `${SLUG}.<kebab>` `` (`SLUG` from Step 0; expected `scr01-cards`); `FILE.complete = false` (SCR-1's eight standard states are shared with G1's file; the coverage test is G1's to flip; say so in the g2 doc).
1. **`scr01-cards.fixtures.ts`** — typed helpers, each a pure function over the Prism body (the FND `OpForce.transform` takes `(body:any)=>any`; type ours precisely):
```ts
import type { components } from "@/api/types.gen";
type TurnResponse = components["schemas"]["TurnResponse"];
type ReplyBlock = components["schemas"]["ReplyBlock"];
export const mapBlocks = (fn: (b: ReplyBlock) => ReplyBlock) => (body: TurnResponse): TurnResponse => ({ ...body, blocks: body.blocks.map(fn) });
export const appendBlocks = (extra: ReplyBlock[]) => (body: TurnResponse): TurnResponse => ({ ...body, blocks: [...body.blocks, ...extra] });
```
   Fixtures (each exported const is a `(body: TurnResponse) => TurnResponse`; each carries a comment `// dev fixture: no named example in the OpenAPI (foundation plan §8.2); base example: <NAME>`):
   - `slotCardUrgent` (base `SLOT_CARD`): `mapBlocks(b => b.type==="slot_card" ? { ...b, urgent: true } : b)`.
   - `emergencyLineStaffed` (base `EMERGENCY_LINE`): `separate_line: null`.
   - `quickChecksShown` (base `QUICK_CHECKS`): `checks = [{ text: "Dev fixture check 1", source }, { text: "Dev fixture check 2", source }]` where `source` is the `ANSWER_WITH_SOURCE` source object copied verbatim (comment names it).
   - `noWindowFits` (base `NO_INFO`): `text: "That's the earliest I can book. I can't add you to a waitlist from here."` (SCREEN_SPECS W: No window fits), `person_key: true`.
   - `partialReply` (base `ANSWER_WITH_SOURCE`): `appendBlocks([<NO_INFO block verbatim, block_id "blk-203">])`.
   - `handoffRefund` (base `HANDOFF`): `variant:"refund"`, `promise_text:"A representative will get to your refund request within 2 business days."`, `due_at:null`, `due_label:null`, `extra_lines:["I can't promise an outcome.","Your reference is MHC-C-0007."]`.
   - `handoffGeneralOnly` (base `HANDOFF`): `followup_chooser.general_only = true`, both channels `on_record: false`.
   - `changeRequestCancel` (base `CHANGE_REQUEST`): `change:"cancel"`, `wanted_text:"Cancel the visit on Wednesday, October 21, 8:00 am – 12:00 pm"`.
   - `changeRequestStaffed` (base `CHANGE_REQUEST`): `promise_text:"A representative will join this chat when available. You can keep chatting with me while you wait, if you like."`, `due_at:null`, `due_label:null`, `cant_guarantee_line:null`, `extra_lines:["Your reference is MHC-C-0009."]`, `phone_support_line:"Phone support is open until 7:00 pm today if you'd like to call."` (SCREEN_SPECS Copy notes: Fee-bearing change).
   - `cancelledWithWrite` (base `CANCELLED`): `settled.actions` gets `{ kind:"cancelled", summary:"Cancelled Wed Oct 21 visit", turn_id, at }` (copy `CANCELLED.writes[0]`) — fixes the contract gap C-9 for the demo.
   Export `FIXTURE_IDS: Record<string, FixtureMeta>` where `FixtureMeta = { base: string; transform: (b: TurnResponse) => TurnResponse; note: string }`, keyed `slot-card-urgent`, `emergency-line-staffed`, `quick-checks-shown`, `no-window-fits`, `partial-reply`, `handoff-refund`, `handoff-general-only`, `change-request-cancel`, `change-request-staffed`, `cancelled-with-write`.
2. **`scr01-cards.ts`**: `export const screenScenarios: ScreenScenarios = { complete: false, scenarios }`. Helper `next(example: string, transform?)` = `{ submitTurn: { example, transform } }`. Scenarios (id suffix · `flowState` exact text or none · `state` · force). Every label ends with " (next reply)" for `submitTurn` ones, and `notes` says "Send any message; the next reply is <EXAMPLE>. The force is consumed by that reply."
| id | flowState | state | force |
|---|---|---|---|
| safety-takeover | Safety takeover | success | `submitTurn` SAFETY |
| burning-smell-unknown | Burning smell, unknown | default | BURNING_CHECK |
| burning-smell-risk-unclear | Burning smell, risk unclear | success | CONDITIONAL_SAFETY |
| burning-smell-ruled-out | Burning smell, both ruled out | default | SLOT_CARD + `slotCardUrgent` |
| someone-in-danger | Someone in danger (no heat, no cooling, leak) | success | EMERGENCY_LINE |
| someone-in-danger-staffed | — | success | EMERGENCY_LINE + `emergencyLineStaffed` |
| quick-checks-offered | Quick checks offered / skipped | default | QUICK_CHECKS |
| quick-checks-shown | — | default | QUICK_CHECKS + `quickChecksShown` |
| urgency-questions | — | default | URGENCY_QUESTIONS |
| where-card | — | default | WHERE_PROMPT |
| slot-card | — | default | SLOT_CARD |
| slot-card-members | — | success | SLOT_CARD_MEMBER |
| out-of-area | Out of area | error | OUT_OF_AREA |
| no-window-fits | No window fits | partial | NO_INFO + `noWindowFits` |
| identity-needed | Window chosen, identity needed | default | LOCATE_PROMPT |
| code-sent | Code sent | default | CODE_SENT |
| code-wrong | Code wrong, tries left | error | CODE_WRONG |
| code-expired | Code expired | error | CODE_EXPIRED |
| code-locked | Code locked (3 wrong) | error | CODE_LOCKED |
| code-cap-reached | — | error | CODE_CAP_REACHED |
| no-match | No match / ambiguous / no contact | error | NOT_VERIFIED |
| verified | Verified | success | VERIFIED_ACCOUNT_INVOICE |
| account-answer | Account answer | success | VERIFIED_ACCOUNT_INVOICE |
| account-membership | — | success | ACCOUNT_MEMBERSHIP |
| account-warranty | — | success | ACCOUNT_WARRANTY |
| dispute-handoff | Dispute / unsupported action | success | HANDOFF |
| slot-taken | Slot taken at write | error | SLOT_TAKEN |
| booked | Booked | success | BOOKED |
| confirm-existing-visit | Confirm existing visit | success | APPOINTMENT |
| fee-free-cancel | Fee-free move / cancel | success | CANCELLED + `cancelledWithWrite` |
| fee-bearing-change | Fee-bearing change request | success | CHANGE_REQUEST |
| fee-bearing-change-staffed | — | success | CHANGE_REQUEST + `changeRequestStaffed` |
| fee-bearing-cancel | Fee-bearing cancel | success | CHANGE_REQUEST + `changeRequestCancel` |
| handoff-in-reply | — | success | HANDOFF |
| handoff-refund | Handoff, refund | success | HANDOFF + `handoffRefund` |
| handoff-general-only | — | partial | HANDOFF + `handoffGeneralOnly` |
| handoff-nobody-online | Handoff, nobody online | success | **`requestPerson` `{ example: "CASE_CREATED" }`**, note: "Tap Talk to a person" |
| handoff-already-open | — | success | `requestPerson` ALREADY_OPEN, note: "Tap Talk to a person" |
| live-queued | Live-queued (simulated staff on shift) | success | `staffing: "simulated_on_shift"`, `requestPerson` LIVE_QUEUED, note: "Tap Talk to a person" |
| failure-signal | Failure signal (two misses) | default | FAILURE_OFFER |
| no-current-source | No current source | partial | NO_INFO |
| partial-reply | — | partial | ANSWER_WITH_SOURCE + `partialReply` |
| answer-with-source | — | default | ANSWER_WITH_SOURCE |
| limit-rate | Limit reached (rate, booking cap) | error | RATE_LIMITED |
| limit-booking-cap | Limit reached (rate, booking cap) | error | BOOKING_CAP |
| spend-cap | Spend cap reached | error | SPEND_CAP_REACHED |
| turn-timeout | — | loading | `submitTurn` `{ sequence: [{ example: "TURN_TIMEOUT" }, { example: "ANSWER_WITH_SOURCE" }] }`, note: "Try again gets a normal answer" |
| busy | — | loading | BUSY |
| ai-paused | — | success | AI_PAUSED |
| session-ended-block | — | disabled | `getChatThread` `{ example: "ENDED_BLOCK" }`, note: "Reload the page; the chat resumes from the thread read" |
   The `flowState` strings above must equal SCREEN_SPECS SCR-1 Flow-states first-column text exactly. `ops` keys use `OperationId` names.
3. **`directors/chat-cards.ts`**: `export const rules: DirectorRule[]`, each `(req) => string | undefined` (do not use the second parameter; `ChatDirectorCtx` is not defined in the foundation, §8 C-10). Helper `isTurnExample(name)` = `OPS.submitTurn.responses.some(r => r.status===200 && r.examples.includes(name))` (`OPS` from `@/api/client`); every returned name passes it. Rules in order:
   1. **explicit:** `text` payload matching `/^demo:\s*([a-z_ ]+)$/i` → upper-snake the capture (`"slot taken"` → `SLOT_TAKEN`); return it when valid.
   2. **burn-1 choices:** `yes` → `SAFETY`; `no` → `SLOT_CARD`; `not_sure` → `CONDITIONAL_SAFETY`.
   3. **qc-1:** `skip_and_book` → `WHERE_PROMPT`; `show_checks` → `QUICK_CHECKS`.
   4. **uq-1:** any choice → `SLOT_CARD`.
   5. **where-1** `form`: `zip_or_city` matching `/^(00000|99999)$|outside/i` → `OUT_OF_AREA`; else `SLOT_CARD`.
   6. **slots-7** `choice`: `"56"` → `LOCATE_PROMPT`; `"57"` → first time `SLOT_TAKEN` (module `Set` `seenTaken`), later `LOCATE_PROMPT`; `"58"` → `BOOKED`. Other options → `LOCATE_PROMPT`.
   7. **loc-1** `form` → `CODE_SENT`.
   8. **code-1** `code`: `111111` → `CODE_WRONG`; `222222` → `CODE_EXPIRED`; `333333` → `CODE_LOCKED`; `444444` → `NOT_VERIFIED`; any other → `VERIFIED_ACCOUNT_INVOICE`. `choice` option `resend` → `CODE_SENT`.
   9. **keywords** on `text` (case-insensitive, first match wins): `/\bgas\b|carbon monoxide|\bco alarm\b/` → SAFETY; `/burning|smells? like (smoke|burn)/` → BURNING_CHECK; `/no heat|no (a\/c|ac|cooling)|\bleak/` → EMERGENCY_LINE; `/\bcancel/` → CANCELLED; `/reschedul|\bmove (my|the)\b/` → CHANGE_REQUEST; `/confirm (my )?(appointment|visit)/` → APPOINTMENT; `/\bbook|schedule|appointment|\bvisit\b|technician/` → QUICK_CHECKS; `/\bbill\b|invoice|charge/` → LOCATE_PROMPT; `/membership|\bplan\b/` → ACCOUNT_MEMBERSHIP; `/warranty/` → ACCOUNT_WARRANTY; `/weather|joke|recipe/` → NO_INFO; `/not getting this|useless/` → FAILURE_OFFER; otherwise `undefined`.
   These keyword sets are G2's; G1's `chat-core.ts` rules must not use them (§8 G1-e).
4. **`reactions/scr01-cards.ts`**: `export const reactions: Reaction[]`:
   - one-shot: `{ when:{ op:"submitTurn" }, then(ctx){ const f = ctx.world.forces.submitTurn; if (ctx.world.scenarioId?.startsWith(`${SLUG}.`) && f && "example" in f) ctx.setForce("submitTurn", null); } }` (a `sequence` force is left alone).
   - `{ when:{ op:"requestPerson", example:"CASE_CREATED" }, then: ctx => ctx.setForce("requestPerson", { example:"ALREADY_OPEN" }) }` and the same for `example:"LIVE_QUEUED"`.
   - `{ when:{ op:"resetDemo" }, then: ctx => { ctx.setForce("requestPerson", null); ctx.setForce("submitTurn", null); } }` and `{ when:{ op:"startChatSession" }, then: ctx => ctx.setForce("requestPerson", null) }`.
5. Tests: `chat-cards.test.ts` (table-driven: each rule row above, including the module state for `57`; every returned name valid; `"demo:slot taken"` → `SLOT_TAKEN`; unknown text → `undefined`; a G2 rule never throws on `payload.kind` `form` with missing values). `reactions/scr01-cards.test.ts` (fake `DevCtx` recording `setForce`; one-shot clears an `example` force but not a `sequence`; requestPerson → ALREADY_OPEN). `scenarios/scr01-cards.test.ts`: ids unique and prefixed `${SLUG}.`; each `flowState` appears verbatim in `docs/ux/03-structure/SCREEN_SPECS.md` (read the file with `fs`, SCR-1 section); each scenario's `ops` example exists in `OPS[op]`; for every `submitTurn` scenario run its `transform` (if any) over `turnExample(base)` and render every resulting block through `cardRenderers` without "Unsupported block"; each fixture changes only what §6 lists (assert the changed field; assert unchanged siblings with `toEqual`).
**Check:** `npx vitest run src/dev` (includes the FND `scenarios.integrity.test.ts` and `scenarios.coverage.test.ts`).

### Step 12 · Visual check (conditional)
If `src/screens/scr01/Scr01.tsx` still contains the text `Stub:` (G1 not landed), skip the browser check, say so in the g2 doc ("pending integration") and rely on the jsdom tests. Otherwise: start `npm run mock` and `npm run dev:mock` in the background (ports 4019 and 5184; remember the two PIDs and stop only those), open `http://127.0.0.1:5184/?signedin=1`, and with Chrome DevTools MCP check at 390 and 1280 wide: apply scenarios from the panel States tab for `safety-takeover`, `slot-card`, `code-sent`, `code-wrong`, `booked`, `fee-bearing-change`, `handoff-in-reply`, `limit-rate`, `turn-timeout`, `session-ended-block`; confirm no red outside the safety card, tiles ≥ 44 px, no horizontal page scroll, focus ring visible on every control, times 12-hour. List what you checked in the g2 doc. Stop both servers.

### Step 13 · `docs/ux/04-prototype/groups/g2-chat-cards.md`
Sections in order: **Status** · **Block → file → example/fixture map** (the §6 table) · **Decisions made** (C-1…C-9 below, verbatim) · **Requests to the integrator and contract owners** (§8) · **Coupling with G1** (§8 G1-a…h) · **Dev layer** (scenario list, director keywords and the `111111…444444` / slot `56|57|58` conventions, reactions) · **Mock artefacts** (follow-up response always `PHONE_MORNINGS`; `requestPerson` example does not follow staffing unless forced) · **Checks run** (table) · **Visual check** (done / pending integration).

### Step 14 · Final gates (once, in this order, stop at the first red)
See §7.

## 6. Data and fixtures

Synthetic only. Every value comes from the OpenAPI named examples (Omar Patel, MHC-C-0007/0008/0009, INV-204411, Jun Park, Riley, `2026-10-16T14:20:00-05:00`). The only invented strings: the two `Dev fixture check N` labels, the cancel `wanted_text`, and the client validation lines in §5 (each marked in the g2 doc).

**State map** (`testing/stateMap.ts`, exported `STATE_MAP: { id: string; block: BlockType; state: string; source: { example: string } | { fixture: string } | { handoff: string } | { thread: string } }[]`; the coverage test checks each source exists). Rows:

| block (state) | source |
|---|---|
| text | example `ANSWER_WITH_SOURCE` |
| source_chip | example `ANSWER_WITH_SOURCE` (deduped) |
| text partial (+ no_info) | fixture `partial-reply` |
| safety | example `SAFETY` |
| conditional_safety | example `CONDITIONAL_SAFETY` |
| burning_check (open) | example `BURNING_CHECK`; answered: test variant `{ ...block, answered: "no" }` |
| emergency_line (nobody online) | example `EMERGENCY_LINE` |
| emergency_line (staffed, no separate line) | fixture `emergency-line-staffed` |
| quick_checks (offer) | example `QUICK_CHECKS` |
| quick_checks (list shown) | fixture `quick-checks-shown` |
| urgency_questions | example `URGENCY_QUESTIONS` |
| where_prompt | example `WHERE_PROMPT` |
| locate_prompt | example `LOCATE_PROMPT` |
| code_prompt sent / wrong / expired | examples `CODE_SENT` / `CODE_WRONG` / `CODE_EXPIRED` |
| code_prompt locked | example `CODE_LOCKED` (its `error` + `handoff`; no `code_prompt` is returned: the field-disabled `locked` state is a test variant `{ ...CODE_SENT.block, state: "locked" }`) |
| slot_card (open / Full day / taken) | example `SLOT_CARD` |
| slot_card (members) | example `SLOT_CARD_MEMBER` |
| slot_card (urgent) | fixture `slot-card-urgent` |
| slot_card (answered) | test variant `{ ...SLOT_CARD.block, answered: "56" }` |
| account_card invoice / membership / warranty | examples `VERIFIED_ACCOUNT_INVOICE` / `ACCOUNT_MEMBERSHIP` / `ACCOUNT_WARRANTY` |
| confirmation | example `BOOKED` |
| appointment | example `APPOINTMENT` |
| cancelled | fixture `cancelled-with-write` (example `CANCELLED` for the no-write guard) |
| change_request (move) | example `CHANGE_REQUEST` |
| change_request (cancel / staffed) | fixtures `change-request-cancel`, `change-request-staffed` |
| handoff nobody_online | examples `HANDOFF`, handoff op `CASE_CREATED`, `ALREADY_OPEN` |
| handoff staffed | example `HANDOFF_STAFFED` |
| handoff refund / general_only | fixtures `handoff-refund`, `handoff-general-only` |
| live_queued | example `LIVE_QUEUED`, handoff op `LIVE_QUEUED` |
| failure_offer | example `FAILURE_OFFER` |
| no_info | example `NO_INFO` |
| no_info (no window fits) | fixture `no-window-fits` |
| notice ×6 | examples `RATE_LIMITED`, `BOOKING_CAP`, `SPEND_CAP_REACHED`, `TURN_TIMEOUT`, `BUSY`, `AI_PAUSED` |
| error SLOT_TAKEN, OUT_OF_AREA, CODE_WRONG, CODE_EXPIRED, CODE_LOCKED, CODE_CAP_REACHED, NOT_VERIFIED | the same-named examples |
| session_ended | thread example `ENDED_BLOCK` |

Not built because SCREEN_SPECS SCR-1 has no such state (do not invent): account/slot card `loading` and `unavailable` skeletons (the loading state is G1's pending line); a slot card for "a day with no windows" beyond the `Full` tab.

## 7. Checks

From `apps/web/`. Nothing here runs the full suite: the slice adds only owned files plus three dev files that replace FND stubs; no shared fixture, config, dependency or module imported across the codebase changes (`build-loop-test-scope` "affected" rule). `src/styles/guard.test.ts` and the FND dev integrity tests are included because they scan the whole tree.

**While iterating**
- `npx vitest run src/screens/scr01/cards/<file>.test.tsx` for the file you are on.
- `npm run typecheck` after each step.

**Once before reporting** (cheapest first, stop at the first red):

| # | Command | Passing looks like |
|---|---|---|
| 1 | `npm run lint` | 0 errors; no new warnings (fix `react-hooks/exhaustive-deps`, do not silence) |
| 2 | `npm run typecheck` | exits 0 (regenerates types first) |
| 3 | `npx vitest run src/screens/scr01/cards src/dev src/styles src/screens` | all green. New files: `parts/{dates,promise,useCardAction,landed,OptionTile,CardParts}.test.ts(x)`, `TextCard`, `SafetyCard`, `EmergencyLineCard`, `ChoiceCards`, `WherePromptCard`, `LocatePromptCard`, `CodePromptCard`, `SlotCard`, `AccountCard`, `VisitCards`, `ChangeRequestCard`, `HandoffCard`, `LiveQueuedCard`, `NoticeCards`, `ErrorCard`, `SessionEndedCard` `.test.tsx`, `cards.coverage.test.tsx`, `src/dev/scenarios/scr01-cards.test.ts`, `src/dev/reactions/scr01-cards.test.ts`, `src/dev/directors/chat-cards.test.ts` |
| 4 | `npm run build && npm run check:dist` | build exits 0; no dev-layer string in `dist/` (proves `cards/**` imports nothing from `src/dev`) |

**Existing tests that must stay green (all foundation tests):** `src/styles/{tokens,guard}.test.ts`, `src/dev/scenarios.integrity.test.ts`, `src/dev/scenarios.coverage.test.ts` (it must still skip: `complete:false`), `src/dev/resolve.test.ts`, `src/dev/stream.test.ts`, `src/routes.test.ts`, `src/screens/stubs.test.tsx`, `src/lib/**`, `src/components/**`. The Python suite is untouched and not run.
No formatter gate exists for this package; ESLint is the style gate.

## 8. Risks and requests

**Collision risks with other slices**
- **G1 (`scr01/core/**`, `Scr01.tsx`):** we meet only at `contract.ts`/`blocks.ts`. Coupling points that G1's plan must honour (also in the g2 doc):
  - **G1-a Retry:** `TURN_TIMEOUT` dispatches `{ kind:"retry", turnId:"" }` because the block carries no turn id. G1 must treat `""` as "the turn this reply answers" (the last failed customer turn id it minted).
  - **G1-b Landing and announcing:** G2 calls `props.landed(...)` and `props.announce(...)` itself, once per `block_id`, for `confirmation` (visit), `cancelled` (visit), `change_request` (request), `handoff` (request), `live_queued` (request) and follow-up saved (request). G1 must **not** also call them for the same events, and should pass no-op `landed`/`announce` while it hydrates history (`getChatThread`), otherwise a reload re-announces every old card. G1 still owns identity landing (`writes[].kind === "verified"`; there is no verified block) and staffing/event announcements.
  - **G1-c Layout:** `blockLayout(block)` from `./cards` tells G1 where a block goes (`bubble`, `card`, `pinned`, `event`). Cards bring their own hairline; wrapping a card block in the grey assistant bubble would double the chrome.
  - **G1-d Settled:** handoff, change request, visit and live-queued cards read `props.settled`. G1 must replace its `settled` from every `submitTurn`, `requestPerson` and `saveFollowUp` response (they all carry `settled`), or the "Follow-up saved" line will not appear.
  - **G1-e Director keywords:** G1's `directors/chat-core.ts` rules must not match the keyword set in Step 11 item 3, the `demo:` prefix, or the card ids `burn-1 qc-1 uq-1 where-1 slots-7 loc-1 code-1`; `pickTurnExample` returns the first answer, so the import order in `directors/index.ts` decides ties. The integrator checks both plans.
  - **G1-f New chat:** `{ kind:"newChat" }` must work after the chat ended; `session_ended` ignores `disabled`.
  - **G1-g Pinned safety:** if G1 mounts the safety block both pinned and in the thread, only the first mounted gets `role="alert"`.
  - **G1-h Scenarios:** `getChatThread`-based scenarios (`session-ended-block`) need G1's resume path (CON-1: thread id kept in the tab, `getChatThread` on reload).
- **Foundation:** none of its files is edited. Names depend on the foundation being finished as written (§4.2); Step 0 stops the work if not.
- **Guard test regexes** (`src/styles/guard.test.ts`): safety tokens only in files under `scr01/cards/` whose name contains `Safety`; no `#xxx` hex-like text anywhere in `src/screens/**` non-test files (avoid `href="#bad"`); no `red-<digit>`, `amber`, `orange`, `text-red…` strings.

**Decisions this plan made (record in the g2 doc; contract owners may overrule)**
- **C-1 Urgency questions protocol.** CON-2 has no way to say which question an answer belongs to. Decision: one `choice` per card, `option = "question_id:answer;…"` in question order (e.g. `temp:yes;water:no;risk:skip`), or `skip`. Request: UI_CONTRACTS CON-2 to name the encoding or add a `form` kind.
- **C-2 Retry id.** Decision in G1-a. Request: add `retry_turn_id` to `NoticeBlock` (it exists only on the top-level `notice`).
- **C-3 Emergency windows label.** SCREEN_SPECS W: Someone in danger wants earliest windows "labelled 'This is a regular booking, not emergency service.'". No contract field carries it, and `urgent` means something else (burning-smell urgent booking). Decision: do not hard-code the sentence; render nothing. Request: a `note` string on `slot_card` (or a `text` block) so the code, not the screen, owns safety wording.
- **C-4 Quick-checks list.** `QUICK_CHECKS.checks` is `null` in the only example; the list state uses fixture `quick-checks-shown` with obviously synthetic text. Request: a named example `QUICK_CHECKS_SHOWN`.
- **C-5 Missing named examples** (fixtures used; request examples): refund handoff, `general_only` chooser, staffed emergency line, change request as cancel and staffed, no-window-fits, partial reply.
- **C-6 Duplicate chip.** `text.sources[]` plus a `source_chip` block repeat one chip in the example; the card dedupes by `(at, passage_id)`. Request: pick one carrier.
- **C-7 Duplicate line.** `CHANGE_REQUEST.extra_lines[1]` equals `cant_guarantee_line`; the card shows it once. Request: keep `extra_lines` to the reference line.
- **C-8 `requestPerson` default.** FND `defaults.ts` answers `CASE_CREATED` whatever the staffing; the live-queued path needs `LIVE_QUEUED` when staffing is on. Request to the integrator: `defaults.ts` `requestPerson` → `LIVE_QUEUED` when `world.staffing === "simulated_on_shift"`, else `CASE_CREATED`. The `live-queued` scenario forces it meanwhile.
- **C-9 Cancelled write missing from `settled.actions`.** `CANCELLED.writes` has the write; `CANCELLED.settled.actions` does not, and `BlockProps` carries `settled` only. The card shows its "cancelled" sentence only when `settled.actions` has `cancelled`; the demo uses fixture `cancelled-with-write`. Request: `settled.actions` to include every write of the turn, or `BlockProps` to carry `writes`.
- **C-10 `ChatDirectorCtx` is referenced but never defined in FND §4.9.** G2 rules use the request only.
- **C-11 Date-only values.** `Format: date` fields have no offset; `parts/dates.ts` builds a Chicago-offset ISO (DST-edge hours 1–2 am on Nov 1 and Mar 14 are not handled; no card uses them).
- **C-12 Code error text.** The sentence is in the `error` block, the invalid field in `code_prompt`; they cannot be linked by `aria-describedby` across blocks. Accepted: the error line has `role="alert"` and the field gets focus and `aria-invalid`.
- **C-13 Motion extras not built** (no keyframes in `base.css`; the foundation owns it): the mint wash on a thread card header, and the check-draw on a chosen tile. Both appear instantly, which is the reduced-motion behaviour anyway. Request: classes `.landed-wash` and `.check-draw` in `base.css`.
- **C-14 Scenario shape.** Scenarios force the *next* reply (one-shot), not an instant state; there is no card gallery route (the kit is foundation-owned). Optional request: a `/__kit` section that renders `cardRenderers` for the state map, if the integrator wants a faster visual review.

**Shared-primitive requests (to the integrator, FND §8.3):** `OptionTile` and a day-tab primitive are built locally in `cards/` (G4 does not need them as far as the group split shows); promote only if another group asks. Everything in C-8 and C-13.

## 9. Readiness

**READY.** No `NEEDS-DECISION`: every open point is decided in §8 with a request to its owner and a small, reversible implementation (one function or constant). One `BLOCKED-ON` condition exists only if the foundation is unfinished when work starts: Step 0 lists the files that must exist (`contract.ts`, `blocks.ts`, `cards/index.ts`, `src/test/render.tsx`, the three dev stubs, `src/dev/scenarios/types.ts`); if any is missing, stop and report `BLOCKED-ON foundation`.

Report back with: test counts per file, the §7 gate outputs, the `SLUG` used, any import-path adjustment made to match the finished foundation (§4.2), the Step 12 result (done or pending integration), and every deviation from this plan with the reason.

## Deviations

Recorded by the implementer, 2026-10-21.

1. `scr01/blocks.tsx` (not `.ts`), `ScreenStub` takes only `id`, `pickTurnExample(req, ctx)`: as in the foundation Deviations; nothing in G2 depended on them.
2. `testing/props.tsx` `renderCard` wraps `AnnounceProvider` around plain RTL `render` instead of `renderWithProviders`. The full providers start a session fetch that logs act() warnings on every card test; cards need only the announce region (RefChip).
3. Added `testing/resets.ts` (`resetCardState`) to clear the module-level Sets (landed, source dedupe, safety alert, code focus) between tests. The modules export `reset...ForTests` as planned.
4. `saveFollowUp` is `PUT`, so `followUpExample` reads the `put` path. `testing/examples.ts` also exports `followUpExample`.
5. `ChatDirectorCtx` exists in `scenarios/types.ts` after all; rules still ignore the second argument. Slot `57` uses one module boolean (`takenShown`) instead of a Set keyed by turn id.
6. `WindowBlock.appointment_id` is a number in the generated types (plan said string).
7. `UrgencyQuestionsCard` has two buttons named "Skip" (each question's answer tile and the card-level one); the test targets the last in the DOM.
8. `ConfirmationCard` shows the contract's timeline step 1 ("Booked") whether or not a booked write is present; only the "Booked" tag is gated on the write. Gating contract text would hide the timeline entirely.
9. `SourceChipView` puts `aria-label` on the chip span inside the `<summary>` (the shared `Disclosure` owns the summary element). The visible text gives the same name to assistive tech.
10. `testing/examples.ts` imports `yaml`, which is not declared in `package.json` (present transitively; `scripts/build-contract-index.mjs` already imports it). Request in the g2 doc.
11. Step 12 not run: pending integration (see the g2 doc).
