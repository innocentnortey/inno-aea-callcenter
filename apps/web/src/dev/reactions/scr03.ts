import type { Reaction } from "../scenarios/types";

// setStaffing has only TURNED_ON and TURNED_OFF_WITH_WAITING (no "off, nobody waiting").
// The mock picks an example without reading the body, so after each write the next write is the opposite one.
// The shared reaction already moves world.staffing from the request body.
export const reactions: Reaction[] = [
  { when: { op: "setStaffing", example: "TURNED_ON" }, then: (ctx) => ctx.setForce("setStaffing", { example: "TURNED_OFF_WITH_WAITING" }) },
  { when: { op: "setStaffing", example: "TURNED_OFF_WITH_WAITING" }, then: (ctx) => ctx.setForce("setStaffing", { example: "TURNED_ON" }) },
];
