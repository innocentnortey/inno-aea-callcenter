import type { Reaction } from "../scenarios/types";

// FLOW-12: a reset clears every code. Source example: listDemoInbox EMPTY.
// FLOW-3: the chat sending a code puts one in the inbox. Source example: listDemoInbox ONE_ACTIVE.
export const reactions: Reaction[] = [
  { when: { op: "resetDemo", status: 200 }, then: (ctx) => ctx.setForce("listDemoInbox", { example: "EMPTY" }) },
  { when: { op: "submitTurn", example: "CODE_SENT" }, then: (ctx) => ctx.setForce("listDemoInbox", { example: "ONE_ACTIVE" }) },
];
