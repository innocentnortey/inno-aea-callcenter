# UX ↔ backend join audit: staff side

**Date:** 2026-10-21. **Kind:** read-only audit. Nothing in `apps/web/**`, `docs/ux/**` or any ticket was edited.
**Verification level of everything below:** read from source and specs only. Nothing was run, so no finding here is
`mock-tested`, let alone integrated (rule [`integrated-journeys`](../../../.claude/rules/integrated-journeys.md) §3).
**Scope:** CON-8 (advance), CON-10, CON-11…CON-17, CON-14, CON-21; screens SCR-4…SCR-9 as they touch staff state; role
gating, `allowed_actions`, the owner role with no actions, `VERSION_CONFLICT`, the escalation → case → staff list →
case view with its brief, and the relayed customer message in the live chat.

**What I compared.**
- **UI side:** `apps/web/src` (API client, `types.gen.ts`, session state, shell, SCR-5/6/7/8 code, dev layer, e2e tests),
  `vite.config.ts`, `playwright.config.ts`, `docs/ux/04-prototype/PROTOTYPE_PLAN.md` and the UX-4 fan-out plans
  (`docs/plans/fanout/2026-10-21-ux4/`).
- **Authority:** `docs/ux/03-structure/ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, `SCREEN_SPECS.md`.
- **Backend:** `docs/design/contracts/stage7/{staff,cases,web}.md`, DO-4 §7, §13 and §16, `7b-decisions/staff.md`,
  the slice plan, and tickets AEA-29, 30, 34–39, 44–47 and 52 (plus AEA-40 and AEA-49 where a seam needed them).

**Relation to the UX session's own list.** `docs/ux/04-prototype/INTEGRATION_HANDOFF.md` §3 ranks 16 gaps (G-01…G-16)
by the same Riverside classes. Where a finding here overlaps one of them, the row cites it:
- B2 extends G-06. G-06 plans the tests; this audit names the code paths that must change.
- E3 is G-13.
- C3 is G-02 and G-03.
- A2 sits next to G-09. G-09 covers labels the UI parses; this audit asks who on the backend produces them.

The findings with no G-item are A1, A3, A4, B1, B4, B5, C1, C2, E1, E2 and G1.

**On the tickets being rewritten:** the addenda (stage7/*.md, DO-4 §16) were treated as the truth wherever a ticket and an
addendum differ. AEA-58 exists only as a slice-plan row (`slice-plan.md:178`); there is no ticket file yet.

## Summary

25 findings: **8 high, 9 medium, 8 low**. The three that would break a staff journey first:

1. **Nothing on the backend defines `allowed_actions`** (A1). The UI enables only the buttons that list names. If the
   backend sends only the CON-13 verbs, then Log a call, Flag, Join chat and the live box all stay dead.
2. **The UI never learns that the role changed under it** (B1, B2). The role lives on the login session (STF-19). The UI
   reads it once, on load. So when another tab switches role, or a demo reset sends everyone back to customer, the queue
   and case view either keep showing stale data or say "didn't load".
3. **Live chat is offered to roles that cannot use it** (C1, C2). The supervisor gets "Claim and join" on the queue and an
   active reply box on a joined case. The real server answers 403 to both, and the queue path leaves the supervisor owning
   a waiting chat nobody can join.

Severity: **H** breaks a staff journey against the real backend, or leaves a field no ticket produces. **M** gives a
wrong or misleading state on a plausible path. **L** is cosmetic, or hardening.

---

## (a) Fields the UI reads that the backend will not send; nullability; enums

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| A1 | **No backend rule produces `allowed_actions`.** The UI's invariant is "every enabled flag is `allowed_actions.includes(key)`". It reads non-CON-13 keys too: `claim_and_join`, `join_chat`, `log_call`, `log_email`, `flag`, `send_live_message`, `hand_back`, `close_chat`. AEA-45 says the logic is all `CaseService`'s, but AEA-29 has no acceptance criterion that computes it, by lifecycle, role and live state. A backend that returns only the CON-13 verbs passes schema validation and leaves every bar button disabled. | H | UI: `apps/web/src/screens/scr06/actionPlan.ts:24-61`; plan `g4-staff-queue-case.md:298`. Backend: `AEA-45.md:138` ("no … `allowed_actions` logic in the route"); `AEA-29.md:120` (AC-9 covers `apply` rejections only); examples `ui-contracts.openapi.yaml:3583` (DEFAULT `[claim, flag]`), `:4621` (LIVE_JOINED), `AEA-45.md:45` (CLAIMED) | AEA-29 (computes), AEA-45 (passes through), AEA-52 (proves at real routes) | Add an AEA-29 AC with the full table: lifecycle × role × live state → list. It must match every OpenAPI example. The owner always gets `[]`. The supervisor never gets `claim_and_join`, `join_chat`, `send_live_message`, `hand_back`, `close_chat`, `log_call` or `log_email` (their x-roles are representative only). `claim_and_join` appears only for representative + `live_queued` + on shift. Add one AEA-52 assertion per role on a seeded case. |
| A2 | **Presentation fields have no producer rule.** The wire `CaseSummary` / `QueueRow` carry display values that DO-4's `CaseSummary` does not have: `reason` as display text (the UI's `h1` is `${reason} · ${level} ${word}`; DO-4's `reason` is the `HandoffReason` enum, so "billing_dispute" would render as is); `priority.word`; `due_label`, including the ", the window start" suffix the UI parses; `age_label`; `follow_up_short`; `queued_at`; `other_cases[].status`; `identity.line` / `demo_note`; `CaseSource.version_label`; and the join key between `BriefItem.source_ids` and `CaseSource.source_id`. On that last one, DO-4 says only "serialised as `source_ids`", and the UI silently drops a chip with no matching source. cases.md says the views are "OpenAPI-shaped by name", but no AC fixes these values. | H | UI: `screens/scr06/caseText.ts` (`caseTitle`, `dueHeadline`), `screens/scr06/SourceChip.tsx` (renders nothing on no match, plan `g4…md:411`). Backend: `internal-components.md:539` (`SourceRef` → `source_ids`, no format); `stage7/cases.md:533-537` ("by name only"); example ids `src-invoice` vs `lookup_log_id` `ll-401` (`ui-contracts.openapi.yaml` CaseDetail DEFAULT) | AEA-29 (view building), AEA-45 AC-3 (pass-through) | Add an AEA-29 AC per field, with the OpenAPI example value as the expected output: reason word map, priority word map, `due_label` format and suffix, the `age_label` rule, the `source_id` scheme that `source_ids` uses. Add a J-6 step: every brief chip on MHC-C-0007 resolves to a source card. |
| A3 | **Customer speaker name on staff surfaces.** The OpenAPI examples carry `display_name: "You"` for the customer in CON-12 `conversation` and in the CON-21 `FRAMES` frame. That is the customer's point of view. The UI renders `display_name ?? kind label`, so a representative would read "You" against the customer's lines. No backend rule names the customer on staff reads. | M | `ui-contracts.openapi.yaml:3819`, `:5952`; `components/shared/messages.tsx:11` | AEA-29 (CON-12), AEA-40 (CON-21 `customer_message` payload); UX for the fallback | Engineering decision: send the customer's display name (or "Customer") on staff reads. The UI should ignore `display_name` for `kind: customer` on SCR-6 until this is settled. |
| A4 | **Do live actions change the case's lifecycle or version?** Three sources disagree. stage7/staff §5 says `join` writes only conversation fields, so the lifecycle stays `claimed` and nothing says `version` moves. The OpenAPI `LIVE_JOINED` example shows lifecycle `in_progress`. AEA-52 AC-4 expects `case_changed` on CON-21 after a join. The UI reloads after `join`, but not after `send`, `hand_back` or `close`. If any of those bump `version`, the representative's next Resolve uses a stale `expected_version`, gets `VERSION_CONFLICT` "changed by Riley" (themselves), and sees "This case changed" after their own hand back. That is the J-7 demo path. | H | `stage7/staff.md:320-327`; `ui-contracts.openapi.yaml:4602-4611`; `AEA-52.md:79`; UI `screens/scr06/useCaseActions.ts:86-90` (join reloads), `:107-117` (no reload) | AEA-46 (decides), AEA-29 (version rule), AEA-52 | Pick one rule and write it into AEA-46's ACs before its plan: (i) live actions never change lifecycle or version and append no `case_changed` (then fix AEA-52 AC-4 and treat the example's `in_progress` as illustrative), or (ii) they do, and the UI reloads after every live action. (i) is recommended: it matches staff §5. |
| A5 | `VERSION_CONFLICT` / `CASE_ALREADY_CLAIMED` examples write `changed_at` as `"2026-10-16 14:31:00-05:00"` (a space, not `T`). The backend will emit ISO 8601 with `T`. The UI's `Date.parse` accepts both in Chrome, so this is harmless today. | L | `ui-contracts.openapi.yaml` applyCaseAction 409 examples; `screens/scr06/errorCopy.ts:32-36` | AEA-08 (records it; the OpenAPI is not edited without Innocent) | Note it; no code change. |
| A6 | The oversight assign dialog writes its own success line ("Assigned MHC-C-0007 to Riley (demo representative).") and ignores the server's `result_line` ("Assigned to Riley (demo)."). A journey that asserts the server's line fails. | L | `screens/scr07/AssignDialog.tsx:56-58`; `stage7/staff.md:346` | UX session | Show `res.result_line`, as SCR-6 already does. |
| A7 | stage7/staff §8 says `ClockAdvanced` carries `date_label`, but OpenAPI `ClockAdvanceResponse` has only `now`, `label` and `became_overdue`. The UI reads `now` and `became_overdue`, so it is unaffected. The OpenAPI has no `additionalProperties: false` anywhere (UX G-07), so the response check would not catch the extra key: it would ship as quiet drift. | L | `stage7/staff.md:386-388`; `ui-contracts.openapi.yaml:10289`; `screens/scr07/DemoControls.tsx:42-43` | AEA-47 | Return exactly the OpenAPI fields; drop `date_label` from the route response. |

## (b) Frontend state vs backend state; refresh and resume

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| B1 | **The role is held on the session, but the UI reads it once.** `getSession` runs on mount. Afterwards the UI changes the role only after its own `switchRole`. There is no re-read on window focus or visibility, and none after a 403 `ROLE_NOT_ALLOWED`. stage7/staff tells the UI to treat `wrong_role` as "switched elsewhere" and re-read `getSession` on focus. As built, tab A (SCR-6 as Riley) keeps Riley's controls after tab B switches to supervisor, and its writes fail with "You can't do that as Riley, demo representative.", which is the wrong role. The same happens after a reset run from another tab. Only the tab that ran the reset re-reads the session. | H | `state/session.tsx:45-56`, `:62-78`; `screens/scr03/useResetDemo.ts:31-33`; requirement `stage7/staff.md:525-527`, STF-19 (`7b-decisions/staff.md:59`); SCREEN_SPECS N-29 (`SCREEN_SPECS.md:661`) | UX session | In `SessionProvider`: re-read `getSession` on `focus` / `visibilitychange`, and whenever any call throws `ROLE_NOT_ALLOWED`. Then `refetchAll()`. `RoleGate` then shows the right panel. |
| B2 | **The queue and case view swallow `ROLE_NOT_ALLOWED`.** `useQueueFeed` keeps the last `shown` list when a poll fails, so a 403 on SCR-5 is invisible and the old queue stays up. With no data yet, it reads "The queue didn't load. Try again." SCR-6 maps every non-404 error to "The case didn't load. Try again." `RoleGate` never passes `reset`, so the copy "The demo was reset, so you're back to the customer role. Pick a role again." reaches only the G5 read screens, through `ReadError`. The SCR-6 action error uses the client's stale role and ignores `details.reason`. | H | `screens/scr05/useQueueFeed.ts:17-24`; `screens/scr05/Scr05.tsx:71-72`; `screens/scr06/Scr06.tsx:112-113`; `components/shell/RoleGate.tsx:20-25`; `screens/reads/ReadError.tsx:9-10`; `screens/scr06/errorCopy.ts:45` | UX session | On `ROLE_NOT_ALLOWED` from a read: run B1's re-read, then render `RoleNotAllowedPanel` with `reset = details.reason === "role_reset"` in place of the body. Never keep stale staff data on screen after a 403. |
| B3 | **The mock cannot show B1, B2 or C1.** The dev world's role is per tab (`sessionStorage`). The mock clears `roleResetPending` after the first refusal, but the backend keeps `role_reset` on every staff call until `switch_role`. And the mock checks roles per operation only, with `applyCaseAction` collapsed to `[representative, supervisor]`, so per-action rules (assign and change_priority are supervisor only) are never refused. | M | `dev/world.ts:29`, `:43`; `dev/resolve.ts:60-63`; `stage7/staff.md:141-142`; `src/api/contract.gen.json` (`applyCaseAction.roles`) | UX session | Keep the dev role in `localStorage` (shared across tabs, like the cookie). Keep `roleResetPending` until `switchRole`. Refuse `assign` / `change_priority` from a representative with the `RoleNotAllowed` example. |
| B4 | **The stream changes the controller but never the live state.** On `controller_changed` the reducer sets `live.controller` only, never `live.state`. A second viewer, either the supervisor or Riley in another browser (same actor, STF-1), keeps "Claim and join" or "queued" after someone joins, and keeps the joined state after a hand back. A join appends no `case_changed` (staff §5), so nothing else tells that view. | M | `screens/scr06/caseReducer.ts:62-67`; `stage7/staff.md:322-325` | UX session | On `controller_changed`: `human` sets `state: "joined"`; `ai` sets `state: "handed_back"`, with `since = at`. Or call `reload()` on any `controller_changed` the view did not cause. |
| B5 | **A first stream connection replays history onto a fresh snapshot.** With no `Last-Event-ID`, CON-21 starts at the newest `demo_reset` id, or 0 when there is none, and replays everything after it. CON-12 `CaseDetail` carries no event id the UI could resume from; CON-1's `StartSessionResponse.events.last_event_id` has no CON-12 twin. So every time SCR-6 opens, old `chat_closed` events re-apply. That forces `live.state = "closed"`, shows "This chat is no longer live." with a disabled reply box, and, for `shift_ended`, the "This case changed" banner. Old event lines are duplicated too. Messages are de-duplicated by `message_id`; nothing else is. | M | `stage7/staff.md:357-361`; `ui-contracts.openapi.yaml:10870` (CaseDetail, no `events`), `:9818` (StartSessionResponse has them); `screens/scr06/caseReducer.ts:68-74` | **Innocent** (contract change), then AEA-45 / AEA-46 and the UX session | See the decision below. Interim UX fix: until the first `case_changed` or `customer_message` newer than `detail.as_of` arrives, ignore stream `chat_closed` / `controller_changed` whose `at <= detail.as_of`. |
| B6 | **A failed first `getSession` that is not a 401 counts as signed out.** A network blip or 5xx at load sends a signed-in reviewer to `/login`. | M | `state/session.tsx:49-54`; `router.tsx:37-42` | UX session | Add an `error` status with a retry line. Redirect only on 401. |
| — | Checked, in line: the selected case lives in the URL; the queue cursor is a reference, not an index; the claimed owner, lifecycle, `version` and `allowed_actions` come only from server responses (`summary` merges); the demo clock is polled every 10 s and on focus; a reload re-reads the session and the case. | — | `screens/scr06/caseReducer.ts:48-49`; `state/demoStatus.tsx:36-56`; `screens/scr05/useRowKeys.ts` | — | — |

**Decision for Innocent (B5), in brief.** The case view loads a snapshot (CON-12), then opens its event stream (CON-21).
The snapshot doesn't say which event it already includes, so the stream replays old events on top of it. A case whose
chat once closed then opens looking "no longer live". **Option A (recommended):** add `events: {last_event_id}` to
`CaseDetail`, as CON-1 already does, and have the UI connect with it as `Last-Event-ID`. This is one additive field;
AEA-45 serialises it and AEA-46 needs nothing new. **Option B:** keep the contract, and have the UI ignore replayed
events older than `as_of`. That works in the common cases, but it relies on demo-clock timestamps, which can tie.
**Option C:** the server starts header-less CON-21 connections at the newest event. This loses any event between the
snapshot and the connect, which breaks the CON-3 "no loss" rule.
**Decision needed:** add `CaseDetail.events.last_event_id` to the OpenAPI (A), or keep the contract and filter on the
client (B)?

## (c) Guards outside mock mode

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| C1 | **"Claim and join" is shown to the supervisor on SCR-5.** `QueueRow` has no `allowed_actions`, so every live row gets the button for both roles that can read the queue. Against the real backend, the claim succeeds and the join answers 403 `ROLE_NOT_ALLOWED`, because `liveChatAction` is representative only. The supervisor now owns a live-queued chat they cannot join. The customer keeps waiting. The message says "Open it and try Join chat", but the supervisor has no Join chat button. | H | `screens/scr05/QueueSections.tsx:26`; `screens/scr05/LiveRow.tsx:47-49`; `screens/scr06/claimAndJoin.ts:20-26`; `screens/scr05/Scr05.tsx:39-55`; x-roles `liveChatAction: [representative]` | UX session | Render the button only when `role === "representative"`. Show the supervisor "Open" only. Add a supervisor scenario that asserts it is absent. |
| C2 | **The reply box is active for the supervisor on a joined case.** `planActions` exempts only the owner, so `liveBox` is `"active"` whenever `live.state === "joined"`. The supervisor sees "You are replying as Riley (demo representative). The assistant is paused." with Send, Hand back and Close enabled. Each answers 403. | H | `screens/scr06/actionPlan.ts:25-29`; `screens/scr06/LiveBox.tsx:19-23`; `screens/scr06/Scr06.tsx:158-161` | UX session (after A1 fixes the list) | Make the box `"active"` only when `allowed_actions` includes `send_live_message` (the `LIVE_JOINED` example lists it). Otherwise show the conversation read only, with the line "Riley is replying in this chat." |
| C3 | **Real-mode browser runs are in progress, but no staff state can be reached in them yet.** The UX session was changing this during the audit: at 08:20 it added `E2E_TARGET=real` (no `webServer`, sign-in through SCR-12, roles and staffing switched through the product's own screens; their G-02). What is left: real mode defaults to a `npm run dev` proxy, not the production `dist` that AEA-49 serves. And every scenario that needs dev forcing is skipped in real mode, which covers most SCR-5/SCR-6 states (live-queued, joined, conflict, role reset). Until the staff journeys exist as product-driven steps, the real login, cookie, AEA-49's 303 and the cross-tab role behaviour stay unexercised for staff. | M | `apps/web/playwright.config.ts:3-8`, `:16-21`; `apps/web/tests/e2e/support/state.ts:1-10`, `:71`; `docs/ux/04-prototype/INTEGRATION_HANDOFF.md` G-02, G-03; AEA-49 AC-3 (`AEA-49.md:81`) | UX session (support) + AEA-58 (runs it) | Point `E2E_BASE_URL` at the AEA-49 server for AEA-58. Write J-6, J-7 and J-8 as product-driven steps (UX G-03, section 4.7), using the selector contract below, so that none of them needs a dev scenario. |
| C4 | A 503 `RESET_IN_PROGRESS` on `switchRole` or `advanceDemoClock` shows a generic failure and ignores `retry_after_ms`. | L | `state/session.tsx:74`; `screens/scr07/DemoControls.tsx:46-48`; `stage7/staff.md:427` | UX session | Say "The demo is resetting. Try again in a few seconds." and disable the control for `retry_after_ms`. |
| — | Checked, in line: 401 anywhere goes to `/login?return_to=…&reason=none\|expired`, the same shape as AEA-49's 303. A 401 on a stream raises the same signal. Every request sends `credentials: "include"`. `/login` itself tolerates a 401 from `getSession`. Route role lists equal the OpenAPI x-roles (SCR-5 rep and supervisor; SCR-6 adds owner; SCR-7 supervisor; SCR-8 all three staff roles; SCR-9 owner and supervisor). The owner's SCR-6 is read only, with no rail. | — | `state/session.tsx:36-43`, `:58`; `api/transport.ts:28-39`; `api/client.ts:69`, `:91`; `routes.ts:14-18` | — | — |

## (d) Error codes: handled vs OpenAPI vs addenda

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| D1 | `NOT_LIVE` has four reasons in staff §5: `not_waiting`, `not_joined`, `chat_closed` and `demo_reset`. The UI tells `demo_reset` apart and calls the rest "This chat has ended." When a Join fails with `not_waiting` (the customer left, or the shift ended), the chat hasn't "ended" from the representative's point of view. | L | `screens/scr06/errorCopy.ts:43-44`; `stage7/staff.md:312-315` | UX session | `not_waiting` → "The customer is no longer waiting in the chat. Reload." with a reload. |
| D2 | There is no client check before a send. A blank reply, or one over 2,000 characters, gets 400 `VALIDATION_ERROR` field `text` (STF-12), shown as "That didn't go through. Try again." The flag form can be submitted with no target chosen (`target: ""` → 400), and flag text has no 2,000 limit either. | L | `screens/scr06/LiveBox.tsx:33-38`; `screens/scr06/ActionForms.tsx:104-115`; `stage7/staff.md:331-336` | UX session | Disable Send while the text is blank, with `maxLength={2000}`. Make the flag target `required` and cap its text at 2,000. |
| — | Checked, in line: `VERSION_CONFLICT` shows "changed by … at …" with Reload; `current_version` is not needed because Reload re-reads the case. `CASE_ALREADY_CLAIMED` handles a `claimed_at` with or without a value (staff §5 sends it, the example omits it). `NOT_CLAIMED_BY_YOU` → "Claim the case first." `REASON_REQUIRED`, `WAKE_UP_REQUIRED` and `OUTCOME_REQUIRED` each get their sentence. `CASE_NOT_FOUND` after a reset gets the "may have been cleared by a demo reset" page. `ROLE_NOT_ALLOWED` on a `liveChatAction` 403 is told apart by `code`, not status (AEA-46 contract note 2). There is no 410 on staff routes; after a reset they answer 404 or 403 `role_reset` (staff §11). For the 403 `role_reset` gap, see B2. | — | `screens/scr06/errorCopy.ts:22-50`; `screens/scr06/Scr06.tsx:104-111`; `AEA-46.md` contract note 2 | — | — |

## (e) CON-21 stream events and replay vs AEA-46

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| E1 | **No ticket AC proves that the relayed customer message reaches CON-21.** web.md §9 and staff §7 give the `customer_message` append to `TurnService` (AEA-40), in the same transaction as the message row. But AEA-40 still lists "who appends it" as needs-decision 4, with no AC. AEA-46 does not append it. AEA-52 AC-14 is "Blocked on ND-52a". The core of J-7 (the customer types, Riley sees it on SCR-6) therefore has no owner AC before wave 3. | H | `stage7/web.md:346-347`; `stage7/staff.md:372-373`; `AEA-40.md:149`; `AEA-52.md:89` | AEA-40 (add the AC), AEA-52 / AEA-51 (settle ND-52a) | AEA-40 AC: with `controller = human`, `submitTurn` writes the message and appends `customer_message` to `case:<ref>` in one transaction, and the payload equals CON-12's `ChatLine` for that message. Add a J-7 step: SCR-6 shows the text within one poll interval. |
| E2 | **The client reconnects after `demo_reset`.** The server closes the stream after sending `demo_reset` (staff §7 step 6). The transport treats any close as a drop and reconnects with `Last-Event-ID` set to the reset id. For non-seeded references that gets 404, and the stream stops. For re-seeded references (MHC-C-0005…0008) the new connection stays open and streams the new case's events into the old view: `customer_message` lands on the pre-reset conversation, and `case_changed` versions are compared with the old version. | M | `stage7/staff.md:357-366`; `api/transport.ts:52-88`; `screens/scr06/useCaseStream.ts` (no stop); `screens/scr06/caseReducer.ts:75-80` | UX session | On `demo_reset`, disable the stream spec (`enabled = false`) and offer Reload. A reload then shows the re-seeded case, or "not found". |
| E3 | **A 403 on the stream stops it silently.** After a role switch or reset, a CON-21 403 ends the stream with no status the screen can show and no session re-read. The case view simply stops receiving customer messages. | M | `api/transport.ts:26`, `:56-59` | UX session | Report `403` as a distinct status (or call B1's session re-read). The case view then shows the role panel. |
| — | Checked, in line with AEA-46: frames are parsed by `id` / `event` / `data`; `: heartbeat` comments are skipped; `Last-Event-ID` is sent on reconnect with backoff of 1, 2, 4 and 5 s; unknown event types are ignored; `customer_message` is de-duplicated by `message_id`; the stream stays open after `chat_closed`, as staff §7 requires; `case_changed` raises "changed" only for a version the user's own writes don't explain. For the replay and controller gaps, see B4 and B5. | — | `api/sse.ts`; `api/transport.ts:54`, `:66-80`, `:84`; `screens/scr06/caseReducer.ts:36-40`, `:61-82` | — | — |

## (f) Production build excludes dev and mock code

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| F1 | `contract.gen.json` is bundled into `dist` because `client.ts` imports it for `OPS`. It carries every operation's `requestExamples`, so synthetic example payloads (the name "Omar Patel", the phone "512-555-0102") ship in the production bundle. The data is synthetic, so nothing leaks, but mock content is in `dist`. | L | `apps/web/src/api/client.ts:2`, `:40`; `apps/web/dist/assets/index-CY_6x921.js` (contains `requestExamples`) | UX session | Split the generated index: a runtime map (method, path, auth) for the app, and the examples file for `src/dev` only. Add `requestExamples` to the `check:dist` needles. |
| F2 | `check:dist` greps for five dev markers only. Test fixtures that live outside `src/dev` (`screens/scr06/case.fixtures.ts`, `specExample.ts`, `screens/scr05/queue.fixtures.ts`, `screens/reads/test/*`) are imported only by tests today, but nothing stops a stray import from shipping them. | L | `apps/web/scripts/check-dist.mjs:11`; file list above | UX session | Add a lint rule (`no-restricted-imports` for `**/*.fixtures`, `**/test/**`, `@/dev/**` from non-test files), or a `check:dist` needle per fixture. |
| — | Checked, in line: the dev layer loads only when `MODE === "mock"`, by dynamic import, so a production build drops `src/dev` (`main.tsx:11-14`; PROTOTYPE_PLAN reports `check:dist` passing). Real-backend mode exists: `npm run dev` proxies `/api` to `127.0.0.1:${API_PORT:-8000}` with cookies included. Production is same-origin through AEA-49. Types are generated from the signed OpenAPI, and `check:gen` catches stale files. | — | `apps/web/src/main.tsx:11-14`; `apps/web/vite.config.ts:8-12`; `apps/web/package.json` scripts | — | — |

## (g) Stable selectors for each staff state a journey asserts

| # | Finding | Sev | Evidence | Owner | Fix |
|---|---|---|---|---|---|
| G1 | **No test ids or state attributes on staff screens.** Journeys must key on copy and ARIA names. Several states a staff journey asserts have no stable hook at all: the live state (joined / handed back / closed), the controller, the owner line, the version-conflict line and its Reload, the role-reset panel, the "changed elsewhere" banner, the live box mode, and the staffing banner. Copy-keyed selectors break on any wording change at UX-5. | M | `grep data-testid apps/web/src/screens` → 3 hits, none on SCR-5/6/7/8 | UX session | Publish the selector contract below in `docs/plans/ux-join/` and add the missing attributes before UX-4 sign-off. |

**Selector contract the staff journeys need** (present = exists today; add = the UX session adds it):

| State a journey asserts | Selector | Status |
|---|---|---|
| Acting role | `role=radiogroup[name="Acting as"]` → radio `[aria-checked=true]` name ends ", current" | present (`components/shell/RoleSwitch.tsx:16`, `:30`) |
| Role refused / role reset panel | `[data-testid=role-panel][data-reason=wrong_role\|role_reset\|customer]` | add |
| Queue row for a case | `role=button` (or link) whose name starts with `P<n> <word>, MHC-C-xxxx` | present (`components/shared/QueueRow.tsx:55-57`) |
| Live queue row, Claim and join | `role=button[name="Claim and join MHC-C-xxxx"]` | present (`screens/scr05/LiveRow.tsx:47`) |
| Queue empty / nobody on shift | `[data-testid=queue-empty]`, `[data-testid=live-queue][data-staffing=nobody_online\|simulated_on_shift]` | add |
| Case loaded, lifecycle | `ol[aria-label="Case state"] li[aria-current=step]` plus `[data-testid=case][data-lifecycle=…][data-version=n]` | partly present (`screens/scr06/LifecycleLine.tsx:22-25`); add the data attributes |
| Owner / claimed by | `[data-testid=case-owner]` | add |
| Brief, eight headings in order | `#brief-1` … `#brief-8`, each `h3` = title as sent; heading 4 tag "Customer says · not checked" | present (`screens/scr06/BriefSection.tsx:14`, `:19`) |
| Brief being written | `[data-testid=brief][data-status=ready\|being_written\|failed]` | add (today copy only, `BriefView.tsx:10`) |
| Promise | `[aria-labelledby=promise-h]`, plus `[data-promise-status=open\|kept\|missed\|changed]` | partly present (`PromiseCard.tsx:13`); add the status |
| Source snapshot vs current | `#src-<source_id>` with `[data-changed-since=true\|false]`, `[data-current-unavailable]` | partly present (`SourceCard.tsx:10`); add the attributes |
| Conversation message (relayed customer line) | `#msg-<message_id>` with `[data-speaker=customer\|representative\|assistant]` | partly present (`ConversationTab.tsx:17`); add the speaker |
| Live box mode, controller | `[data-testid=live-box][data-mode=active\|disabled\|ended-by-reset][data-controller=ai\|human]` | add |
| Action result line | `#case-result`, `#queue-result` | present (`useCaseActions.ts:18`, `Scr05.tsx:64`) |
| Action error, conflict and Reload | `[data-testid=action-error][data-code=VERSION_CONFLICT…]` with `role=button[name=Reload]` | add (code today: `ActionArea.tsx`) |
| Changed elsewhere banner | `[data-testid=case-stale]` | add |
| Oversight lanes, clock advance result | `[data-lane=p0_p1\|overdue\|due_soon\|unowned\|stuck_waiting]`, `#demo-controls-result` | lanes add; result present (`DemoControls.tsx:87`) |
| Review list row, reviewed | `[data-flag-id=flg-n][data-status=new\|reviewed]` | add |

---

## What the UX session must provide for the staff journeys, and by when

The order these depend on, from the slice plan (`slice-plan.md:90-94`, `:163`, `:176`, `:178`): **UX-4 signed → AEA-49
serves `dist` → AEA-58 runs browser journeys (wave 3) → UX-5 signed → AEA-55 reruns the UX-5 suite against the real
backend (wave 4).**

**Before UX-4 sign-off.** AEA-49 and AEA-58 are gated on it, so whatever ships in `dist` then is what AEA-58 tests.
1. The H fixes inside `apps/web`: B1 (session re-read on focus and on `ROLE_NOT_ALLOWED`), B2 (role panel instead of
   stale data or "didn't load"), C1 (no Claim and join for the supervisor), C2 (reply box only with
   `send_live_message`). C2 relies on A1's list; build it against the OpenAPI examples now.
2. The selector contract above, published in `docs/plans/ux-join/`, with the "add" rows built.
3. The mock aligned with the backend (B3), so the H fixes can be seen in mock mode: a role shared across tabs,
   `role_reset` kept until a switch, per-action roles.
4. The production build command and output path stated in one place (`npm run build` → `apps/web/dist`, with
   `check:dist` green), and F1's split so mock examples leave `dist`.

**Before AEA-58 starts (wave 3, after AEA-49).**
5. A `real` Playwright project (C3): `baseURL` from env, no `webServer`, a sign-in helper that uses SCR-12, and no
   `?signedin`, `?role` or `?scenario`. AEA-58's pytest-playwright suite can reuse its selectors and login steps.
6. For each staff journey, the steps and expected UI state, keyed to the selectors:
   - **J-6:** an escalation in chat → the row on SCR-5 → SCR-6 with eight headings, the promise, and the source chips
     resolving (A2).
   - **J-7:** claim and join → reply → the customer's relayed line on SCR-6 (E1) → hand back → resolve, with no
     self-conflict (A4).
   - **J-8:** role switch in tab B is seen by tab A; a reset from another tab shows the `role_reset` panel; refresh and
     resume of the case view.

**Before UX-5 sign-off** (the UX-5 suite is what AEA-55 reruns):
7. B4, B6, E2, E3, D1, D2, A6. Also the B5 interim client filter, or Option A wired in if Innocent picks it.
8. Every staff scenario that is a dev fixture with no named example (PROTOTYPE_PLAN "Dev fixtures") rechecked against
   the backend ACs once A1, A2 and A4 are settled, so the mock does not encode a different `allowed_actions` table than
   AEA-29 builds.

**Before AEA-55 (wave 4):** the UX-5 suite passes in real mode against the integrated backend, with no mock-only code
path exercised.

**Backend items that must land in the tickets before their wave-2 plans start** (they are being rewritten now):
- **AEA-29:** A1 (the `allowed_actions` table) and A2 (presentation values, the `source_id` scheme).
- **AEA-46:** A4 (the live-action version and lifecycle rule).
- **AEA-40:** E1 (the `customer_message` append AC).
- **AEA-29 / AEA-40:** A3 (the customer name on staff reads).
- **AEA-47:** A7.
- **Innocent:** the B5 decision.
