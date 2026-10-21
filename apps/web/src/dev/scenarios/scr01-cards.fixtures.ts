// G2 dev fixtures: transforms over named Prism examples for card states the OpenAPI has no example for
// (foundation plan 8.2). Each is a pure function over the example body.
import type { components } from "@/api/types.gen";

export type TurnResponse = components["schemas"]["TurnResponse"];
type ReplyBlock = components["schemas"]["ReplyBlock"];
type Transform = (body: TurnResponse) => TurnResponse;

export const mapBlocks = (fn: (b: ReplyBlock) => ReplyBlock): Transform => (body) => ({ ...body, blocks: body.blocks.map(fn) });
export const appendBlocks = (extra: ReplyBlock[]): Transform => (body) => ({ ...body, blocks: [...body.blocks, ...extra] });

// The ANSWER_WITH_SOURCE source object, copied verbatim.
const AFTER_HOURS_SOURCE = {
  passage_id: "fee_schedule_2026#after-hours",
  file: "policies/fee_schedule_2026.pdf",
  section: "After-hours dispatch",
  version_date: "2026-01-01",
  excerpt: "After-hours dispatch: $149.",
  audience: "customer",
  version_label: "Effective Jan 1, 2026",
} as const;

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: SLOT_CARD
export const slotCardUrgent: Transform = mapBlocks((b) => (b.type === "slot_card" ? { ...b, urgent: true } : b));

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: EMERGENCY_LINE
export const emergencyLineStaffed: Transform = mapBlocks((b) => (b.type === "emergency_line" ? { ...b, separate_line: null } : b));

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: QUICK_CHECKS
export const quickChecksShown: Transform = mapBlocks((b) =>
  b.type === "quick_checks"
    ? { ...b, checks: [{ text: "Dev fixture check 1", source: { ...AFTER_HOURS_SOURCE } }, { text: "Dev fixture check 2", source: { ...AFTER_HOURS_SOURCE } }] }
    : b,
);

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: NO_INFO
export const noWindowFits: Transform = mapBlocks((b) =>
  b.type === "no_info" ? { ...b, text: "That's the earliest I can book. I can't add you to a waitlist from here.", person_key: true } : b,
);

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: ANSWER_WITH_SOURCE
export const partialReply: Transform = (body) => {
  const first = body.blocks[0];
  return appendBlocks([{
    block_id: "blk-203",
    type: "no_info",
    speaker: { kind: "assistant", display_name: "Meridian assistant" },
    at: first?.at ?? "2026-10-16T14:20:00-05:00",
    text: "I don't have that information.",
    person_key: true,
  }])(body);
};

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: HANDOFF
export const handoffRefund: Transform = mapBlocks((b) =>
  b.type === "handoff"
    ? {
        ...b,
        variant: "refund",
        promise_text: "A representative will get to your refund request within 2 business days.",
        due_at: null,
        due_label: null,
        extra_lines: ["I can't promise an outcome.", "Your reference is MHC-C-0007."],
      }
    : b,
);

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: HANDOFF
export const handoffGeneralOnly: Transform = mapBlocks((b) =>
  b.type === "handoff"
    ? { ...b, followup_chooser: { ...b.followup_chooser, general_only: true, channels: b.followup_chooser.channels.map((c) => ({ ...c, on_record: false })) } }
    : b,
);

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: CHANGE_REQUEST
export const changeRequestCancel: Transform = mapBlocks((b) =>
  b.type === "change_request" ? { ...b, change: "cancel", wanted_text: "Cancel the visit on Wednesday, October 21, 8:00 am – 12:00 pm" } : b,
);

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: CHANGE_REQUEST
export const changeRequestStaffed: Transform = mapBlocks((b) =>
  b.type === "change_request"
    ? {
        ...b,
        promise_text: "A representative will join this chat when available. You can keep chatting with me while you wait, if you like.",
        due_at: null,
        due_label: null,
        cant_guarantee_line: null,
        extra_lines: ["Your reference is MHC-C-0009."],
        phone_support_line: "Phone support is open until 7:00 pm today if you'd like to call.",
      }
    : b,
);

// dev fixture: no named example in the OpenAPI (foundation plan 8.2); base example: CANCELLED.
// Adds the `cancelled` write that CANCELLED.writes has but CANCELLED.settled.actions lacks (contract request C-9).
export const cancelledWithWrite: Transform = (body) => ({
  ...body,
  settled: {
    ...body.settled,
    actions: [
      ...body.settled.actions,
      { kind: "cancelled", summary: "Cancelled Wed Oct 21 visit", turn_id: body.turn_id, at: body.blocks[0]?.at ?? "2026-10-16T14:20:00-05:00" },
    ],
  },
});

export interface FixtureMeta { base: string; transform: Transform; note: string }
export const FIXTURE_IDS: Record<string, FixtureMeta> = {
  "slot-card-urgent": { base: "SLOT_CARD", transform: slotCardUrgent, note: "urgent slot card" },
  "emergency-line-staffed": { base: "EMERGENCY_LINE", transform: emergencyLineStaffed, note: "no separate line while staffed" },
  "quick-checks-shown": { base: "QUICK_CHECKS", transform: quickChecksShown, note: "checks list open, two synthetic checks" },
  "no-window-fits": { base: "NO_INFO", transform: noWindowFits, note: "no window fits sentence" },
  "partial-reply": { base: "ANSWER_WITH_SOURCE", transform: partialReply, note: "answer with source, then no_info" },
  "handoff-refund": { base: "HANDOFF", transform: handoffRefund, note: "refund variant" },
  "handoff-general-only": { base: "HANDOFF", transform: handoffGeneralOnly, note: "unverified customer: general destination only" },
  "change-request-cancel": { base: "CHANGE_REQUEST", transform: changeRequestCancel, note: "fee-bearing cancel" },
  "change-request-staffed": { base: "CHANGE_REQUEST", transform: changeRequestStaffed, note: "staffed promise and phone line" },
  "cancelled-with-write": { base: "CANCELLED", transform: cancelledWithWrite, note: "adds the cancelled write to settled.actions" },
};
