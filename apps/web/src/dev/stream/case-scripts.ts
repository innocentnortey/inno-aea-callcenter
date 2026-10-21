import type { components } from "@/api/types.gen";
import type { StreamScript } from "./types";

type CaseEvent = components["schemas"]["CaseEvent"];
// Event ids start at 31; the OpenAPI Last-Event-ID example is 30. Every event is typed, so a schema change breaks the build.

// OpenAPI streamCaseEvents FRAMES, first frame (values copied; id differs)
const customerMessage = {
  event_id: 31, type: "customer_message", at: "2026-10-16T14:23:10-05:00",
  message: { message_id: "m-90", speaker: { kind: "customer", display_name: "You" }, at: "2026-10-16T14:23:10-05:00", text: "Thanks, that helps." },
} satisfies CaseEvent;
// OpenAPI streamCaseEvents FRAMES, second frame
const chatClosed = { event_id: 32, type: "chat_closed", at: "2026-10-16T14:24:00-05:00", reason: "closed_by_staff" } satisfies CaseEvent;

export const caseScripts: Record<string, StreamScript> = {
  customerReply: { thread: "MHC-C-0007", steps: [{ afterMs: 4000, event: customerMessage }] },
  replyThenClosed: { thread: "MHC-C-0007", steps: [{ afterMs: 4000, event: customerMessage }, { afterMs: 3000, event: chatClosed }] },
  // dev fixture: no named example in the OpenAPI (foundation plan 8.2); the HANDED_BACK live response carries since 14:22
  handedBack: {
    thread: "MHC-C-0007",
    steps: [{ afterMs: 3000, event: { event_id: 33, type: "controller_changed", at: "2026-10-16T14:22:00-05:00", controller: { kind: "ai", display_name: null }, line: "Handed back to the assistant at 2:22 pm" } satisfies CaseEvent }],
  },
  // dev fixture: no named example in the OpenAPI (foundation plan 8.2); wording from the SCREEN_SPECS flow state
  resetEnded: {
    thread: "MHC-C-0007",
    steps: [{ afterMs: 3000, event: { event_id: 34, type: "demo_reset", at: "2026-10-16T14:25:00-05:00", line: "This chat ended because the demo was reset." } satisfies CaseEvent }],
  },
  // dev fixture: version 4 and 14:31 mirror the VERSION_CONFLICT example's current_version / changed_at
  caseChangedElsewhere: {
    thread: "MHC-C-0007",
    steps: [{ afterMs: 3000, event: { event_id: 35, type: "case_changed", at: "2026-10-16T14:31:00-05:00", version: 4, lifecycle: "claimed" } satisfies CaseEvent }],
  },
  // dev fixture: no named example in the OpenAPI (foundation plan 8.2)
  shiftEnded: {
    thread: "MHC-C-0012",
    steps: [
      { afterMs: 3000, event: { event_id: 36, type: "chat_closed", at: "2026-10-16T14:26:00-05:00", reason: "shift_ended" } satisfies CaseEvent },
      { afterMs: 500, event: { event_id: 37, type: "case_changed", at: "2026-10-16T14:26:00-05:00", version: 4, lifecycle: "unassigned" } satisfies CaseEvent },
    ],
  },
};
