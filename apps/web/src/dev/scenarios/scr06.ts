import type { Scenario, ScreenScenarios } from "./types";
import { caseScripts } from "../stream/case-scripts";
import { claimedByDemoSupervisor, claimedByMe, emptyHeadings, shiftEndedPromise, stuckWaiting } from "./case-transforms";

const CASE = "/staff/cases/MHC-C-0007";
const base = { screen: "SCR-6", route: CASE } as const;
const claimed = { getCase: { example: "DEFAULT", transform: claimedByMe } } as const;

const scenarios: Scenario[] = [
  { ...base, id: "scr06.default", state: "default", label: "Unclaimed billing dispute", notes: "Claim split button; Sources tab; Demo seed; Join chat disabled with its reason." },
  { ...base, id: "scr06.empty-nothing-recorded", state: "empty", label: "Two sections empty", ops: { getCase: { example: "DEFAULT", transform: emptyHeadings([5, 7]) } }, notes: "Sections 5 and 7 read 'Nothing recorded.'" },
  { ...base, id: "scr06.loading", state: "loading", label: "Case loading", ops: { getCase: { hang: true } } },
  { ...base, id: "scr06.partial-brief-pending", state: "partial", label: "Brief being written", ops: { getCase: { example: "BRIEF_BEING_WRITTEN" }, getQueue: { example: "BRIEF_BEING_WRITTEN" } } },
  { ...base, id: "scr06.partial-source-unavailable", state: "partial", label: "A source can't be read", notes: "DEFAULT already has the FAQ source unreadable." },
  { ...base, id: "scr06.partial-trimmed", state: "partial", label: "A brief section was trimmed", ops: { getCase: { example: "TRIMMED_STOP" } }, notes: "Section 3 shows the removed-line note." },
  { ...base, id: "scr06.error-not-found", state: "error", label: "No such case", route: "/staff/cases/MHC-C-0099", notes: "The case director answers CASE_NOT_FOUND for an unknown reference." },
  { ...base, id: "scr06.error-owner-readonly", state: "error", label: "Business owner: read-only case", role: "owner", notes: "No named example exists for the owner view: the case director sets allowed_actions to [] for the owner." },
  { ...base, id: "scr06.error-reason-missing", state: "error", label: "Release without a reason", ops: claimed, notes: "Open Release and submit empty. Also Wait without a time, Resolve without an outcome." },
  { ...base, id: "scr06.stale-changed-since", state: "stale", flowState: "Changed since", label: "A source changed since the AI saw it", notes: "DEFAULT has the membership record changed." },
  {
    ...base, id: "scr06.stale-version-conflict", state: "stale", label: "Someone else changed the case",
    ops: { applyCaseAction: { example: "VERSION_CONFLICT", status: 409 }, getCase: { sequence: [{ example: "DEFAULT" }, { example: "DEFAULT", transform: claimedByDemoSupervisor }] } },
    notes: "Click Claim: the conflict sentence and Reload; Reload shows the case claimed by the demo supervisor.",
  },
  { ...base, id: "scr06.stale-case-changed-elsewhere", state: "stale", label: "Case changed elsewhere (stream)", stream: caseScripts.caseChangedElsewhere, notes: "After 3 s: 'This case changed. Show the latest.'" },
  {
    ...base, id: "scr06.stale-stuck-waiting", state: "stale", flowState: "Stuck waiting", label: "Wake-up time has passed",
    ops: { getCase: { example: "WAITING", transform: stuckWaiting("2026-10-16T14:00:00-05:00") } }, notes: "Header 'Wake-up time passed (Fri 2:00 pm). Pick it back up.'; primary 'Pick it back up'.",
  },
  { ...base, id: "scr06.stale-overdue", state: "stale", flowState: "Overdue", label: "Overdue refund request", route: "/staff/cases/MHC-C-0005", notes: "The case director re-skins DEFAULT from the queue row: Overdue after the due headline." },
  { ...base, id: "scr06.stale-shift-ended", state: "stale", flowState: "Shift ended before claim", label: "Promise changed after the shift ended", ops: { getCase: { example: "DEFAULT", transform: shiftEndedPromise() } } },
  { ...base, id: "scr06.success-claimed", state: "success", label: "Claim the case", notes: "Click Claim: 'Claimed · Riley (demo)'; lifecycle moves to Claimed; Log a call enabled." },
  { ...base, id: "scr06.success-contact-logged", state: "success", label: "Log a call", ops: claimed, notes: "Log a call, Reached, Record: activity 'Called · Reached the customer · Demo: recorded, not sent'." },
  { ...base, id: "scr06.success-resolved", state: "success", label: "Resolve the case", ops: claimed, notes: "Resolve with an outcome: lands on /staff/queue with 'MHC-C-0007 resolved.'" },
  { ...base, id: "scr06.success-flagged", state: "success", label: "Flag the case", notes: "Flag, pick one, Add to review list: 'Added to the review list.'" },
  { ...base, id: "scr06.success-waiting", state: "success", flowState: "Waiting", label: "Set waiting", ops: claimed, notes: "Set waiting with a date and time: header 'Wakes ...'." },
  { ...base, id: "scr06.success-released", state: "success", flowState: "Released", label: "Release the case", ops: claimed, notes: "Release with a reason: 'Released.', back to Unassigned." },
  { ...base, id: "scr06.success-assigned", state: "success", flowState: "Assign or reprioritise (supervisor)", label: "Supervisor assigns or reprioritises", role: "supervisor", notes: "Assign to Riley with a reason, or Change priority to P2." },
  { ...base, id: "scr06.disabled-before-claim", state: "disabled", label: "Actions before the claim", notes: "Resolve, Set waiting, Close unresolved say 'Claim the case first.'; Join chat explains itself; no Assign or priority for the representative." },
  {
    ...base, id: "scr06.disabled-live-box", state: "disabled", flowState: "Handed back", label: "Hand the chat back",
    ops: { getCase: { example: "LIVE_JOINED" }, liveChatAction: { example: "HANDED_BACK" } }, notes: "Hand back: 'Handed back to the assistant at 2:22 pm'; the live box is disabled.",
  },
  { ...base, id: "scr06.flow-live-queued", state: "default", flowState: "Live-queued case", label: "Customer waiting in the chat", route: "/staff/cases/MHC-C-0012", staffing: "simulated_on_shift", notes: "Lifecycle starts at Live-queued; 'Claim and join'." },
  {
    ...base, id: "scr06.flow-live-joined", state: "success", flowState: "Joined, AI paused", label: "Joined, assistant paused", staffing: "simulated_on_shift",
    ops: { getCase: { example: "LIVE_JOINED" } }, stream: caseScripts.customerReply, notes: "Live box on the Conversation tab; after 4 s 'Thanks, that helps.' arrives.",
  },
  {
    ...base, id: "scr06.flow-chat-closed", state: "success", flowState: "Chat closed", label: "The chat closes", ops: { getCase: { example: "LIVE_JOINED" } }, stream: caseScripts.replyThenClosed,
    notes: "After 7 s: 'Chat closed at 2:24 pm'; live box disabled; Resolve and Close unresolved available.",
  },
  {
    ...base, id: "scr06.flow-reset-ended", state: "error", flowState: "Customer chat ended by reset", label: "The demo was reset mid-chat",
    ops: { getCase: { example: "LIVE_JOINED" }, liveChatAction: { example: "NOT_LIVE", status: 409 } }, stream: caseScripts.resetEnded, notes: "Live box: 'This chat ended because the demo was reset.'",
  },
  { ...base, id: "scr06.flow-safety", state: "default", flowState: "Safety case", label: "Gas smell safety case", route: "/staff/cases/MHC-C-0008", notes: "P0 in the title; 'No due time: safety'." },
  { ...base, id: "scr06.flow-fee-bearing", state: "default", flowState: "Fee-bearing change request", label: "Fee-bearing change request", route: "/staff/cases/MHC-C-0009", notes: "The example's due label says Sat Oct 17; SCREEN_SPECS prints Fri (contract data difference)." },
  { ...base, id: "scr06.flow-seeded", state: "default", flowState: "Seeded demo case", label: "Seeded demo case", notes: "The 'Demo seed' tag." },
];
export const screenScenarios: ScreenScenarios = { complete: true, scenarios };
