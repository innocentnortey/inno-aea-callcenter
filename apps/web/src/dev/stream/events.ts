// Dev fixtures for scripted streams, typed against the OpenAPI schemas so a schema change breaks the build.
// Only three events exist as named OpenAPI examples (the chat FRAMES: representative_joined, ai_paused, staff_message);
// the rest carry "dev fixture: no named example in the OpenAPI (see foundation plan section 8.2)".
import type { components } from "@/api/types.gen";

type ChatEvent = components["schemas"]["ChatEvent"];
type CaseEvent = components["schemas"]["CaseEvent"];
const RILEY = { kind: "representative", display_name: "Riley" } as const;
const SYSTEM = { kind: "event", display_name: null } as const;
const AT = "2026-10-16T14:22:00-05:00";

export const chatEvents = {
  // OpenAPI example: streamChatEvents FRAMES, id 12
  representative_joined: (): ChatEvent => ({ event_id: 0, type: "representative_joined", at: AT, speaker: RILEY, display_name: "Riley", line: "Riley (demo representative) has joined." }),
  // OpenAPI example: streamChatEvents FRAMES, id 13
  ai_paused: (): ChatEvent => ({ event_id: 0, type: "ai_paused", at: AT, speaker: SYSTEM, line: "The assistant is paused while Riley is here." }),
  // OpenAPI example: streamChatEvents FRAMES, id 14
  staff_message: (): ChatEvent => ({ event_id: 0, type: "staff_message", at: "2026-10-16T14:22:40-05:00", speaker: RILEY, message_id: "m-88", text: "Hi Omar, I can look at the after-hours charge with you." }),
  // dev fixture: no named example in the OpenAPI (see foundation plan section 8.2)
  ai_resumed: (): ChatEvent => ({ event_id: 0, type: "ai_resumed", at: "2026-10-16T14:30:00-05:00", speaker: SYSTEM, line: "The assistant is back." }),
  // dev fixture: no named example in the OpenAPI (see foundation plan section 8.2)
  chat_closed: (): ChatEvent => ({ event_id: 0, type: "chat_closed", at: "2026-10-16T14:24:00-05:00", speaker: SYSTEM, line: "Riley closed this chat.", composer_disabled: true }),
  // dev fixture: no named example in the OpenAPI (see foundation plan section 8.2); staffing bodies copy getStaffing ON
  staffing_changed: (): ChatEvent => ({
    event_id: 0, type: "staffing_changed", at: AT, speaker: SYSTEM,
    staffing: { mode: "simulated_on_shift", label: "Simulated staff on shift (demo)", banner: "Simulated staffing (demo). No Meridian employee is online." },
    line: "Simulated staffing is on (demo).",
  }),
  // dev fixture: no named example in the OpenAPI (see foundation plan section 8.2); handoff and settled copy submitTurn HANDOFF
  shift_ended: (): ChatEvent => ({
    event_id: 0, type: "shift_ended", at: AT, speaker: SYSTEM, line: "The simulated shift ended.",
    handoff: {
      block_id: "blk-901", type: "handoff", speaker: { kind: "assistant", display_name: "Meridian assistant" }, at: "2026-10-16T14:20:00-05:00",
      card_id: "handoff-1", options: [], answered: null, reference: "MHC-C-0007", variant: "nobody_online",
      promise_text: "No representative is online right now. A representative will get back to you within 1 business day",
      due_at: "2026-10-19T19:00:00-05:00", due_label: "by Monday, October 19, 7:00 pm",
      extra_lines: ["Your reference is MHC-C-0007."], produced_by_code: true,
      followup_chooser: {
        legend: "We'll follow up by email unless you'd prefer a phone call.",
        channels: [
          { channel: "email", label: "Email · the address on your account", on_record: true },
          { channel: "phone", label: "Phone call · the number ending in 02", on_record: true },
        ],
        windows: [{ window: "morning", label: "Mornings" }, { window: "afternoon", label: "Afternoons" }, { window: "any", label: "Any time" }],
        general_only: false,
      },
    },
    settled: {
      built_from: "conversation_state", visit: null,
      request: {
        reference: "MHC-C-0007", promise_text: "No representative is online right now. A representative will get back to you within 1 business day",
        due_at: "2026-10-19T19:00:00-05:00", due_label: "by Monday, October 19, 7:00 pm", extra_lines: ["Your reference is MHC-C-0007."], live_queued: false, followup: null,
      },
      identity: { status: "verified", hint: "the phone ending in 02" }, replying: { kind: "ai", display_name: null }, actions: [],
    },
  }),
  // dev fixture: no named example in the OpenAPI (see foundation plan section 8.2); clock copies getDemoClock ADVANCED
  clock_changed: (): ChatEvent => ({
    event_id: 0, type: "clock_changed", at: AT, speaker: SYSTEM,
    demo_clock: { now: "2026-10-19T07:00:00-05:00", label: "Mon Oct 19, 2026 · 7:00 am", date_label: "Mon Oct 19, 2026 (demo date)" },
  }),
  // dev fixture: no named example in the OpenAPI (see foundation plan section 8.2)
  demo_reset: (): ChatEvent => ({ event_id: 0, type: "demo_reset", at: AT, speaker: SYSTEM, line: "The demo was reset." }),
} satisfies Record<string, () => ChatEvent>;

export const caseEvents = {
  // OpenAPI example: streamCaseEvents FRAMES, id 5
  customer_message: (): CaseEvent => ({
    event_id: 0, type: "customer_message", at: "2026-10-16T14:23:10-05:00",
    message: { message_id: "m-90", speaker: { kind: "customer", display_name: "You" }, at: "2026-10-16T14:23:10-05:00", text: "Thanks, that helps." },
  }),
  // OpenAPI example: streamCaseEvents FRAMES, id 6
  chat_closed: (): CaseEvent => ({ event_id: 0, type: "chat_closed", at: "2026-10-16T14:24:00-05:00", reason: "closed_by_staff" }),
  // dev fixture: no named example in the OpenAPI (see foundation plan section 8.2)
  controller_changed: (): CaseEvent => ({ event_id: 0, type: "controller_changed", at: AT, controller: { kind: "human", display_name: "Riley" }, line: "Riley took over." }),
  // dev fixture: no named example in the OpenAPI (see foundation plan section 8.2)
  case_changed: (): CaseEvent => ({ event_id: 0, type: "case_changed", at: AT, version: 2, lifecycle: "claimed" }),
  // dev fixture: no named example in the OpenAPI (see foundation plan section 8.2)
  demo_reset: (): CaseEvent => ({ event_id: 0, type: "demo_reset", at: AT, line: "The demo was reset." }),
} satisfies Record<string, () => CaseEvent>;
