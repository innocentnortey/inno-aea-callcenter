// G2 (chat cards): scenarios that force the NEXT chat reply (or the handoff / thread read) to show each card state.
import type { OpForce, Scenario, ScreenScenarios, StandardState } from "./types";
import * as fx from "./scr01-cards.fixtures";

const SLUG = "scr01-cards";
type Transform = (b: fx.TurnResponse) => fx.TurnResponse;

const next = (example: string, transform?: Transform): OpForce => (transform ? { example, transform } : { example });
const NEXT_NOTE = (example: string) => `Send any message; the next reply is ${example}. The force is consumed by that reply.`;

function turn(id: string, state: StandardState, label: string, example: string, transform?: Transform, flowState?: string, notes?: string): Scenario {
  return {
    id: `${SLUG}.${id}`, screen: "SCR-1", state, flowState, route: "/", role: "customer",
    label: `${label} (next reply)`, ops: { submitTurn: next(example, transform) }, notes: notes ?? NEXT_NOTE(example),
  };
}
function person(id: string, state: StandardState, label: string, example: string, flowState?: string, staffing?: Scenario["staffing"]): Scenario {
  return {
    id: `${SLUG}.${id}`, screen: "SCR-1", state, flowState, route: "/", role: "customer", staffing,
    label, ops: { requestPerson: { example } }, notes: "Tap Talk to a person",
  };
}

const scenarios: Scenario[] = [
  turn("safety-takeover", "success", "Safety takeover", "SAFETY", undefined, "Safety takeover"),
  turn("burning-smell-unknown", "default", "Burning smell question", "BURNING_CHECK", undefined, "Burning smell, unknown"),
  turn("burning-smell-risk-unclear", "success", "Conditional safety card", "CONDITIONAL_SAFETY", undefined, "Burning smell, risk unclear"),
  turn("burning-smell-ruled-out", "default", "Urgent slot card", "SLOT_CARD", fx.slotCardUrgent, "Burning smell, both ruled out"),
  turn("someone-in-danger", "success", "Emergency line card", "EMERGENCY_LINE", undefined, "Someone in danger (no heat, no cooling, leak)"),
  turn("someone-in-danger-staffed", "success", "Emergency line card, staffed", "EMERGENCY_LINE", fx.emergencyLineStaffed),
  turn("quick-checks-offered", "default", "Quick checks offered", "QUICK_CHECKS", undefined, "Quick checks offered / skipped"),
  turn("quick-checks-shown", "default", "Quick checks shown", "QUICK_CHECKS", fx.quickChecksShown),
  turn("urgency-questions", "default", "Urgency questions", "URGENCY_QUESTIONS"),
  turn("where-card", "default", "Where card", "WHERE_PROMPT"),
  turn("slot-card", "default", "Slot card", "SLOT_CARD"),
  turn("slot-card-members", "success", "Slot card with member windows", "SLOT_CARD_MEMBER"),
  turn("out-of-area", "error", "Out of area", "OUT_OF_AREA", undefined, "Out of area"),
  turn("no-window-fits", "partial", "No window fits", "NO_INFO", fx.noWindowFits, "No window fits"),
  turn("identity-needed", "default", "Identity needed", "LOCATE_PROMPT", undefined, "Window chosen, identity needed"),
  turn("code-sent", "default", "Code sent", "CODE_SENT", undefined, "Code sent"),
  turn("code-wrong", "error", "Code wrong", "CODE_WRONG", undefined, "Code wrong, tries left"),
  turn("code-expired", "error", "Code expired", "CODE_EXPIRED", undefined, "Code expired"),
  turn("code-locked", "error", "Code locked", "CODE_LOCKED", undefined, "Code locked (3 wrong)"),
  turn("code-cap-reached", "error", "Code cap reached", "CODE_CAP_REACHED"),
  turn("no-match", "error", "No match", "NOT_VERIFIED", undefined, "No match / ambiguous / no contact"),
  turn("verified", "success", "Verified, invoice shown", "VERIFIED_ACCOUNT_INVOICE", undefined, "Verified"),
  turn("account-answer", "success", "Account answer", "VERIFIED_ACCOUNT_INVOICE", undefined, "Account answer"),
  turn("account-membership", "success", "Membership card", "ACCOUNT_MEMBERSHIP"),
  turn("account-warranty", "success", "Warranty card", "ACCOUNT_WARRANTY"),
  turn("dispute-handoff", "success", "Dispute handoff", "HANDOFF", undefined, "Dispute / unsupported action"),
  turn("slot-taken", "error", "Slot taken", "SLOT_TAKEN", undefined, "Slot taken at write"),
  turn("booked", "success", "Booked", "BOOKED", undefined, "Booked"),
  turn("confirm-existing-visit", "success", "Existing visit", "APPOINTMENT", undefined, "Confirm existing visit"),
  turn("fee-free-cancel", "success", "Fee-free cancel", "CANCELLED", fx.cancelledWithWrite, "Fee-free move / cancel"),
  turn("fee-bearing-change", "success", "Fee-bearing change request", "CHANGE_REQUEST", undefined, "Fee-bearing change request"),
  turn("fee-bearing-change-staffed", "success", "Change request, staffed", "CHANGE_REQUEST", fx.changeRequestStaffed),
  turn("fee-bearing-cancel", "success", "Fee-bearing cancel", "CHANGE_REQUEST", fx.changeRequestCancel, "Fee-bearing cancel"),
  turn("handoff-in-reply", "success", "Handoff in a reply", "HANDOFF"),
  turn("handoff-refund", "success", "Handoff, refund", "HANDOFF", fx.handoffRefund, "Handoff, refund"),
  turn("handoff-general-only", "partial", "Handoff, general follow-up only", "HANDOFF", fx.handoffGeneralOnly),
  person("handoff-nobody-online", "success", "Talk to a person, nobody online", "CASE_CREATED", "Handoff, nobody online"),
  person("handoff-already-open", "success", "Talk to a person, already open", "ALREADY_OPEN"),
  {
    ...person("live-queued", "success", "Talk to a person, staff on shift", "LIVE_QUEUED", "Live-queued (simulated staff on shift)", "simulated_on_shift"),
  },
  turn("failure-signal", "default", "Failure offer", "FAILURE_OFFER", undefined, "Failure signal (two misses)"),
  turn("no-current-source", "partial", "No current source", "NO_INFO", undefined, "No current source"),
  turn("partial-reply", "partial", "Answer then no information", "ANSWER_WITH_SOURCE", fx.partialReply),
  turn("answer-with-source", "default", "Answer with source", "ANSWER_WITH_SOURCE"),
  turn("limit-rate", "error", "Rate limit", "RATE_LIMITED", undefined, "Limit reached (rate, booking cap)"),
  turn("limit-booking-cap", "error", "Booking cap", "BOOKING_CAP", undefined, "Limit reached (rate, booking cap)"),
  turn("spend-cap", "error", "Spend cap", "SPEND_CAP_REACHED", undefined, "Spend cap reached"),
  {
    id: `${SLUG}.turn-timeout`, screen: "SCR-1", state: "loading", route: "/", role: "customer", label: "Turn timeout (next reply)",
    ops: { submitTurn: { sequence: [{ example: "TURN_TIMEOUT" }, { example: "ANSWER_WITH_SOURCE" }] } },
    notes: "Send any message; Try again gets a normal answer",
  },
  turn("busy", "loading", "Busy", "BUSY"),
  turn("ai-paused", "success", "Assistant paused", "AI_PAUSED"),
  {
    id: `${SLUG}.session-ended-block`, screen: "SCR-1", state: "disabled", route: "/", role: "customer", label: "Session ended block",
    ops: { getChatThread: { example: "ENDED_BLOCK" } }, notes: "Reload the page; the chat resumes from the thread read",
  },
];

export const screenScenarios: ScreenScenarios = { complete: false, scenarios };
