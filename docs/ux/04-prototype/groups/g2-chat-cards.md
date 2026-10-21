# UX-4 group G2: chat cards (SCR-1 reply-block renderers)

## Status

Built 2026-10-21 by `fanout-implementer` from `docs/plans/fanout/2026-10-21-ux4/g2-chat-cards.md`. All 24 `ReplyBlock` types have a renderer in `apps/web/src/screens/scr01/cards/registry.tsx`. Scenario file slug: `scr01-cards` (`complete: false`; the eight standard SCR-1 states are covered by G1's file). Visual check: **pending integration** (see the end).

## Block, file and example or fixture map

| Block (state) | File | Source of the state |
|---|---|---|
| text, source_chip | `TextCard.tsx`, `SourceChipView.tsx`, `sourceDedupe.ts` | example `ANSWER_WITH_SOURCE`; fixture `partial-reply` |
| safety, conditional_safety | `SafetyCard.tsx` | `SAFETY`, `CONDITIONAL_SAFETY` |
| emergency_line | `EmergencyLineCard.tsx` | `EMERGENCY_LINE`; fixture `emergency-line-staffed` |
| burning_check, quick_checks, urgency_questions | `ChoiceCards.tsx` | `BURNING_CHECK`, `QUICK_CHECKS` (+ fixture `quick-checks-shown`), `URGENCY_QUESTIONS` |
| where_prompt, locate_prompt, code_prompt | `WherePromptCard.tsx`, `LocatePromptCard.tsx`, `CodePromptCard.tsx` | `WHERE_PROMPT`, `LOCATE_PROMPT`, `CODE_SENT`, `CODE_WRONG`, `CODE_EXPIRED`; locked is a test variant |
| slot_card | `SlotCard.tsx` | `SLOT_CARD`, `SLOT_CARD_MEMBER`; fixture `slot-card-urgent` |
| account_card | `AccountCard.tsx` | `VERIFIED_ACCOUNT_INVOICE`, `ACCOUNT_MEMBERSHIP`, `ACCOUNT_WARRANTY` |
| confirmation, appointment, cancelled | `VisitCards.tsx` | `BOOKED`, `APPOINTMENT`, `CANCELLED`; fixture `cancelled-with-write` |
| change_request | `ChangeRequestCard.tsx` | `CHANGE_REQUEST`; fixtures `change-request-cancel`, `change-request-staffed` |
| handoff, live_queued | `HandoffCard.tsx`, `FollowUpChooser.tsx`, `LiveQueuedCard.tsx` | `HANDOFF`, `HANDOFF_STAFFED`, `LIVE_QUEUED`, handoff ops; fixtures `handoff-refund`, `handoff-general-only` |
| notice, failure_offer, no_info | `NoticeCards.tsx` | six notice examples, `FAILURE_OFFER`, `NO_INFO`; fixture `no-window-fits` |
| error | `ErrorCard.tsx` | seven error examples |
| session_ended | `SessionEndedCard.tsx` | thread example `ENDED_BLOCK` |

The machine-readable map is `cards/testing/stateMap.ts`, checked by `cards.coverage.test.tsx`.

## Decisions made (from the plan, C-1 to C-14; contract owners may overrule)

- **C-1 Urgency questions.** One `choice` per card, `option = "question_id:answer;..."` in question order (`temp:yes;water:no;risk:skip`), or `skip`. Request: CON-2 to name the encoding.
- **C-2 Retry id.** `TURN_TIMEOUT` dispatches `{ kind: "retry", turnId: "" }`; G1 treats `""` as the turn this reply answers. Request: `retry_turn_id` on `NoticeBlock`.
- **C-3 Emergency windows label.** The sentence "This is a regular booking, not emergency service." is not hard-coded (no contract field). Request: a `note` on `slot_card`.
- **C-4 Quick-checks list.** Only a fixture shows it (`checks` is null in the example). Request: example `QUICK_CHECKS_SHOWN`.
- **C-5 Missing examples** (fixtures used): refund handoff, `general_only`, staffed emergency line, change request as cancel and staffed, no window fits, partial reply.
- **C-6 Duplicate chip.** `text.sources[]` and a following `source_chip` repeat one passage; the card dedupes by `(at, passage_id)`.
- **C-7 Duplicate line.** `CHANGE_REQUEST.extra_lines[1]` equals `cant_guarantee_line`; shown once.
- **C-8 `requestPerson` default.** `defaults.ts` should answer `LIVE_QUEUED` when staffing is on; the `live-queued` scenario forces it meanwhile.
- **C-9 Cancelled write.** `CANCELLED.settled.actions` lacks the `cancelled` write, so the live mock renders only "There's no fee."; fixture `cancelled-with-write` fixes the demo. Request: put every write of the turn in `settled.actions`, or give `BlockProps` the turn's `writes`.
- **C-10** `ChatDirectorCtx` is now defined (`{ world }`); G2 rules ignore it.
- **C-11 Date-only values** are turned into Chicago-offset ISO by `parts/dates.ts` (the 1 to 2 am hours of the DST changes are not handled; no card uses them).
- **C-12 Code error sentence** lives in the `error` block, the invalid field in `code_prompt`; not linkable by `aria-describedby`. The error line is `role="alert"` and the field takes focus once.
- **C-13 Motion extras not built:** mint wash on a thread card header and the check-draw on a chosen tile (no keyframes in `base.css`). Request: `.landed-wash` and `.check-draw`.
- **C-14 Scenario shape.** Scenarios force the next reply (one-shot); there is no card gallery route.

Client copy added (not in the contract): "Enter a ZIP code or city.", "Fill in every field above.", "Enter the 6-digit code.", "Choose a window to continue.", and the locate-card switch buttons ("Use my customer ID instead", "Use my invoice number instead", "Use my name and phone instead").

## Requests to the integrator and contract owners

- C-8 above (`defaults.ts`). C-13 above (`base.css` classes). C-2, C-3, C-4, C-9 to the contract owners.
- Declare `yaml` in `package.json` devDependencies: `cards/testing/examples.ts` imports it (it is present only through `scripts/build-contract-index.mjs`'s dependency chain; `scripts/` already imports it).
- Optional: a `/__kit` section that renders `cardRenderers` for `STATE_MAP`.

## Coupling with G1

- **G1-a Retry:** see C-2. **G1-b Landing and announcing:** G2 calls `props.landed(...)` and `props.announce(...)` itself, once per `block_id`, for confirmation, cancelled (only with the write), change_request, handoff, live_queued and a saved follow-up. G1 should pass no-op `landed`/`announce` while it hydrates history so a reload does not re-announce.
- **G1-c Layout:** `blockLayout(block)` (`bubble | card | pinned | event`) is exported from `./cards`; cards bring their own hairline.
- **G1-d Settled:** the follow-up saved line only shows when G1 replaces `settled` from `saveFollowUp`, `requestPerson` and `submitTurn` responses.
- **G1-e Director:** G2's keyword set, the `demo:` prefix and the card ids `burn-1 qc-1 uq-1 where-1 slots-7 loc-1 code-1` must not be matched by `chat-core.ts` (the first rule to answer wins; `directors/index.ts` lists core first).
- **G1-f:** `{ kind: "newChat" }` must work after the chat ended; `session_ended` ignores `disabled`.
- **G1-g:** the safety block mounted twice announces once (module Set keyed by `block_id`).
- **G1-h:** `session-ended-block` needs G1's resume path.
- Agreed with G1 section 8.1: `dispatch` never rejects; `useCardAction` also tolerates a rejection (returns false).

## Dev layer

- **Scenarios** (`src/dev/scenarios/scr01-cards.ts`, 51 entries, ids `scr01-cards.<name>`): one per card state; each `submitTurn` one forces the next reply and is consumed by it. Fixtures in `scr01-cards.fixtures.ts` (`FIXTURE_IDS`, 10).
- **Director** (`src/dev/directors/chat-cards.ts`): `demo:<name>` forces an example. Card taps: burn-1 yes/no/not_sure; qc-1 skip_and_book/show_checks; uq-1 any; where-1 `99999`, `00000` or "outside" gives OUT_OF_AREA; slots-7 `56` goes to identity, `57` is SLOT_TAKEN the first time only, `58` is BOOKED; loc-1 gives CODE_SENT; code-1 `111111` wrong, `222222` expired, `333333` locked, `444444` NOT_VERIFIED, anything else verified (invoice). Then keywords (gas, burning, no heat, cancel, reschedule, confirm, book, invoice, membership, warranty, weather, useless).
- **Reactions** (`src/dev/reactions/scr01-cards.ts`): one-shot `example` force consumed after its reply; `requestPerson` CASE_CREATED or LIVE_QUEUED then ALREADY_OPEN; `resetDemo` and `startChatSession` clear forces.

## Mock artefacts

The follow-up response is always `PHONE_MORNINGS`; `requestPerson` does not follow staffing unless forced; Prism returns one fixed `settled` per example, so the visit window in the confirmation card comes from `settled.visit` when ids match, else from the label.

## Checks run

| Command | Result |
|---|---|
| `npx eslint` on the owned files | 0 errors, 0 warnings |
| `npx tsc -b --noEmit` | exit 0 |
| `npx vitest run src/screens/scr01/cards src/dev src/styles` | 35 files, 449 passed, 1 skipped (the coverage test skips while `complete: false`) |
| `npm run build` and `npm run check:dist` | build ok; "dist is clean: no dev-layer markers" |

Per-file counts: parts (dates 3, promise 4, landed 1, useCardAction 2, OptionTile 3, CardParts 3), TextCard 2, SafetyCard 3, EmergencyLineCard 2, ChoiceCards 6, WherePromptCard 2, LocatePromptCard 3, CodePromptCard 7, SlotCard 7, AccountCard 3, VisitCards 6, ChangeRequestCard 3, HandoffCard 7, LiveQueuedCard 2, NoticeCards 8, ErrorCard 4, SessionEndedCard 2, cards.coverage 4, scenarios 14, reactions 4, director 33.

## Visual check

**Pending integration.** G1's `Scr01.tsx` landed while G2 was being finished, but G1 and the integrator were still editing; the browser check (390 and 1280 wide: safety-takeover, slot-card, code-sent, code-wrong, booked, fee-bearing-change, handoff-in-reply, limit-rate, turn-timeout, session-ended-block) was not run. jsdom tests cover content, roles, states and the 12-hour rule only, not layout, 44 px rendering, focus rings or colour.
